import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import AcrylicStone, QuartzStone, StoneImage

from ._parser_utils import emit, normalize_model_payload


SOURCE_URL = "https://primax.pro/bitrix/catalog_export/export_BjM.xml"
SITE_URL = "https://primax.pro/"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PrimaxStoneImporter/1.0)"}
REQUEST_TIMEOUT = 30

QUARTZ_CATEGORY_ID = "2"
ACRYLIC_CATEGORY_ID = "1"

QUARTZ_ABOUT_BRAND = (
    "Primax — это премиальный бренд искусственного камня и кварцевого агломерата из Южной Кореи, из которого изготавливают долговечные столешницы, подоконники и мебель. Внешне материал идеально повторяет текстуру дорогого мрамора, но при этом он гораздо прочнее, не впитывает жидкости, не боится пятен от кофе или вина и полностью безопасен для продуктов."
)
ACRYLIC_ABOUT_BRAND = (
    "Primax — это премиальный бренд искусственного камня и кварцевого агломерата из Южной Кореи, из которого изготавливают долговечные столешницы, подоконники и мебель. Внешне материал идеально повторяет текстуру дорогого мрамора, но при этом он гораздо прочнее, не впитывает жидкости, не боится пятен от кофе или вина и полностью безопасен для продуктов."
)


class Command(BaseCommand):
    help = "Импортирует кварцевый и акриловый камень Primax из XML-фида."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=SOURCE_URL,
            help="URL или локальный путь к XML-файлу.",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Не скачивать preview и дополнительные изображения.",
        )
        parser.add_argument(
            "--test-mode",
            action="store_true",
            help="Тестовый режим: обрабатываются только первые 5 offer из XML.",
        )

    def handle(self, *args, **options):
        source = options["source"]
        skip_images = options["skip_images"]
        test_mode = options["test_mode"]

        root = self._load_root(source)
        offers = root.findall(".//offers/offer")
        if test_mode:
            original_count = len(offers)
            offers = offers[:5]
            emit(
                self.stdout.write,
                "INFO",
                f"Включён test-mode: будут обработаны только первые 5 offer из {original_count}",
            )

        quartz_count = 0
        acrylic_count = 0
        skipped_count = 0

        for index, offer in enumerate(offers, start=1):
            category_id = (offer.findtext("categoryId") or "").strip()
            article_hint = (offer.findtext("model") or "").strip() or (offer.get("id") or "").strip()
            emit(self.stdout.write, "INFO", f"[{index}/{len(offers)}] Обработка offer article={article_hint or 'UNKNOWN'}")

            if category_id == QUARTZ_CATEGORY_ID:
                self._sync_offer(
                    offer=offer,
                    model_class=QuartzStone,
                    material=QuartzStone.MaterialChoices.QUARTZ,
                    brand=QuartzStone.BrandStoneChoices.PRIMAX_QUARTZ,
                    about_brand=QUARTZ_ABOUT_BRAND,
                    color_mapper=self._map_quartz_color,
                    texture_mapper=self._map_quartz_texture,
                    faktura_mapper=self._map_quartz_faktura,
                    link_serf=QuartzStone.LinkSerfChoices.PRIMAX,
                    skip_images=skip_images,
                )
                quartz_count += 1
                continue

            if category_id == ACRYLIC_CATEGORY_ID:
                self._sync_offer(
                    offer=offer,
                    model_class=AcrylicStone,
                    material=AcrylicStone.MaterialChoices.ACRYL,
                    brand=AcrylicStone.BrandStoneChoices.PRIMAX,
                    about_brand=ACRYLIC_ABOUT_BRAND,
                    color_mapper=self._map_acrylic_color,
                    texture_mapper=self._map_acrylic_texture,
                    faktura_mapper=lambda _offer, _params: None,
                    link_serf=AcrylicStone.LinkSerfChoices.PRIMAX,
                    skip_images=skip_images,
                )
                acrylic_count += 1
                continue

            skipped_count += 1
            emit(self.stdout.write, "WARN", f"Offer пропущен: неизвестный categoryId={category_id!r}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Импорт завершен: quartz={quartz_count}, acrylic={acrylic_count}, "
                f"skipped={skipped_count}, test_mode={test_mode}, skip_images={skip_images}"
            )
        )

    def _load_root(self, source):
        try:
            if source.startswith("http://") or source.startswith("https://"):
                request = Request(source, headers=REQUEST_HEADERS)
                with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                    data = response.read()
                return ET.fromstring(data)
            return ET.parse(source).getroot()
        except Exception as exc:
            raise CommandError(f"Не удалось загрузить XML из {source}: {exc}") from exc

    def _sync_offer(
        self,
        *,
        offer,
        model_class,
        material,
        brand,
        about_brand,
        color_mapper,
        texture_mapper,
        faktura_mapper,
        link_serf,
        skip_images,
    ):
        params = self._get_params(offer)
        raw_name = (offer.findtext("name") or "").strip()
        base_article = (offer.findtext("model") or "").strip() or (offer.get("id") or "").strip()
        if not base_article:
            raise CommandError("У offer отсутствует model/id, не из чего собрать article.")
        article = f"{base_article}_primax"

        emit(self.stdout.write, "INFO", f"Подготовка payload для {model_class.__name__} article={article}")
        raw_defaults = {
            "name_stone": self._build_name(raw_name, base_article),
            "abt_prise": None,
            "material": material,
            "country": None,
            "thickness": self._parse_thickness(raw_name),
            "about_brand": about_brand,
            "archive": offer.get("available") != "true",
            "brand_stone": brand,
            "color": color_mapper(params),
            "texture": texture_mapper(params),
            "faktura": faktura_mapper(offer, params),
            "link_serf": link_serf,
        }
        defaults = normalize_model_payload(
            model_class,
            raw_defaults,
            self.stdout.write,
            choice_aliases={
                "link_serf": {
                    "Primax": AcrylicStone.LinkSerfChoices.PRIMAX,
                    "PrimaxQuartz": QuartzStone.LinkSerfChoices.PRIMAX,
                }
            },
        )

        with transaction.atomic():
            stone, created = model_class.objects.get_or_create(article=article, defaults=defaults)
            if created:
                emit(self.stdout.write, "INFO", f"Создан stone article={article} id={stone.pk}")
            else:
                for field_name, value in defaults.items():
                    setattr(stone, field_name, value)
                stone.save()
                emit(self.stdout.write, "INFO", f"Обновлён stone article={article} id={stone.pk}")

            if skip_images:
                emit(self.stdout.write, "INFO", f"Изображения пропущены для article={article}")
                return

            image_urls = self._collect_image_urls(offer, params)
            if not image_urls:
                emit(self.stdout.write, "WARN", f"Не найдены изображения для article={article}")
                return

            preview_url = image_urls[0]
            example_urls = image_urls[1:]

            self._replace_preview(stone, article, preview_url)
            deleted_count = self._delete_example_images(stone)
            emit(self.stdout.write, "INFO", f"Удалено старых StoneImage: {deleted_count}")

            for index, image_url in enumerate(example_urls, start=1):
                self._create_example_image(stone, article, index, image_url)

    def _get_params(self, offer):
        params = {}
        multi_params = {}
        for param in offer.findall("param"):
            key = (param.attrib.get("name") or "").strip()
            value = (param.text or "").strip()
            if not key:
                continue
            params[key] = value
            multi_params.setdefault(key, []).append(value)
        params["_multi"] = multi_params
        return params

    def _build_name(self, raw_name, article):
        parts = [part.strip() for part in raw_name.split(",") if part.strip()]
        if len(parts) >= 2:
            if parts[0] == article:
                return parts[1]
            return parts[1]
        cleaned = re.sub(rf"^\s*{re.escape(article)}\s*[, -]*\s*", "", raw_name).strip()
        return cleaned or article

    def _parse_thickness(self, raw_name):
        match = re.search(r"(\d+)\s*мм", raw_name or "", flags=re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _map_quartz_color(self, params):
        color = (params.get("Цвет") or "").strip().lower()
        if "беж" in color:
            return QuartzStone.ColorChoices.BEIGE
        if "сер" in color:
            return QuartzStone.ColorChoices.GREY
        if "тем" in color:
            return QuartzStone.ColorChoices.DARK
        if "многоцвет" in color:
            return QuartzStone.ColorChoices.MULTICOLOR
        if "свет" in color:
            return QuartzStone.ColorChoices.LIGHT
        return None

    def _map_acrylic_color(self, params):
        color = (params.get("Цвет") or "").strip().lower()
        if "беж" in color:
            return AcrylicStone.ColorChoices.BEIGE
        if "сер" in color:
            return AcrylicStone.ColorChoices.GREY
        if "тем" in color:
            return AcrylicStone.ColorChoices.DARK
        if "многоцвет" in color:
            return AcrylicStone.ColorChoices.MULTICOLOR
        if "свет" in color:
            return AcrylicStone.ColorChoices.LIGHT
        return None

    def _map_quartz_texture(self, params):
        collection = (params.get("Коллекция") or "").strip()
        if collection == QuartzStone.TextureChoices.PRIMAX_QUARTZ_FRESCO:
            return QuartzStone.TextureChoices.PRIMAX_QUARTZ_FRESCO
        if collection == QuartzStone.TextureChoices.PRIMAX_QUARTZ:
            return QuartzStone.TextureChoices.PRIMAX_QUARTZ
        return None

    def _map_acrylic_texture(self, params):
        collection = (params.get("Коллекция") or "").strip()
        if collection == AcrylicStone.TextureChoices.PRIMAX_PREMIUM:
            return AcrylicStone.TextureChoices.PRIMAX_PREMIUM
        if collection == AcrylicStone.TextureChoices.PRIMAX_BASIC:
            return AcrylicStone.TextureChoices.PRIMAX_BASIC
        if collection == AcrylicStone.TextureChoices.PRIMAX_MARBLE:
            return AcrylicStone.TextureChoices.PRIMAX_MARBLE
        return None

    def _map_quartz_faktura(self, offer, _params):
        raw_name = (offer.findtext("name") or "").upper()
        if "FBP" in raw_name:
            return QuartzStone.FakturaChoices.FBP
        return QuartzStone.FakturaChoices.STANDARD

    def _collect_image_urls(self, offer, params):
        urls = []
        picture = (offer.findtext("picture") or "").strip()
        if picture:
            urls.append(urljoin(SITE_URL, picture))

        for image_path in params.get("_multi", {}).get("Дополнительные изображения", []):
            image_url = urljoin(SITE_URL, image_path)
            if image_url not in urls:
                urls.append(image_url)

        emit(self.stdout.write, "INFO", f"Найдено изображений: {len(urls)}")
        return urls

    def _replace_preview(self, stone, article, image_url):
        self._delete_field_file(stone.priview_img, f"старый preview для article={article}")
        saved_name = self._save_remote_file(
            field_file=stone.priview_img,
            storage_name=self._build_image_name(article, "preview", image_url),
            image_url=image_url,
        )
        stone.save(update_fields=["priview_img"])
        emit(self.stdout.write, "INFO", f"Сохранён preview в media: {saved_name}")

    def _delete_example_images(self, stone):
        deleted_count = 0
        for stone_image in list(stone.example_images.all()):
            self._delete_field_file(
                stone_image.image,
                f"старый StoneImage id={stone_image.pk} article={stone.article}",
            )
            stone_image.delete()
            deleted_count += 1
        return deleted_count

    def _create_example_image(self, stone, article, index, image_url):
        stone_image = StoneImage(stone=stone)
        saved_name = self._save_remote_file(
            field_file=stone_image.image,
            storage_name=self._build_image_name(article, f"example_{index}", image_url),
            image_url=image_url,
        )
        stone_image.save()
        emit(self.stdout.write, "INFO", f"Сохранён StoneImage #{index} в media: {saved_name}")

    def _save_remote_file(self, *, field_file, storage_name, image_url):
        content = self._download_binary(image_url)
        if not content:
            raise CommandError(f"Не удалось скачать изображение: {image_url}")

        field_file.save(storage_name, ContentFile(content), save=False)
        saved_name = field_file.name
        storage = field_file.storage
        if not storage.exists(saved_name):
            raise CommandError(
                f"Файл не появился в media после сохранения: url={image_url} target={saved_name}"
            )

        try:
            absolute_path = storage.path(saved_name)
        except Exception:
            absolute_path = saved_name

        emit(self.stdout.write, "INFO", f"Файл сохранён: {image_url} -> {absolute_path}")
        return saved_name

    def _delete_field_file(self, field_file, context):
        if not field_file or not field_file.name:
            return
        storage = field_file.storage
        existing_name = field_file.name
        if storage.exists(existing_name):
            storage.delete(existing_name)
            emit(self.stdout.write, "INFO", f"Удалён файл из media: {existing_name} ({context})")

    def _download_binary(self, url):
        try:
            request = Request(url, headers=REQUEST_HEADERS)
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                content = response.read()
        except Exception as exc:
            emit(self.stdout.write, "WARN", f"Ошибка скачивания {url}: {exc}")
            return None

        if not content:
            emit(self.stdout.write, "WARN", f"Пустой ответ при скачивании {url}")
            return None
        return content

    def _build_image_name(self, article, label, image_url):
        clean_article = re.sub(r"[^a-zA-Z0-9_-]+", "_", article)
        extension_match = re.search(r"(\.[a-zA-Z0-9]+)(?:\?|$)", image_url)
        extension = extension_match.group(1).lower() if extension_match else ".jpg"
        return f"{clean_article}_{label}{extension}"

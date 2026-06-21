import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin
from urllib.request import urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import AcrylicStone, QuartzStone, StoneImage
from ._parser_utils import emit, normalize_model_payload


SOURCE_URL = 'https://primax.pro/bitrix/catalog_export/export_BjM.xml'
SITE_URL = 'https://primax.pro/'

QUARTZ_CATEGORY_ID = '2'
ACRYLIC_CATEGORY_ID = '1'

QUARTZ_ABOUT_BRAND = (
    'PrimaxQuartz - линейка кварцевого камня Primax. '
    'Данные импортированы из XML-каталога поставщика.'
)
ACRYLIC_ABOUT_BRAND = (
    'Primax - линейка акрилового камня. '
    'Данные импортированы из XML-каталога поставщика.'
)


class Command(BaseCommand):
    help = 'Импортирует кварцевый и акриловый камень Primax из XML-фида.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default=SOURCE_URL,
            help='URL или локальный путь к XML-файлу.',
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Не скачивать preview и дополнительные изображения.',
        )

    def handle(self, *args, **options):
        source = options['source']
        skip_images = options['skip_images']
        root = self._load_root(source)
        offers = root.findall('.//offers/offer')

        quartz_count = 0
        acrylic_count = 0
        skipped_count = 0

        for offer in offers:
            category_id = (offer.findtext('categoryId') or '').strip()

            if category_id == QUARTZ_CATEGORY_ID:
                emit(self.stdout.write, 'INFO', f'Quartz offer article={(offer.findtext("model") or "").strip() or (offer.get("id") or "").strip()}')
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
            elif category_id == ACRYLIC_CATEGORY_ID:
                emit(self.stdout.write, 'INFO', f'Acrylic offer article={(offer.findtext("model") or "").strip() or (offer.get("id") or "").strip()}')
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
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Импорт завершен: quartz={quartz_count}, acrylic={acrylic_count}, skipped={skipped_count}'
            )
        )

    def _load_root(self, source):
        try:
            if source.startswith('http://') or source.startswith('https://'):
                with urlopen(source) as response:
                    data = response.read()
                return ET.fromstring(data)
            return ET.parse(source).getroot()
        except Exception as exc:
            raise CommandError(f'Не удалось загрузить XML из {source}: {exc}') from exc

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
        raw_name = (offer.findtext('name') or '').strip()
        article = (offer.findtext('model') or '').strip() or (offer.get('id') or '').strip()
        if not article:
            raise CommandError('У оффера отсутствует model/id, не из чего собрать article.')

        emit(self.stdout.write, 'INFO', f'Preparing payload for {model_class.__name__} article={article}')
        raw_defaults = {
            'name_stone': self._build_name(raw_name, article),
            'abt_prise': self._parse_price(offer.findtext('price')),
            'material': material,
            'country': None,
            'thickness': self._parse_thickness(raw_name),
            'about_brand': about_brand,
            'archive': offer.get('available') != 'true',
            'brand_stone': brand,
            'color': color_mapper(params),
            'texture': texture_mapper(params),
            'faktura': faktura_mapper(offer, params),
            'link_serf': link_serf,
        }
        defaults = normalize_model_payload(
            model_class,
            raw_defaults,
            self.stdout.write,
            choice_aliases={
                'link_serf': {
                    'Primax': AcrylicStone.LinkSerfChoices.PRIMAX,
                    'PrimaxQuartz': QuartzStone.LinkSerfChoices.PRIMAX,
                }
            },
        )

        with transaction.atomic():
            stone, created = model_class.objects.get_or_create(article=article, defaults=defaults)
            if not created:
                for field_name, value in defaults.items():
                    setattr(stone, field_name, value)
                stone.save()
                emit(self.stdout.write, 'INFO', f'Updated stone article={article} id={stone.pk}')
            else:
                emit(self.stdout.write, 'INFO', f'Created stone article={article} id={stone.pk}')

            if skip_images:
                emit(self.stdout.write, 'INFO', f'Skip images for article={article}')
                return

            image_urls = self._collect_image_urls(offer, params)
            if not image_urls:
                emit(self.stdout.write, 'WARN', f'No images found for article={article}')
                return

            preview_saved = self._save_preview(stone, article, image_urls[0])
            if not preview_saved:
                self.stdout.write(self.style.WARNING(f'Не удалось сохранить preview для {article}'))

            stone.example_images.all().delete()
            for index, image_url in enumerate(image_urls, start=1):
                content = self._download_binary(image_url)
                if not content:
                    continue
                stone_image = StoneImage(stone=stone)
                stone_image.image.save(
                    self._build_image_name(article, index, image_url),
                    ContentFile(content),
                    save=True,
                )

    def _get_params(self, offer):
        params = {}
        multi_params = {}
        for param in offer.findall('param'):
            key = (param.attrib.get('name') or '').strip()
            value = (param.text or '').strip()
            if not key:
                continue
            params[key] = value
            multi_params.setdefault(key, []).append(value)
        params['_multi'] = multi_params
        return params

    def _build_name(self, raw_name, article):
        parts = [part.strip() for part in raw_name.split(',') if part.strip()]
        if len(parts) >= 2:
            return f'{parts[0]}, {parts[1]}'
        return raw_name or article

    def _parse_price(self, raw_price):
        try:
            return Decimal((raw_price or '0').strip())
        except (InvalidOperation, AttributeError):
            return None

    def _parse_thickness(self, raw_name):
        match = re.search(r'(\d+)\s*мм', raw_name or '', flags=re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _map_quartz_color(self, params):
        color = (params.get('Цвет') or '').strip().lower()
        if 'беж' in color:
            return QuartzStone.ColorChoices.BEIGE
        if 'сер' in color:
            return QuartzStone.ColorChoices.GREY
        if 'тем' in color:
            return QuartzStone.ColorChoices.DARK
        if 'многоцвет' in color:
            return QuartzStone.ColorChoices.MULTICOLOR
        if 'свет' in color:
            return QuartzStone.ColorChoices.LIGHT
        return None

    def _map_acrylic_color(self, params):
        color = (params.get('Цвет') or '').strip().lower()
        if 'беж' in color:
            return AcrylicStone.ColorChoices.BEIGE
        if 'сер' in color:
            return AcrylicStone.ColorChoices.GREY
        if 'тем' in color:
            return AcrylicStone.ColorChoices.DARK
        if 'многоцвет' in color:
            return AcrylicStone.ColorChoices.MULTICOLOR
        if 'свет' in color:
            return AcrylicStone.ColorChoices.LIGHT
        return None

    def _map_quartz_texture(self, params):
        collection = (params.get('Коллекция') or '').strip()
        if collection == QuartzStone.TextureChoices.PRIMAX_QUARTZ_FRESCO:
            return QuartzStone.TextureChoices.PRIMAX_QUARTZ_FRESCO
        if collection == QuartzStone.TextureChoices.PRIMAX_QUARTZ:
            return QuartzStone.TextureChoices.PRIMAX_QUARTZ
        return None

    def _map_acrylic_texture(self, params):
        collection = (params.get('Коллекция') or '').strip()
        if collection == AcrylicStone.TextureChoices.PRIMAX_PREMIUM:
            return AcrylicStone.TextureChoices.PRIMAX_PREMIUM
        if collection == AcrylicStone.TextureChoices.PRIMAX_BASIC:
            return AcrylicStone.TextureChoices.PRIMAX_BASIC
        if collection == AcrylicStone.TextureChoices.PRIMAX_MARBLE:
            return AcrylicStone.TextureChoices.PRIMAX_MARBLE
        return None

    def _map_quartz_faktura(self, offer, _params):
        raw_name = (offer.findtext('name') or '').upper()
        if 'FBP' in raw_name:
            return QuartzStone.FakturaChoices.FBP
        return QuartzStone.FakturaChoices.STANDARD

    def _collect_image_urls(self, offer, params):
        urls = []
        picture = (offer.findtext('picture') or '').strip()
        if picture:
            urls.append(urljoin(SITE_URL, picture))

        for image_path in params.get('_multi', {}).get('Дополнительные изображения', []):
            image_url = urljoin(SITE_URL, image_path)
            if image_url not in urls:
                urls.append(image_url)
        return urls

    def _save_preview(self, stone, article, image_url):
        content = self._download_binary(image_url)
        if not content:
            return False
        stone.priview_img.save(
            self._build_image_name(article, 0, image_url),
            ContentFile(content),
            save=True,
        )
        return True

    def _download_binary(self, url):
        try:
            with urlopen(url) as response:
                return response.read()
        except Exception:
            return None

    def _build_image_name(self, article, index, image_url):
        clean_article = re.sub(r'[^a-zA-Z0-9_-]+', '_', article)
        extension_match = re.search(r'(\.[a-zA-Z0-9]+)(?:\?|$)', image_url)
        extension = extension_match.group(1) if extension_match else '.jpg'
        return f'{clean_article}_{index}{extension}'

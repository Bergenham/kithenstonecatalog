import re
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import StoneImage

from ._parser_utils import emit, normalize_model_payload


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
PREVIEW_PATTERN = re.compile(r"(?i)(?:^|[\s\-_])zoom$")


def extract_name_from_stem(stem, article):
    value = stem.strip()
    article_pattern = re.escape(article).replace("\\ ", r"\s*")
    value = re.sub(rf"^{article_pattern}(?:[\s\-_]+)?", "", value, flags=re.IGNORECASE)
    value = re.sub(r"(?i)[\s\-_]*(zoom|int[\s\-_]*\d+|\d+|sl)$", "", value)
    value = re.sub(r"[_\-]+", " ", value)
    value = re.sub(r"\s{2,}", " ", value).strip(" -_")
    return value or article.replace("-", " ").strip()


def is_preview_stem(stem):
    return PREVIEW_PATTERN.search(stem.strip()) is not None


def parse_four_digits(stem):
    match = re.match(r"^\s*(\d{4})(?:[\s\-_]+)?(.+?)?\s*$", stem)
    if not match:
        return None
    article = match.group(1)
    return article, extract_name_from_stem(stem, article)


def parse_letter_three_digits(stem):
    match = re.match(r"^\s*([A-Za-zА-Яа-я]\d{3})(?:[\s\-_]+)?(.+?)?\s*$", stem)
    if not match:
        return None
    article = match.group(1).upper()
    return article, extract_name_from_stem(stem, article)


def parse_prefixed_digits(stem):
    match = re.match(r"^\s*([A-Za-zА-Яа-я]{1,3}\d{3,4})(?:[\s\-_]+)?(.+?)?\s*$", stem)
    if not match:
        return None
    article = match.group(1).upper()
    return article, extract_name_from_stem(stem, article)


def parse_letter_dash_digits(stem):
    match = re.match(r"^\s*([A-Za-zА-Яа-я]-\d{3,4})(?:[\s\-_]+)?(.+?)?\s*$", stem)
    if not match:
        return None
    article = match.group(1).upper()
    return article, extract_name_from_stem(stem, article)


def parse_neomarm(stem):
    match = re.match(r"^\s*([A-Za-zА-Яа-я])\s*(\d{3})(?:[\s\-_]+)?(.+?)?\s*$", stem)
    if not match:
        return None
    article = f"{match.group(1).upper()}{match.group(2)}"
    raw_article = f"{match.group(1)} {match.group(2)}"
    return article, extract_name_from_stem(stem, raw_article)


class FlatBrandImportCommand(BaseCommand):
    source_dir = None
    model_class = None
    article_suffix = ""
    about_brand = "TODO: fill brand description"
    parse_article_and_name = None
    help = "Импорт камней из плоского каталога изображений."

    def add_arguments(self, parser):
        parser.add_argument("--source-dir", default=str(self.source_dir), help="Путь к каталогу с изображениями.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать, что будет импортировано, без записи в БД.",
        )
        parser.add_argument(
            "--test-mode",
            action="store_true",
            help="Тестовый режим: обрабатываются только первые 5 изображений.",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"]).expanduser()
        dry_run = options["dry_run"]
        test_mode = options["test_mode"]

        if not source_dir.exists():
            raise CommandError(f"Папка не найдена: {source_dir}")
        if not source_dir.is_dir():
            raise CommandError(f"Ожидалась папка, но получен путь к файлу: {source_dir}")
        if self.model_class is None or self.parse_article_and_name is None:
            raise CommandError("Команда настроена не полностью.")

        files = sorted(
            path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
        if not files:
            raise CommandError(f"В папке нет изображений: {source_dir}")

        if test_mode:
            original_count = len(files)
            files = files[:5]
            emit(
                self.stdout.write,
                "INFO",
                f"Включён test-mode: будут обработаны только первые 5 изображений из {original_count}",
            )

        groups = {}
        skipped_files = 0

        for path in files:
            parsed = self.parse_article_and_name(path.stem)
            if parsed is None:
                skipped_files += 1
                emit(self.stdout.write, "WARN", f"Файл пропущен: не удалось извлечь article из {path.name}")
                continue

            article_key, name_stone = parsed
            bucket = groups.setdefault(
                article_key,
                {
                    "name_stone": name_stone,
                    "preview": None,
                    "examples": [],
                    "source_names": [],
                },
            )
            if not bucket["name_stone"] and name_stone:
                bucket["name_stone"] = name_stone

            bucket["source_names"].append(path.name)
            if is_preview_stem(path.stem):
                if bucket["preview"] is not None:
                    emit(
                        self.stdout.write,
                        "WARN",
                        f"Для article={article_key} найден второй preview {path.name}, заменяю {bucket['preview'].name}",
                    )
                bucket["preview"] = path
            else:
                bucket["examples"].append(path)

        emit(self.stdout.write, "INFO", f"Найдено групп: {len(groups)}, пропущено файлов: {skipped_files}")

        created_count = 0
        updated_count = 0
        skipped_groups = 0
        total_groups = len(groups)

        for index, article_key in enumerate(sorted(groups), start=1):
            group = groups[article_key]
            article = f"{article_key}{self.article_suffix}"
            name_stone = group["name_stone"]

            emit(self.stdout.write, "INFO", f"[{index}/{total_groups}] Обработка article={article}")

            if not name_stone:
                skipped_groups += 1
                emit(self.stdout.write, "WARN", f"Группа {article} пропущена: пустое name_stone")
                continue
            if group["preview"] is None:
                skipped_groups += 1
                emit(self.stdout.write, "WARN", f"Группа {article} пропущена: не найден ZOOM")
                continue

            raw_defaults = self.build_defaults(name_stone)
            defaults = normalize_model_payload(self.model_class, raw_defaults, self.stdout.write)

            emit(
                self.stdout.write,
                "INFO",
                (
                    f"Группа {article_key}: name_stone={name_stone!r}, "
                    f"preview={group['preview'].name}, examples={len(group['examples'])}"
                ),
            )

            if dry_run:
                emit(self.stdout.write, "INFO", f"DRY RUN: {article} не записывается в БД")
                continue

            created = self.sync_group(
                article=article,
                defaults=defaults,
                preview_path=group["preview"],
                example_paths=group["examples"],
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Импорт завершён: created={created_count}, updated={updated_count}, "
                f"skipped_groups={skipped_groups}, skipped_files={skipped_files}, "
                f"dry_run={dry_run}, test_mode={test_mode}"
            )
        )

    def build_defaults(self, name_stone):
        return {
            "name_stone": name_stone,
            "abt_prise": None,
            "material": None,
            "country": None,
            "thickness": None,
            "about_brand": self.about_brand,
            "archive": False,
            "brand_stone": None,
            "color": None,
            "texture": None,
            "faktura": None,
            "link_serf": None,
        }

    def sync_group(self, *, article, defaults, preview_path, example_paths):
        with transaction.atomic():
            stone, created = self.model_class.objects.get_or_create(article=article, defaults=defaults)
            if created:
                emit(self.stdout.write, "INFO", f"Создан объект article={article} id={stone.pk}")
            else:
                for field_name, value in defaults.items():
                    setattr(stone, field_name, value)
                stone.save()
                emit(self.stdout.write, "INFO", f"Обновлён объект article={article} id={stone.pk}")

            self.replace_preview(stone, article, preview_path)
            emit(self.stdout.write, "INFO", f"Сохранён preview в media: {preview_path.name}")

            deleted_count = self.delete_example_images(stone)
            emit(self.stdout.write, "INFO", f"Удалено старых StoneImage: {deleted_count}")

            for index, example_path in enumerate(sorted(example_paths), start=1):
                self.create_example_image(stone, article, index, example_path)
                emit(self.stdout.write, "INFO", f"Сохранён StoneImage #{index} в media: {example_path.name}")

        return created

    def build_storage_name(self, article, label, suffix):
        return f"{article}_{label}{suffix.lower()}"

    def replace_preview(self, stone, article, preview_path):
        self.delete_field_file(stone.priview_img, f"старый preview для article={article}")
        saved_name = self.save_binary_file(
            field_file=stone.priview_img,
            storage_name=self.build_storage_name(article, "preview", preview_path.suffix),
            source_path=preview_path,
        )
        stone.save(update_fields=["priview_img"])
        emit(self.stdout.write, "INFO", f"Preview записан в storage: {saved_name}")

    def delete_example_images(self, stone):
        deleted_count = 0
        existing_images = list(stone.example_images.all())
        for image in existing_images:
            self.delete_field_file(image.image, f"старый StoneImage id={image.pk} article={stone.article}")
            image.delete()
            deleted_count += 1
        return deleted_count

    def create_example_image(self, stone, article, index, example_path):
        stone_image = StoneImage(stone=stone)
        saved_name = self.save_binary_file(
            field_file=stone_image.image,
            storage_name=self.build_storage_name(article, f"example_{index}", example_path.suffix),
            source_path=example_path,
        )
        stone_image.save()
        emit(self.stdout.write, "INFO", f"StoneImage #{index} записан в storage: {saved_name}")

    def save_binary_file(self, *, field_file, storage_name, source_path):
        data = source_path.read_bytes()
        if not data:
            raise CommandError(f"Файл пустой и не может быть импортирован: {source_path}")

        field_file.save(storage_name, ContentFile(data), save=False)
        saved_name = field_file.name
        storage = field_file.storage
        if not storage.exists(saved_name):
            raise CommandError(f"Файл не появился в media после сохранения: source={source_path} target={saved_name}")

        try:
            absolute_path = storage.path(saved_name)
        except Exception:
            absolute_path = saved_name

        emit(self.stdout.write, "INFO", f"Файл сохранён: {source_path.name} -> {absolute_path}")
        return saved_name

    def delete_field_file(self, field_file, context):
        if not field_file or not field_file.name:
            return

        storage = field_file.storage
        existing_name = field_file.name
        if storage.exists(existing_name):
            storage.delete(existing_name)
            emit(self.stdout.write, "INFO", f"Удалён файл из media: {existing_name} ({context})")

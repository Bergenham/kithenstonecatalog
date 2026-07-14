import re
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import QuartzStone, StoneImage

from ._parser_utils import emit, normalize_model_payload


SOURCE_DIR = Path(r"D:\Project.com\САЙТ\Основная коллекция (AM)")
ABOUT_BRAND = "Etna Quartz — это крупный федеральный поставщик и производитель премиального кварцевого агломерата, выпускаемого по итальянской технологии Breton Stone. Бренд предлагает долговечный материал, состоящий на 93% из натурального кварца, и располагает широким ассортиментом (более 30 цветов), что делает его оптимальным выбором для изготовления кухонных столешниц, подоконников и облицовки."
ARTICLE_SUFFIX = "_etnaquartz"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".webm", ".mpeg", ".mpg", ".m4v"}


class Command(BaseCommand):
    help = "Импортирует QuartzStone из папок коллекции ETNA Quartz."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            default=str(SOURCE_DIR),
            help="Путь к корневой папке с коллекцией.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать, что будет импортировано, без записи в БД.",
        )
        parser.add_argument(
            "--test-mode",
            action="store_true",
            help="Тестовый режим: обрабатываются только первые 5 папок.",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"]).expanduser()
        dry_run = options["dry_run"]
        test_mode = options["test_mode"]

        if not source_dir.exists():
            raise CommandError(f"Папка не найдена: {source_dir}")
        if not source_dir.is_dir():
            raise CommandError(f"Ожидалась папка, но получен путь к файлу: {source_dir}")

        stone_dirs = sorted(path for path in source_dir.iterdir() if path.is_dir())
        if not stone_dirs:
            raise CommandError(f"В папке нет подпапок с декорами: {source_dir}")

        if test_mode:
            original_count = len(stone_dirs)
            stone_dirs = stone_dirs[:5]
            emit(
                self.stdout.write,
                "INFO",
                f"Включён test-mode: будут обработаны только первые 5 папок из {original_count}",
            )

        emit(self.stdout.write, "INFO", f"Найдено папок декоров: {len(stone_dirs)}")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for index, stone_dir in enumerate(stone_dirs, start=1):
            emit(self.stdout.write, "INFO", f"[{index}/{len(stone_dirs)}] Обработка папки {stone_dir.name}")

            parsed = self._parse_dir_name(stone_dir.name)
            if parsed is None:
                skipped_count += 1
                emit(self.stdout.write, "WARN", f"Папка пропущена: не удалось извлечь article/name из {stone_dir.name!r}")
                continue

            article, name_stone = parsed
            prepared = self._prepare_folder(stone_dir)
            if prepared is None:
                skipped_count += 1
                emit(self.stdout.write, "WARN", f"Папка {stone_dir.name!r} пропущена: preview 'zoom' не найден.")
                continue

            raw_defaults = {
                "name_stone": name_stone,
                "abt_prise": None,
                "material": QuartzStone.MaterialChoices.QUARTZ,
                "country": None,
                "thickness": None,
                "about_brand": ABOUT_BRAND,
                "archive": False,
                "brand_stone": None,
                "color": None,
                "texture": None,
                "faktura": None,
                "link_serf": None,
            }
            emit(self.stdout.write, "INFO", f"Подготовка QuartzStone article={article}")
            defaults = normalize_model_payload(QuartzStone, raw_defaults, self.stdout.write)

            emit(
                self.stdout.write,
                "INFO",
                (
                    f"Папка {stone_dir.name}: name_stone={name_stone!r}, "
                    f"preview={prepared['preview'].name}, examples={len(prepared['examples'])}, "
                    f"videos_skipped={prepared['videos_skipped']}"
                ),
            )

            if dry_run:
                emit(self.stdout.write, "INFO", f"DRY RUN: QuartzStone article={article} не записывается в БД")
                continue

            created = self._sync_folder(
                article=article,
                defaults=defaults,
                preview_path=prepared["preview"],
                example_paths=prepared["examples"],
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Импорт завершён: created={created_count}, updated={updated_count}, "
                f"skipped={skipped_count}, dry_run={dry_run}, test_mode={test_mode}"
            )
        )

    def _parse_dir_name(self, dir_name):
        match = re.match(r"^\s*(\S+)\s+(\S+)\s+-\s+(.+?)\s*$", dir_name)
        if not match:
            return None

        article_base = f"{match.group(1)}_{match.group(2)}"
        article = f"{article_base}{ARTICLE_SUFFIX}"
        name_stone = re.sub(r"\s{2,}", " ", match.group(3)).strip()
        if not article_base or not name_stone:
            return None
        return article, name_stone

    def _prepare_folder(self, stone_dir):
        preview = None
        examples = []
        videos_skipped = 0

        for path in sorted(stone_dir.iterdir(), key=lambda item: item.name.casefold()):
            if not path.is_file():
                continue

            suffix = path.suffix.lower()
            stem = path.stem.strip().casefold()

            if suffix in VIDEO_EXTENSIONS:
                videos_skipped += 1
                continue

            if suffix not in IMAGE_EXTENSIONS:
                emit(self.stdout.write, "WARN", f"Неизвестный файл пропущен: {path}")
                continue

            if stem == "zoom":
                preview = path
                continue

            examples.append(path)

        if preview is None:
            return None

        return {
            "preview": preview,
            "examples": examples,
            "videos_skipped": videos_skipped,
        }

    def _sync_folder(self, *, article, defaults, preview_path, example_paths):
        with transaction.atomic():
            stone, created = QuartzStone.objects.get_or_create(article=article, defaults=defaults)
            if created:
                emit(self.stdout.write, "INFO", f"Создан QuartzStone article={article} id={stone.pk}")
            else:
                for field_name, value in defaults.items():
                    setattr(stone, field_name, value)
                stone.save()
                emit(self.stdout.write, "INFO", f"Обновлён QuartzStone article={article} id={stone.pk}")

            self._replace_preview(stone, article, preview_path)
            deleted_count = self._delete_example_images(stone)
            emit(self.stdout.write, "INFO", f"Удалено старых StoneImage: {deleted_count}")

            for index, example_path in enumerate(example_paths, start=1):
                self._create_example_image(stone, article, index, example_path)

        return created

    def _replace_preview(self, stone, article, preview_path):
        self._delete_field_file(stone.priview_img, f"старый preview для article={article}")
        saved_name = self._save_local_file(
            field_file=stone.priview_img,
            storage_name=self._build_storage_name(article, "preview", preview_path.suffix),
            source_path=preview_path,
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

    def _create_example_image(self, stone, article, index, example_path):
        stone_image = StoneImage(stone=stone)
        saved_name = self._save_local_file(
            field_file=stone_image.image,
            storage_name=self._build_storage_name(article, f"example_{index}", example_path.suffix),
            source_path=example_path,
        )
        stone_image.save()
        emit(self.stdout.write, "INFO", f"Сохранён StoneImage #{index} в media: {saved_name}")

    def _save_local_file(self, *, field_file, storage_name, source_path):
        data = source_path.read_bytes()
        if not data:
            raise CommandError(f"Файл пустой и не может быть импортирован: {source_path}")

        field_file.save(storage_name, ContentFile(data), save=False)
        saved_name = field_file.name
        storage = field_file.storage
        if not storage.exists(saved_name):
            raise CommandError(
                f"Файл не появился в media после сохранения: source={source_path} target={saved_name}"
            )

        try:
            absolute_path = storage.path(saved_name)
        except Exception:
            absolute_path = saved_name

        emit(self.stdout.write, "INFO", f"Файл сохранён: {source_path.name} -> {absolute_path}")
        return saved_name

    def _delete_field_file(self, field_file, context):
        if not field_file or not field_file.name:
            return

        storage = field_file.storage
        existing_name = field_file.name
        if storage.exists(existing_name):
            storage.delete(existing_name)
            emit(self.stdout.write, "INFO", f"Удалён файл из media: {existing_name} ({context})")

    def _build_storage_name(self, article, label, suffix):
        return f"{article}_{label}{suffix.lower()}"

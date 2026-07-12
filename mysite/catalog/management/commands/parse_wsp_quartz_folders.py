import re
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import QuartzStone, StoneImage

from ._parser_utils import emit, normalize_model_payload


SOURCE_DIR = Path(r"D:\Project.com\WSP STONE ДЕКОРЫ")
ABOUT_BRAND = "WSP Stone — это бренд надежного искусственного камня (кварцевого агломерата), сочетающий в себе природную эстетику и передовые технологии. Благодаря высокой прочности, термостойкости и гигиеничности, материал идеально подходит для создания стильных и долговечных кухонных столешниц, подоконников и лестниц"
ARTICLE_SUFFIX = "_WSP"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".webm", ".mpeg", ".mpg", ".m4v"}


class Command(BaseCommand):
    help = "Импортирует QuartzStone и StoneImage из папок WSP STONE."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            default=str(SOURCE_DIR),
            help="Путь к корневой папке с декорами WSP STONE.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать, что будет импортировано, без записи в БД.",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"]).expanduser()
        dry_run = options["dry_run"]

        if not source_dir.exists():
            raise CommandError(f"Папка не найдена: {source_dir}")
        if not source_dir.is_dir():
            raise CommandError(f"Ожидалась папка, но получен путь к файлу: {source_dir}")

        stone_dirs = sorted(path for path in source_dir.iterdir() if path.is_dir())
        if not stone_dirs:
            raise CommandError(f"В папке нет подпапок с декорами: {source_dir}")

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

            parsed_article, name_stone = parsed
            article = f"{parsed_article}{ARTICLE_SUFFIX}"
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
                f"Импорт завершён: created={created_count}, updated={updated_count}, skipped={skipped_count}, dry_run={dry_run}"
            )
        )

    def _parse_dir_name(self, dir_name):
        match = re.match(r"^\s*(\S+)\s+(.+?)\s*$", dir_name)
        if not match:
            return None
        article = match.group(1).strip()
        name_stone = re.sub(r"\s{2,}", " ", match.group(2)).strip()
        if not article or not name_stone:
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
                emit(self.stdout.write, "WARN", f"Неизвестный файл пропущен: {path.name}")
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

            with preview_path.open("rb") as preview_file:
                stone.priview_img.save(
                    self._build_storage_name(article, "preview", preview_path.suffix),
                    File(preview_file),
                    save=True,
                )
            emit(self.stdout.write, "INFO", f"Сохранён preview: {preview_path.name}")

            deleted_count, _ = stone.example_images.all().delete()
            emit(self.stdout.write, "INFO", f"Удалено старых StoneImage: {deleted_count}")

            for index, example_path in enumerate(example_paths, start=1):
                with example_path.open("rb") as example_file:
                    stone_image = StoneImage(stone=stone)
                    stone_image.image.save(
                        self._build_storage_name(article, f"example_{index}", example_path.suffix),
                        File(example_file),
                        save=True,
                    )
                emit(self.stdout.write, "INFO", f"Сохранён StoneImage #{index}: {example_path.name}")

        return created

    def _build_storage_name(self, article, label, suffix):
        return f"{article}_{label}{suffix.lower()}"

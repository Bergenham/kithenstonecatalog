"""Validate a complete bundle before writing, then commit DB and new Storage files.

Existing file names are never overwritten/deleted. Only files allocated by this run
are removed on failure; a failed cleanup is reported with its exact storage name.
"""

import csv
import hashlib
import logging
import re
import tempfile
import warnings
from dataclasses import dataclass
from io import StringIO
from pathlib import Path, PurePosixPath
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import connection, transaction
from PIL import Image, UnidentifiedImageError

from .models import AcrylicStone, CeramicsStone, NaturalStone, QuartzStone, Stone, StoneImage


logger = logging.getLogger(__name__)
ENTITY_TYPES = {
    'quartz': (QuartzStone, Stone.MaterialChoices.QUARTZ),
    'acrylic': (AcrylicStone, Stone.MaterialChoices.ACRYL),
    'natural': (NaturalStone, Stone.MaterialChoices.NATURAL),
    'ceramics': (CeramicsStone, Stone.MaterialChoices.CERAMIC),
}
REQUIRED_ENTITY_FIELDS = {'entity_type', 'article', 'name_stone', 'preview'}
OPTIONAL_ENTITY_FIELDS = {
    'abt_prise', 'country', 'thickness', 'about_brand', 'archive',
    'brand_stone', 'color', 'texture', 'faktura', 'link_serf',
}
EXAMPLE_FIELDS = {'example_id', 'article', 'image'}
IMAGE_TYPES = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10000
MAX_PIXELS = 40_000_000
CHUNK_SIZE = 64 * 1024


class BundleError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(errors))


@dataclass
class Report:
    entities_created: int = 0
    entities_updated: int = 0
    entities_unchanged: int = 0
    examples_created: int = 0
    examples_updated: int = 0
    examples_unchanged: int = 0


@dataclass
class StagedImage:
    path: Path
    digest: str
    suffix: str


@dataclass
class PlannedRecord:
    instance: object
    image_field: str
    image: StagedImage
    action: str
    location: str
    image_changed: bool


class CatalogImporter:
    def __init__(self, root, delimiter=','):
        self.root = Path(root).resolve()
        self.delimiter = delimiter
        self.errors = []
        self.created_files = []
        self.images = {}
        self.total_bytes = 0
        self.committed = False
        self.rollback_confirmed = True

    def run(self, dry_run=False):
        if connection.in_atomic_block:
            raise BundleError(['Импорт должен запускаться вне внешней транзакции.'])
        self.errors = []
        self.created_files = []
        self.images = {}
        self.total_bytes = 0
        self.committed = False
        self.rollback_confirmed = True
        try:
            with tempfile.TemporaryDirectory(prefix='catalog-import-', ignore_cleanup_errors=True) as staging:
                self.staging = Path(staging)
                entities = self.read_csv('entities.csv', REQUIRED_ENTITY_FIELDS,
                                         OPTIONAL_ENTITY_FIELDS)
                examples = self.read_csv('examples.csv', EXAMPLE_FIELDS)
                # Both CSVs and all referenced images are checked before DB writes.
                with transaction.atomic():
                    if connection.vendor == 'postgresql' and not dry_run:
                        # Serialize this command across processes, including new IDs
                        # for which select_for_update cannot yet acquire a row lock.
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [472018236])
                    entity_plan, parents = self.plan_entities(entities)
                    example_plan = self.plan_examples(examples, parents)
                    if self.errors:
                        raise BundleError(self.errors)
                    report = self.report(entity_plan, example_plan)
                    if not dry_run:
                        self.apply(entity_plan, example_plan)
                self.committed = True
                return report
        except BaseException as exc:
            cleanup_errors = [] if self.committed else self.cleanup()
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                for error in cleanup_errors:
                    logger.error(error)
                raise
            errors = exc.errors if isinstance(exc, BundleError) else [
                f'Ошибка операции: {type(exc).__name__}: {exc}'
            ]
            raise BundleError(errors + cleanup_errors) from exc

    def package_path(self, name):
        # Enforce portable forward-slash paths. Reject Windows drives, UNC paths,
        # traversal, alternate data streams and symlinks (even pointing inside).
        if not name or '\\' in name or ':' in name or any(ord(c) < 32 for c in name):
            raise ValueError(f'Недопустимый относительный путь: {name!r}')
        relative = PurePosixPath(name)
        if relative.is_absolute() or any(part in {'', '.', '..'} for part in name.split('/')):
            raise ValueError(f'Путь выходит за пределы пакета или не нормализован: {name!r}')
        current = self.root
        for part in relative.parts:
            current = current / part
            if current.is_symlink() or current.is_junction():
                raise ValueError(f'Символические ссылки и junction запрещены: {name!r}')
        resolved = current.resolve(strict=True)
        if not resolved.is_relative_to(self.root) or not resolved.is_file():
            raise ValueError(f'Ожидался файл внутри пакета: {name!r}')
        return resolved

    def read_csv(self, filename, required, optional=frozenset()):
        rows = []
        try:
            path = self.package_path(filename)
            if path.stat().st_size > MAX_CSV_BYTES:
                raise ValueError('CSV превышает 5 MiB')
            with path.open('rb') as source:
                data = source.read(MAX_CSV_BYTES + 1)
            if len(data) > MAX_CSV_BYTES:
                raise ValueError('CSV превышает 5 MiB')
            with StringIO(data.decode('utf-8-sig'), newline='') as stream:
                reader = csv.DictReader(stream, delimiter=self.delimiter, strict=True)
                headers = reader.fieldnames or []
                if len(headers) != len(set(headers)) or not required.issubset(headers):
                    raise ValueError(f'Нужны уникальные колонки: {", ".join(sorted(required))}')
                unknown = set(headers) - required - optional
                if unknown:
                    raise ValueError(f'Неизвестные колонки: {", ".join(sorted(unknown))}')
                seen = set()
                key = 'article' if filename == 'entities.csv' else 'example_id'
                for row_number, row in enumerate(reader, start=1):
                    location = f'{filename}:{reader.line_num}'
                    if row_number > MAX_ROWS:
                        raise ValueError(f'CSV содержит больше {MAX_ROWS} записей')
                    if None in row or any(value is None for value in row.values()):
                        self.errors.append(f'{location}: число значений не совпадает с колонками')
                        continue
                    row = {field: value.strip() for field, value in row.items()}
                    if not any(row.values()):
                        continue
                    row['_location'] = location
                    if not row[key] or row[key] in seen:
                        self.errors.append(f'{location}: пустой или повторный {key}: {row[key]!r}')
                        continue
                    seen.add(row[key])
                    rows.append(row)
        except (OSError, ValueError, UnicodeError, csv.Error) as exc:
            self.errors.append(f'{filename}: {exc}')
        return rows

    def stage_image(self, name):
        if name in self.images:
            return self.images[name]
        source = self.package_path(name)
        suffix = source.suffix.lower()
        if suffix not in IMAGE_TYPES:
            raise ValueError('Изображение должно быть JPEG, PNG или WebP')
        if source.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError('Изображение превышает 20 MiB')
        staged = self.staging / uuid4().hex
        digest = hashlib.sha256()
        size = 0
        with source.open('rb') as stream, staged.open('xb') as destination:
            for chunk in iter(lambda: stream.read(CHUNK_SIZE), b''):
                size += len(chunk)
                self.total_bytes += len(chunk)
                if size > MAX_IMAGE_BYTES or self.total_bytes > MAX_TOTAL_BYTES:
                    raise ValueError('Превышен лимит изображения (20 MiB) или пакета (512 MiB)')
                digest.update(chunk)
                destination.write(chunk)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(staged, formats=['JPEG', 'PNG', 'WEBP']) as image:
                    if image.format != IMAGE_TYPES[suffix]:
                        raise ValueError('Расширение изображения не соответствует содержимому')
                    if image.width * image.height > MAX_PIXELS or getattr(image, 'is_animated', False):
                        raise ValueError('Изображение превышает 40 мегапикселей или анимировано')
                    image.verify()
                # verify() alone does not decode all pixel data (e.g. truncated JPEG).
                with Image.open(staged, formats=['JPEG', 'PNG', 'WEBP']) as image:
                    image.load()
        except (OSError, UnidentifiedImageError, Image.DecompressionBombWarning,
                Image.DecompressionBombError) as exc:
            raise ValueError(f'Повреждённое или небезопасное изображение: {name}') from exc
        result = StagedImage(staged, digest.hexdigest(), suffix)
        self.images[name] = result
        return result

    def image_changed(self, field_file, staged):
        if not field_file:
            return True
        digest = hashlib.sha256()
        try:
            with field_file.storage.open(field_file.name, 'rb') as stream:
                for chunk in iter(lambda: stream.read(CHUNK_SIZE), b''):
                    digest.update(chunk)
        except FileNotFoundError:
            return True
        return digest.hexdigest() != staged.digest

    def plan_entities(self, rows):
        plan, parents = [], {}
        for row in rows:
            try:
                if row['entity_type'] not in ENTITY_TYPES:
                    raise ValueError('entity_type: разрешены quartz, acrylic, natural, ceramics')
                model, material = ENTITY_TYPES[row['entity_type']]
                existing = Stone.objects.filter(article=row['article']).first()
                if existing:
                    # Changing a subtype would leave another child table behind.
                    if not model.objects.filter(pk=existing.pk).exists():
                        raise ValueError('Артикул уже существует у другого типа камня')
                    instance = model.objects.select_for_update().get(pk=existing.pk)
                    other_types = [cls for cls, _ in ENTITY_TYPES.values() if cls != model]
                    if any(cls.objects.filter(pk=existing.pk).exists() for cls in other_types):
                        raise ValueError('У камня несколько дочерних типов; требуется ручная проверка')
                else:
                    instance = model(article=row['article'])
                before = {field: getattr(instance, field)
                          for field in OPTIONAL_ENTITY_FIELDS | {'name_stone', 'material'}}
                instance.name_stone = row['name_stone']
                instance.material = material
                for field in OPTIONAL_ENTITY_FIELDS & row.keys():
                    value = row[field]
                    if field == 'archive':
                        if value.lower() not in {'true', 'false', '1', '0'}:
                            raise ValueError('archive: ожидается true, false, 1 или 0')
                        value = value.lower() in {'true', '1'}
                    elif not value:
                        value = None
                    if field == 'thickness' and value is not None and not re.fullmatch(r'[0-9]+', value):
                        raise ValueError('thickness: ожидается целое число миллиметров')
                    setattr(instance, field, value)
                staged = self.stage_image(row['preview'])
                changed = self.image_changed(instance.priview_img, staged)
                # Validate the model, including inherited field validators/choices,
                # without assigning the package path as a persistent Storage name.
                old_name = instance.priview_img.name
                instance.priview_img = 'stones/import-validation' + staged.suffix
                instance.full_clean()
                instance.priview_img = old_name
                action = 'created' if existing is None else (
                    'updated' if changed or any(getattr(instance, key) != value
                                              for key, value in before.items()) else 'unchanged'
                )
                plan.append(PlannedRecord(instance, 'priview_img', staged, action,
                                          row['_location'], changed))
                parents[row['article']] = instance
            except (ValueError, OSError, ValidationError) as exc:
                self.errors.append(f'{row["_location"]}: {exc}')
        return plan, parents

    def plan_examples(self, rows, parents):
        plan = []
        for row in rows:
            try:
                if not row['article'] or not row['example_id']:
                    raise ValueError('Обязательны article и example_id')
                parent = parents.get(row['article'])
                if parent is None:
                    parent = Stone.objects.select_for_update().filter(article=row['article']).first()
                if parent is None:
                    raise ValueError(f'Родитель с article={row["article"]!r} не найден')
                instance = StoneImage.objects.select_for_update().filter(import_id=row['example_id']).first()
                existing = instance is not None
                if existing and (parent.pk is None or instance.stone_id != parent.pk):
                    raise ValueError('example_id уже принадлежит другому камню; перенос запрещён')
                if not existing:
                    instance = StoneImage(import_id=row['example_id'])
                staged = self.stage_image(row['image'])
                changed = self.image_changed(instance.image, staged)
                old_name = instance.image.name
                instance.image = 'stones/import-validation' + staged.suffix
                instance.stone = parent
                # A new parent has no PK yet. Its own full_clean ran above;
                # the real FK is assigned/checked when saving after that parent.
                instance.full_clean(exclude=['stone'])
                instance.image = old_name
                action = 'created' if not existing else 'updated' if changed else 'unchanged'
                plan.append(PlannedRecord(instance, 'image', staged, action,
                                          row['_location'], changed))
            except (ValueError, OSError, ValidationError) as exc:
                self.errors.append(f'{row["_location"]}: {exc}')
        return plan

    @staticmethod
    def report(entities, examples):
        report = Report()
        for prefix, plan in [('entities', entities), ('examples', examples)]:
            for record in plan:
                key = f'{prefix}_{record.action}'
                setattr(report, key, getattr(report, key) + 1)
        return report

    def apply(self, entities, examples):
        for record in entities + examples:
            if record.action == 'unchanged':
                continue
            try:
                if record.image_changed:
                    self.save_image(record)
                record.instance.save()
            except Exception as exc:
                raise BundleError([f'{record.location}: ошибка сохранения: {exc}']) from exc

    def save_image(self, record):
        field_file = getattr(record.instance, record.image_field)
        storage = field_file.storage
        filename = uuid4().hex + record.image.suffix
        target = field_file.field.generate_filename(record.instance, filename)
        # Pre-register our unique target to remove even a partial write that raises.
        # No shared/previous name is ever passed to Storage.save().
        if storage.exists(target):
            raise ValueError('Коллизия нового имени файла; повторите импорт')
        self.created_files.append((storage, target))
        with record.image.path.open('rb') as stream:
            actual = storage.save(target, File(stream), max_length=field_file.field.max_length)
        if actual != target:
            self.created_files.append((storage, actual))
        setattr(record.instance, record.image_field, actual)

    def cleanup(self):
        errors = []
        for storage, name in reversed(self.created_files):
            try:
                # A lost COMMIT acknowledgement is ambiguous: never remove a
                # file still referenced by the DB, or when the DB is unavailable.
                referenced = (Stone.objects.filter(priview_img=name).exists()
                              or StoneImage.objects.filter(image=name).exists())
                if referenced:
                    self.rollback_confirmed = False
                    errors.append(f'Новый файл {name!r} уже связан с записью БД; сохранён. '
                                  'Проверьте результат COMMIT перед повторным импортом.')
                    continue
            except Exception as exc:
                self.rollback_confirmed = False
                errors.append(f'Не удалось проверить ссылки БД для нового файла {name!r}; '
                              f'файл сохранён: {exc}')
                continue
            try:
                storage.delete(name)
            except Exception as exc:
                errors.append(f'Не удалось удалить новый файл {name!r}: {exc}')
        return errors

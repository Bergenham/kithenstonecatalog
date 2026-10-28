import csv
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, IntegrityError, connection
from django.test import TransactionTestCase, override_settings
from PIL import Image

from .catalog_import import CatalogImporter
from .models import AcrylicStone, CeramicsStone, NaturalStone, QuartzStone, Stone, StoneImage


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class ImportCatalogTests(TransactionTestCase):
    def setUp(self):
        # Storage is attached to model fields at import time; settings alone do
        # not give each test a fresh instance of that cached backend.
        storage = InMemoryStorage()
        for model, field in [(Stone, 'priview_img'), (StoneImage, 'image')]:
            self.enterContext(patch.object(model._meta.get_field(field), 'storage', storage))
        self.temp = TemporaryDirectory(prefix='catalog-bundle-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image_bytes = self.make_image('red')
        self.write_image('images/entity_001/preview.jpg', self.image_bytes)
        self.write_image('images/entity_001/example_01.jpg', self.make_image('blue'))
        self.write_image('images/entity_001/example_02.png', self.make_image('green', 'PNG'))
        self.entities = [{
            'entity_type': 'quartz', 'article': 'Q-001', 'name_stone': 'Test quartz',
            'preview': 'images/entity_001/preview.jpg',
            'abt_prise': '12345.67', 'country': 'Чехия', 'thickness': '20',
            'brand_stone': 'Technistone', 'archive': 'false',
        }]
        self.examples = [
            {'example_id': 'Q-001-kitchen', 'article': 'Q-001',
             'image': 'images/entity_001/example_01.jpg'},
            {'example_id': 'Q-001-bathroom', 'article': 'Q-001',
             'image': 'images/entity_001/example_02.png'},
        ]
        self.write_bundle()

    @staticmethod
    def make_image(color, format='JPEG'):
        output = BytesIO()
        Image.new('RGB', (8, 8), color).save(output, format=format)
        return output.getvalue()

    def write_image(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def write_csv(self, filename, rows, fields):
        with (self.root / filename).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def write_bundle(self):
        fields = list(self.entities[0]) if self.entities else [
            'entity_type', 'article', 'name_stone', 'preview'
        ]
        self.write_csv('entities.csv', self.entities, fields)
        self.write_csv('examples.csv', self.examples, ['example_id', 'article', 'image'])

    def run_import(self, **options):
        output = StringIO()
        call_command('import_catalog', str(self.root), stdout=output, stderr=StringIO(), **options)
        return output.getvalue()

    def stored_files(self):
        storage = Stone._meta.get_field('priview_img').storage
        result = []

        def walk(path):
            dirs, files = storage.listdir(path)
            result.extend(f'{path}/{name}'.lstrip('/') for name in files)
            for directory in dirs:
                walk(f'{path}/{directory}'.lstrip('/'))

        walk('')
        return sorted(result)

    def test_new_stone_with_preview_and_multiple_examples(self):
        output = self.run_import()

        stone = QuartzStone.objects.get(article='Q-001')
        self.assertEqual(stone.material, Stone.MaterialChoices.QUARTZ)
        self.assertEqual(str(stone.abt_prise), '12345.67')
        self.assertEqual(stone.example_images.count(), 2)
        self.assertEqual(stone.priview_img.read(), self.image_bytes)
        self.assertTrue(stone.priview_img.name.startswith('stones/quartz/previews/'))
        self.assertEqual(len(self.stored_files()), 3)
        self.assertIn('объекты создано=1', output)
        self.assertIn('примеры создано=2', output)

    def test_dry_run_does_not_write_database_or_storage(self):
        with patch.object(InMemoryStorage, 'save', side_effect=AssertionError('Storage write')):
            output = self.run_import(dry_run=True)

        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(StoneImage.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])
        self.assertIn('DRY-RUN', output)
        self.assertIn('примеры создано=2', output)

    def test_preview_is_mandatory_even_on_update(self):
        for value in ['', 'images/missing.jpg']:
            with self.subTest(value=value):
                self.entities[0]['preview'] = value
                self.write_bundle()
                with self.assertRaises(CommandError):
                    self.run_import()
                self.assertEqual(Stone.objects.count(), 0)
                self.assertEqual(self.stored_files(), [])

    def test_nonexistent_parent_cancels_the_entire_bundle(self):
        self.examples[0]['article'] = 'NOT-FOUND'
        self.write_bundle()
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_repeated_import_does_not_create_records_or_files(self):
        self.run_import()
        before = self.stored_files()
        ids = list(StoneImage.objects.values_list('pk', flat=True))

        output = self.run_import()

        self.assertEqual(Stone.objects.count(), 1)
        self.assertEqual(list(StoneImage.objects.values_list('pk', flat=True)), ids)
        self.assertEqual(before, self.stored_files())
        self.assertIn('объекты создано=0, обновлено=0, без изменений=1', output)
        self.assertIn('примеры создано=0, обновлено=0, без изменений=2', output)

    def test_importer_can_be_reused_without_stale_staged_files(self):
        importer = CatalogImporter(self.root)
        importer.run(dry_run=True)
        report = importer.run()
        self.assertEqual(report.entities_created, 1)
        self.assertEqual(StoneImage.objects.count(), 2)

    def test_update_changes_fields_and_images_without_replacing_ids(self):
        self.run_import()
        stone = QuartzStone.objects.get()
        example = StoneImage.objects.get(import_id='Q-001-kitchen')
        old_preview, old_example = stone.priview_img.name, example.image.name
        self.entities[0]['name_stone'] = 'Updated quartz'
        self.entities[0]['abt_prise'] = '20000.00'
        self.write_image(self.entities[0]['preview'], self.make_image('white'))
        self.write_image(self.examples[0]['image'], self.make_image('black'))
        self.write_bundle()

        output = self.run_import()

        stone.refresh_from_db()
        example.refresh_from_db()
        self.assertEqual(stone.name_stone, 'Updated quartz')
        self.assertEqual(str(stone.abt_prise), '20000.00')
        self.assertNotEqual(stone.priview_img.name, old_preview)
        self.assertNotEqual(example.image.name, old_example)
        self.assertIn(old_preview, self.stored_files())
        self.assertIn(old_example, self.stored_files())
        self.assertEqual(Stone.objects.count(), 1)
        self.assertEqual(StoneImage.objects.count(), 2)
        self.assertIn('объекты создано=0, обновлено=1', output)
        self.assertIn('примеры создано=0, обновлено=1', output)

    def test_update_of_preexisting_stone_and_omitted_columns_are_preserved(self):
        self.run_import()
        stone = QuartzStone.objects.get()
        stone.about_brand = 'Keep existing description'
        stone.save()
        self.entities[0]['name_stone'] = 'Updated quartz'
        self.write_bundle()
        self.run_import()
        stone.refresh_from_db()
        self.assertEqual(stone.about_brand, 'Keep existing description')

    def test_absent_records_and_legacy_examples_are_not_deleted(self):
        self.run_import()
        stone = QuartzStone.objects.get()
        legacy = StoneImage(stone=stone)
        legacy.image.save('legacy.jpg', ContentFile(self.image_bytes), save=True)
        self.entities = []
        self.examples = []
        self.write_bundle()
        self.run_import()
        self.assertEqual(Stone.objects.count(), 1)
        self.assertEqual(StoneImage.objects.count(), 3)
        legacy.refresh_from_db()
        self.assertIsNone(legacy.import_id)

    def test_examples_can_reference_existing_parent_not_in_entities_csv(self):
        self.run_import()
        self.entities = []
        self.examples = [{'example_id': 'extra-example', 'article': 'Q-001',
                          'image': 'images/entity_001/example_01.jpg'}]
        self.write_bundle()
        self.run_import()
        self.assertEqual(StoneImage.objects.count(), 3)

    def test_error_mid_import_rolls_back_database_and_new_files(self):
        with patch.object(StoneImage, 'save', side_effect=IntegrityError('simulated failure')):
            with self.assertRaises(CommandError):
                self.run_import()

        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(StoneImage.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_error_after_first_example_rolls_back_all_saved_rows_and_files(self):
        original_save = StoneImage.save
        calls = []

        def save_then_fail(instance, *args, **kwargs):
            calls.append(instance.import_id)
            if len(calls) == 2:
                raise IntegrityError('second example failed')
            return original_save(instance, *args, **kwargs)

        with patch.object(StoneImage, 'save', new=save_then_fail):
            with self.assertRaises(CommandError):
                self.run_import()
        self.assertEqual(len(calls), 2)
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(StoneImage.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_commit_failure_cleans_new_files_after_database_rollback(self):
        with patch.object(connection, 'commit', side_effect=DatabaseError('COMMIT failed')):
            with self.assertRaises(CommandError):
                self.run_import()
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(StoneImage.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_cleanup_keeps_files_when_commit_result_is_uncertain(self):
        self.run_import()
        stone = QuartzStone.objects.get()
        importer = CatalogImporter(self.root)
        importer.created_files = [(stone.priview_img.storage, stone.priview_img.name)]

        errors = importer.cleanup()

        self.assertEqual(len(errors), 1)
        self.assertIn('уже связан', errors[0])
        self.assertEqual(stone.priview_img.read(), self.image_bytes)

    def test_cleanup_keeps_files_if_database_is_unavailable(self):
        storage = Stone._meta.get_field('priview_img').storage
        storage.save('pending.jpg', ContentFile(self.image_bytes))
        importer = CatalogImporter(self.root)
        importer.created_files = [(storage, 'pending.jpg')]
        with patch.object(Stone.objects, 'filter', side_effect=DatabaseError('DB offline')):
            errors = importer.cleanup()
        self.assertEqual(len(errors), 1)
        self.assertIn('файл сохранён', errors[0])
        self.assertTrue(storage.exists('pending.jpg'))

    def test_failed_update_preserves_original_database_and_files(self):
        self.run_import()
        stone = QuartzStone.objects.get()
        old_name, old_preview = stone.name_stone, stone.priview_img.name
        before = self.stored_files()
        self.entities[0]['name_stone'] = 'Changed quartz'
        self.write_image(self.entities[0]['preview'], self.make_image('yellow'))
        self.write_image(self.examples[0]['image'], self.make_image('black'))
        self.write_bundle()
        with patch.object(StoneImage, 'save', side_effect=IntegrityError('failure')):
            with self.assertRaises(CommandError):
                self.run_import()

        stone.refresh_from_db()
        self.assertEqual((stone.name_stone, stone.priview_img.name), (old_name, old_preview))
        self.assertEqual(before, self.stored_files())
        self.assertEqual(stone.priview_img.read(), self.image_bytes)

    def test_partial_storage_write_is_cleaned_on_failure(self):
        original_save = InMemoryStorage.save

        def save_then_raise(storage, name, content, **kwargs):
            original_save(storage, name, content, **kwargs)
            raise OSError('failure after write')

        with patch.object(InMemoryStorage, 'save', new=save_then_raise):
            with self.assertRaises(CommandError):
                self.run_import()
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_storage_assigned_names_are_tracked_for_rollback(self):
        original_save = InMemoryStorage.save

        def renamed_save(storage, name, content, **kwargs):
            renamed = name.replace('.', '_storage.')
            return original_save(storage, renamed, content, **kwargs)

        with patch.object(InMemoryStorage, 'save', new=renamed_save):
            with patch.object(StoneImage, 'save', side_effect=IntegrityError('failure')):
                with self.assertRaises(CommandError):
                    self.run_import()
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_cleanup_failure_reports_storage_name(self):
        errors = StringIO()
        with patch.object(StoneImage, 'save', side_effect=IntegrityError('failure')):
            with patch.object(InMemoryStorage, 'delete', side_effect=OSError('offline')):
                with self.assertRaises(CommandError):
                    call_command('import_catalog', str(self.root), stdout=StringIO(), stderr=errors)
        self.assertIn('Не удалось удалить новый файл', errors.getvalue())
        self.assertIn('stones/quartz/previews/', errors.getvalue())
        self.assertEqual(Stone.objects.count(), 0)

    def test_invalid_paths_are_rejected(self):
        for path in ['../outside.jpg', '/etc/passwd', 'C:/outside.jpg',
                     'images\\outside.jpg', 'images/../outside.jpg',
                     '//server/share.jpg', 'images/file.jpg:stream',
                     'images/./file.jpg']:
            with self.subTest(path=path):
                self.entities[0]['preview'] = path
                self.write_bundle()
                with self.assertRaises(CommandError):
                    self.run_import()
                self.assertEqual(Stone.objects.count(), 0)
                self.assertEqual(self.stored_files(), [])

    def test_symlink_is_rejected_when_platform_supports_it(self):
        target = self.root / 'images/entity_001/preview.jpg'
        link = self.root / 'linked.jpg'
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest('Creating symbolic links is not permitted on this system')
        self.entities[0]['preview'] = 'linked.jpg'
        self.write_bundle()
        with self.assertRaises(CommandError):
            self.run_import()

    def test_symlink_detection_rejects_package_before_file_read(self):
        importer = CatalogImporter(self.root)
        with patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaisesRegex(ValueError, 'Символические ссылки'):
                importer.package_path('images/entity_001/preview.jpg')

    def test_duplicate_identifiers_are_rejected(self):
        for section in ['entities', 'examples']:
            with self.subTest(section=section):
                records = getattr(self, section)
                records.append(records[0].copy())
                self.write_bundle()
                with self.assertRaises(CommandError):
                    self.run_import()
                records.pop()
                self.assertEqual(Stone.objects.count(), 0)

    def test_model_validation_rejects_invalid_values(self):
        for field, value in [('name_stone', 'tiny'), ('abt_prise', '12.00'),
                             ('abt_prise', 'NaN'), ('abt_prise', '100.123'),
                             ('country', 'Unknown'), ('thickness', '12.5'),
                             ('thickness', '-1'), ('brand_stone', 'Unknown'),
                             ('archive', 'maybe'), ('entity_type', 'unknown')]:
            with self.subTest(field=field, value=value):
                original = self.entities[0][field]
                self.entities[0][field] = value
                self.write_bundle()
                with self.assertRaises(CommandError):
                    self.run_import()
                self.entities[0][field] = original
                self.assertEqual(Stone.objects.count(), 0)

    def test_file_type_content_and_size_are_validated(self):
        cases = [('bad.svg', b'<svg/>'), ('bad.jpg', b'not an image'),
                 ('mismatch.png', self.image_bytes)]
        for path, content in cases:
            with self.subTest(path=path):
                self.write_image(path, content)
                self.entities[0]['preview'] = path
                self.write_bundle()
                with self.assertRaises(CommandError):
                    self.run_import()
        self.entities[0]['preview'] = 'images/entity_001/preview.jpg'
        self.write_bundle()
        with patch('catalog.catalog_import.MAX_IMAGE_BYTES', 10):
            with self.assertRaises(CommandError):
                self.run_import()
        with patch('catalog.catalog_import.MAX_PIXELS', 10):
            with self.assertRaises(CommandError):
                self.run_import()
        with patch('catalog.catalog_import.MAX_TOTAL_BYTES', 10):
            with self.assertRaises(CommandError):
                self.run_import()
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_subtype_change_is_rejected(self):
        self.run_import()
        self.entities[0]['entity_type'] = 'acrylic'
        self.entities[0]['brand_stone'] = 'Hanex'
        self.write_bundle()
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(AcrylicStone.objects.count(), 0)
        self.assertEqual(QuartzStone.objects.count(), 1)

    def test_example_cannot_be_reparented(self):
        self.run_import()
        self.entities[0]['article'] = 'Q-002'
        self.examples[0]['article'] = 'Q-002'
        self.write_bundle()
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(Stone.objects.count(), 1)

    def test_all_four_subtypes_and_webp_are_supported(self):
        self.entities = []
        self.examples = []
        self.write_image('preview.webp', self.make_image('white', 'WEBP'))
        for kind in ['quartz', 'acrylic', 'natural', 'ceramics']:
            self.entities.append({'entity_type': kind, 'article': kind,
                                  'name_stone': f'Test {kind}', 'preview': 'preview.webp'})
        self.write_bundle()
        self.run_import()
        for model in [QuartzStone, AcrylicStone, NaturalStone, CeramicsStone]:
            self.assertEqual(model.objects.count(), 1)
        self.assertEqual(Stone.objects.count(), 4)

    def test_bad_csv_structure_is_rejected(self):
        for content in [
            'entity_type,article,name_stone\nquartz,Q-001,Test quartz\n',
            'entity_type,article,article,name_stone,preview\n',
            'entity_type,article,name_stone,preview,typo\n',
            'entity_type,article,name_stone,preview\nquartz,Q-001\n',
        ]:
            with self.subTest(content=content):
                (self.root / 'entities.csv').write_text(content, encoding='utf-8')
                with self.assertRaises(CommandError):
                    self.run_import()
                self.assertEqual(Stone.objects.count(), 0)

    def test_csv_size_and_row_limits_are_enforced(self):
        with patch('catalog.catalog_import.MAX_CSV_BYTES', 10):
            with self.assertRaises(CommandError):
                self.run_import()
        self.examples.append(self.examples[0].copy())
        self.write_bundle()
        with patch('catalog.catalog_import.MAX_ROWS', 1):
            with self.assertRaises(CommandError):
                self.run_import()
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_dry_run_also_rejects_invalid_bundle(self):
        self.entities[0]['preview'] = 'missing.jpg'
        self.write_bundle()
        with self.assertRaises(CommandError):
            self.run_import(dry_run=True)
        self.assertEqual(Stone.objects.count(), 0)
        self.assertEqual(self.stored_files(), [])

    def test_existing_preview_is_still_required_on_update(self):
        self.run_import()
        before = self.stored_files()
        self.entities[0]['preview'] = ''
        self.write_bundle()
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(Stone.objects.count(), 1)
        self.assertEqual(before, self.stored_files())

    def test_real_demo_bundle_can_be_imported_twice(self):
        bundle = Path(__file__).resolve().parents[2] / 'examples' / 'catalog_bundle'
        call_command('import_catalog', str(bundle), stdout=StringIO())
        before = self.stored_files()
        output = StringIO()
        call_command('import_catalog', str(bundle), stdout=output)
        self.assertEqual(Stone.objects.count(), 2)
        self.assertEqual(StoneImage.objects.count(), 3)
        self.assertEqual(before, self.stored_files())
        self.assertIn('объекты создано=0, обновлено=0, без изменений=2', output.getvalue())

    def test_semicolon_delimiter_is_supported(self):
        for filename in ['entities.csv', 'examples.csv']:
            path = self.root / filename
            path.write_text(path.read_text(encoding='utf-8-sig').replace(',', ';'), encoding='utf-8')
        self.run_import(delimiter=';')
        self.assertEqual(Stone.objects.count(), 1)
        self.assertEqual(StoneImage.objects.count(), 2)

from django.core.management.base import BaseCommand, CommandError

from catalog.catalog_import import BundleError, CatalogImporter


class Command(BaseCommand):
    help = 'Импорт каталога из entities.csv, examples.csv и изображений пакета.'

    def add_arguments(self, parser):
        parser.add_argument('bundle', help='Каталог с entities.csv и examples.csv')
        parser.add_argument('--dry-run', action='store_true', help='Проверить без записи в БД и Storage')
        parser.add_argument('--delimiter', choices=[',', ';'], default=',')

    def handle(self, *args, **options):
        importer = CatalogImporter(options['bundle'], delimiter=options['delimiter'])
        try:
            report = importer.run(dry_run=options['dry_run'])
        except BundleError as exc:
            for error in exc.errors:
                self.stderr.write(error)
            counts = ('создано=0, обновлено=0' if importer.rollback_confirmed
                      else 'создано/обновлено: результат COMMIT требует проверки')
            self.stdout.write(f'Итог: {counts}; ошибочных записей/операций={len(exc.errors)}. '
                              'Импорт не завершён; проверьте сообщения об откате/очистке.')
            raise CommandError('Импорт отменён. Исправьте ошибки и повторите запуск.') from exc
        mode = 'DRY-RUN: план' if options['dry_run'] else 'Импорт завершён'
        self.stdout.write(self.style.SUCCESS(
            f'{mode}: объекты создано={report.entities_created}, '
            f'обновлено={report.entities_updated}, без изменений={report.entities_unchanged}; '
            f'примеры создано={report.examples_created}, обновлено={report.examples_updated}, '
            f'без изменений={report.examples_unchanged}; ошибок=0.'
        ))

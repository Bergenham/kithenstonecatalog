from decimal import Decimal
from django.core.management.base import BaseCommand
from django.apps import apps
from ...models import AcrylicStone

class Command(BaseCommand):
    help = 'Set abt_prise=101 and thickness=12 for all AcrylicStone instances'

    def handle(self, *args, **options):
        # Найти модель по имени в проекте
        Model = AcrylicStone
        target_price = Decimal('101.00')
        target_thickness = 12

        updated = 0
        for obj in Model.objects.all().iterator():
            obj.abt_prise = target_price
            obj.thickness = target_thickness
            obj.save(update_fields=['abt_prise', 'thickness'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Готово — обновлено {updated} экземпляров AcrylicStone.'))

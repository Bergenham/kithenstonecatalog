# from django.core.management.base import BaseCommand
# from catalog.models import QuartzStone
#
#
# class Command(BaseCommand):
#     help = 'Обновляет поле link_serf для объектов QuartzStone на основе первой буквы бренда'
#
#     def handle(self, *args, **kwargs):
#         # Получаем все объекты QuartzStone
#         quartz_stones = QuartzStone.objects.filter()
#
#         # Счетчики для статистики
#         updated_count = 0
#         skipped_count = 0
#
#         for stone in quartz_stones:
#             # Если поле link_serf уже заполнено - пропускаем
#
#
#             # Получаем первую букву бренда в верхнем регистре
#             brand_first_letter = stone.brand_stone[0].upper() if stone.brand_stone else None
#
#             # Устанавливаем значение в зависимости от первой буквы
#             if brand_first_letter == 'C':
#                 stone.link_serf = QuartzStone.LinkSerfChoices.CAESARSTONE
#                 stone.save()
#                 updated_count += 1
#             elif brand_first_letter == 'T':
#                 stone.link_serf = QuartzStone.LinkSerfChoices.TECHNISTONE
#                 stone.save()
#                 updated_count += 1
#             else:
#                 skipped_count += 1
#
#         # Формируем отчет о выполнении
#         self.stdout.write(self.style.SUCCESS(
#             f"Обновление завершено! "
#             f"Обновлено: {updated_count}, "
#             f"Пропущено: {skipped_count}, "
#             f"Всего обработано: {quartz_stones.count()}"
#         ))
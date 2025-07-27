from django.http import HttpResponse
from openpyxl import Workbook
from catalog.models import QuartzStone, AcrylicStone, NaturalStone, CeramicsStone
from ..models import  UserBidModel


def export_stones(request, model, filename, title):
    items = model.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.title = title

    headers = [
        'Название камня',
        'Примерная цена',
        'Материал камня',
        'Страна изготовления',
        'Толщина (мм)',
        'Артикул',
        'О бренде',
        'В архиве',
        'Бренд',
        'Цвет',
        'Текстура',
        'Фактура',
        'Ссылка на сертификаты'
    ]
    ws.append(headers)

    for item in items:
        ws.append([
            item.name_stone,
            item.abt_prise,
            item.get_material_display(),
            item.get_country_display(),
            item.thickness,
            item.article,
            item.about_brand,
            'Да' if item.archive else 'Нет',
            item.get_brand_stone_display(),
            item.get_color_display(),
            item.get_texture_display(),
            item.get_faktura_display(),
            item.get_link_serf_display(),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'
    wb.save(response)
    return response


# Независимая функция для экспорта заявок
def export_userbids(request):
    bids = UserBidModel.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.title = 'Заявки пользователей'

    headers = [
        'Полное имя',
        'Телефон',
        'Email',
        'Статус активности',
        'Согласие с политикой',
        'Дата создания'
    ]
    ws.append(headers)

    for bid in bids:
        ws.append([
            bid.full_name,
            bid.phone,
            bid.email,
            'Активен' if bid.is_active else 'Неактивен',
            'Да' if bid.AWtPP else 'Нет',
            bid.created_at.strftime("%d.%m.%Y %H:%M")
        ])

    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            try:
                value_length = len(str(cell.value))
                if value_length > max_length:
                    max_length = value_length
            except Exception:
                pass

        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column_letter].width = adjusted_width

    return wb

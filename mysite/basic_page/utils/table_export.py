from io import BytesIO
import warnings

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.drawing.image import Image as SpreadsheetImage
from PIL import Image as PillowImage, UnidentifiedImageError

from ..models import UserBidModel


MISSING_VALUE = 'Отсутствует'
IMAGE_WIDTH = 110
IMAGE_HEIGHT = 110
EXPORT_IMAGE_SIZE = (IMAGE_WIDTH * 2, IMAGE_HEIGHT * 2)
# Source photos are only needed as small worksheet thumbnails.  Decoding a
# multi-megapixel original would make one export consume hundreds of MB.
MAX_EXPORT_SOURCE_PIXELS = 20_000_000


def safe_spreadsheet_value(value):
    """Prevent Excel from interpreting user-controlled strings as formulas."""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def display_export_value(value):
    """Keep missing database values readable and hide their Python representation."""
    if value is None or value == '' or value == 'None':
        return MISSING_VALUE
    return safe_spreadsheet_value(value)


def add_image_to_cell(worksheet, cell, field_file):
    """Embed a stored image in a worksheet cell, skipping unavailable files safely."""
    if not field_file or not field_file.name:
        return False

    try:
        field_file.open('rb')
        # Turn Pillow's decompression-bomb warning into a handled error rather
        # than attempting to allocate memory for an unsafe source image.
        with warnings.catch_warnings():
            warnings.simplefilter('error', PillowImage.DecompressionBombWarning)
            source_image = PillowImage.open(field_file)
        with source_image:
            if source_image.width * source_image.height > MAX_EXPORT_SOURCE_PIXELS:
                return False
            # JPEG can decode directly to the requested reduced resolution.
            source_image.draft('RGB', EXPORT_IMAGE_SIZE)
            source_image.thumbnail(EXPORT_IMAGE_SIZE, PillowImage.Resampling.LANCZOS)
            image_bytes = BytesIO()
            source_image.convert('RGB').save(
                image_bytes, format='JPEG', quality=82, optimize=True,
            )
        image_bytes.seek(0)
    except (
        FileNotFoundError, OSError, UnidentifiedImageError, ValueError,
        PillowImage.DecompressionBombWarning, PillowImage.DecompressionBombError,
    ):
        return False
    finally:
        try:
            field_file.close()
        except (AttributeError, OSError):
            pass

    image = SpreadsheetImage(image_bytes)
    image.width = IMAGE_WIDTH
    image.height = IMAGE_HEIGHT
    worksheet.add_image(image, cell.coordinate)
    return True


def _autosize_columns(worksheet):
    for column in worksheet.columns:
        max_length = max((len(str(cell.value or '')) for cell in column), default=0)
        worksheet.column_dimensions[column[0].column_letter].width = min(
            max(max_length + 2, 14), 45,
        )


def export_stones(request, model, filename, title):
    with_images = request.GET.get('with_images') == '1'
    items = list(model.objects.prefetch_related('example_images').all())

    wb = Workbook()
    ws = wb.active
    ws.title = title

    headers = [
        'Название камня', 'Примерная цена', 'Материал камня',
        'Страна изготовления', 'Толщина (мм)', 'Артикул', 'О бренде',
        'В архиве', 'Бренд', 'Цвет', 'Текстура', 'Фактура',
        'Ссылка на сертификаты',
    ]
    max_examples = 0
    examples_by_item = {}
    if with_images:
        for item in items:
            examples = list(item.example_images.all())
            examples_by_item[item.pk] = examples
            max_examples = max(max_examples, len(examples))
        headers.extend(['Превью'] + [
            f'Пример изображения №{number}'
            for number in range(1, max_examples + 1)
        ])
    ws.append(headers)
    ws.freeze_panes = 'A2'

    for item in items:
        row = [
            display_export_value(item.name_stone),
            display_export_value(item.abt_prise),
            display_export_value(item.get_material_display()),
            display_export_value(item.get_country_display()),
            display_export_value(item.thickness),
            display_export_value(item.article),
            display_export_value(item.about_brand),
            'Да' if item.archive else 'Нет',
            display_export_value(item.get_brand_stone_display()),
            display_export_value(item.get_color_display()),
            display_export_value(item.get_texture_display()),
            display_export_value(item.get_faktura_display()),
            # Choice display returns the readable certificate name, not its URL.
            display_export_value(item.get_link_serf_display()),
        ]
        if with_images:
            row.extend([''] * (max_examples + 1))
        ws.append(row)

        if with_images:
            worksheet_row = ws.max_row
            ws.row_dimensions[worksheet_row].height = 88
            add_image_to_cell(ws, ws.cell(worksheet_row, 14), item.priview_img)
            for index, example in enumerate(examples_by_item[item.pk], start=15):
                add_image_to_cell(ws, ws.cell(worksheet_row, index), example.image)

    _autosize_columns(ws)
    if with_images:
        for column_index in range(14, 15 + max_examples):
            ws.column_dimensions[ws.cell(1, column_index).column_letter].width = 18

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'
    wb.save(response)
    return response


def export_userbids(request):
    bids = UserBidModel.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.title = 'Заявки пользователей'

    headers = [
        'Полное имя', 'Телефон', 'Email', 'Статус активности',
        'Согласие с политикой', 'Дата создания',
    ]
    ws.append(headers)

    for bid in bids:
        ws.append([
            safe_spreadsheet_value(bid.full_name),
            safe_spreadsheet_value(bid.phone),
            safe_spreadsheet_value(bid.email),
            'Активен' if bid.is_active else 'Неактивен',
            'Да' if bid.AWtPP else 'Нет',
            bid.created_at.strftime('%d.%m.%Y %H:%M'),
        ])

    _autosize_columns(ws)
    return wb

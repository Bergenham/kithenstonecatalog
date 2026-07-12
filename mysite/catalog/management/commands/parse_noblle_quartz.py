from pathlib import Path

from catalog.models import QuartzStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_letter_three_digits


class Command(FlatBrandImportCommand):
    help = "Импортирует QuartzStone для NOBLLE из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\NOBLLE Quartz\Noblle. Фото ассортимента")
    model_class = QuartzStone
    article_suffix = "_NOBLLE"
    about_brand = "NOBLLE (Noblle Quartz) — молодой и амбициозный бренд кварцевого камня фабричного китайского производства, созданный для тех, кто ищет максимально бюджетное решение без потери в качестве. Камень абсолютно не имеет пор, поэтому не впитывает вино или кофе, легок в уходе и сертифицирован на гигиеничность. Главная фишка бренда — возможность получить эксклюзивные и сложные трендовые дизайны (вроде полупрозрачных светопроводящих плит или текстуры редкого камня Патагония) по рекордно низкой для рынка цене."
    parse_article_and_name = staticmethod(parse_letter_three_digits)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = QuartzStone.MaterialChoices.QUARTZ
        return defaults

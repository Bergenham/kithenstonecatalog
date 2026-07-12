from pathlib import Path

from catalog.models import QuartzStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_four_digits


class Command(FlatBrandImportCommand):
    help = "Импортирует QuartzStone для Caesarstone из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\Caesarstone")
    model_class = QuartzStone
    article_suffix = "_CAESARSTONE"
    about_brand = "CAESARSTONE — это легендарный израильский бренд, первопроходец мирового рынка и абсолютный премиум-класс в мире кварцевого камня. Покупая Caesarstone, клиент платит за безупречный статус, эталонное качество и уникальный люксовый дизайн от мировых студий. Состав идеален (90% натурального кварца), материал обладает повышенной износостойкостью и поставляется с официальной международной гарантией. Это выбор для тех, кто делает дорогой ремонт на десятилетия и не привык компромиссам в интерьере."
    parse_article_and_name = staticmethod(parse_four_digits)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = QuartzStone.MaterialChoices.QUARTZ
        return defaults

from pathlib import Path

from catalog.models import AcrylicStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_letter_dash_digits


class Command(FlatBrandImportCommand):
    help = "Импортирует AcrylicStone для GRANDEX из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\GRANDEX\GRANDEX. Фото ассортимента")
    model_class = AcrylicStone
    article_suffix = "_GRANDEX"
    about_brand = "GRANDEX — это мировой лидер среди премиального акрилового камня, производящийся на узкоспециализированном высокотехнологичном заводе в Южной Корее. Материал ценится дизайнерами за высочайшую чистоту состава (акриловые смолы без дешевых примесей), что делает его невероятно прочным, экологичным и долговечным. Коллекции Grandex включают в себя потрясающие палитры с глубокими текстурами, мерцающими блестками и полупрозрачными включениями. Отличный выбор, если нужна долговечная, абсолютно бесшовная и статусная дизайнерская мебель."
    parse_article_and_name = staticmethod(parse_letter_dash_digits)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = AcrylicStone.MaterialChoices.ACRYL
        return defaults

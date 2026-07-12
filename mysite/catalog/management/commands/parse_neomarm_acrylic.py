from pathlib import Path

from catalog.models import AcrylicStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_neomarm


class Command(FlatBrandImportCommand):
    help = "Импортирует AcrylicStone для NEOMARM из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\NEOMARM")
    model_class = AcrylicStone
    article_suffix = "_NEOMARM"
    about_brand = "NEOMARM — специализированная серия эксклюзивного акрилового камня, созданная с одной главной целью: безупречно имитировать благородный итальянский мрамор, сохраняя все плюсы акрила. Столешница или подоконник из Neomarm будут иметь характерные мягкие разводы, глубокие жилы и благородные цвета натурального мрамора, но при этом поверхность останется теплой, гигиеничной, бесшовной и не впитает пролитый сок или пятна, в отличие от пористого оригинала."
    parse_article_and_name = staticmethod(parse_neomarm)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = AcrylicStone.MaterialChoices.ACRYL
        return defaults

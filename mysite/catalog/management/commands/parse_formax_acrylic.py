from pathlib import Path

from catalog.models import AcrylicStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_letter_dash_digits


class Command(FlatBrandImportCommand):
    help = "Импортирует AcrylicStone для FORMAX из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\Formax\FORMAX. Фото ассортимента")
    model_class = AcrylicStone
    article_suffix = "_FORMAX"
    about_brand = "FORMAX — качественный акриловый листовой камень, который выбирают ради создания бесшовных, монолитных поверхностей любой формы. В отличие от кварца, этот материал пластичен при нагревании: из него можно отлить столешницу, плавно переходящую в мойку без единого стыка и грязевых швов. Он приятный и теплый на ощупь, полностью ремонтопригоден (любые царапины легко полируются до состояния новых на месте) и идеально подходит для радиусных интерьеров, интегрированных раковин и ванных комнат."
    parse_article_and_name = staticmethod(parse_letter_dash_digits)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = AcrylicStone.MaterialChoices.ACRYL
        return defaults

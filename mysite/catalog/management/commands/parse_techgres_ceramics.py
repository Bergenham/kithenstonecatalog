from pathlib import Path

from catalog.models import CeramicsStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_prefixed_digits


class Command(FlatBrandImportCommand):
    help = "Импортирует CeramicsStone для TECHGRES из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\TECHGRES\TECHGRES. Фото ассортимента")
    model_class = CeramicsStone
    article_suffix = "_TECHGRES"
    about_brand = "TECHGRES — инновационный бренд крупноформатного керамогранита высокой прочности (не кварцевый камень, а именно широкоформатная керамика). Благодаря толщине плит до 12-20 мм и технологии сквозного рисунка Full Body Print он идеально имитирует природные каменные плиты. Керамогранит TechGres обладает нулевым поглощением влаги, не боится агрессивной химии, ультрафиолета и морозов, поэтому его выбирают не только для кухонных зон, но и для облицовки стен, полов, каминов и даже уличных фасадов."
    parse_article_and_name = staticmethod(parse_prefixed_digits)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = CeramicsStone.MaterialChoices.CERAMIC
        return defaults

from pathlib import Path

from catalog.models import QuartzStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_four_digits


class Command(FlatBrandImportCommand):
    help = "Импортирует QuartzStone для AVANT из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\AVANT Quartz\AVANT. Фото ассортимента")
    model_class = QuartzStone
    article_suffix = "_AVANT"
    about_brand = "AVANT (Avant Quartz) — один из самых продаваемых и проверенных брендов кварцевого агломерата в России, выпускающийся в Китае по заказу крупного российского дистрибьютора. Камень знаменит своими уникальными, очень естественными мраморными и гранитными рисунками, которые в точности повторяют французскую классику. Он сертифицирован для использования в детских и медицинских учреждениях, чрезвычайно прочен и стоит в разы дешевле европейских аналогов, являясь «золотой серединой» для кухонных столешниц."
    parse_article_and_name = staticmethod(parse_four_digits)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = QuartzStone.MaterialChoices.QUARTZ
        return defaults

from pathlib import Path

from catalog.models import QuartzStone

from ._flat_brand_parser import FlatBrandImportCommand, parse_letter_three_digits


class Command(FlatBrandImportCommand):
    help = "Импортирует QuartzStone для АВАРУС из плоского каталога."
    source_dir = Path(r"D:\Project.com\САЙТ\АВАРУС Кварц\АВАРУС. Фото ассортимента")
    model_class = QuartzStone
    article_suffix = "_AVARUS"
    about_brand = "AVARUS — это единственный бренд кварцевого агломерата, который производится полностью в России на современном европейском оборудовании. В его составе до 95% натурального кварца, что делает камень невероятно прочным (крепче гранита), устойчивым к царапинам и перепадам температур. Палитра собрала самые популярные у российских покупателей текстуры (мрамор, гранит, моноколор), а локальное производство гарантирует быструю доставку, пожизненную гарантию и лучшее соотношение цены и европейского качества без переплат за импорт."
    parse_article_and_name = staticmethod(parse_letter_three_digits)

    def build_defaults(self, name_stone):
        defaults = super().build_defaults(name_stone)
        defaults["material"] = QuartzStone.MaterialChoices.QUARTZ
        return defaults

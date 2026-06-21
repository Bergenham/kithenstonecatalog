from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


def get_upload_path(instance, filename):
    material_folders = {
        'Кварцевый камень': 'quartz',
        'Акриловый камень': 'acrylic',
        'Натуральный камень': 'natural',
        'Керамический камень': 'ceramics'
    }
    folder = material_folders.get(instance.material, 'other')
    return f'stones/{folder}/previews/{filename}'


class Stone(models.Model):
    class MaterialChoices(models.TextChoices):
        QUARTZ = 'Кварцевый камень', 'Кварцевый камень'
        ACRYL = 'Акриловый камень', 'Акриловый камень'
        NATURAL = 'Натуральный камень', 'Натуральный камень'
        CERAMIC = 'Керамический камень', 'Керамический камень'

    class CountryChoices(models.TextChoices):
        CZECH = 'Чехия', 'Чехия'
        ISRAEL = 'Израиль', 'Израиль'
        SOUTH_KOREA = 'Южная Корея', 'Южная Корея'
        CHINA = 'Китай', 'Китай'

    name_stone = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(5)],
        verbose_name='Название камня'
    )

    abt_prise = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[
            MinValueValidator(100),
            MaxValueValidator(9999999.99)
        ],
        verbose_name='Примерная цена',
        null=True,
        blank=True
    )

    priview_img = models.ImageField(
        upload_to=get_upload_path,
        verbose_name='Превью изображение'
    )

    material = models.CharField(
        max_length=50,
        choices=MaterialChoices.choices,
        verbose_name='Материал камня',
        null=True,
        blank=True
    )

    country = models.CharField(
        max_length=50,
        choices=CountryChoices.choices,
        verbose_name='Страна изготовления',
        null=True,
        blank=True
    )

    thickness = models.PositiveIntegerField(
        validators=[MaxValueValidator(9999)],
        verbose_name='Толщина (мм)',
        null=True,
        blank=True
    )

    article = models.CharField(max_length=100, unique=True, verbose_name='Артикул', null=True, blank=True)
    about_brand = models.TextField(verbose_name='О бренде', null=True, blank=True)
    archive = models.BooleanField(default=False, verbose_name='В архиве')

    def __str__(self):
        return self.name_stone


class StoneImage(models.Model):
    stone = models.ForeignKey(
        Stone,
        on_delete=models.CASCADE,
        related_name='example_images',
        verbose_name='Камень'
    )
    image = models.ImageField(
        upload_to='stones/examples/',
        verbose_name='Пример изображения'
    )

    class Meta:
        verbose_name = 'Пример изображения'
        verbose_name_plural = 'Примеры изображений'

    def __str__(self):
        return f'Изображение для {self.stone.name_stone}'


class QuartzStone(Stone):
    class BrandStoneChoices(models.TextChoices):
        CAESARSTONE = 'Caesarstone'
        TECHNISTONE = 'Technistone'
        PRIMAX_QUARTZ = 'PrimaxQuartz'

    class ColorChoices(models.TextChoices):
        BEIGE = 'Бежевый', 'Бежевый'
        WHITE = 'Белый', 'Белый'
        BROWN = 'Коричневый', 'Коричневый'
        GREY = 'Серый', 'Серый'
        DARK_GREY = 'Темносерый', 'Темносерый'
        BLACK = 'Черный', 'Черный'
        LIGHT = 'Светлый', 'Светлый'
        DARK = 'Темный', 'Темный'
        MULTICOLOR = 'Многоцветный', 'Многоцветный'

    class TextureChoices(models.TextChoices):
        CONCRETE = 'Бетон', 'Бетон'
        MARBLE = 'Мраморная', 'Мраморная'
        SINGLE_COLOR = 'Однотонная', 'Однотонная'
        TERRAZZO = 'Терраццо', 'Терраццо'
        PRIMAX_QUARTZ = 'Праймакс Кварц', 'Праймакс Кварц'
        PRIMAX_QUARTZ_FRESCO = 'Праймакс Кварц Фреско', 'Праймакс Кварц Фреско'

    class FakturaChoices(models.TextChoices):
        HONED = 'Матовая', 'Матовая'
        POLISHED = 'Полированная', 'Полированная'
        STANDARD = 'Стандартная', 'Стандартная'
        FBP = 'FBP', 'FBP'

    class LinkSerfChoices(models.TextChoices):
        CAESARSTONE = 'https://drive.google.com/drive/folders/1YgXlFi8KKDzPHz5IheKJlbepOqd1sl3M', 'Caesarstone'
        TECHNISTONE = 'https://technistone.ru/info/certificates/', 'Technistone'
        PRIMAX = 'https://primax.pro/catalog/acryl/certificates/', 'Primax'

    brand_stone = models.CharField(
        max_length=50,
        choices=BrandStoneChoices.choices,
        verbose_name='Бренд',
        null=True,
        blank=True,
    )
    color = models.CharField(
        max_length=50,
        choices=ColorChoices.choices,
        verbose_name='Цвет',
        null=True,
        blank=True,
    )
    texture = models.CharField(
        max_length=70,
        choices=TextureChoices.choices,
        verbose_name='Текстура',
        null=True,
        blank=True,
    )
    faktura = models.CharField(
        max_length=50,
        choices=FakturaChoices.choices,
        verbose_name='Фактура',
        null=True,
        blank=True,
    )
    link_serf = models.CharField(
        choices=LinkSerfChoices.choices,
        verbose_name='Ссылка на сертификаты',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Кварцевый камень'
        verbose_name_plural = 'Кварцевые камни'


class AcrylicStone(Stone):
    class BrandStoneChoices(models.TextChoices):
        HANEX = 'Hanex'
        DURASEIN = 'Durasein'
        PRIMAX = 'Primax'

    class ColorChoices(models.TextChoices):
        BEIGE = 'Бежевый', 'Бежевый'
        WHITE = 'Белый', 'Белый'
        YELLOW = 'Жёлтый', 'Жёлтый'
        BROWN = 'Коричневый', 'Коричневый'
        LIGHT_BLUE = 'Светло-голубой', 'Светло-голубой'
        LIGHT_BROWN = 'Светло-коричневый', 'Светло-коричневый'
        LIGHT_GREY = 'Светло-серый', 'Светло-серый'
        GREY = 'Серый', 'Серый'
        DARK_BROWN = 'Темно-коричневый', 'Темно-коричневый'
        DARK_RED = 'Темно-красный', 'Темно-красный'
        DARK_GREY = 'Темно-серый', 'Темно-серый'
        BLACK = 'Черный', 'Черный'
        GREEN = 'Зеленый', 'Зеленый'
        RED = 'Красный', 'Красный'
        ORANGE = 'Оранжевый', 'Оранжевый'
        LIGHT_GREEN = 'Светло-зеленый', 'Светло-зеленый'
        BLUE = 'Синий', 'Синий'
        LIGHT = 'Светлый', 'Светлый'
        DARK = 'Темный', 'Темный'
        MULTICOLOR = 'Многоцветный', 'Многоцветный'

    class TextureChoices(models.TextChoices):
        MARBLE = 'Мраморная', 'Мраморная'
        SINGLE_COLOR = 'Однотонная', 'Однотонная'
        SANDS = 'Пески', 'Пески'
        MEDIUM_CHIP = 'Средний чип', 'Средний чип'
        LARGE_CHIP = 'Крупный чип', 'Крупный чип'
        WHITE = 'Белый', 'Белый'
        PRIMAX_PREMIUM = 'Праймакс премиальный', 'Праймакс премиальный'
        PRIMAX_BASIC = 'Праймакс Базовый', 'Праймакс Базовый'
        PRIMAX_MARBLE = 'Праймакс мраморный', 'Праймакс мраморный'

    class FakturaChoices(models.TextChoices):
        SILKY = 'silky', 'Шелковистая'
        PEARL = 'pearl', 'Жемчужная'

    class LinkSerfChoices(models.TextChoices):
        HANEX = 'https://ssd.su/upload/iblock/74f/3hlh6ielnui9v0yw53ua78vqy1iikpdp.zip', 'Сертификат Hanex(ССД)'
        DURASEIN = 'https://ssd.su/upload/iblock/a62/2n2gdb8s43pfs2bqjt7g6wdwdx0vwvcf.zip', 'Сертификат Durasein(ССД)'
        PRIMAX = 'https://primax.pro/catalog/acryl/certificates/', 'Primax'

    brand_stone = models.CharField(
        max_length=50,
        choices=BrandStoneChoices.choices,
        verbose_name='Бренд',
        null=True,
        blank=True,
    )
    color = models.CharField(
        max_length=50,
        choices=ColorChoices.choices,
        verbose_name='Цвет',
        null=True,
        blank=True,
    )
    texture = models.CharField(
        max_length=70,
        choices=TextureChoices.choices,
        verbose_name='Текстура',
        null=True,
        blank=True,
    )
    faktura = models.CharField(
        max_length=50,
        choices=FakturaChoices.choices,
        verbose_name='Фактура',
        null=True,
        blank=True,
    )
    link_serf = models.CharField(
        max_length=200,
        choices=LinkSerfChoices.choices,
        verbose_name='Ссылка на сертификаты',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Акриловый камень'
        verbose_name_plural = 'Акриловые камни'


class NaturalStone(Stone):
    # Choices для природного камня
    class BrandStoneChoices(models.TextChoices):
        NATURE_STONE = 'n_stone', 'NatureStone'
        MOUNTAIN_GEMS = 'm_gems', 'MountainGems'

    class ColorChoices(models.TextChoices):
        FOREST = 'forest', 'Лесной'
        SANDSTONE = 'sandstone', 'Песчаник'

    class TextureChoices(models.TextChoices):
        CRACKED = 'cracked', 'Трещиноватая'
        LAYERED = 'layered', 'Слоистая'

    class FakturaChoices(models.TextChoices):
        ROCKY = 'rocky', 'Скалистая'
        AGED = 'aged', 'Состаренная'

    class LinkSerfChoices(models.TextChoices):
        NAT_CERT = 'nat_cert.pdf', 'Сертификат природного камня'
        ORIGIN = 'origin.pdf', 'Сертификат происхождения'

    # Переопределение полей
    brand_stone = models.CharField(
        max_length=50,
        choices=BrandStoneChoices.choices,
        verbose_name='Бренд',
        null=True,
        blank=True,
    )
    color = models.CharField(
        max_length=50,
        choices=ColorChoices.choices,
        verbose_name='Цвет',
        null=True,
        blank=True,
    )
    texture = models.CharField(
        max_length=50,
        choices=TextureChoices.choices,
        verbose_name='Текстура',
        null=True,
        blank=True,
    )
    faktura = models.CharField(
        max_length=50,
        choices=FakturaChoices.choices,
        verbose_name='Фактура',
        null=True,
        blank=True,
    )
    link_serf = models.CharField(
        max_length=50,
        choices=LinkSerfChoices.choices,
        verbose_name='Ссылка на сертификаты',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Природный камень'
        verbose_name_plural = 'Природные камни'


class CeramicsStone(Stone):
    class BrandStoneChoices(models.TextChoices):
        CERAM_PRO = 'ceram_p', 'CeramPro'
        TILE_MASTER = 'tile_m', 'TileMaster'

    class ColorChoices(models.TextChoices):
        GRAPHITE = 'graphite', 'Графитовый'
        IVORY = 'ivory', 'Слоновая кость'

    class TextureChoices(models.TextChoices):
        GEOMETRIC = 'geometric', 'Геометрическая'
        CONCRETE = 'concrete', 'Бетон'

    class FakturaChoices(models.TextChoices):
        GLASSY = 'glassy', 'Стекловидная'
        RUSTIC = 'rustic', 'Рустикальная'

    class LinkSerfChoices(models.TextChoices):
        CERAM_CERT = 'ceram_cert.pdf', 'Сертификат керамики'
        HEAT_RESIST = 'heat_res.pdf', 'Термостойкость'

    brand_stone = models.CharField(
        max_length=50,
        choices=BrandStoneChoices.choices,
        verbose_name='Бренд',
        null=True,
        blank=True,
    )
    color = models.CharField(
        max_length=50,
        choices=ColorChoices.choices,
        verbose_name='Цвет',
        null=True,
        blank=True,
    )
    texture = models.CharField(
        max_length=50,
        choices=TextureChoices.choices,
        verbose_name='Текстура',
        null=True,
        blank=True,
    )
    faktura = models.CharField(
        max_length=50,
        choices=FakturaChoices.choices,
        verbose_name='Фактура',
        null=True,
        blank=True,
    )
    link_serf = models.CharField(
        max_length=50,
        choices=LinkSerfChoices.choices,
        verbose_name='Ссылка на сертификаты',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Керамический камень'
        verbose_name_plural = 'Керамические камни'

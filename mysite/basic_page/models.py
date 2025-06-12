from django.db import models
from django.core.validators import MinLengthValidator

class InfoStone(models.Model):
    name = models.CharField(
        max_length=25,
        unique=True,
        verbose_name='Название камня',
        help_text='Минимум 4 символа',
        validators=[MinLengthValidator(4)]
    )
    main_image = models.ImageField(
        upload_to='stones/main/',
        verbose_name='Главное изображение'
    )
    another_name = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name='Альтернативное название'
    )

    class Meta:
        verbose_name = 'Камень'
        verbose_name_plural = 'Камни'

    def __str__(self):
        return self.name

class StoneDescription(models.Model):
    info_stone = models.ForeignKey(
        InfoStone,
        on_delete=models.CASCADE,
        related_name='descriptions',
        verbose_name='Связанный камень'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название характеристики'
    )
    full_description = models.TextField(
        verbose_name='Полное описание'
    )
    image_description = models.ImageField(
        upload_to='stones/descriptions/',
        blank=True,
        verbose_name='Изображение для описания'
    )

    class Meta:
        verbose_name = 'Описание камня'
        verbose_name_plural = 'Описания камней'
        unique_together = [['info_stone', 'name']]

    def __str__(self):
        return f"{self.info_stone.name} - {self.name}"

class Company(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название компании'
    )
    company_image = models.ImageField(
        upload_to='companies/',
        verbose_name='Логотип компании'
    )
    description = models.TextField(
        verbose_name='Описание компании'
    )
    produced_stones = models.ManyToManyField(
        InfoStone,
        related_name='manufacturers',
        verbose_name='Производимые камни'
    )

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'

    def __str__(self):
        return self.name
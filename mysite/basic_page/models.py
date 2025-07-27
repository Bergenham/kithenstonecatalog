from django.db import models
from django.core.validators import MinLengthValidator


class UserBidModel(models.Model):
    full_name = models.CharField(
        max_length=30,
        validators=[MinLengthValidator(3)],
        verbose_name="Полное имя"
    )
    phone = models.CharField(
        max_length=30,
        verbose_name="Телефон"
    )
    email = models.EmailField(verbose_name="Email")

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    AWtPP = models.BooleanField(  # Agree With The Privacy Policy
        default=True,
        verbose_name="Согласен"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"


    def __str__(self):
        return self.full_name
# Generated by Django 5.2.4 on 2025-07-29 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_alter_stone_country'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stone',
            name='article',
            field=models.CharField(max_length=100, unique=True, verbose_name='Артикул'),
        ),
    ]

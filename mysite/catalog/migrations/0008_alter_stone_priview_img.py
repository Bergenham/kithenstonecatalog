# Generated by Django 5.2.4 on 2025-07-29 17:04

import catalog.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_alter_stone_article'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stone',
            name='priview_img',
            field=models.ImageField(upload_to=catalog.models.get_upload_path, verbose_name='Превью изображение'),
        ),
    ]

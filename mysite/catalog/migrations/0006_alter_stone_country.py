# Generated by Django 5.2.4 on 2025-07-28 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_alter_quartzstone_link_serf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stone',
            name='country',
            field=models.CharField(choices=[('Чехия', 'Чехия'), ('Израиль', 'Израиль')], max_length=50, verbose_name='Страна изготовления'),
        ),
    ]

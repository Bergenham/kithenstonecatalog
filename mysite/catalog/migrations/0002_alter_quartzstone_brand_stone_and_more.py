# Generated by Django 5.1.7 on 2025-07-18 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quartzstone',
            name='brand_stone',
            field=models.CharField(choices=[('caesarstone', 'Caesarstone'), ('technistone', 'Technistone')], max_length=50, verbose_name='Бренд'),
        ),
        migrations.AlterField(
            model_name='quartzstone',
            name='color',
            field=models.CharField(choices=[('Бежевый', 'Beige'), ('Белый', 'White'), ('Коричневый', 'Brown'), ('Серый', 'Grey'), ('Темно-серый', 'Dark Grey'), ('Черный', 'Black')], max_length=50, verbose_name='Цвет'),
        ),
        migrations.AlterField(
            model_name='quartzstone',
            name='faktura',
            field=models.CharField(choices=[('Матовая', 'Honed'), ('Полированная', 'Polished')], max_length=50, verbose_name='Фактура'),
        ),
        migrations.AlterField(
            model_name='quartzstone',
            name='link_serf',
            field=models.CharField(choices=[('q_cert.pdf', 'Q Cert'), ('q_safe.pdf', 'Q Safety')], max_length=50, verbose_name='Ссылка на сертификаты'),
        ),
        migrations.AlterField(
            model_name='quartzstone',
            name='texture',
            field=models.CharField(choices=[('Бетон', 'Concrete'), ('Мраморная', 'Marble'), ('Однотонная', 'Single Color'), ('Тераццо', 'Terrazzo')], max_length=50, verbose_name='Текстура'),
        ),
        migrations.AlterField(
            model_name='stone',
            name='country',
            field=models.CharField(choices=[('Кварцевый камень', 'Quartz')], max_length=50, verbose_name='Страна изготовления'),
        ),
        migrations.AlterField(
            model_name='stone',
            name='material',
            field=models.CharField(choices=[('Кварцевый камень', 'Quartz'), ('Акриловый камень', 'Acryl'), ('Натуральный камень', 'Natural'), ('Керамический камень', 'Ceramic')], max_length=50, verbose_name='Материал камня'),
        ),
    ]

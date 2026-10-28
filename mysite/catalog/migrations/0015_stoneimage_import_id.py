from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0014_alter_acrylicstone_brand_stone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stoneimage',
            name='import_id',
            field=models.CharField(
                max_length=100, unique=True, null=True, blank=True,
                editable=False, verbose_name='Идентификатор пакетного импорта',
            ),
        ),
    ]

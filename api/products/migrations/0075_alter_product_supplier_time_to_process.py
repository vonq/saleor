# Generated by Django 3.2 on 2021-04-28 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0074_auto_20210428_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='supplier_time_to_process',
            field=models.IntegerField(default=0, null=True, verbose_name='Supplier time to process (hours)'),
        ),
    ]

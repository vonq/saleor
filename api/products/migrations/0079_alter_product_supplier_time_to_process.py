# Generated by Django 3.2 on 2021-05-05 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0078_auto_20210504_1019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='supplier_time_to_process',
            field=models.PositiveIntegerField(default=0, verbose_name='Supplier time to process (hours)'),
        ),
    ]
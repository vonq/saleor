# Generated by Django 3.2 on 2021-04-28 16:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0072_category_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='time_to_process',
            new_name='supplier_time_to_process',
        ),
    ]

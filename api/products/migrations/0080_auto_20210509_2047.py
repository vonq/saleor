# Generated by Django 3.2 on 2021-05-09 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0079_alter_product_supplier_time_to_process'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='product',
            name='products_pr_created_1360ea_idx',
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['-created'], name='products_pk_created_4dbf65_idx'),
        ),
        migrations.AlterModelTable(
            name='product',
            table='products_pkb_product',
        ),
    ]

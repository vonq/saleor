# Generated by Django 3.1.7 on 2021-03-24 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0143_rename_product_images_to_product_media'),
        ('campaign', '0003_auto_20210323_1617'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='products',
            field=models.ManyToManyField(blank=True, related_name='campaign', to='product.Product'),
        ),
    ]
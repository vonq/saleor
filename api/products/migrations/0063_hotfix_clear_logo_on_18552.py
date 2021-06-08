# Generated by Django 3.1.3 on 2020-11-17 10:39

from django.db import migrations
import uuid


class Migration(migrations.Migration):

    def clear_logo_on_18552(apps, schema_editor):
        Product = apps.get_model("products", "Product")
        product_18552 = Product.objects.filter(id=18552).first()
        if product_18552 is not None:
            product_18552.logo_rectangle = None
            product_18552.logo_square = None
            product_18552.logo_rectangle_uncropped = None
            product_18552.logo_square_uncropped = None

            product_18552.save(update_fields=['logo_rectangle', 'logo_square', 'logo_rectangle_uncropped', 'logo_square_uncropped'])

    dependencies = [
        ('products', '0062_auto_20210325_1219'),
    ]

    operations = [
        migrations.RunPython(clear_logo_on_18552, reverse_code=migrations.RunPython.noop),
    ]

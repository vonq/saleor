# Generated by Django 3.2.4 on 2021-06-25 17:33

from django.db import migrations
from api.products.models import Product as ProductModel


class Migration(migrations.Migration):
    def migrate_ats_availability_flag(apps, schema_editor):
        Product = apps.get_model("products", "Product")
        for product in Product.objects.all():
            product_should_be_available_in_ats = (
                product.available_in_jmp
                and product.salesforce_product_type
                in [
                    ProductModel.SalesforceProductType.JOB_BOARD,
                    ProductModel.SalesforceProductType.SOCIAL,
                    ProductModel.SalesforceProductType.GOOGLE,
                ]
            )
            if product.available_in_ats != product_should_be_available_in_ats:
                product.available_in_ats = product_should_be_available_in_ats
                product.save()

    dependencies = [
        ("products", "0091_alter_channel_type"),
    ]

    operations = [
        migrations.RunPython(
            migrate_ats_availability_flag, reverse_code=migrations.RunPython.noop
        )
    ]

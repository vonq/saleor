# Generated by Django 3.1.7 on 2021-03-12 11:02

from django.db import migrations


class Migration(migrations.Migration):
    def populate_cross_postings(apps, schema_editor):
        Product = apps.get_model("products", "Product")
        for row in Product.objects.all():
            salesforce_cross_postings = row.salesforce_cross_postings
            if salesforce_cross_postings:
                row.cross_postings = salesforce_cross_postings
            try:
                row.save(update_fields=['cross_postings'])
            except Exception as e:
                print(f"Failed to save product {row.id} due to {e}")

    dependencies = [
        ('products', '0057_auto_20210312_1102'),
    ]

    operations = [
        migrations.RunPython(populate_cross_postings, reverse_code=migrations.RunPython.noop),

    ]

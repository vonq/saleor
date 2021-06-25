# Generated by Django 3.2.4 on 2021-06-25 10:47

from django.db import migrations, transaction
import csv
import os


class Migration(migrations.Migration):
    def populate_remarks(apps, schema_editor):
        Product = apps.get_model("products", "Product")
        with open(
            os.path.join(os.path.dirname(__file__), "data/Salesforce_data.csv")
        ) as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    with transaction.atomic():
                        product = Product.objects.get(salesforce_id=row["Uuid__c"])
                        product.remarks = row["Remarks__c"]
                        product.save(update_fields=["remarks"])
                except Exception as e:
                    print(f"Failed to save product due to {e}")

    dependencies = [
        ("products", "0083_alter_remarks_add_reason"),
    ]

    operations = [
        migrations.RunPython(populate_remarks, reverse_code=migrations.RunPython.noop)
    ]

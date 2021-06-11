# Generated by Django 3.2 on 2021-04-15 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0065_auto_20210408_1150"),
    ]

    operations = [
        migrations.AlterField(
            model_name="channel",
            name="salesforce_sync_status",
            field=models.CharField(
                choices=[
                    ("synced", "Synced"),
                    ("unsynced", "Unsynced"),
                    ("pending", "Pending"),
                    ("errored", "Errored"),
                ],
                default="unsynced",
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="salesforce_sync_status",
            field=models.CharField(
                choices=[
                    ("synced", "Synced"),
                    ("unsynced", "Unsynced"),
                    ("pending", "Pending"),
                    ("errored", "Errored"),
                ],
                default="unsynced",
                max_length=8,
            ),
        ),
    ]
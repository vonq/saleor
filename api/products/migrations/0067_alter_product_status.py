# Generated by Django 3.2 on 2021-04-19 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0066_auto_20210415_1743"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Blacklisted", "Blacklisted"),
                    ("Disabled", "Disabled"),
                    ("Negotiated", "Negotiated"),
                    ("Trial", "Trial"),
                    ("Active", "Active"),
                    ("None", "--None--"),
                ],
                default=None,
                max_length=12,
                null=True,
            ),
        ),
    ]
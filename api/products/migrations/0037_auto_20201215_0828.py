# Generated by Django 3.1.4 on 2020-12-15 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0036_auto_20201209_1141"),
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
                    ("None", "--None--"),
                ],
                default=None,
                max_length=12,
                null=True,
            ),
        ),
    ]

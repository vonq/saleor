# Generated by Django 3.1.4 on 2020-12-22 12:21
from django.db import migrations
from api.currency.conversion import refresh_exchange_rates


def seed_initially_supported_currencies(apps, schema_editor):
    Currency = apps.get_model("currency", "Currency")

    Currency.objects.bulk_create(
        [
            Currency(code="GBP", name="British Pound"),
            Currency(code="USD", name="US Dollar"),
        ]
    )


def seed_exchange_rates(apps, schema_editor):
    refresh_exchange_rates(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("currency", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_initially_supported_currencies),
        migrations.RunPython(seed_exchange_rates),
    ]
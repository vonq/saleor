# Generated by Django 3.1.7 on 2021-03-29 09:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("campaign", "0006_auto_20210326_1101"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="campaign",
            name="products",
        ),
    ]

# Generated by Django 3.1.4 on 2020-12-18 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0038_auto_20201216_1641"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="is_active",
            field=models.BooleanField(default=False),
        ),
    ]
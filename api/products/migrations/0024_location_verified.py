# Generated by Django 3.1.3 on 2020-11-20 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0023_auto_20201119_0523"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="approved",
            field=models.BooleanField(default=False),
        ),
    ]
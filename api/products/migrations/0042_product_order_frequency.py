# Generated by Django 3.1.5 on 2021-01-18 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0041_auto_20201208_1744'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='order_frequency',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]

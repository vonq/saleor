# Generated by Django 3.1.7 on 2021-03-12 13:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0058_auto_20210312_1102'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='salesforce_cross_postings',
        ),
    ]

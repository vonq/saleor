# Generated by Django 3.1.3 on 2020-11-11 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_product_salesforce'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='salesforce_cross_postings',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
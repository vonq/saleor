# Generated by Django 3.1.7 on 2021-03-23 14:47

from django.db import migrations, models
import django_countries.fields
import saleor.checkout.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0143_rename_product_images_to_product_media'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=250)),
                ('country', django_countries.fields.CountryField(default=saleor.checkout.models.get_default_country, max_length=2)),
                ('industry', models.CharField(max_length=50)),
                ('seniority', models.CharField(max_length=30)),
                ('education', models.CharField(max_length=40)),
                ('job_function', models.CharField(max_length=255)),
                ('products', models.ManyToManyField(related_name='products', to='product.Product')),
            ],
        ),
    ]
# Generated by Django 3.1.3 on 2020-11-19 12:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0024_location_verified'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobtitle',
            name='industry',
        ),
    ]
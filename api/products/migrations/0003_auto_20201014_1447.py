# Generated by Django 3.1.2 on 2020-10-14 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_auto_20201014_0926'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='within',
        ),
        migrations.AddField(
            model_name='location',
            name='within',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.location'),
        ),
    ]

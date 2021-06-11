# Generated by Django 3.1.5 on 2021-01-26 18:10
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Industry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mapi_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('name_en', models.CharField(max_length=255, null=True)),
                ('name_de', models.CharField(max_length=255, null=True)),
                ('name_nl', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='JobCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mapi_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('name_en', models.CharField(max_length=255, null=True)),
                ('name_de', models.CharField(max_length=255, null=True)),
                ('name_nl', models.CharField(max_length=255, null=True)),
            ],
        ),
    ]
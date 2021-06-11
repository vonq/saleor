# Generated by Django 3.1.2 on 2020-10-27 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_mapboxlocation'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='name_de',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='channel',
            name='name_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='channel',
            name='name_nl',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='industry',
            name='name_de',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='industry',
            name='name_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='industry',
            name='name_nl',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='jobfunction',
            name='name_de',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='jobfunction',
            name='name_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='jobfunction',
            name='name_nl',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='name_de',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='name_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='jobtitle',
            name='name_nl',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='canonical_name_de',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='canonical_name_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='canonical_name_nl',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='description_de',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='description_en',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='description_nl',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='title_de',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='title_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='title_nl',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
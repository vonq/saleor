# Generated by Django 3.1.2 on 2020-10-13 12:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('url', models.CharField(max_length=300)),
                ('type', models.CharField(choices=[('job board', 'Job Board'), ('social media', 'Social Media'), ('community', 'Community'), ('publication', 'Publication'), ('aggregator', 'Aggregator')], default='job board', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Industry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name_plural': 'industries',
            },
        ),
        migrations.CreateModel(
            name='JobFunction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.jobfunction')),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('country_code', models.CharField(max_length=3, null=True)),
                ('mapbox_id', models.CharField(blank=True, max_length=50, null=True)),
                ('mapbox_text', models.CharField(blank=True, max_length=100, null=True)),
                ('mapbox_placename', models.CharField(blank=True, max_length=300, null=True)),
                ('mapbox_place_type', models.CharField(blank=True, max_length=500, null=True)),
                ('mapbox_shortcode', models.CharField(blank=True, max_length=10, null=True)),
                ('mapbox_within', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mapbox_location', to='products.location')),
                ('within', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.location')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('url', models.CharField(max_length=300)),
                ('description', models.TextField(default='')),
                ('logo_url', models.CharField(blank=True, default=None, max_length=300, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=True)),
                ('is_archived', models.BooleanField(default=True)),
                ('product_solution', models.CharField(max_length=20, null=True)),
                ('interests', models.CharField(blank=True, default='', max_length=200, null=True)),
                ('salesforce_id', models.CharField(max_length=20, null=True)),
                ('salesforce_product_type', models.CharField(max_length=30, null=True)),
                ('desq_product_id', models.BigIntegerField(null=True)),
                ('similarweb_estimated_monthly_visits', models.CharField(blank=True, default=None, max_length=300, null=True)),
                ('similarweb_top_country_shares', models.TextField(blank=True, default=None, null=True)),
                ('channel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.channel')),
                ('industries', models.ManyToManyField(blank=True, null=True, related_name='industries', related_query_name='industry', to='products.Industry')),
                ('job_functions', models.ManyToManyField(blank=True, null=True, related_name='job_functions', related_query_name='job_function', to='products.JobFunction')),
                ('locations', models.ManyToManyField(blank=True, null=True, related_name='locations', to='products.Location')),
            ],
        ),
        migrations.CreateModel(
            name='JobTitle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('frequency', models.IntegerField(blank=True, default=0, null=True)),
                ('canonical', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('alias_of', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.jobtitle')),
                ('industry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.industry')),
                ('jobFunction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.jobfunction')),
            ],
        ),
    ]
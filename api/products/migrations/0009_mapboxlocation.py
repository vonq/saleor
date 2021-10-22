import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0008_auto_20201021_1449'),
    ]

    operations = [
        migrations.CreateModel(
            name='MapboxLocation',
            fields=[
                ('mapbox_id', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('mapbox_data', models.JSONField()),
                ('mapbox_context', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), default=list, size=None)),
                ('mapbox_placename', models.CharField(blank=True, max_length=300, null=True)),
            ],
        ),
    ]

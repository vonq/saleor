# Generated by Django 3.2.4 on 2021-06-25 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0084_populate_remarks_correctly"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="remarks",
            field=models.CharField(max_length=600, null=True),
        )
    ]

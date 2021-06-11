# Generated by Django 3.1.6 on 2021-02-09 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0047_auto_20210204_1439'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='is_my_own_product',
        ),
        migrations.AddField(
            model_name='product',
            name='salesforce_product_solution',
            field=models.TextField(choices=[('Awareness', 'Awareness'), ('Job Marketing', 'Job Marketing'), ('Always on', 'Always on'), ('My Own Channel', 'My Own Channel'), ('Subscription', 'Subscription'), ('Internal', 'Internal'), ('None', '--None--')], default='None', null=True),
        ),
    ]
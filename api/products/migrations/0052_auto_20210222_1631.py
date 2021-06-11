# Generated by Django 3.1.6 on 2021-02-22 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0051_auto_20210222_1124"),
    ]

    operations = [
        migrations.AddField(
            model_name="postingrequirement",
            name="posting_requirement_type_de",
            field=models.TextField(
                choices=[
                    ("Location", "Location"),
                    ("Salary Indication", "Salary Indication"),
                    ("Career Level", "Career level"),
                    ("Language Specific", "Language Specific"),
                    ("Contact Information", "Contact Information"),
                    (
                        "Company Registration Information",
                        "Company Registration Information",
                    ),
                    ("Facebook Profile", "Facebook Profile"),
                    ("LinkedIn Profile", "LinkedIn Profile"),
                    ("Xing Profile", "Xing Profile"),
                    ("Hours", "Hours"),
                    ("None", "--None--"),
                ],
                default="None",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="postingrequirement",
            name="posting_requirement_type_en",
            field=models.TextField(
                choices=[
                    ("Location", "Location"),
                    ("Salary Indication", "Salary Indication"),
                    ("Career Level", "Career level"),
                    ("Language Specific", "Language Specific"),
                    ("Contact Information", "Contact Information"),
                    (
                        "Company Registration Information",
                        "Company Registration Information",
                    ),
                    ("Facebook Profile", "Facebook Profile"),
                    ("LinkedIn Profile", "LinkedIn Profile"),
                    ("Xing Profile", "Xing Profile"),
                    ("Hours", "Hours"),
                    ("None", "--None--"),
                ],
                default="None",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="postingrequirement",
            name="posting_requirement_type_nl",
            field=models.TextField(
                choices=[
                    ("Location", "Location"),
                    ("Salary Indication", "Salary Indication"),
                    ("Career Level", "Career level"),
                    ("Language Specific", "Language Specific"),
                    ("Contact Information", "Contact Information"),
                    (
                        "Company Registration Information",
                        "Company Registration Information",
                    ),
                    ("Facebook Profile", "Facebook Profile"),
                    ("LinkedIn Profile", "LinkedIn Profile"),
                    ("Xing Profile", "Xing Profile"),
                    ("Hours", "Hours"),
                    ("None", "--None--"),
                ],
                default="None",
                null=True,
            ),
        ),
    ]
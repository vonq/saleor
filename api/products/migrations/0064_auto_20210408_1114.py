# Generated by Django 3.2 on 2021-04-08 11:14

from django.db import migrations, models
from api.products.models import PostingRequirement as FixedPostingRequirement


def migrate_has_html_posting(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    PostingRequirement = apps.get_model("products", "PostingRequirement")
    products_with_html_posting = Product.objects.filter(has_html_posting=True)
    html_requirement, _ = PostingRequirement.objects.get_or_create(
        posting_requirement_type=FixedPostingRequirement.PostingRequirementType.HTML_POSTING
    )
    for product in products_with_html_posting:
        product.posting_requirements.add(html_requirement)
        product.save()


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0063_hotfix_clear_logo_on_18552"),
    ]

    operations = [
        migrations.AlterField(
            model_name="postingrequirement",
            name="posting_requirement_type",
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
                    ("HTML Posting", "HTML Posting"),
                    ("None", "--None--"),
                ],
                default="None",
                null=True,
            ),
        ),
        migrations.AlterField(
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
                    ("HTML Posting", "HTML Posting"),
                    ("None", "--None--"),
                ],
                default="None",
                null=True,
            ),
        ),
        migrations.AlterField(
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
                    ("HTML Posting", "HTML Posting"),
                    ("None", "--None--"),
                ],
                default="None",
                null=True,
            ),
        ),
        migrations.AlterField(
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
                    ("HTML Posting", "HTML Posting"),
                    ("None", "--None--"),
                ],
                default="None",
                null=True,
            ),
        ),
        migrations.RunPython(
            migrate_has_html_posting, reverse_code=migrations.RunPython.noop
        ),
    ]
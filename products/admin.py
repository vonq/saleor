from django.contrib import admin

from modeltranslation.admin import TranslationAdmin

from api.products.models import (
    Product,
    Channel,
    JobTitle,
    JobFunction,
    Location,
    Industry,
)


@admin.register(Product)
class ProductAdmin(TranslationAdmin):
    fields = [
        "title",
        "url",
        "channel",
        "description",
        "industries",
        "job_functions",
        "is_active",
        "salesforce_product_category",
        "salesforce_industries",
        "locations",
        "similarweb_top_country_shares",
    ]
    filter_horizontal = ("industries", "job_functions", "locations")
    search_fields = ("title", "description")


@admin.register(Channel)
class ChannelAdmin(TranslationAdmin):
    fields = ["name", "url", "type"]
    list_display = ("name", "url", "type")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(JobTitle)
class JobTitleAdmin(TranslationAdmin):
    fields = ["name", "job_function", "industry", "canonical", "alias_of", "active"]
    list_display = (
        "name",
        "job_function",
        "industry",
        "canonical",
        "alias_of",
        "active",
        "frequency",
    )
    list_filter = ("job_function", "canonical", "active")
    search_fields = ("name",)
    ordering = ("-frequency",)


@admin.register(JobFunction)
class JobFunctionAdmin(TranslationAdmin):
    fields = ["name", "parent"]
    list_display = ("name", "parent")
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(TranslationAdmin):
    fields = ("canonical_name", "mapbox_within", "mapbox_place_type")
    list_display = (
        "fully_qualified_place_name",
        "canonical_name",
        "mapbox_within",
        "mapbox_place_type",
    )
    search_fields = ("mapbox_placename", "canonical_name")


@admin.register(Industry)
class IndustryAdmin(TranslationAdmin):
    list_display = ("name",)
    search_fields = ("name",)

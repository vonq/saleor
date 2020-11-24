from django.contrib import admin
from django.db.models import Count

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
        "status",
    ]
    filter_horizontal = ("industries", "job_functions", "locations")
    search_fields = ("title", "description")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "locations":
            # only show Locations marked as "approved" for admin panel selection
            kwargs["queryset"] = Location.objects.filter(approved=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Channel)
class ChannelAdmin(TranslationAdmin):
    fields = ["name", "url", "type"]
    list_display = ("name", "url", "type")
    list_filter = ("type",)
    search_fields = ("name",)


@admin.register(JobTitle)
class JobTitleAdmin(TranslationAdmin):
    fields = ["name", "job_function", "canonical", "alias_of", "active"]
    list_display = (
        "name",
        "job_function",
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
    fields = ("canonical_name", "mapbox_within", "mapbox_place_type", "approved")
    list_display = (
        "full_location_name",
        "approved",
        "canonical_name",
        "mapbox_within",
        "mapbox_place_type",
        "products_count",
    )
    search_fields = ("mapbox_placename", "canonical_name")
    list_filter = ("approved",)

    def products_count(self, location):
        return location.products_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(products_count=Count("products"))
        return queryset


@admin.register(Industry)
class IndustryAdmin(TranslationAdmin):
    list_display = ("name",)
    search_fields = ("name",)

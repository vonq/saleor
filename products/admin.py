from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import Count
from django import forms

from modeltranslation.admin import TranslationAdmin
from rest_framework.utils import json

from api.field_permissions.admin import PermissionBasedFieldsMixin
from api.products.models import (
    Product,
    Channel,
    JobTitle,
    JobFunction,
    Location,
    Industry,
)

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from api.products.models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Product)
class ProductAdmin(PermissionBasedFieldsMixin, TranslationAdmin):
    readonly_fields = [
        "salesforce_id",
        "unit_price",
        "rate_card_price",
    ]

    fields = [
        "title",
        "url",
        "channel",
        "description",
        "industries",
        "job_functions",
        "status",
        "is_active",
        "is_recommended",
        "has_html_posting",
        "salesforce_product_category",
        "salesforce_industries",
        "locations",
        "similarweb_top_country_shares",
        "tracking_method",
        "logo_url",
        "salesforce_product_type",
        "salesforce_cross_postings",
        "duration_days",
        "time_to_process",
        "salesforce_id",
        "unit_price",
        "rate_card_price",
    ]
    filter_horizontal = ("industries", "job_functions", "locations")
    search_fields = ("title", "description")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "locations":
            # only show Locations marked as "approved" for admin panel selection
            kwargs["queryset"] = Location.objects.filter(approved=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = "__all__"

    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        widget=FilteredSelectMultiple(verbose_name="products", is_stacked=False),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["products"].initial = self.instance.product_set.all()

    def _save_m2m(self):
        super()._save_m2m()
        self.instance.product_set.set(self.cleaned_data["products"])


@admin.register(Channel)
class ChannelAdmin(TranslationAdmin):
    form = ChannelForm
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


class MapboxAutocompleteWidget(forms.widgets.Input):
    template_name = "django/forms/widgets/mapbox.html"


class EditLocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ("canonical_name", "mapbox_place_type", "mapbox_within")


class NewLocationForm(forms.ModelForm):
    location_name = forms.CharField(
        widget=MapboxAutocompleteWidget(attrs={"id": "mapbox_placename"})
    )
    mapbox_hidden = forms.CharField(
        widget=forms.HiddenInput(attrs={"id": "geocoder-data"})
    )

    class Meta:
        model = Location
        fields = ()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("mapbox_hidden"):
            return cleaned_data

        self.instance = Location.from_mapbox_result(
            json.loads(cleaned_data["mapbox_hidden"])
        )
        if Location.objects.filter(
            mapbox_id=self.instance.mapbox_id, approved=True
        ).exists():
            self.add_error("location_name", "This location is already present.")
            return cleaned_data

        if Location.objects.filter(
            mapbox_id=self.instance.mapbox_id, approved=False
        ).exists():
            self.instance = Location.objects.get(mapbox_id=self.instance.mapbox_id)

        # locations manually added via admin
        # will be considered approved by default
        self.instance.approved = True

        return cleaned_data


@admin.register(Location)
class LocationAdmin(TranslationAdmin):
    fields = (
        "canonical_name",
        "mapbox_within",
        "mapbox_place_type",
        "approved",
        "mapbox_id",
    )
    list_display = (
        "full_location_name",
        "approved",
        "canonical_name",
        "mapbox_within",
        "mapbox_place_type",
        "products_count",
        "mapbox_id",
    )
    search_fields = ("mapbox_placename", "canonical_name")
    list_filter = ("approved",)

    def products_count(self, location):
        return location.products_count

    def add_view(self, request, form_url="", extra_context=None):
        self.form = NewLocationForm
        self.fieldsets = (
            (
                None,
                {
                    "fields": ("location_name", "mapbox_hidden"),
                },
            ),
        )
        self.fields = ()

        return super().add_view(request, form_url, {"mapbox_key": settings.MAPBOX_KEY})

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.form = EditLocationForm
        self.fields = (
            "canonical_name",
            "mapbox_within",
            "mapbox_place_type",
            "mapbox_context",
            "approved",
        )
        self.readonly_fields = ("mapbox_context",)
        self.fieldsets = ()
        return super().change_view(request, object_id, form_url, extra_context)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(products_count=Count("products"))
        return queryset


@admin.register(Industry)
class IndustryAdmin(TranslationAdmin):
    list_display = ("name",)
    search_fields = ("name",)

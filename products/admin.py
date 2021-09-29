from ajax_select.fields import AutoCompleteSelectField
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from image_cropping import ImageCroppingMixin
from modeltranslation.admin import TranslationAdmin
from mptt.admin import MPTTModelAdmin
from mptt.forms import TreeNodeChoiceField
from rest_framework.utils import json
from reversion_compare.admin import CompareVersionAdmin

from api.field_permissions.admin import PermissionBasedFieldsMixin
from api.products.models import (
    Product,
    Channel,
    JobTitle,
    JobFunction,
    Location,
    Industry,
    Category,
    PostingRequirement,
)
from api.products.models import Profile
from api.products.signals import channel_updated, product_updated


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    readonly_fields = (
        "content_type",
        "user",
        "action_time",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )
    list_display = ["object_repr", "user", "content_type", "action_flag", "action_time"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, *args, **kwargs):
        return False

    def has_add_permission(self, request):
        return False


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class JobFunctionTreeModelInlineForm(forms.ModelForm):
    jobfunction = TreeNodeChoiceField(queryset=JobFunction.objects.all())


class JobFunctionModelInline(admin.TabularInline):
    model = Product.job_functions.through
    form = JobFunctionTreeModelInlineForm
    extra = 0


class ProductForm(forms.ModelForm):
    unit_price = forms.FloatField(required=True, label="List Price (€)")
    rate_card_price = forms.FloatField(required=True, label="Rate Card Price (€)")
    purchase_price = forms.FloatField(required=True, label="Purchase Price (€)")
    customer_id = AutoCompleteSelectField(
        "customer", required=False, help_text=None, label="Customer ID"
    )

    class Meta:
        model = Product
        fields = "__all__"
        help_texts = {
            "time_to_process": "This is auto-calculated by summing up the supplier time to process and vonq time to process.",
            "available_in_hapi": "Products must be of type Job Board, Social or Google to be available in HAPI",
        }
        widgets = {
            "remarks": forms.Textarea(
                attrs={
                    "rows": "10",
                    "cols": "100",
                    "maxlength": "32768",
                }
            ),
        }

    @staticmethod
    def is_valid_cropping_area(cropping_string):
        cropping = cropping_string.split(",")
        cropping = tuple([int(t) for t in cropping])
        x_point = (cropping[0], cropping[1])
        y_point = (cropping[2], cropping[3])
        return x_point != y_point

    def _save_m2m(self):
        super()._save_m2m()
        product_updated.send(sender=self.instance.__class__, instance=self.instance)

    def save(self, commit=True):
        self.instance.salesforce_sync_status = Product.SyncStatusChoices.PENDING
        return super().save(commit)

    def clean_cropping_rectangle(self):
        if not self.cleaned_data["cropping_rectangle"]:
            return self.cleaned_data["cropping_rectangle"]

        crop_rectangle = self.cleaned_data["cropping_rectangle"]
        if not self.is_valid_cropping_area(crop_rectangle):
            raise ValidationError("Invalid cropping area, must be non-null")
        return crop_rectangle

    def clean_cropping_square(self):
        if not self.cleaned_data["cropping_square"]:
            return self.cleaned_data["cropping_square"]

        crop_square = self.cleaned_data["cropping_square"]
        if not self.is_valid_cropping_area(crop_square):
            raise ValidationError("Invalid cropping area, must be non-null")
        return crop_square


@admin.register(Product)
class ProductAdmin(
    CompareVersionAdmin,
    ImageCroppingMixin,
    PermissionBasedFieldsMixin,
    TranslationAdmin,
    DynamicArrayMixin,
):
    form = ProductForm
    list_display = [
        "external_product_name",
        "url",
        "created",
        "updated",
        "status",
        "salesforce_sync_status",
    ]
    readonly_fields = [
        "external_product_name",
        "product_id",
        "logo_url",
        "logo_square_url",
        "logo_rectangle_url",
        "salesforce_id",
        "salesforce_sync_status",
        "salesforce_last_sync",
        "updated",
        "created",
        "time_to_process",
    ]
    inlines = (JobFunctionModelInline,)

    def time_to_process(self, product):
        return (product.supplier_time_to_process or 0) + (
            product.vonq_time_to_process or 0
        )

    time_to_process.short_description = "Time to process"

    fields = [
        "title",
        "external_product_name",
        "url",
        "channel",
        "description",
        "industries",
        "categories",
        "job_functions",
        "status",
        "available_in_jmp",
        "available_in_ats",
        "is_recommended",
        "remarks",
        "reason",
        "customer_id",
        "salesforce_product_category",
        "locations",
        "tracking_method",
        "posting_requirements",
        "logo_rectangle_url",
        "logo_rectangle_uncropped",
        "cropping_rectangle",
        "logo_square_url",
        "logo_square_uncropped",
        "cropping_square",
        "salesforce_product_type",
        "cross_postings",
        "duration_days",
        "time_to_process",
        "supplier_time_to_process",
        "supplier_setup_time",
        "vonq_time_to_process",
        "product_id",
        "unit_price",
        "rate_card_price",
        "rate_card_url",
        "purchase_price",
        "pricing_method",
        "purchase_price_method",
        "salesforce_product_solution",
        "salesforce_sync_status",
        "salesforce_last_sync",
        "salesforce_id",
        "created",
        "updated",
    ]
    filter_horizontal = (
        "industries",
        "categories",
        "job_functions",
        "locations",
        "posting_requirements",
    )
    search_fields = ("channel__name", "title_en", "title_de", "title_nl")
    autocomplete_fields = ("channel",)

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
    salesforce_account_id = AutoCompleteSelectField(
        "account", required=True, help_text=None, label="Salesforce Account"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["products"].initial = self.instance.product_set.all()

    def _save_m2m(self):
        super()._save_m2m()
        self.instance.product_set.set(self.cleaned_data["products"])
        channel_updated.send(sender=self.instance.__class__, instance=self.instance)

    def save(self, commit=True):
        self.instance.salesforce_sync_status = Channel.SyncStatusChoices.PENDING
        return super().save(commit)


class JobTitleAdminForm(forms.ModelForm):
    class Meta:
        model = JobTitle
        fields = ["name", "job_function", "canonical", "alias_of", "active"]

    def clean(self):
        cleaned_data = super().clean()
        is_canonical = cleaned_data.get("canonical")
        alias = cleaned_data.get("alias_of")
        if is_canonical and alias is not None:
            raise ValidationError("A canonical job title can't also be an alias.")
        return cleaned_data


@admin.register(Channel)
class ChannelAdmin(CompareVersionAdmin, TranslationAdmin):
    form = ChannelForm
    ordering = ["name"]
    list_display = ("name", "url", "type", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)
    readonly_fields = (
        "salesforce_id",
        "salesforce_sync_status",
        "salesforce_last_sync",
    )


@admin.register(JobTitle)
class JobTitleAdmin(TranslationAdmin):
    form = JobTitleAdminForm
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
class TreeJobFunctionAdmin(TranslationAdmin, MPTTModelAdmin):
    fields = ["name", "parent", "vonq_taxonomy_value"]
    list_display = ("name", "parent")
    search_fields = ("name",)
    mptt_level_indent = 36


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
            "mapbox_id",
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


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ("name", "type")
    search_fields = ("name",)
    list_filter = ("type",)


@admin.register(PostingRequirement)
class PostingRequirementAdmin(TranslationAdmin):
    list_display = ("posting_requirement_type",)


def get_admin_from_sf_uuid(request, uuid):
    """
    Small utility view to redirect an admin/edit/<salesforce_uuid>
    request to the admin panel edit view for the product
    """
    try:
        product = Product.objects.get(salesforce_id=uuid)
    except Product.DoesNotExist:
        raise Http404()

    return redirect(reverse("admin:products_product_change", args=(product.id,)))

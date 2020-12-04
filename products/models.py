import itertools
import uuid
from typing import List, Iterable

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import FieldError
from django.db import models
from django.db.models import QuerySet, Q, Max, Func, F
from django.db.models.functions import Cast
from modeltranslation.fields import TranslationFieldDescriptor

from api.field_permissions.models import FieldPermissionModelMixin
from api.products.geocoder import Geocoder
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class AcrossLanguagesQuerySet(QuerySet):
    def filter_across_languages(self, **kwargs):
        """
        A convenience method to allow querying translated fields
        for every available translation.
        """

        query = Q()

        # split the filter string
        for k, v in kwargs.items():
            field, *q_type = k.split("__")

            # is this field a multi language field?
            if not isinstance(getattr(self.model, field), TranslationFieldDescriptor):
                raise FieldError(f"Field {field} is not a TranslationField")

            # do we have a query type?
            query_type = f"{'__'}{q_type[0]}" if q_type else ""

            # explicitly set a postfix language according to the supported languages
            for language in settings.LANGUAGES:
                query |= Q(**{f"{field}_{language[0]}{query_type}": v})

        return self.filter(query)


class Industry(models.Model):
    name = models.CharField(max_length=100)

    objects = AcrossLanguagesQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "industries"


class JobFunction(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "JobFunction", on_delete=models.CASCADE, null=True, blank=True
    )

    objects = AcrossLanguagesQuerySet.as_manager()

    def __str__(self):
        return self.name


class JobTitle(models.Model):
    name = models.CharField(max_length=100)
    job_function = models.ForeignKey(
        "JobFunction", on_delete=models.CASCADE, null=True, blank=True
    )
    frequency = models.IntegerField(default=0, null=True, blank=True)
    canonical = models.BooleanField(default=True)
    alias_of = models.ForeignKey(
        "JobTitle", on_delete=models.CASCADE, null=True, blank=True
    )
    active = models.BooleanField(default=True)

    objects = AcrossLanguagesQuerySet.as_manager()

    def __str__(self):
        return self.name


class Location(models.Model):
    # https://docs.mapbox.com/api/search/#data-types
    TYPE_CHOICES = [
        ("place", "City, town or village"),
        ("district", "Prefecture or county"),
        ("region", "State or province"),
        ("country", "Country"),
        ("continent", "Continent"),
        ("world", "International"),
    ]

    @property
    def fully_qualified_place_name(self):
        return self.mapbox_placename

    canonical_name = models.CharField(max_length=200, null=True)

    @property
    def place_type(self):
        return self.mapbox_place_type

    @property
    def geocoder_id(self):
        return self.mapbox_id

    @property
    def short_code(self):
        return self.mapbox_shortcode

    @property
    def within(self):
        return self.mapbox_within

    @property
    def context(self):
        return self.mapbox_context

    @property
    def full_location_name(self):
        if self.mapbox_within:
            return f"{self.canonical_name}, {self.mapbox_within.full_location_name}"
        return self.canonical_name

    desq_name_en = models.CharField(max_length=100, null=True)
    desq_country_code = models.CharField(max_length=3, null=True)

    country_code = models.CharField(max_length=10, null=True, blank=True)

    # mapbox fields
    mapbox_id = models.CharField(max_length=50, null=True, blank=True)
    mapbox_text = models.CharField(max_length=100, null=True, blank=True)
    mapbox_placename = models.CharField(max_length=300, null=True, blank=True)
    mapbox_context = ArrayField(
        base_field=models.CharField(max_length=50, blank=False), default=list
    )
    mapbox_place_type = ArrayField(
        base_field=models.CharField(
            max_length=500, null=True, blank=True, choices=TYPE_CHOICES
        ),
        default=list,
    )
    mapbox_shortcode = models.CharField(max_length=10, null=True, blank=True)
    mapbox_within = models.ForeignKey(
        "Location",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="mapbox_location",
    )  # link up

    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_location_name} ({', '.join(self.place_type)})"

    @classmethod
    def get_country_short_code(cls, location: dict):
        if "country" in location["place_type"]:
            return location["properties"].get("short_code")
        if "context" in location:
            return location["context"][-1].get("short_code")
        return None

    @classmethod
    def from_mapbox_result(cls, mapbox_response: dict):
        location = cls()
        location.mapbox_id = mapbox_response["id"]
        location.mapbox_placename = mapbox_response["place_name"]
        location.canonical_name = mapbox_response["text"]
        location.mapbox_text = mapbox_response["text"]
        location.mapbox_place_type = []
        location.country_code = cls.get_country_short_code(mapbox_response)
        for place_type in mapbox_response["place_type"]:
            location.mapbox_place_type.append(place_type)
        if "short_code" in mapbox_response["properties"]:
            location.mapbox_shortcode = mapbox_response["properties"]["short_code"]
        if "context" in mapbox_response:
            country = mapbox_response["place_name"].split(",")[-1].strip()
            continent = Geocoder.get_continent_for_country(country)
            location.mapbox_context = [
                place["id"] for place in mapbox_response["context"]
            ]
            location.mapbox_context.extend([f"continent.{continent}", "world"])
            country_entity = Location.objects.filter(
                canonical_name=country, mapbox_place_type=["country"]
            )
            if country_entity.exists():
                location.mapbox_within_id = country_entity.first().id
        return location

    @classmethod
    def from_mapbox_autocomplete_response(cls, mapbox_response: list):
        locations = [cls.from_mapbox_result(result) for result in mapbox_response]

        existing = cls.objects.filter(
            mapbox_id__in=[location.mapbox_id for location in locations]
        )
        existing_ids = [location.mapbox_id for location in existing]

        created = Location.objects.bulk_create(
            filter(lambda x: x.mapbox_id not in existing_ids, locations)
        )

        return list(
            itertools.chain(
                sorted(existing, key=lambda x: x.products.count(), reverse=True),
                created,
            )
        )

    @classmethod
    def list_context_locations_ids(cls, location_ids: Iterable[str]) -> List[str]:
        qs = cls.objects.filter(id__in=location_ids)

        if not qs.exists():
            return []

        return list(
            itertools.chain(
                qs.values_list("mapbox_id", flat=True),
                itertools.chain.from_iterable(
                    qs.values_list("mapbox_context", flat=True)
                ),
            )
        )


class Channel(models.Model):
    salesforce_id = models.CharField(max_length=20, null=True)
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=300)
    TYPE_CHOICES = [
        ("job board", "Job Board"),
        ("social media", "Social Media"),
        ("community", "Community"),
        ("publication", "Publication"),
        ("aggregator", "Aggregator"),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="job board")

    def __str__(self):
        return str(self.name)


class IndexSearchableProductMixin:
    industries: QuerySet
    job_functions: QuerySet
    locations: QuerySet
    similarweb_top_country_shares: dict
    status: str
    is_active: bool

    @property
    def all_industries(self) -> Iterable["Industry"]:
        return self.industries.all()

    @property
    def all_job_functions(self) -> Iterable["JobFunction"]:
        return self.job_functions.all()

    @property
    def all_locations(self) -> Iterable["Location"]:
        return self.locations.all()

    @property
    def searchable_industries_ids(self):
        return [industry.id for industry in self.all_industries]

    @property
    def filterable_status(self):
        return self.status or "None"

    @property
    def searchable_industries_names(self):
        return [industry.name for industry in self.all_industries]

    @property
    def searchable_job_functions_ids(self):
        return [function.id for function in self.all_job_functions]

    @property
    def searchable_job_functions_names(self):
        return [function.name for function in self.all_job_functions]

    @property
    def searchable_job_titles_ids(self):
        return [
            jobtitle.id
            for jobtitle in itertools.chain.from_iterable(
                [function.jobtitle_set.all() for function in self.all_job_functions]
            )
        ]

    @property
    def searchable_job_titles_names(self) -> List[str]:
        return [
            jobtitle.name
            for jobtitle in itertools.chain.from_iterable(
                [function.jobtitle_set.all() for function in self.all_job_functions]
            )
        ]

    @property
    def searchable_locations_ids(self):
        return [location.id for location in self.all_locations]

    @property
    def searchable_locations_names(self):
        return [location.fully_qualified_place_name for location in self.all_locations]

    @property
    def searchable_locations_context_ids(self):
        def location_id_from_mapbox_id(mapbox_id):
            location_for_mapbox_id = Location.objects.filter(mapbox_id=mapbox_id)
            if not location_for_mapbox_id.exists():
                return

            # Remember: we might have duplicates here...
            # FIXME with a UNIQUE constraint on mapbox_id for Locations table
            location = location_for_mapbox_id[0]
            return location.id

        return list(
            itertools.chain.from_iterable(
                [
                    [
                        location_id_from_mapbox_id(location_id)
                        for location_id in location.mapbox_context
                    ]
                    for location in self.all_locations
                ]
            )
        )

    @property
    def searchable_locations_context_mapbox_ids(self):
        mapbox_context_ids = itertools.chain.from_iterable(
            [
                [mapbox_id for mapbox_id in location.mapbox_context]
                for location in self.all_locations
            ]
        )

        mapbox_ids = [location.mapbox_id for location in self.all_locations]

        return list(itertools.chain(mapbox_context_ids, mapbox_ids))

    @property
    def searchable_locations_context_names(self):
        def fully_qualified_place_name_from_mapbox_id(mapbox_id):
            location_for_mapbox_id = Location.objects.filter(mapbox_id=mapbox_id)
            if not location_for_mapbox_id.exists():
                return

            # Remember: we might have duplicates here...
            # FIXME with a UNIQUE constraint on mapbox_id for Locations table
            location = location_for_mapbox_id[0]
            return location.fully_qualified_place_name or location.mapbox_placename

        return list(
            itertools.chain.from_iterable(
                [
                    [
                        fully_qualified_place_name_from_mapbox_id(location_id)
                        for location_id in location.mapbox_context
                    ]
                    for location in self.all_locations
                ]
            )
        )

    @property
    def primary_similarweb_location(self):
        top_country_shares = self.similarweb_top_country_shares
        if not top_country_shares:
            return

        return sorted(top_country_shares, key=top_country_shares.get, reverse=True)[0]

    @property
    def secondary_similarweb_location(self):
        top_country_shares = self.similarweb_top_country_shares
        if not top_country_shares or len(top_country_shares) < 2:
            return

        return sorted(top_country_shares, key=top_country_shares.get, reverse=True)[1]

    @property
    def maximum_locations_cardinality(self):
        if self.locations.count() == 0:
            return 0
        return self.locations.annotate(
            locations_cardinality=Cast(
                Max(Func(F("mapbox_context"), function="CARDINALITY")),
                models.IntegerField(),
            )
        ).values_list("locations_cardinality", flat=True)[0]


class Product(FieldPermissionModelMixin, models.Model, IndexSearchableProductMixin):
    def set_product_id(self):
        if self.desq_product_id:
            product_id = self.desq_product_id
        elif self.salesforce_id:
            product_id = self.salesforce_id
        else:
            product_id = uuid.uuid4()
        if product_id != self.product_id:
            self.product_id = product_id

    def save(self, *args, **kwargs):
        self.set_product_id()
        super(Product, self).save(*args, **kwargs)

    class Meta:
        permissions = (
            # field level permissions, formatted as "can_{view|change}_{modelname}_{fieldname}"
            # Used to further restrict the ability of a user
            # to make changes to a model from the admin panel.
            # This will only apply to users/groups who can already change a model, and only
            # for fields explicitly declared in these permission field
            # https://docs.djangoproject.com/en/3.1/ref/models/options/#permissions
            ("can_view_product_industries", "Can view product industries"),
            ("can_change_product_industries", "Can change product industries"),
            ("can_view_product_job_functions", "Can view product job functions"),
            ("can_change_product_job_functions", "Can change product job functions"),
        )

    class TrackingMethod(models.TextChoices):
        FIXED = "Fixed duration", _("Fixed duration")
        SLOTS = "Slots", _("Slots")
        FREE = "Free", _("Free")
        PROGRAMMATIC = "Programmatic", _("Programmatic")
        NA = "N/A", _("N/A")

    class SalesforceProductCategory(models.TextChoices):
        WALLET = "Wallet", _("Wallet")
        INTERNAL = "Internal Product", _("Internal Product")
        GENERIC = "Generic Product", _("Generic Product")
        CUSTOMER_SPECIFIC = "Customer Specific Product", _("Customer Specific Product")
        NONE = None, _("--None--")

    class SalesforceProductType(models.TextChoices):
        SOCIAL = "Social", _("Social")
        PRINT = "Print / Offline", _("Print / Offline")
        HANDLING_FEE = "Handling fee", _("Handling fee")
        IMAGE_CREATION = "Image creation", _("Image creation")
        WEBSITE_CREATION = "Website creation", _("Website creation")
        VONQ_SERVICES = "VONQ Services/Hours", _("VONQ Services/Hours")
        VIDEO_CREATION = "Video creation", _("Video creation")
        TEXT_SERVICES = "Text services", _("Text services")
        OTHER = "Other", _("Other")
        FINANCE = "Finance", _("Finance")
        JOB_BOARD = "Jobboard", _("Jobboard")
        SUBSCRIPTION = "Subscription", _("Subscription")
        WALLET = "Wallet", _("Wallet")
        GOOGLE = "Google", _("Google")
        NONE = None, _("--None--")

    @property
    def external_product_name(self):
        if self.channel and self.channel.name:
            return self.channel.name + " - " + self.title
        return self.title

    title = models.CharField(max_length=200, null=True)
    url = models.URLField(max_length=300, null=True, blank=True)
    channel = models.ForeignKey(
        Channel, on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField(default="", null=True, blank=True)
    industries = models.ManyToManyField(
        Industry,
        related_name="industries",
        related_query_name="industry",
        blank=True,
    )
    job_functions = models.ManyToManyField(
        JobFunction,
        related_name="job_functions",
        related_query_name="job_function",
        blank=True,
    )
    logo_url = models.CharField(max_length=300, null=True, blank=True, default=None)
    is_active = models.BooleanField(default=False)

    available_in_ats = models.BooleanField(default=True)
    available_in_jmp = models.BooleanField(default=True)

    duration_days = models.IntegerField(null=True, blank=True)
    time_to_process = models.IntegerField(null=True, blank=True)

    unit_price = models.FloatField(null=True, blank=True)
    rate_card_price = models.FloatField(null=True, blank=True)

    locations = models.ManyToManyField(Location, related_name="products", blank=True)

    interests = models.CharField(max_length=200, default="", blank=True, null=True)

    status = models.CharField(
        max_length=12,
        choices=[
            ("Blacklisted", "Blacklisted"),
            ("Disabled", "Disabled"),
            ("Negotiated", "Negotiated"),
            ("Trial", "Trial"),
            (None, "--None--"),
        ],
        default=None,
        blank=True,
        null=True,
    )

    salesforce_id = models.CharField(max_length=36, null=True, blank=True)
    product_id = models.CharField(
        max_length=36,
        unique=True,
        default=uuid.uuid4,
    )

    salesforce_product_type = models.TextField(
        choices=SalesforceProductType.choices,
        default=SalesforceProductType.NONE,
        null=True,
    )
    salesforce_product_category = models.TextField(
        choices=SalesforceProductCategory.choices,
        default=SalesforceProductCategory.NONE,
        null=True,
    )
    salesforce_industries = ArrayField(
        base_field=models.CharField(max_length=80, blank=False), default=list
    )
    salesforce_job_categories = ArrayField(
        base_field=models.CharField(max_length=80, blank=False), default=list
    )
    salesforce_cross_postings = models.JSONField(null=True, blank=True, default=list)

    is_recommended = models.BooleanField(default=False)
    has_html_posting = models.BooleanField(default=False)

    tracking_method = models.TextField(
        choices=TrackingMethod.choices, default=TrackingMethod.FIXED
    )

    desq_product_id = models.CharField(max_length=10, null=True, blank=True)

    similarweb_estimated_monthly_visits = models.CharField(
        max_length=300, null=True, blank=True, default=None
    )
    similarweb_top_country_shares = models.JSONField(
        null=True, blank=True, default=dict
    )

    # similarweb_top_country_shares contains a dictionary of countries (in short alpha_2 format)
    # and the share of traffic that comes from that country, like so:
    # {
    #     'de': 94,
    #     'fr': 1,
    #     'ph': 0,
    #     'rs': 0,
    #     'za': 0
    # }

    objects = AcrossLanguagesQuerySet.as_manager()

    def __str__(self):
        return str(self.title) + " : " + str(self.url)


class Profile(models.Model):
    class Type(models.TextChoices):
        JMP = "jmp", _("JMP")
        ATS = "ats", _("ATS")
        INTERNAL = "internal", _("Internal")

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.TextField(
        max_length=15, blank=True, choices=Type.choices, default=Type.INTERNAL
    )


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "profile"):
        Profile.objects.create(user=instance)
    instance.profile.save()

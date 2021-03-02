import itertools
import re
import uuid
import datetime
from typing import List, Iterable
from storages.backends.s3boto3 import S3Boto3Storage
from dateutil.tz import UTC
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import FieldError
from django.db import models
from django.db.models import QuerySet, Q, Max, Func, F, Case, When
from django.db.models.functions import Cast
from image_cropping import ImageRatioField
from modeltranslation.fields import TranslationFieldDescriptor
from mptt.models import MPTTModel
from PIL import Image
from api.field_permissions.models import FieldPermissionModelMixin
from api.products.geocoder import Geocoder
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from api.settings import AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME
import requests
from django.core.exceptions import ValidationError
import tempfile
from io import BytesIO
from django.core.files import File


class CreatedUpdatedModelMixin(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class SFSyncable(CreatedUpdatedModelMixin):
    class Meta:
        abstract = True

    class SyncStatusChoices(models.TextChoices):
        SYNCED = "synced"
        UNSYNCED = "unsynced"
        PENDING = "pending"

    salesforce_sync_status = models.CharField(
        max_length=8,
        choices=SyncStatusChoices.choices,
        default=SyncStatusChoices.UNSYNCED,
    )
    salesforce_last_sync = models.DateTimeField(default=None, null=True)

    def mark_as_synced(self):
        self.salesforce_sync_status = self.SyncStatusChoices.SYNCED
        self.salesforce_last_sync = datetime.datetime.now(tz=UTC)
        self.save()


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

    # don't allow deletion of vonq industries that have mappings to pkb industries
    vonq_taxonomy_value = models.ForeignKey(
        "vonqtaxonomy.Industry", on_delete=models.RESTRICT, null=False, blank=False
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "industries"


class Category(models.Model):
    name = models.CharField(max_length=100)

    objects = AcrossLanguagesQuerySet.as_manager()

    class Type(models.TextChoices):
        CAREER_LEVEL = (
            "career level",
            _("Career level"),
        )
        INDUSTRY = (  # placeholder for future reference
            "industry",
            _("Industry"),
        )

    type = (
        models.CharField(max_length=50, null=True, blank=True, choices=Type.choices),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"


class JobFunction(MPTTModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "JobFunction",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        name="parent",
        related_name="children",
    )
    # don't allow deletion of vonq categories that have mappings to job functions
    vonq_taxonomy_value = models.ForeignKey(
        "vonqtaxonomy.JobCategory", on_delete=models.RESTRICT, null=False, blank=False
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


class Location(CreatedUpdatedModelMixin):
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

    mapbox_bounding_box = ArrayField(
        base_field=models.FloatField(null=False, blank=False), default=list
    )

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
        location.mapbox_bounding_box = mapbox_response.get("bbox", [])
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
        locations_ids = [location.mapbox_id for location in locations]

        existing = cls.objects.filter(mapbox_id__in=locations_ids).order_by(
            Case(
                *[
                    When(mapbox_id=mapbox_id, then=pos)
                    for pos, mapbox_id in enumerate(locations_ids)
                ]
            )
        )

        existing_ids = [location.mapbox_id for location in existing]

        if existing.count() < len(locations):
            created = Location.objects.bulk_create(
                filter(lambda x: x.mapbox_id not in existing_ids, locations)
            )

            return itertools.chain(
                existing,
                created,
            )

        return existing

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


class Channel(SFSyncable):
    class Type(models.TextChoices):
        JOB_BOARD = (
            "job board",
            _("Job Board"),
        )
        SOCIAL_MEDIA = (
            "social media",
            _("Social Media"),
        )
        COMMUNITY = (
            "community",
            _("Community"),
        )
        PUBLICATION = (
            "publication",
            _("Publication"),
        )
        AGGREGATOR = (
            "aggregator",
            _("Aggregator"),
        )
        NOT_CHANNEL = (
            "not channel",
            _("Not Channel"),
        )

    salesforce_id = models.CharField(max_length=20, null=True)
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=300)
    is_active = models.BooleanField(default=False)
    salesforce_account_id = models.CharField(
        max_length=20, null=True, verbose_name="Salesforce Account"
    )
    type = models.CharField(max_length=20, choices=Type.choices, default="job board")

    def __str__(self):
        return str(self.name)


class PostingRequirement(models.Model):
    class PostingRequirementType(models.TextChoices):
        LOCATION = "Location", _("Location")
        SALARY_INDICATION = "Salary Indication", _("Salary Indication")
        CAREER_LEVEL = "Career Level", _("Career level")
        LANGUAGE_SPECIFIC = "Language Specific", _("Language Specific")
        CONTACT_INFO = "Contact Information", _("Contact Information")
        COMPANY_REGISTRATION_INFO = (
            "Company Registration Information",
            _("Company Registration Information"),
        )
        FB_PROFILE = "Facebook Profile", _("Facebook Profile")
        LI_PROFILE = "LinkedIn Profile", _("LinkedIn Profile")
        XING_PROFILE = "Xing Profile", _("Xing Profile")
        HOURS = "Hours", _("Hours")
        NONE = None, _("--None--")

    posting_requirement_type = models.TextField(
        choices=PostingRequirementType.choices,
        default=PostingRequirementType.NONE,
        null=True,
    )

    def __str__(self):
        return str(self.posting_requirement_type)


class IndexSearchableProductMixin:
    industries: QuerySet
    job_functions: QuerySet
    locations: QuerySet
    similarweb_top_country_shares: dict
    status: str
    external_product_name: str
    is_active: bool

    @property
    def all_industries(self) -> Iterable["Industry"]:
        return self.industries.all()

    @property
    def all_job_functions(self) -> Iterable["JobFunction"]:
        return self.job_functions.all()

    @property
    def all_descendants_job_functions(self) -> Iterable["JobFunction"]:
        return list(
            set(
                function
                for function in itertools.chain.from_iterable(
                    [
                        job_function.get_descendants()
                        for job_function in self.all_job_functions
                    ]
                )
            )
        )

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

    def _job_title_info_from_function(self, job_function_iterator, job_title_field):
        return list(
            set(
                getattr(jobtitle, job_title_field)
                for jobtitle in itertools.chain.from_iterable(
                    [function.jobtitle_set.all() for function in job_function_iterator]
                )
            )
        )

    @property
    def searchable_job_titles_ids(self):
        return self._job_title_info_from_function(self.all_job_functions, "id")

    @property
    def searchable_job_titles_names(self) -> List[str]:
        return self._job_title_info_from_function(self.all_job_functions, "name")

    @property
    def searchable_descendants_job_titles_ids(self):
        return self._job_title_info_from_function(
            self.all_descendants_job_functions, "id"
        )

    @property
    def searchable_descendants_job_titles_names(self) -> List[str]:
        return self._job_title_info_from_function(
            self.all_descendants_job_functions, "name"
        )

    @property
    def searchable_locations_ids(self):
        return [location.id for location in self.all_locations]

    @property
    def searchable_locations_mapbox_ids(self):
        return [location.mapbox_id for location in self.all_locations]

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
            set(
                list(
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

        return list(set(list(itertools.chain(mapbox_context_ids, mapbox_ids))))

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
            set(
                list(
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

    @property
    def searchable_product_title(self):
        return self.external_product_name

    @property
    def is_addon(self):
        return self.salesforce_product_type in Product.SalesforceProductType.addons()

    @property
    def is_product(self):
        return self.salesforce_product_type in Product.SalesforceProductType.products()

    @property
    def channel_type(self):
        if self.channel and self.channel.type:
            return self.channel.type

    @property
    def is_generic(self):
        return (
            self.industries.count() == 0
            # TODO migrate industry values instead, use "all" root job function
            or self.industries.filter(name_en="Generic").exists()
        ) and self.job_functions.count() == 0

    @property
    def is_international(self):
        return self.locations.count() == 0 or any(
            [location.within is None for location in self.locations.all()]
        )


class Product(FieldPermissionModelMixin, SFSyncable, IndexSearchableProductMixin):
    def set_product_id(self):
        if self.desq_product_id:
            product_id = self.desq_product_id
        elif self.salesforce_id:
            product_id = self.salesforce_id
        else:
            if re.match(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[45][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
                str(self.product_id),
                re.I,
            ):
                product_id = self.product_id
            else:
                product_id = uuid.uuid4()
        if product_id != self.product_id:
            self.product_id = product_id

    def generate_cropped_images(self):
        def crop_image(cropping_str, image, name):
            cropping = cropping_str.split(",")
            cropping = tuple([int(t) for t in cropping])
            img_io = BytesIO()
            cropped_img = image.crop(cropping)
            cropped_img.save(img_io, format="png")
            return File(img_io, name=name)

        def should_crop_logo() -> bool:
            """ Returns whether the cropping process should de executed. Functions are used for lazy evaluation """

            def is_newly_uploaded_logo():
                return not current_obj or self.logo != current_obj.logo

            def selections_changed():
                return (
                    self.cropping_square != current_obj.cropping_square
                    or self.cropping_rectangle != current_obj.cropping_rectangle
                )

            def selections_exist():
                return self.cropping_square and self.cropping_rectangle

            return (
                self.logo
                and selections_exist()
                and (is_newly_uploaded_logo() or selections_changed())
            )

        def load_image(temporary_file_path, content):
            temporary_file_path.write(content)
            temporary_file_path.seek(0)
            return Image.open(temporary_file_path.name)

        current_obj = Product.objects.filter(id=self.id).first()
        if should_crop_logo():
            if not current_obj or self.logo != current_obj.logo:
                # Saves to upload the new logo
                super(Product, self).save()
            response = requests.get(self.logo_url)
            with tempfile.NamedTemporaryFile() as fp:
                img = load_image(fp, response.content)
                self.logo_rectangle = crop_image(
                    self.cropping_rectangle, img, "rectangle.png"
                )
                self.logo_square = crop_image(self.cropping_square, img, "square.png")

    def save(self, *args, **kwargs):
        self.set_product_id()
        self.generate_cropped_images()
        super(Product, self).save(*args, **kwargs)

    class Logo:
        @staticmethod
        def logo_path(instance, filename):
            return "{0}/{1}".format(instance.product_id, filename)

        @staticmethod
        def validate_logo_size(value):
            filesize = value.size

            if filesize > 1048576:
                raise ValidationError(
                    "The maximum file size that can be uploaded is 1MB"
                )
            else:
                return value

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

    class SalesforceProductSolution(models.TextChoices):
        AWARENESS = "Awareness", _("Awareness")
        JOB_MARKETING = "Job Marketing", _("Job Marketing")
        ALWAYS_ON = "Always on", _("Always on")
        MY_OWN_CHANNEL = "My Own Channel", _("My Own Channel")
        SUBSCRIPTION = "Subscription", _("Subscription")
        INTERNAL = "Internal", _("Internal")
        NONE = None, _("--None--")

    class Status(models.TextChoices):
        BLACKLISTED = (
            "Blacklisted",
            _("Blacklisted"),
        )
        DISABLED = (
            "Disabled",
            _("Disabled"),
        )
        NEGOTIATED = (
            "Negotiated",
            _("Negotiated"),
        )
        TRIAL = (
            "Trial",
            _("Trial"),
        )
        NONE = (
            None,
            _("--None--"),
        )

    class PurchasePriceMethodType(models.TextChoices):
        FIXED = "Fixed", _("Fixed")
        VARIABLE = "Variable", _("Variable")
        NONE = None, _("--None--")

    class PricingMethodType(models.TextChoices):
        PORTFOLIO_DE = "Portfolio DE", _("Portfolio DE")
        PORTFOLIO_INT = "Portfolio INT", _("Portfolio INT")
        PORTFOLIO_NL = "Portfolio NL", _("Portfolio NL")
        PORTFOLIO_UK = "Portfolio UK", _("Portfolio UK")
        PORTFOLIO_US = "Portfolio US", _("Portfolio US")
        PREMIUM_DE = "Premium DE", _("Premium DE")
        PREMIUM_INT = "Premium INT", _("Premium INT")
        PORTFOLIO_FR = "Portfolio FR", _("Portfolio FR")
        PREMIUM_NL = "Premium NL", _("Premium NL")
        PREMIUM_UK = "Premium UK", _("Premium UK")
        PREMIUM_FR = "Premium FR", _("Premium FR")
        PREMIUM_US = "Premium US", _("Premium US")
        TROPICAL_DE = "Tropical DE", _("Tropical DE")
        TROPICAL_INT = "Tropical INT", _("Tropical INT")
        TROPICAL_NL = "Tropical NL", _("Tropical NL")
        TROPICAL_UK = "Tropical UK", _("Tropical UK")
        ADDITIONAL = "Additional", _("Additional")
        INDEED_ALWAYS_ON = "Indeed Always On", _("Indeed Always On")
        TRAFFIQ_SEA_VONQ = "TraffiQ / SEA (VONQ Team)", _("TraffiQ / SEA (VONQ Team)")
        TRAFFIQ_SEA_EXPAND_ONLINE = (
            "TraffiQ / SEA (Expand Online)",
            _("TraffiQ / SEA (Expand Online)"),
        )
        PROJECT_MANAGEMENT = (
            "Project Management (e.g. hours)",
            _("Project Management (e.g. hours)"),
        )
        ADDON_FINANCIAL = "Addon: financial", _("Addon: financial")
        INTERNAL_TRACKING_TECHNICAL = (
            "Internal / Tracking / Technical",
            _("Internal / Tracking / Technical"),
        )
        KICKBACKS = "Kickbacks", _("Kickbacks")
        SUBSCRIPTION = "Subscription", _("Subscription")
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

        @classmethod
        def addons(cls):
            return [
                cls.PRINT,
                cls.IMAGE_CREATION,
                cls.WEBSITE_CREATION,
                cls.VONQ_SERVICES,
                cls.VIDEO_CREATION,
                cls.TEXT_SERVICES,
            ]

        @classmethod
        def products(cls):
            return [cls.JOB_BOARD, cls.SOCIAL, cls.GOOGLE]

    @property
    def external_product_name(self):
        if self.channel and self.channel.name:
            if self.title:
                return self.channel.name + " - " + self.title
            return self.channel.name
        return self.title

    @property
    def logo_url(self):
        if self.logo:
            return f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{self.logo.name}"
        return self.salesforce_logo_url

    @property
    def logo_square_url(self):
        if self.logo:
            return f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{self.logo_square.name}"
        return None

    @property
    def logo_rectangle_url(self):
        if self.logo:
            return f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{self.logo_rectangle.name}"
        return None

    @property
    def is_my_own_product(self):
        if (
            self.salesforce_product_solution
            == self.SalesforceProductSolution.MY_OWN_CHANNEL
            and self.salesforce_product_category
            == self.SalesforceProductCategory.CUSTOMER_SPECIFIC
        ):
            return True
        return False

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
    categories = models.ManyToManyField(
        Category,
        related_name="categories",
        related_query_name="category",
        blank=True,
    )

    job_functions = models.ManyToManyField(
        JobFunction, name="job_functions", related_name="products", blank=True
    )
    posting_requirements = models.ManyToManyField(
        PostingRequirement,
        related_name="posting_requirements",
        related_query_name="posting_requirement",
        blank=True,
    )

    salesforce_logo_url = models.CharField(
        max_length=300, null=True, blank=True, default=None
    )
    cropping_square = ImageRatioField("logo", "68x68")
    cropping_rectangle = ImageRatioField("logo", "270x90")

    logo = models.ImageField(
        null=True,
        blank=True,
        upload_to=Logo.logo_path,
        storage=S3Boto3Storage(),
        validators=[
            Logo.validate_logo_size,
        ],
        help_text="Rules: Logo size must be 1MB max. Logo file must be an image.",
    )
    logo_square = models.ImageField(
        null=True,
        blank=True,
        upload_to=Logo.logo_path,
        storage=S3Boto3Storage(),
    )
    logo_rectangle = models.ImageField(
        null=True,
        blank=True,
        upload_to=Logo.logo_path,
        storage=S3Boto3Storage(),
    )
    is_active = models.BooleanField(default=False)

    available_in_ats = models.BooleanField(default=True)
    available_in_jmp = models.BooleanField(default=True)

    duration_days = models.IntegerField(null=True, blank=True)
    time_to_process = models.IntegerField(
        null=True, blank=True, verbose_name="Time to process (hours)"
    )

    unit_price = models.FloatField(null=True, blank=True)
    rate_card_price = models.FloatField(null=True, blank=True)
    purchase_price = models.FloatField(null=True, blank=True)
    purchase_price_method = models.CharField(
        choices=PurchasePriceMethodType.choices,
        default=PurchasePriceMethodType.NONE,
        null=True,
        max_length=10,
    )
    pricing_method = models.CharField(
        choices=PricingMethodType.choices,
        default=PricingMethodType.NONE,
        null=True,
        max_length=40,
    )

    locations = models.ManyToManyField(Location, related_name="products", blank=True)

    interests = models.CharField(max_length=200, default="", blank=True, null=True)

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
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
    salesforce_product_solution = models.TextField(
        choices=SalesforceProductSolution.choices,
        default=SalesforceProductSolution.NONE,
        null=True,
    )
    salesforce_industries = ArrayField(
        base_field=models.CharField(max_length=80, blank=True), default=list
    )
    salesforce_job_categories = ArrayField(
        base_field=models.CharField(max_length=80, blank=False), default=list
    )
    salesforce_cross_postings = models.JSONField(null=True, blank=True, default=list)

    customer_id = models.CharField(null=True, blank=True, max_length=36)

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

    order_frequency = models.FloatField(null=True, blank=True, default=0)

    objects = AcrossLanguagesQuerySet.as_manager()

    def __str__(self):
        return str(self.title) + " : " + str(self.url)


class Profile(CreatedUpdatedModelMixin):
    class Type(models.TextChoices):
        JMP = "jmp", _("JMP")
        MAPI = "mapi", _("MAPI")
        INTERNAL = "internal", _("Internal")

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.TextField(
        max_length=15, blank=True, choices=Type.choices, default=Type.INTERNAL
    )

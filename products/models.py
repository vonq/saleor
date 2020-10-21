from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import QuerySet, Q, Func, F


class Industry(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "industries"


class JobFunction(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('JobFunction', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class JobTitle(models.Model):
    name = models.CharField(max_length=100)
    jobFunction = models.ForeignKey('JobFunction', on_delete=models.CASCADE, null=True, blank=True)
    industry = models.ForeignKey('Industry', on_delete=models.CASCADE, null=True, blank=True)
    frequency = models.IntegerField(default=0, null=True, blank=True)
    canonical = models.BooleanField(default=True)
    alias_of = models.ForeignKey('JobTitle', on_delete=models.CASCADE, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Location(models.Model):
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

    desq_name_en = models.CharField(max_length=100, null=True)
    desq_country_code = models.CharField(max_length=3, null=True)

    # mapbox fields
    mapbox_id = models.CharField(max_length=50, null=True, blank=True)
    mapbox_text = models.CharField(max_length=100, null=True, blank=True)
    mapbox_placename = models.CharField(max_length=300, null=True, blank=True)
    mapbox_context = ArrayField(base_field=models.CharField(max_length=50, blank=False), default=list)
    mapbox_place_type = ArrayField(base_field=models.CharField(max_length=500, null=True, blank=True), default=list)
    mapbox_shortcode = models.CharField(max_length=10, null=True, blank=True)
    mapbox_within = models.ForeignKey('Location', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='mapbox_location')  # link up

    def __str__(self):
        return str(self.canonical_name)

    @classmethod
    def from_mapbox_response(cls, mapbox_response: list):
        locations = []
        for result in mapbox_response:
            location = cls()
            location.mapbox_id = result['id']
            location.mapbox_placename = result['place_name']
            location.text = result['text']
            location.mapbox_place_type = []
            for place_type in result['place_type']:
                location.mapbox_place_type.append(place_type)
            if 'short_code' in result['properties']:
                location.mapbox_shortcode = result['properties']['short_code']
            if 'context' in result:
                location.mapbox_context = result['context']

            locations.append(location)
        return locations


class Channel(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=300, unique=True)
    TYPE_CHOICES = [
        ('job board', 'Job Board'),
        ('social media', 'Social Media'),
        ('community', 'Community'),
        ('publication', 'Publication'),
        ('aggregator', 'Aggregator')
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='job board')

    def __str__(self):
        return str(self.name)


class LocationIdsQuerySet(models.QuerySet):
    def by_location_ids(self, location_ids: list) -> QuerySet:
        qs = self
        if location_ids:
            qs = qs.filter(
                Q(locations__mapbox_context__overlap=location_ids) |
                Q(locations__mapbox_id__in=location_ids)
            )
        qs = qs.annotate(
            # the more specific a location, the longer its context (['place', 'district', 'country'...)
            # so we'll sort by descending cardinality to put most location-specific products first
            locations_cardinality=Func(F('locations__mapbox_context'), function='CARDINALITY')
        ).order_by('-locations_cardinality')
        return qs


class Product(models.Model):
    title = models.CharField(max_length=200, null=True)
    url = models.URLField(max_length=300, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(default='', null=True, blank=True)
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
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=True)

    available_in_ats = models.BooleanField(default=True)
    available_in_jmp = models.BooleanField(default=True)

    salesforce_product_category = models.CharField(max_length=20, null=True)

    locations = models.ManyToManyField(Location, related_name="locations", blank=True)

    interests = models.CharField(max_length=200, default='', blank=True, null=True)

    salesforce_id = models.CharField(max_length=36, null=True)
    salesforce_product_type = models.CharField(max_length=30, null=True)
    desq_product_id = models.BigIntegerField(null=True)

    similarweb_estimated_monthly_visits = models.CharField(max_length=300, null=True, blank=True, default=None)
    similarweb_top_country_shares = models.TextField(null=True, blank=True, default=None)

    objects = LocationIdsQuerySet.as_manager()

    def __str__(self):
        return str(self.title) + ' : ' + str(self.url)

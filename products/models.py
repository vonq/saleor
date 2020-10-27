import itertools
from typing import List

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import FieldError
from django.db import models
from django.db.models import QuerySet, Q
from django_pg_bulk_update import bulk_update_or_create
from modeltranslation.fields import TranslationFieldDescriptor


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
    parent = models.ForeignKey('JobFunction', on_delete=models.CASCADE, null=True, blank=True)

    objects = AcrossLanguagesQuerySet.as_manager()

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

    objects = AcrossLanguagesQuerySet.as_manager()

    def __str__(self):
        return self.name


class MapboxLocation(models.Model):
    mapbox_placename = models.CharField(name="mapbox_placename", max_length=300, null=True, blank=True)
    mapbox_id = models.CharField(name='mapbox_id', max_length=200, primary_key=True)
    mapbox_context = ArrayField(base_field=models.CharField(max_length=50, blank=False), default=list)
    mapbox_data = models.JSONField(name='mapbox_data')

    def __str__(self):
        return self.mapbox_placename or self.mapbox_id

    @classmethod
    def save_mapbox_response(cls, *mapbox_locations: dict) -> int:
        updated = bulk_update_or_create(
            cls,
            [{'mapbox_id': location['id'], 'mapbox_data': location, 'mapbox_placename': location['place_name'],
              'mapbox_context': [item['id'] for item in location.get('context', [])]}
             for location in mapbox_locations],
            key_fields='mapbox_id')
        return updated

    @classmethod
    def list_context_locations_ids(cls, location_ids: List[str]) -> List[str]:
        qs = cls.objects.filter(mapbox_id__in=location_ids)

        if not qs.exists():
            return []

        return list(
            itertools.chain.from_iterable(
                MapboxLocation.objects.all().values_list('mapbox_context', flat=True)
            )
        )


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

    objects = AcrossLanguagesQuerySet.as_manager()

    def __str__(self):
        return str(self.title) + ' : ' + str(self.url)

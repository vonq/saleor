from django.contrib.postgres.fields import ArrayField
from django.db import models


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
    geocoder_id = models.CharField(max_length=64, null=True, unique=True)
    place_name = models.CharField(max_length=200, null=True)
    text = models.CharField(max_length=200, null=True)
    place_type = ArrayField(base_field=models.CharField(max_length=10, blank=False), default=list,
                            blank=False)

    within = models.ForeignKey('Location',  on_delete=models.SET_NULL, null=True, blank=True)
    mapbox_context = ArrayField(base_field=models.CharField(max_length=50, blank=False), default=list)
    short_code = models.CharField(max_length=8, null=True)

    def __str__(self):
        return self.place_name

    @classmethod
    def from_mapbox_response(cls, mapbox_response: list):
        locations = []
        for result in mapbox_response:
            location = cls()
            location.geocoder_id = result['id']
            location.place_name = result['place_name']
            location.text = result['text']
            location.place_type = result['place_type']
            if 'short_code' in result['properties']:
                location.short_code = result['properties']['short_code']
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
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=300, unique=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(default='')
    industries = models.ManyToManyField(
        Industry,
        related_name="industries",
        related_query_name="industry",
        blank=True,
        null=True,
    )
    job_functions = models.ManyToManyField(
        JobFunction,
        related_name="job_functions",
        related_query_name="job_function",
        blank=True,
        null=True,
    )
    logo_url = models.CharField(max_length=300, null=True, blank=True, default=None)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=True)

    product_solution = models.CharField(max_length=20, null=True)

    locations = models.ManyToManyField(Location, related_name="locations", null=True, blank=True)

    interests = models.CharField(max_length=200, default='', blank=True, null=True)

    salesforce_id = models.CharField(max_length=20, null=True)
    salesforce_product_type = models.CharField(max_length=30, null=True)
    desq_product_id = models.BigIntegerField(null=True)

    similarweb_estimated_monthly_visits = models.CharField(max_length=300, null=True, blank=True, default=None)
    similarweb_top_country_shares = models.TextField(null=True, blank=True, default=None)

    def __str__(self):
        return self.title + ' : ' + self.url

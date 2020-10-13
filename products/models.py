from django.contrib.postgres.fields import ArrayField
from django.db import models
from rest_framework.fields import DictField


class Industry(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "industries"


class JobFunction(models.Model):
    name = models.CharField(max_length=100)
    # parent = models.ForeignKey('JobFunction', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


# treating title as separate from function for now
class JobTitle(models.Model):
    name = models.CharField(max_length=100)
    # jobFunction = models.ForeignKey('JobFunction', on_delete=models.CASCADE, null=True, blank=True)
    # industry = models.ForeignKey('Industry', on_delete=models.CASCADE, null=True, blank=True)
    freq = models.IntegerField(default=0, null=True, blank=True)  # from demo sample
    canonical = models.BooleanField(default=True)
    # alias_of = models.ForeignKey('JobTitle', on_delete=models.CASCADE, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    # level = one of
    # within = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True) # should only be null for 'Global'
    alpha_2 = models.CharField(max_length=2, null=True)
    alpha_3 = models.CharField(max_length=3, null=True)
    country_code = models.CharField(max_length=3, null=True)

    # mapbox fields


    place_name = models.CharField(max_length=200)
    text = models.CharField(max_length=200)


    id = models.CharField(max_length=64, null=False, primary_key=True)
    # place_type = models.CharField(max_length=500, null=True, blank=True) # can be a list
    place_type = ArrayField(base_field=models.CharField(max_length=10, null=True, blank=False), default=list, blank=False)
    # short_code = models.CharField(max_length=8, blank=False, null=False)
    # mapbox_within = models.ForeignKey('Location', on_delete=models.CASCADE, null=True, blank=True, related_name='Location') # link up

    def __str__(self):
        return self.name #+ ' : ' + self.within.name if not self.within is None else ''


class ChannelProduct(models.Model):
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=300)
    description = models.TextField(default='')
    scraped_li_a_list = models.TextField(default='')  # temporary scaffolding
    # industry = models.ManyToManyField(
    #     Industry,
    #     related_name="industries",
    #     related_query_name="industry",
    #     blank=True,
    #     null=True,
    # )
    # jobFunctions = models.ManyToManyField(
    #     JobFunction,
    #     related_name="job_functions",
    #     related_query_name="job_function",
    #     blank=True,
    #     null=True,
    # )
    logo_url = models.CharField(max_length=300, null=True, blank=True, default=None)
    blacklisted = models.BooleanField(default=False)
    html_posting = models.BooleanField(default=False)
    toReview = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    # location = models.ForeignKey(Location,  # to deprecate
    #                              on_delete=models.CASCADE,
    #                              null=True,
    #                             blank=True
    #                              )
    # locations = models.ManyToManyField(Location, related_name="locations", null=True, blank=True)

    total_visits_6_months = models.BigIntegerField(null=True, blank=True)
    female_audience_is_predominant = models.NullBooleanField(null=True, blank=True)
    audience_age_range = models.CharField(max_length=10, default='', blank=True)
    interests = models.CharField(max_length=200, default='', blank=True)
    passive_active = models.CharField(max_length=20, default='', blank=True)
    # screenshot_url = models.CharField(max_length=300)

    similarweb_estimated_monthly_visits = models.CharField(max_length=300, null=True, blank=True, default=None)
    similarweb_top_country_shares = models.TextField(null=True, blank=True, default=None)

    TYPE_CHOICES = [
        ('job board', 'Job Board'),
        ('social media', 'Social Media'),
        ('community', 'Community'),
        ('publication', 'Publication'),
        ('aggregator', 'Aggregator')
    ]
    channel_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='job board')

    def __str__(self):
        return self.title + ' : ' + self.url
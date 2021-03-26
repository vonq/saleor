from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django_countries.fields import CountryField

from ..account.models import PossiblePhoneNumberField
from ..checkout.models import get_default_country


class Campaign(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='campaigns', on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField('product.Product', related_name='campaign', blank=True)
    title = models.CharField(max_length=250, blank=True)
    country = CountryField(default=get_default_country)
    industry = models.CharField(max_length=100)
    seniority = models.CharField(max_length=50)
    education = models.CharField(max_length=50)
    job_function = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)


class JobInfo(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=250, blank=True)
    campaign = models.OneToOneField('campaign.Campaign', related_name='job_info', on_delete=models.CASCADE)
    industry = models.CharField(max_length=100)
    job_description = models.CharField(max_length=250, blank=True)
    link_to_job_detail_page = models.URLField(max_length=200, blank=True)
    link_to_job_app_page = models.URLField(max_length=200, blank=True)
    exp_year = models.PositiveSmallIntegerField(default=0)
    education = models.CharField(max_length=50)
    employment_type = models.CharField(max_length=40)
    hours_per_week = ArrayField(models.PositiveIntegerField(default=0), size=2)
    salary_interval = ArrayField(models.PositiveIntegerField(default=0), size=2)
    currency = models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH)
    period = models.CharField(max_length=30, blank=True)
    contact_info_name = models.CharField(max_length=250, blank=True)
    contact_phone = PossiblePhoneNumberField(blank=True)

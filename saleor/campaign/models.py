from django.conf import settings
from django.db import models
from django_countries.fields import CountryField

from ..checkout.models import get_default_country


class Campaign(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='campaigns', on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField('product.Product', related_name='campaign', blank=True)
    title = models.CharField(max_length=250, blank=True)
    country = CountryField(default=get_default_country)
    industry = models.CharField(max_length=50)
    seniority = models.CharField(max_length=30)
    education = models.CharField(max_length=40)
    job_function = models.CharField(max_length=255)

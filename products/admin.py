from django.contrib import admin

# Register your models here.
from modeltranslation.admin import TranslationAdmin

from api.products.models import Product, Channel, JobTitle, JobFunction, Location, Industry


@admin.register(Product)
class ProductAdmin(TranslationAdmin):
    fields = ['title', 'url', 'channel', 'description', 'industries', 'job_functions', 'is_active',
              'salesforce_product_category', 'locations']
    search_fields = ('title', 'description')


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    fields = ['name', 'url', 'type']
    list_display = ('name', 'url', 'type')
    list_filter = ('type',)
    search_fields = ('name',)


@admin.register(JobTitle)
class JobTitleAdmin(TranslationAdmin):
    fields = ['name', 'jobFunction', 'industry', 'canonical', 'alias_of', 'active']
    list_display = ('name', 'jobFunction', 'industry', 'canonical', 'alias_of', 'active')
    list_filter = ('jobFunction', 'canonical', 'active')
    search_fields = ('name',)


@admin.register(JobFunction)
class JobFunctionAdmin(TranslationAdmin):
    fields = ['name', 'parent']
    list_display = ('name', 'parent')
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('fully_qualified_place_name', 'canonical_name', 'place_type')
    search_fields = ('mapbox_placename', 'canonical_name')


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    pass

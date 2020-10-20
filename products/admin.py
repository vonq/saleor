from django.contrib import admin

# Register your models here.
from api.products.models import Product, Channel, JobTitle, JobFunction, Location


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fields = ['title', 'url', 'channel', 'description', 'industries', 'job_functions', 'is_active', 'product_solution',
              'locations']
    search_fields = ('title', 'description')


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    fields = ['name', 'url', 'type']
    list_display = ('name', 'url', 'type')
    list_filter = ('type',)
    search_fields = ('name',)


@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    fields = ['name', 'jobFunction', 'industry', 'canonical', 'alias_of', 'active']
    list_display = ('name', 'jobFunction', 'industry', 'canonical', 'alias_of', 'active')
    list_filter = ('jobFunction', 'canonical', 'active')
    search_fields = ('name',)


@admin.register(JobFunction)
class JobFunctionAdmin(admin.ModelAdmin):
    fields = ['name', 'parent']
    list_display = ('name', 'parent')
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('place_name', 'place_text', 'place_type')
    search_fields = ('place_name', 'place_text')

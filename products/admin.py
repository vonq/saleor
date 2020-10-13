from django.contrib import admin

# Register your models here.
from api.products.models import Product, Channel


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(Channel)
class ProductAdmin(admin.ModelAdmin):
    pass

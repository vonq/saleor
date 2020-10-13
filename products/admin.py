from django.contrib import admin

# Register your models here.
from api.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass

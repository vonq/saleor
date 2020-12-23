from django.contrib import admin

from api.currency.models import ExchangeRate, Currency


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    pass


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    pass

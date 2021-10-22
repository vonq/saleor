from django.contrib import admin

from api.igb.models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    fields = ("customer_name", "customer_id", "channel", "credentials", "facets")

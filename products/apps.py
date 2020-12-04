from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.conf import settings


class ProductsConfig(AppConfig):
    name = "api.products"
    verbose_name = "[Experimental] Products Search"

    def ready(self):
        from api.products.models import Channel, Product
        from api.products.signals import (
            create_or_update_user_profile,
            sync_channel_with_salesforce,
            sync_product_with_salesforce,
            channel_updated,
            product_updated,
        )

        User = get_user_model()

        post_save.connect(create_or_update_user_profile, sender=User)

        if settings.SALESFORCE_SYNC_ENABLED:
            channel_updated.connect(sync_channel_with_salesforce, sender=Channel)
            product_updated.connect(sync_product_with_salesforce, sender=Product)

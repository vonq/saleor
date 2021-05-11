"""
For the purpose of this command we'll assume that the PKB tables
are already populated with the relevant Products and Channel –
this might come from a loadddata within the products django sub-app.
"""
import datetime

from django.core.management.base import BaseCommand

from api.products.models import Product as PkbProduct
from saleor.product.models import Product as SaleorProduct, ProductVariant, \
    ProductVariantChannelListing, Channel, ProductType, ProductChannelListing


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """
        Pick a PKB product
        - Create a Product
        - Create a Channel (possibly a default channel...)
        - Attach a Product Variant
        - Attach a Product Variant Channel Listing
        - Set prices and weights
        """

        gbp_channel, _ = Channel.objects.get_or_create(name="Default GBP Channel", currency_code="GBP", slug="gbp-channel", is_active=True)
        usd_channel, _ = Channel.objects.get_or_create(name="Default USD Channel", currency_code="USD", slug="usd-channel", is_active=True)
        eur_channel, _ = Channel.objects.get_or_create(name="Default GBP Channel", currency_code="EUR", slug="eur-channel", is_active=True)

        default_product_type, _ = ProductType.objects.get_or_create(name="Default", slug="Default", has_variants=False, is_shipping_required=False, is_digital=True)

        pkb_products = PkbProduct.objects.all()
        breakpoint()
        for pkb_product in pkb_products:
            saleor_product, _ = SaleorProduct.objects.get_or_create(
                product_type=default_product_type,
                name=pkb_product.title or "Untitled",
                slug=pkb_product.product_id
            )
            saleor_product_variant, _ = ProductVariant.objects.get_or_create(
                id=pkb_product.id,  # IMPORTANT
                name=pkb_product.title or "Untitled",
                sku=pkb_product.product_id,
                product=saleor_product,
                track_inventory=False
            )

            saleor_product.default_variant = saleor_product_variant
            saleor_product.save()

            saleor_product_channel_listing, _ = ProductChannelListing.objects.get_or_create(
                product=saleor_product,
                channel=eur_channel,
                visible_in_listings=True,
                is_published=True,
                available_for_purchase=datetime.datetime(1970, 1, 1, 0, 0)
            )
            saleor_product_variant_channel_listing, _ = ProductVariantChannelListing.objects.get_or_create(
                variant=saleor_product_variant,
                channel=eur_channel,
                currency="EUR",
                price_amount=pkb_product.unit_price or 0
            )

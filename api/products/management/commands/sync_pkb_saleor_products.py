"""
For the purpose of this command we'll assume that the PKB tables
are already populated with the relevant Products and Channel –
this might come from a loadddata within the products django sub-app.
"""

from django.core.management.base import BaseCommand

from api.products.models import Product as PkbProduct
from saleor.product.models import Product as SaleorProduct, ProductVariant, ProductVariantChannelListing, Channel, ProductType



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

        gbp_channel, _ = Channel.objects.get_or_create(name="Default GBP Channel", currency_code="GBP", slug="gbp-channel")
        usd_channel, _ = Channel.objects.get_or_create(name="Default USD Channel", currency_code="USD", slug="usd-channel")
        eur_channel, _ = Channel.objects.get_or_create(name="Default EUR Channel", currency_code="EUR", slug="eur-channel")

        default_product_type, _ = ProductType.objects.get_or_create(name="Default", slug="Default", has_variants=False, is_shipping_required=False, is_digital=True)

        pkb_products = PkbProduct.objects.all()
        breakpoint()
        for pkb_product in pkb_products:
            saleor_product = SaleorProduct.objects.create(
                product_type=default_product_type,
                name=pkb_product.title,
                slug=pkb_product.product_id
            )
            saleor_product_variant = ProductVariant.objects.create(
                sku=pkb_products.product_id,
                product=saleor_product
            )
            saleor_product_variant_channel_listing = ProductVariantChannelListing.objects.create(
                variant=saleor_product_variant,
                channel=eur_channel,
                currency="EUR",
                price_amount=pkb_product.unit_price
            )


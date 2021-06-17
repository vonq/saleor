"""
For the purpose of this command we'll assume that the PKB tables
are already populated with the relevant Products and Channel –
this might come from a loadddata within the products django sub-app.
"""
import datetime

from django.core.management.base import BaseCommand

from api.products.models import Product as PkbProduct
from saleor.product.models import (
    Product as SaleorProduct,
    ProductVariant,
    ProductVariantChannelListing,
    Channel,
    ProductType,
    ProductChannelListing,
    Category,
)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """
        Pick a PKB product
        - Create a Product
        -- product type - boards and addons
        -- product category?
        -- name
        -- price in each currency for each channel?

        - Create a Channel (possibly a default channel...)
        - Attach a Product Variant
        - Attach a Product Variant Channel Listing
        - Set prices and weights
        """

        eur_channel, _ = Channel.objects.get_or_create(
            name="Default EUR Channel",
            currency_code="EUR",
            slug="default-channel",
            is_active=True,
        )

        default_product_type, _ = ProductType.objects.get_or_create(
            name="Default",
            slug="Default",
            has_variants=False,
            is_shipping_required=False,
            is_digital=False,
        )
        default_product_category, _ = Category.objects.get_or_create(
            name="Channels", slug="channels"
        )

        pkb_products = PkbProduct.objects.filter(status=PkbProduct.Status.ACTIVE)
        for pkb_product in pkb_products:
            try:
                saleor_product, _ = SaleorProduct.objects.get_or_create(
                    product_type=default_product_type,
                    category=default_product_category,
                    name=pkb_product.external_product_name or "Untitled",
                    slug=pkb_product.product_id,
                )
                saleor_product_variant, _ = ProductVariant.objects.get_or_create(
                    id=pkb_product.id,  # IMPORTANT
                    name=pkb_product.external_product_name or "Untitled",
                    sku=pkb_product.product_id,
                    product=saleor_product,
                    track_inventory=False,
                )

                saleor_product.default_variant = saleor_product_variant
                saleor_product.save()

                (
                    saleor_product_channel_listing,
                    _,
                ) = ProductChannelListing.objects.get_or_create(
                    product=saleor_product,
                    channel=eur_channel,
                    visible_in_listings=True,
                    is_published=True,
                    available_for_purchase=datetime.date.today(),
                    discounted_price_amount=pkb_product.unit_price or 0,
                )
                (
                    saleor_product_variant_channel_listing,
                    _,
                ) = ProductVariantChannelListing.objects.get_or_create(
                    variant=saleor_product_variant,
                    channel=eur_channel,
                    currency="EUR",
                    price_amount=pkb_product.unit_price or 0,
                    cost_price_amount=pkb_product.purchase_price or 0,
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error importing {pkb_product.external_product_name}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Imported {pkb_product.external_product_name}")
                )

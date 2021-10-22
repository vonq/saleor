from typing import List, Optional, Iterable, Any

from django.core.exceptions import ValidationError

from vonq.plugins.metadata import MetadataSerializer, FinalMetadataSerializer
from saleor.checkout.fetch import CheckoutInfo, CheckoutLineInfo
from saleor.checkout.models import Checkout
from saleor.discount import DiscountInfo
from saleor.plugins.base_plugin import BasePlugin


class CheckoutDetailsPlugin(BasePlugin):
    PLUGIN_NAME = "validate_checkout_details"
    PLUGIN_ID = "validate1"
    PLUGIN_DESCRIPTION = ""
    CONFIG_STRUCTURE = None
    DEFAULT_CONFIGURATION = []
    DEFAULT_ACTIVE = True

    def preprocess_order_creation(
            self,
            checkout_info: "CheckoutInfo",
            discounts: List["DiscountInfo"],
            lines: Optional[Iterable["CheckoutLineInfo"]],
            previous_value: Any,
    ):
        if not checkout_info.checkout.metadata:
            raise ValidationError("No metadata provided in the checkout object")

        checkout_metadata = FinalMetadataSerializer(
            data=checkout_info.checkout.metadata)
        if not checkout_metadata.is_valid(raise_exception=False):
            raise ValidationError(checkout_metadata.errors)
        return previous_value

    def checkout_updated(self, checkout: "Checkout", previous_value: Any) -> Any:
        checkout_metadata = MetadataSerializer(data=checkout.metadata)
        if not checkout_metadata.is_valid(raise_exception=False):
            raise ValidationError(checkout_metadata.errors)
        return previous_value

from typing import List, Optional, Iterable, Any

from django.core.exceptions import ValidationError

from saleor.checkout.fetch import CheckoutInfo, CheckoutLineInfo
from saleor.checkout.models import Checkout
from saleor.discount import DiscountInfo
from saleor.plugins.base_plugin import BasePlugin
from dataclasses import dataclass


class VacancyDetails:
    @classmethod
    def validate(cls, metadata):
        return False



class CheckoutDetailsPlugin(BasePlugin):
    PLUGIN_NAME = "validate_checkout_details"
    PLUGIN_ID = "validate1"
    PLUGIN_DESCRIPTION = ""
    CONFIG_STRUCTURE = None
    DEFAULT_CONFIGURATION = []
    DEFAULT_ACTIVE = False


    def preprocess_checkout_creation(
            self, checkout_info: "CheckoutInfo",
            discounts: List["DiscountInfo"],
            lines: Optional[Iterable["CheckoutLineInfo"]], previous_value: Any):
        print("Preprocessing in progress")
        checkout_info.checkout.metadata = {'added': True}
        return

    def preprocess_order_creation(
        self,
        checkout_info: "CheckoutInfo",
        discounts: List["DiscountInfo"],
        lines: Optional[Iterable["CheckoutLineInfo"]],
        previous_value: Any,
    ):
        # if not checkout_info.checkout.metadata:
        #    raise ValidationError("No metadata provided")
        raise ValidationError("This should raise!")

    def checkout_updated(self, checkout: "Checkout", previous_value: Any) -> Any:
        return previous_value
        {
            "vacancy": {
                "seniority": 1,
            },
            "target_group": {
                "industry": 2
            }
        }
        raise ValidationError({"address": "Address invalid?!"})

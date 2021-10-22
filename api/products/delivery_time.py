from dataclasses import dataclass
from math import floor, ceil
from typing import List

from api.products.models import Product


@dataclass
class TotalDeliveryTime:
    days_to_process: int
    days_to_setup: int

    @property
    def total_days(self):
        return self.days_to_setup + self.days_to_process


def calculate_delivery_time(products: List[Product]):
    if not products:
        return TotalDeliveryTime(days_to_setup=0, days_to_process=0)

    time_to_process_in_hours = max(
        product.total_time_to_process for product in products
    )
    time_to_setup_in_hours = max(product.supplier_setup_time for product in products)

    return TotalDeliveryTime(
        days_to_process=ceil(time_to_process_in_hours / 24),
        days_to_setup=ceil(time_to_setup_in_hours / 24),
    )

from typing import Optional

from django.core.management.base import BaseCommand

from api.products.models import Product, Location, Channel, PostingRequirement
import json


class Command(BaseCommand):
    help = """
    Updates Salesforce data given a file
    """

    # A map between the names we have in our models and the field names from the file
    fields_to_update_map = {
        "title": "jmp_product_name",
        "description": "description",
        "is_active": "is_active",
        "salesforce_product_type": "type",
        "available_in_jmp": "is_available_on_jmp",
        "available_in_ats": "is_available_in_ats",
        "desq_product_id": "desq_id",
        "url": "channel_url",
        "salesforce_product_category": "product_category",
        "salesforce_logo_url": "product_logo",
        "cross_postings": "cross_postings",
        "salesforce_industries": "industries",
        "salesforce_job_categories": "job_categories",
        "duration_days": "duration",
        "supplier_time_to_process": "time_to_process",
        "unit_price": "unit_price",
        "rate_card_price": "rate_card_price",
        "description_nl": "description_nl",
        "description_de": "description_de",
        "title_nl": "product_name_nl",
        "title_de": "product_name_de",
        "status": "status",
        "is_recommended": "is_recommended_product",
        "has_html_posting": "has_html_posting",
        "tracking_method": "tracking_method",
        "purchase_price_method": "purchase_price_method",
        "pricing_method": "pricing_method",
        "purchase_price": "purchase_price",
        "customer_id": "customer_id",
        "salesforce_id": "salesforce_id",
        "salesforce_product_solution": "product_solution",
        "created": "created_date",
        "rate_card_url": "rate_card_url",
    }

    channel_fields_to_update_map = {
        "name": "channel_name",
        "salesforce_id": "channel_id",
        "salesforce_account_id": "account_id",
    }

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="The path to the json file")

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]
        try:
            with open(json_file) as json_file:
                self.stdout.write("Refreshing Salesforce data...")
                for row in json_file:
                    product = json.loads(row)
                    self.__update(product)
            self.stdout.write(self.style.SUCCESS("Success"))

        except OSError:
            self.stdout.write(self.style.ERROR('Could not open file "%s".' % json_file))

    def __update(self, new: dict):
        """
        Updates or creates product (and its channel) based on a dict with data.
        Only fields present in fields_to_update_map and channel_fields_to_update_map will be updated.
        :param new: The dict with fields to be updated
        :return:
        """
        current_product = self.__update_product(new=new)
        current_channel = self.__update_channel(new=new)
        if current_channel:
            current_channel.save()
            self.__link_product_to_channel(current_product, current_channel)
        current_product.save()

    def __link_product_to_channel(self, product: Product, channel: Channel):
        """Updates a product's channel foreign key"""
        if product.channel != channel:
            self.stdout.write(
                "Updating product {}'s channel to {}".format(
                    product.title, channel.name
                )
            )
            product.channel = channel

    def __update_product(self, new: dict) -> Product:
        product_id = (
            new.get("desq_id") if new.get("desq_id") else new.get("salesforce_id")
        )
        current_product, product_created_flag = Product.objects.get_or_create(
            product_id=product_id
        )
        if product_created_flag:
            self.stdout.write(
                "Creating product {} id {}".format(
                    new.get("jmp_product_name"), product_id
                )
            )
        self.__update_product_fields(current=current_product, new=new)
        return current_product

    def __update_channel(self, new: dict) -> Optional[Channel]:
        channel_id = new.get("channel_id")
        if not channel_id:
            return None
        current_channel, channel_created_flag = Channel.objects.get_or_create(
            salesforce_id=channel_id
        )
        if channel_created_flag:
            self.stdout.write("Creating channel {}".format(new.get("channel_name")))
        self.__update_channel_fields(current=current_channel, new=new)
        return current_channel

    def __update_product_fields(self, current, new):
        for current_field_name, new_field_name in self.fields_to_update_map.items():
            if current_field_name == "locations":
                self.__add_locations(
                    product=current, new_field_name=new_field_name, new_product=new
                )
            elif current_field_name == "has_html_posting":
                self.__map_html_posting_requirement(product=current, new_product=new)
            else:
                self.__update_field(
                    current_field_name=current_field_name,
                    current_obj=current,
                    new_field_name=new_field_name,
                    new_obj=new,
                )

    def __update_channel_fields(self, current, new):
        for (
            current_field_name,
            new_field_name,
        ) in self.channel_fields_to_update_map.items():
            self.__update_field(
                current_field_name=current_field_name,
                current_obj=current,
                new_field_name=new_field_name,
                new_obj=new,
            )

    def __update_field(
        self,
        current_field_name: str,
        current_obj,
        new_field_name: str,
        new_obj: dict,
    ):
        """
        Updates a specific field for a given product
        :param current_field_name: The field to be updated
        :param current_obj: The product to be updated
        :param new_field_name: The equivalent field name
        :param new_obj: The dict containing the new data
        :return:
        """
        current_value = getattr(current_obj, current_field_name)
        new_value = new_obj.get(new_field_name)
        if new_value != "" and new_value is not None and current_value != new_value:
            self.stdout.write(
                "Updating {} from '{}' to '{}' (Product id {})".format(
                    current_field_name, current_value, new_value, current_obj.id
                )
            )
            setattr(current_obj, current_field_name, new_value)

    def __add_locations(self, product, new_field_name: str, new_product: dict):
        """
        Adds locations to a given product.
        Existing locations will not be replaced/removed.
        :param product: The product to be updated
        :param new_field_name: The equivalent location field name
        :param new_product: The dict containing the new data
        :return:
        """
        # Locations we want to ignore as they're not available on mapbox
        excluded_names = [
            "East Midlands",
            "West Midlands",
            "Yorkshire & Humberside",
            "North West",
            "North East",
            "East of England",
            "South West",
            "South East",
            "North",
        ]

        current_locations = [
            location.desq_name_en for location in product.locations.all()
        ]
        new_locations = new_product.get(new_field_name, [])
        for new_location in new_locations:
            if (
                new_location not in current_locations
                and new_location not in excluded_names
            ):
                self.stdout.write(
                    "Adding location {} to product id {}".format(
                        new_location, product.id
                    )
                )
                db_location = Location.objects.get(
                    desq_name_en=new_location  # assuming location names in SF are const and unique
                )
                product.locations.add(db_location)  # won't duplicate

    def __map_html_posting_requirement(self, product, new_product):
        new_value = new_product.get("has_html_posting")
        if new_value:
            if (
                product.posting_requirements.filter(
                    posting_requirement_type="HTML Posting"
                ).count()
                == 0
            ):
                req, _ = PostingRequirement.objects.get_or_create(
                    posting_requirement_type="HTML Posting"
                )
                self.stdout.write(
                    f"Adding HTML posting requirement to product id {product.id}"
                )
                product.posting_requirements.add(req)

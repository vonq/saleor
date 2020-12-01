from django.core.management.base import BaseCommand

from api.products.models import Product, Location
import json


class Command(BaseCommand):
    help = """
    Updates Salesforce data given a file
    """

    # A map between the names we have in our models and the field names from the file
    fields_to_update_map = {
        "title": "product_name",
        "description": "description",
        "is_active": "is_active",
        "salesforce_product_type": "type",
        "available_in_jmp": "is_available_on_jmp",
        "available_in_ats": "is_available_in_ats",
        "desq_product_id": "desq_id",
        "url": "channel_url",
        "salesforce_product_category": "product_category",
        "logo_url": "product_logo",
        "salesforce_cross_postings": "cross_postings",
        "locations": "relevant_location_names",
        "salesforce_industries": "industries",
        "salesforce_job_categories": "job_categories",
        "duration_days": "duration",
        "time_to_process": "time_to_process",
        "unit_price": "unit_price",
        "rate_card_price": "rate_card_price",
        "description_nl": "description_nl",
        "description_de": "description_de",
        "title_nl": "product_name_nl",
        "title_de": "product_name_de",
        "status": "status",
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
                    self.__update_product(product)
            self.stdout.write(self.style.SUCCESS("Success"))

        except OSError:
            self.stdout.write(self.style.ERROR('Could not open file "%s".' % json_file))

    def __update_product(self, new: dict):
        """
        Updates or creates a product based on a dict with data.
        Only fields present in fields_to_update_map will be updated.
        :param new: The dict with fields to be updated
        :return:
        """
        current, product_created_flag = Product.objects.get_or_create(
            salesforce_id=new["salesforce_id"]
        )
        if product_created_flag:
            self.stdout.write("Creating product {}".format(new["product_name"]))
        for current_field_name, new_field_name in self.fields_to_update_map.items():
            if current_field_name == "locations":
                self.__add_locations(
                    product=current, new_field_name=new_field_name, new_product=new
                )
            else:
                self.__update_field(
                    current_field_name=current_field_name,
                    current_obj=current,
                    new_field_name=new_field_name,
                    new_obj=new,
                )
        current.save()

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

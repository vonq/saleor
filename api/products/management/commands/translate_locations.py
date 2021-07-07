import csv
from typing import Any

from api.products.models import Location

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """
           Ingest translations for location names in German and Dutch
           """

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")

    def handle(self, *args: Any, **options: Any):
        csv_file = options["csv_file"]
        translated = 0
        try:
            with open(csv_file, mode="r") as fp:
                reader = csv.DictReader(fp)
                assert {
                    "id",
                    "mapbox_placename_nl",
                    "mapbox_placename_de",
                    "mapbox_text_nl",
                    "mapbox_text_de",
                }.issubset(set(reader.fieldnames))
                for row in reader:
                    location_id = row["id"]
                    try:
                        location = Location.objects.get(pk=row["id"])
                        self.stdout.write(
                            self.style.NOTICE(f"Translating {location.mapbox_text}...")
                        )
                        location.mapbox_placename_nl = row["mapbox_placename_nl"]
                        location.mapbox_placename_de = row["mapbox_placename_de"]
                        location.mapbox_text_nl = row["mapbox_text_nl"]
                        location.mapbox_text_de = row["mapbox_text_de"]
                        location.canonical_name_nl = row["mapbox_text_nl"]
                        location.canonical_name_de = row["mapbox_text_de"]
                        location.save()
                        translated += 1
                    except Location.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Could not find location with id {location_id}"
                            )
                        )
                        continue
        except OSError:
            self.stdout.write(self.style.ERROR(f"Could not open file {csv_file}"))
        except AssertionError:
            self.stdout.write(self.style.ERROR("Invalid CSV file format"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Translated {translated} locations successfully")
            )

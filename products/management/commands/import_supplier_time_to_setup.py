import csv
from django.core.management.base import BaseCommand

from api.products.models import Product


class Command(BaseCommand):
    help = """
    Imports supplier time to setup 
    """

    required_columns = ["Uuid", "Time to create account"]

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")
        parser.add_argument(
            "-o",
            "--overwrite",
            action="store_true",
            help="Overwrite values.",
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]
        overwrite = kwargs["overwrite"]

        total_time_to_setup_applied = 0

        try:
            with open(csv_file, mode="r") as fp:
                reader = csv.DictReader(fp)
                if not set(self.required_columns).issubset(set(reader.fieldnames)):
                    self.stdout.write(
                        self.style.ERROR(
                            f"The CSV is missing one of the required columns: {','.join(self.required_columns)}"
                        )
                    )
                    exit(1)
                self.stdout.write("Applying Supplier SLAs...")

                for row in reader:
                    try:
                        total_time_to_setup_applied += self.__apply_sla(row, overwrite)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Exception occurred: {str(e)}")
                        )
            self.stdout.write(
                self.style.SUCCESS(
                    "Success. {} products updated.".format(total_time_to_setup_applied)
                )
            )

        except OSError:
            self.stdout.write(self.style.ERROR('Could not open file "%s".' % csv_file))

    def __apply_sla(self, row: dict, overwrite) -> int:
        time_to_setup_applied = 0
        row = {k: v.strip() for k, v in row.items()}
        product = Product.objects.get(salesforce_id=row["Uuid"])

        if not product.supplier_setup_time or overwrite:
            product.supplier_setup_time = int(row["Time to create account"])
            time_to_setup_applied += 1
        product.save()
        self.stdout.write(
            self.style.SUCCESS(f"Imported SLA for Salesforce UUID: {row['Uuid']}")
        )
        return time_to_setup_applied

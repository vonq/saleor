import csv
from typing import Tuple

from django.core.management.base import BaseCommand

from api.products.models import JobTitle


class Command(BaseCommand):
    help = """
    Adds Dutch and German translations to job titles.
    Takes as input a CSV file with the same format as https://docs.google.com/spreadsheets/d/1RUnTbM1e3fwpF7mxZ2tyzCPl3ctjRJz0P_sdIwUXrno 
    """

    required_columns = [
        "English Label",
        "Auto Dutch Translation",
        "Auto German Translation",
        "Better Dutch translation",
        "Better German translation",
    ]

    nl_translations_applied = 0
    de_translations_applied = 0

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Force applying translations even if they already exist.",
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]
        force_translate = kwargs["force"]

        total_nl_translations_applied = 0
        total_de_translations_applied = 0

        try:
            with open(csv_file, mode="r") as fp:
                reader = csv.DictReader(fp, fieldnames=self.required_columns)
                self.stdout.write("Applying translations...")
                for row in reader:
                    nl_applied, de_applied = self.__translate(row, force_translate)
                    total_de_translations_applied += de_applied
                    total_nl_translations_applied += nl_applied

            self.stdout.write(
                self.style.SUCCESS(
                    "Success. {} German translations, {} Dutch translations applied.".format(
                        total_de_translations_applied, total_nl_translations_applied
                    )
                )
            )

        except OSError:
            self.stdout.write(self.style.ERROR('Could not open file "%s".' % csv_file))

    @staticmethod
    def __translate(row: dict, force_translate) -> Tuple[int, int]:
        nl_translations_applied = 0
        de_translations_applied = 0

        qs = JobTitle.objects.filter(name__iexact=row["English Label"])

        # trim translations, just in case
        row = {k: v.strip() for k, v in row.items()}

        for job_title in qs:  # type: JobTitle
            if job_title.name_de and not force_translate:
                continue
            job_title.name_de = (
                row["Better German translation"]
                if row["Better German translation"]
                else row["Auto German Translation"]
            )
            de_translations_applied += 1

            if job_title.name_nl and not force_translate:
                continue
            job_title.name_nl = (
                row["Better Dutch translation"]
                if row["Better Dutch translation"]
                else row["Auto Dutch Translation"]
            )
            nl_translations_applied += 1
            job_title.save()

        return nl_translations_applied, de_translations_applied

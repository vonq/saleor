import json
import os
from typing import Type, Union

from django.core.management.base import BaseCommand
from django.db.models import Model

from api.vonqtaxonomy.models import (
    Industry as MapiIndustry,
    JobCategory as MapiJobCategory,
)
from api.products.models import Industry as PkbIndustry, JobFunction as PkbJobFunction
from api.vonqtaxonomy.igb import igb_industries, igb_job_categories

dirname = os.path.dirname(__file__)
mappings_directory = os.path.join(dirname, "../../mappings/")


class Command(BaseCommand):
    help = """
    Imports mappings from PKB taxonomy to old VONQ taxonomy for the purpose of mapping PKB orders in IGB
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-i",
            "--mapi_industries_taxonomy_file",
            type=str,
            help="The path to the industries mapping file.",
            required=False,
        )
        parser.add_argument(
            "-m",
            "--industries_mapping_file",
            type=str,
            help="The path to the industries mapping file.",
            required=False,
        )

        parser.add_argument(
            "-j",
            "--mapi_job_categories_taxonomy_file",
            type=str,
            help="The path to the MAPI job categories taxonomy.",
            required=False,
        )
        parser.add_argument(
            "-n",
            "--job_function_mapping_file",
            type=str,
            help="The path to the job functions mapping file.",
            required=False,
        )

    def handle(self, *args, **options):
        mapi_industries_taxonomy_file = options.get(
            "mapi_industries_taxonomy_file"
        ) or os.path.join(mappings_directory, "vonq_industries.json")
        mapi_job_categories_taxonomy_file = options.get(
            "mapi_job_categories_taxonomy_file"
        ) or os.path.join(mappings_directory, "vonq_jobcategories.json")

        industries_mappings_path = options.get(
            "industries_mapping_file"
        ) or os.path.join(mappings_directory, "backward_industry_mapping.json")
        job_functions_mappings_path = options.get(
            "job_function_mapping_file"
        ) or os.path.join(mappings_directory, "backward_job_function_mapping.json")

        for file_path in [
            mapi_industries_taxonomy_file,
            mapi_job_categories_taxonomy_file,
            industries_mappings_path,
            job_functions_mappings_path,
        ]:
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.ERROR(
                        'Could not open industries mapping file "%s".'
                        % industries_mappings_path
                    )
                )
                exit(1)

        mapi_industries = json.load(open(mapi_industries_taxonomy_file))
        industries_mappings = json.load(open(industries_mappings_path))

        mapi_job_categories = json.load(open(mapi_job_categories_taxonomy_file))
        job_functions_mappings = json.load(open(job_functions_mappings_path))

        try:
            self._import_vonq_taxonomy(MapiIndustry, mapi_industries)
            self._map_pkb_to_vonq_taxonomy(
                PkbIndustry, MapiIndustry, industries_mappings
            )

            self._import_vonq_taxonomy(MapiJobCategory, mapi_job_categories)
            self._map_pkb_to_vonq_taxonomy(
                PkbJobFunction, MapiJobCategory, job_functions_mappings
            )
        except ItemNotInIgbError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            exit(1)

    def _import_vonq_taxonomy(
        self, taxonomy_model: Type[Model], mapi_taxonomy_response: list
    ):
        for mapi_taxonomy_item in mapi_taxonomy_response:
            if (
                taxonomy_model.objects.filter(mapi_id=mapi_taxonomy_item["id"]).count()
                > 0
            ):
                continue

            taxonomy_item = taxonomy_model(mapi_id=mapi_taxonomy_item["id"])
            for name in mapi_taxonomy_item["name"]:
                if name["languageCode"] == "en_GB":
                    taxonomy_item.name_en = name["value"]
                elif name["languageCode"] == "nl_NL":
                    taxonomy_item.name_nl = name["value"]
                elif name["languageCode"] == "de_DE":
                    taxonomy_item.name_de = name["value"]

            taxonomy_item.save()

    def _map_pkb_to_vonq_taxonomy(
        self,
        pkb_model: Union[Type[PkbIndustry], Type[PkbJobFunction]],
        vonq_model: Union[Type[MapiIndustry], Type[MapiJobCategory]],
        mappings: dict,
    ):
        for key, value in mappings.items():
            # in the input file, pkb taxonomy items are in english
            try:
                pkb_item = pkb_model.objects.get(name_en=key)
            except pkb_model.DoesNotExist:
                # if the industry is simply not there, skip & continue
                continue

            # in the raw file passed by DS, some pkb items are mapped to multiple vonq items
            value = value[0] if type(value) == list else value
            vonq_item = vonq_model.objects.get(name_en=value)

            if (
                vonq_item.name_nl not in igb_industries
                and vonq_item.name_nl not in igb_job_categories
            ):
                raise ItemNotInIgbError(
                    'Item "{value}" of type {type} not in IGB'.format(
                        value=vonq_item.name, type=type(vonq_item)
                    )
                )

            pkb_item.vonq_taxonomy_value = vonq_item
            pkb_item.save()


class ItemNotInIgbError(Exception):
    pass

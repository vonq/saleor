from typing import Type

from django.core.management import BaseCommand
from django.db.models import Model

from api.products.models import (
    Industry,
    Category,
    JobFunction,
    JobTitle,
    Location,
    PostingRequirement,
    Channel,
    Product,
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Import the full PKB data (including taxonomies) into Saleor's tables

        1. Import taxonomies
            1. Industry
            2. Category
            3. JobFunction
            4. JobTitle
            5. Location
            6. PostingRequirement

        2. Import products
            1. Channel
            2. Product
        """

        def move_entity_across(model: Type[Model]) -> None:
            self.stdout.write(f"*** Fetching {model} from PKB...")
            entities = model.objects.using("pkb").all()
            self.stdout.write(f"*** Saving {entities.count()} {model} into Saleor...")
            model.objects.using("default").bulk_create(entities)

        move_entity_across(Industry)
        move_entity_across(Category)
        move_entity_across(JobFunction)
        move_entity_across(JobTitle)
        move_entity_across(Location)

        # There's an entity PostingRequirement that gets created
        # as part of a PKB migration... (Products:0064)
        PostingRequirement.objects.using("default").delete()
        move_entity_across(PostingRequirement)

        move_entity_across(Channel)
        move_entity_across(Product)

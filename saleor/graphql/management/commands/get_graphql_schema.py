from django.core.management.base import BaseCommand

# [CORE]: Use the schema as imported in the urls
from saleor.urls import schema


class Command(BaseCommand):
    help = "Writes SDL for GraphQL API schema to stdout"

    def handle(self, *args, **options):
        self.stdout.write(str(schema))

from django.apps import apps
from django.core.management import BaseCommand

from api.currency.conversion import refresh_exchange_rates


class Command(BaseCommand):
    help = """
        Refresh our own storage of foreign currency exchange against EUR
        """

    def handle(self, *args, **options):
        refresh_exchange_rates(apps)

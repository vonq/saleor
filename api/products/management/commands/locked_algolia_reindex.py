from django.core.management import BaseCommand, call_command

from api.locks import acquire_database_transaction_lock


class Command(BaseCommand):
    help = """
        Prevent several reindexing processes running against the index
        at the same time by acquiring a transaction database lock.
        """

    def handle(self, *args, **kwargs):
        with acquire_database_transaction_lock(__name__) as acquired:
            if acquired:
                call_command("algolia_reindex")
            else:
                self.stdout.write(
                    self.style.ERROR("Indexing already in progress, skipping.")
                )

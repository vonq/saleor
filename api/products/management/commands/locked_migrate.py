from django.core.management import BaseCommand, call_command

from api.locks import acquire_database_transaction_lock


class Command(BaseCommand):
    help = """
        Prevent several migration processes running against the database
        at the same time by acquiring a transaction database lock.
        """

    def handle(self, *args, **kwargs):
        with acquire_database_transaction_lock(__name__) as acquired:
            if acquired:
                call_command("migrate", "--noinput")
            else:
                self.stdout.write(
                    self.style.ERROR("Migration already in progress, skipping.")
                )

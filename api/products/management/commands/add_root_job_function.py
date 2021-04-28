from django.core.management.base import BaseCommand
from api.products.models import JobFunction


class Command(BaseCommand):
    help = """
    Adds a root job function if it doesn't already exist
    """
    ROOT_JOB_FUNCTION = JobFunction(
        name_en="All job functions",
        name_nl="Alle functies",
        name_de="Alle Jobfunktionen",
    )

    def handle(self, *args, **kwargs):
        root_job_functions = JobFunction.objects.filter(parent_id=None)
        if root_job_functions.count() == 1:
            return
        all_jf = self.ROOT_JOB_FUNCTION.save()
        for root_jf in root_job_functions:
            root_jf.move_to(all_jf, "first-child")
            root_jf.save()

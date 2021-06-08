from unittest.mock import patch, mock_open

from algoliasearch_django.decorators import disable_auto_indexing
from django.test import TestCase, tag
from django.core import management

from api.products.models import JobTitle

csv_data = """
English Label,Auto Dutch Translation,Auto German Translation,Better Dutch translation,Better German translation
Recruitment Consultant,Recruitment Consultant,Personalberater,,
Customer Assistant,Customer Assistant,Kundenassistent,Customer Assistant Better Translation,Kundenassistent Better Translation
"""


@disable_auto_indexing
@tag("unit")
class CommandTests(TestCase):
    def setUp(self) -> None:
        jt1 = JobTitle(name="Recruitment Consultant", name_de="potato")
        jt1.save()

        jt2 = JobTitle(name="Customer Assistant")
        jt2.save()

    @patch("builtins.open", new_callable=mock_open, read_data=csv_data)
    def test_adds_translations_only_where_missing(self, mock_file):
        management.call_command("translate_job_titles", "some/path")
        self.assertEquals(
            JobTitle.objects.filter_across_languages(name="Personalberater").count(), 0
        )
        self.assertEquals(
            JobTitle.objects.filter_across_languages(
                name="Kundenassistent Better Translation"
            ).count(),
            1,
        )

    @patch("builtins.open", new_callable=mock_open, read_data=csv_data)
    def test_overwrites_existing_translations_when_forced(self, mock_file):
        management.call_command("translate_job_titles", "some/path", "--force")
        self.assertEquals(
            JobTitle.objects.filter_across_languages(name="Personalberater").count(), 1
        )

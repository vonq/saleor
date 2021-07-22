from urllib.parse import quote_plus

from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import JobFunction, JobTitle
from api.vonqtaxonomy.models import JobCategory as VonqJobCategory
from api.tests.integration.search import SearchTestCase
from api.products.search.index import JobFunctionIndex, JobTitleIndex


@tag("algolia")
@tag("integration")
class JobTitleSearchTestCase(SearchTestCase):
    model_index_class_pairs = [
        (JobTitle, JobTitleIndex),
        (
            JobFunction,
            JobFunctionIndex,
        ),
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        pkb_job_category = VonqJobCategory.objects.create(mapi_id=1, name="Something")

        software_development = JobFunction(name="Software Development")
        software_development.vonq_taxonomy_value = pkb_job_category
        software_development.save()
        cls.software_development_id = software_development.id

        python_developer = JobTitle(
            name_en="Python Developer",
            name_nl="Python-ontwikkelaar",
            frequency=1,
            canonical=True,
            active=True,
        )

        snake_tamer = JobTitle(
            name="Snake tamer",
            name_de="Schlangenentwickler",
            frequency=1,
            active=True,
            canonical=False,
        )

        python_developer.save()
        snake_tamer.save()
        cls.snake_tamer_id = snake_tamer.id
        snake_tamer.alias_of = python_developer
        snake_tamer.save()

        # add job function and re-index
        python_developer.job_function = software_development
        python_developer.save()

        cls.python_developer_id = python_developer.id

        java_developer = JobTitle(
            name="Java Developer",
            name_de="Arbeitslos",
            frequency=100000,
            canonical=True,
            active=True,
        )

        cls.java_developer_id = java_developer.id
        java_developer.save()

        nurse_job_titles = [
            ("registered nurse", 1538),
            ("staff nurse", 1134),
            ("nursery nurse", 780),
            ("nursery assistant", 1538),
            ("nursery manager", 1000),
        ]

        for title, frequency in nurse_job_titles:
            JobTitle.objects.create(
                name=title,
                name_nl=f"{title} in dutch",
                frequency=frequency,
                canonical=True,
                active=True,
            )

    def test_can_search_in_default_language(self):
        resp = self.client.get(reverse("job-titles") + "?text=pyth")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 1)
        self.assertEqual(resp.json()["results"][0]["name"], "Python Developer")

    def test_most_frequent_job_title_is_at_the_top(self):
        resp = self.client.get(reverse("job-titles") + "?text=Developer")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 2)
        self.assertEqual(resp.json()["results"][0]["name"], "Java Developer")

    def test_can_search_across_languages(self):
        resp1 = self.client.get(reverse("job-titles") + "?text=Python-ontwikkelaar")
        resp2 = self.client.get(reverse("job-titles") + "?text=arbeit")
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(len(resp1.json()["results"]), 1)
        self.assertEqual(resp1.json()["results"][0]["name"], "Python Developer")

        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(resp2.json()["results"]), 1)
        self.assertEqual(resp2.json()["results"][0]["name"], "Java Developer")

    def test_includes_job_function_where_available(self):
        resp = self.client.get(reverse("job-titles") + "?text=python")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 1)
        self.assertEqual(
            resp.json()["results"][0]["job_function"]["id"],
            self.software_development_id,
        )

    def test_ranks_exact_word_matches_first_regardless_of_frequency(self):
        resp = self.client.get(reverse("job-titles") + "?text=nurse").json()

        self.assertEqual(resp["results"][0]["name"], "registered nurse")

    def test_ranks_exact_matches_first_but_still_matches_partially_ordered_by_frequency(
        self,
    ):
        resp = self.client.get(reverse("job-titles") + "?text=nurse").json()

        self.assertEqual(resp["results"][0]["name"], "registered nurse")
        self.assertEqual(resp["results"][1]["name"], "staff nurse")
        self.assertEqual(resp["results"][2]["name"], "nursery nurse")
        self.assertEqual(resp["results"][3]["name"], "nursery assistant")
        self.assertEqual(resp["results"][4]["name"], "nursery manager")

    def test_decompounds_dutch_words(self):
        resp = self.client.get(reverse("job-titles") + "?text=ontwikkelaar")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["results"]), 1)
        # Python developer has been named Python-ontwikkelaar in Dutch
        self.assertEqual(
            resp.json()["results"][0]["id"],
            self.python_developer_id,
        )

    def test_does_fuzzy_search_reasonably_well(self):
        resp = self.client.get(
            reverse("job-titles")
            + "?text="
            + quote_plus(
                "Senior Developer Flask/Django/Python 10k+ EUR/decade starting today"
            )
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json()["results"][0]["id"],
            self.python_developer_id,
        )

from django.test import TestCase

from algoliasearch_django.decorators import disable_auto_indexing
from django.test import tag
from rest_framework.reverse import reverse

from api.products.models import JobFunction
from api.vonqtaxonomy.models import JobCategory as VonqJobCategory


@tag("unit")
@disable_auto_indexing
class JobFunctionViewTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()

        vonq_job_category = VonqJobCategory.objects.create(mapi_id=1, name="Whatever")

        self.engineering = JobFunction.objects.create(
            name="Engineering",
            name_de="Schlangenentwickler",
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

        self.software_engineering = JobFunction.objects.create(
            name="Software Engineering",
            name_de="Arbeitslos",
            parent_id=self.engineering.id,
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

    def test_can_list_in_default_language(self):
        resp = self.client.get(reverse("job-functions"))
        self.assertEqual(resp.status_code, 200)

        self.assertListEqual(
            resp.json(),
            [
                {
                    "id": self.engineering.id,
                    "name": "Engineering",
                    "children": [
                        {
                            "id": self.software_engineering.id,
                            "name": "Software Engineering",
                            "children": [],
                        }
                    ],
                }
            ],
        )


@tag("unit")
@disable_auto_indexing
class JobFunctionTreeStructureTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        vonq_job_category = VonqJobCategory.objects.create(mapi_id=1, name="Whatever")

        cls.engineering = JobFunction.objects.create(
            name="Engineering", vonq_taxonomy_value_id=vonq_job_category.id
        )

        cls.software_development = JobFunction.objects.create(
            name="Software Engineering",
            parent_id=cls.engineering.id,
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

        cls.civil_engineering = JobFunction.objects.create(
            name="Civil Engineering",
            parent_id=cls.engineering.id,
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

        cls.java_development = JobFunction.objects.create(
            name="Java Software Development",
            parent_id=cls.software_development.id,
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

        cls.bad_java_development = JobFunction.objects.create(
            name="Bad Java Development",
            parent_id=cls.java_development.id,
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

        cls.construction = JobFunction.objects.create(
            name="Construction", vonq_taxonomy_value_id=vonq_job_category.id
        )

        cls.architect = JobFunction.objects.create(
            name="Architect",
            parent_id=cls.construction.id,
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

        cls.designer = JobFunction.objects.create(
            name="Designer",
            parent_id=cls.architect.id,
            vonq_taxonomy_value_id=vonq_job_category.id,
        )

    def test_list_view_returns_a_nested_structure(self):
        resp = self.client.get(reverse("job-functions"))

        self.assertListEqual(
            resp.json(),
            [
                {
                    "id": self.engineering.id,
                    "name": "Engineering",
                    "children": [
                        {
                            "id": self.software_development.id,
                            "name": "Software Engineering",
                            "children": [
                                {
                                    "id": self.java_development.id,
                                    "name": "Java Software Development",
                                    "children": [
                                        {
                                            "id": self.bad_java_development.id,
                                            "name": "Bad Java Development",
                                            "children": [],
                                        }
                                    ],
                                }
                            ],
                        },
                        {
                            "id": self.civil_engineering.id,
                            "name": "Civil Engineering",
                            "children": [],
                        },
                    ],
                },
                {
                    "id": self.construction.id,
                    "name": "Construction",
                    "children": [
                        {
                            "id": self.architect.id,
                            "name": "Architect",
                            "children": [
                                {
                                    "id": self.designer.id,
                                    "name": "Designer",
                                    "children": [],
                                }
                            ],
                        }
                    ],
                },
            ],
        )

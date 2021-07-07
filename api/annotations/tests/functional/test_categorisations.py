from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import Industry, JobFunction, Product
from api.vonqtaxonomy.models import (
    JobCategory as DesqJobCategory,
    Industry as DesqIndustry,
)


@tag("functional")
class CategorisationViewTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=False)

        self.board1 = Product(title="Fashion jobs")
        self.board1.save()

        self.board2 = Product(title="Hospitality jobs")
        self.board2.save()

        vonq_job_function = DesqJobCategory(
            mapi_id=123,
            name="A DESQ job category that needs to be associated to all job functions in this test",
            name_nl="DESQ job category in Dutch",
        )
        vonq_job_function.save()
        vonq_industry = DesqIndustry(
            mapi_id=456,
            name="A DESQ industry that needs to be associated to all industries in this test",
            name_nl="DESQ Industry in Dutch",
        )
        vonq_industry.save()

        engineering = JobFunction(
            name="Engineering", vonq_taxonomy_value_id=vonq_job_function.id
        )
        engineering.save()
        self.engineering = engineering.id

        software_engineering = JobFunction(
            name="Software Engineering",
            parent=engineering,
            vonq_taxonomy_value_id=vonq_job_function.id,
        )
        software_engineering.save()

        self.i1 = Industry(name="B Industry", vonq_taxonomy_value_id=vonq_industry.id)
        # breakpoint()
        self.i1.save()

        self.i2 = Industry(name="A Industry", vonq_taxonomy_value_id=vonq_industry.id)
        self.i2.save()
        self.i2.vonq_taxonomy_value_id = vonq_industry.id
        self.i2.save()

    def _login_as_superuser(self):
        User.objects.create_superuser(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_superuser_required(self):
        resp = self.client.post(
            reverse("annotations:add_categorisation"),
            {},
            content_type="application/json",
        )
        self.assertNotEqual(resp.status_code, 200)

    def test_can_add_job_function_categorisation(self):
        payload = {
            "field": "job_functions",
            "id": self.board1.id,
            "categoryName": "Engineering",
        }

        self._login_as_superuser()
        resp = self.client.post(
            reverse("annotations:add_categorisation"),
            payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            Product.objects.all()
            .filter(pk=self.board1.id)
            .first()
            .job_functions.all()
            .count(),
            1,
        )
        self.assertEqual(
            Product.objects.all()
            .filter(pk=self.board1.id)
            .first()
            .job_functions.first()
            .name,
            "Engineering",
        )

        self.assertEqual(
            Product.objects.all()
            .filter(pk=self.board2.id)
            .first()
            .job_functions.count(),
            0,
        )

    def test_can_add_industry_categorisation(self):
        self._login_as_superuser()
        payload = {
            "field": "industries",
            "id": self.board1.id,
            "categoryName": "B Industry",
        }

        resp = self.client.post(
            reverse("annotations:add_categorisation"),
            payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            Product.objects.all()
            .filter(pk=self.board1.id)
            .first()
            .industries.first()
            .name,
            "B Industry",
        )

        self.assertEqual(
            Product.objects.all().filter(pk=self.board2.id).first().industries.count(),
            0,
        )

    def tearDown(self) -> None:
        self.client.logout()

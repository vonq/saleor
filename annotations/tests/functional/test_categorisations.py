from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import Industry, JobFunction, Product


@tag("functional")
class CategorisationViewTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=False)

        self.board1 = Product(title="Fashion jobs")
        self.board1.save()

        self.board2 = Product(title="Hospitality jobs")
        self.board2.save()

        engineering = JobFunction(name="Engineering")
        engineering.save()
        self.engineering = engineering.id

        software_engineering = JobFunction(
            name="Software Engineering", parent=engineering
        )
        software_engineering.save()
        self.software_engineering = software_engineering.id

        self.i1 = Industry(name="B Industry")
        self.i2 = Industry(
            name="A Industry",
        )
        self.i2.save()
        self.i1.save()

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

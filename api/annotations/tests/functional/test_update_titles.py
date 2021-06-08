from django.test import Client, TestCase, tag
from django.contrib.auth.models import User
from rest_framework.reverse import reverse

from api.products.models import JobTitle, Product


@tag("functional")
class CategorisationViewTestCase(TestCase):
    def setUp(self) -> None:

        self.client = Client(enforce_csrf_checks=False)
        # self.client.login(username="user", password="pass")

        self.board1 = Product(title="Fashion jobs")
        self.board1.save()

        self.board2 = Product(title="Hospitality jobs")
        self.board2.save()

        self.jt1 = JobTitle(name="Potato peeler", active=False, canonical=True)
        self.jt1.save()
        self.jt2 = JobTitle(name="Snake tamer", active=False, canonical=True)
        self.jt2.save()

    def _login_as_superuser(self):
        User.objects.create_superuser(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_superuser_required(self):
        resp = self.client.post(
            reverse("annotations:update_title"),
            {},
            content_type="application/json",
        )
        self.assertNotEqual(resp.status_code, 200)

    def test_can_update_job_title_details(self):
        self._login_as_superuser()
        payload = {
            "id": self.jt1.id,
            "active": False,
            "canonical": False,
            "alias_of__id": self.jt2.id,
        }
        resp = self.client.post(
            reverse("annotations:update_title"),
            payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        updated_jt = JobTitle.objects.filter(pk=self.jt1.id).first()

        self.assertEqual(updated_jt.active, False)
        self.assertEqual(updated_jt.canonical, False)
        self.assertEqual(updated_jt.alias_of.id, self.jt2.id)

        updated_jt2 = JobTitle.objects.filter(pk=self.jt2.id).first()
        self.assertTrue(self.jt2 == updated_jt2)

    def tearDown(self) -> None:
        self.client.logout()

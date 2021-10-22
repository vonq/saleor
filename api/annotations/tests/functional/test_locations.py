from django.contrib.auth.models import User
from django.test import Client, TestCase, tag
from rest_framework.reverse import reverse

from api.products.models import Product, Location


@tag("functional")
class SetLocationViewTestCase(TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=False)

        self.congo = Location(canonical_name="Congo")
        self.congo.save()

        self.london = Location(canonical_name="London")
        self.london.save()

        self.france = Location(canonical_name="France")
        self.france.save()

        self.board = Product(title="Fashion jobs")
        self.board.save()

        self.board.locations.add(self.congo)
        self.board.save()

        self.board2 = Product(title="Other jobs")
        self.board2.save()

    def _login_as_superuser(self):
        User.objects.create_superuser(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_superuser_required(self):
        resp = self.client.post(
            reverse("annotations:set_locations"),
            {},
            content_type="application/json",
        )
        self.assertNotEqual(resp.status_code, 200)

    def test_can_set_locations(self):
        self._login_as_superuser()

        payload = {
            "id": self.board.id,
            "locations": ["London", "France"],
        }

        resp = self.client.post(
            reverse("annotations:set_locations"),
            payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            Product.objects.all().filter(pk=self.board.id).first().locations.count(),
            2,
        )

        self.assertEqual(
            Product.objects.all()
            .filter(pk=self.board.id)
            .first()
            .locations.first()
            .canonical_name,
            "London",
        )

        self.assertEqual(
            Product.objects.all()
            .filter(pk=self.board.id)
            .first()
            .locations.last()
            .canonical_name,
            "France",
        )

        self.assertEqual(
            Product.objects.all().filter(pk=self.board2.id).first().locations.count(),
            0,
        )

    def tearDown(self) -> None:
        self.client.logout()

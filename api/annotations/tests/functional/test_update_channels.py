from django.test import Client, TestCase, tag
from django.contrib.auth.models import User
from rest_framework.reverse import reverse

from api.products.models import Channel, Product


@tag("functional")
class TypeViewTestCase(TestCase):
    def setUp(self) -> None:

        self.client = Client(enforce_csrf_checks=False)
        # self.client.login(username="user", password="pass")

        self.board1 = Product(title="Fashion jobs")
        self.board1.save()

        self.board2 = Product(title="Hospitality jobs")
        self.board2.save()

        self.channel1 = Channel(type="community", name="AcmeJobs", url="acmejobs.com")
        self.channel1.save()

        self.board1.channel = self.channel1
        self.board2.channel = self.channel1

        self.channel2 = Channel(type="aggregator", name="BettaJobs", url="bettajobs.co")
        self.channel2.save()

    def _login_as_superuser(self):
        User.objects.create_superuser(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_superuser_required(self):
        resp = self.client.post(
            reverse("annotations:set_channel"),
            {},
            content_type="application/json",
        )
        self.assertNotEqual(resp.status_code, 200)

    def test_can_update_channel_type(self):
        self._login_as_superuser()
        payload = {"id": self.channel1.id, "type": "job board"}
        resp = self.client.post(
            reverse("annotations:set_channel"),
            payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        updated_channel1 = Channel.objects.filter(pk=self.channel1.id).first()

        self.assertEqual(updated_channel1.type, "job board")

        updated_channel2 = Channel.objects.filter(pk=self.channel2.id).first()
        self.assertTrue(self.channel2 == updated_channel2)

    def test_cannot_set_invalid_channel_type(self):
        self._login_as_superuser()
        payload = {"id": self.channel1.id, "type": "bollocks"}
        resp = self.client.post(
            reverse("annotations:set_channel"),
            payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)

        updated_channel1 = Channel.objects.filter(pk=self.channel1.id).first()

        self.assertEqual(updated_channel1.type, "community")

        updated_channel2 = Channel.objects.filter(pk=self.channel2.id).first()
        self.assertTrue(self.channel2 == updated_channel2)

    def tearDown(self) -> None:
        self.client.logout()

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class AuthenticatedTestCase(TestCase):
    def setUp(self) -> None:
        user = User.objects.create(username="test", password="test")
        self.client.force_login(user)

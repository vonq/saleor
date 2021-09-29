import time

from django.contrib.auth import get_user_model


def force_user_login(client, profile_type):
    User = get_user_model()
    hapi_user = User.objects.create(username=f"test_{time.time_ns()}", password="test")
    hapi_user.profile.type = profile_type
    client.force_login(hapi_user)

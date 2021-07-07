import time

from django.contrib.auth import get_user_model


def force_user_login(client, profile_type):
    User = get_user_model()
    mapi_user = User.objects.create(username=f"test_{time.time_ns()}", password="test")
    mapi_user.profile.type = profile_type
    client.force_login(mapi_user)

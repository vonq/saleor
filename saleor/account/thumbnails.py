from django.contrib.auth import get_user_model

from ..celeryconf import app
from ..core.utils import create_thumbnails

User = get_user_model()


@app.task
def create_user_avatar_thumbnails(user_id):
    """Create thumbnails for user avatar."""
    create_thumbnails(
        pk=user_id, model=User, size_set="user_avatars", image_attr="avatar"
    )

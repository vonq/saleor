import django.dispatch
from django.contrib.auth import get_user_model
from django_q.tasks import async_task

from api.products.models import Profile, SFSyncable
from api.salesforce import sync

User = get_user_model()

channel_updated = django.dispatch.Signal()
product_updated = django.dispatch.Signal()


def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "profile"):
        Profile.objects.create(user=instance)
    instance.profile.save()


def sync_channel_with_salesforce(sender, instance, **kwargs):
    if instance.salesforce_id:
        async_task(
            sync.update_channel,
            channel_instance=instance,
            q_options={"task_name": f"channel-update-{instance.salesforce_id}"},
        )
    else:
        async_task(
            sync.push_channel,
            channel_instance=instance,
            q_options={"task_name": f"channel-create-{instance.name}"},
        )


def sync_product_with_salesforce(sender, instance, **kwargs):
    if not instance.salesforce_last_sync:
        async_task(
            sync.push_product,
            product_instance=instance,
            q_options={"task_name": f"product-create-{instance.title}"},
        )
    else:
        async_task(
            sync.update_product,
            product_instance=instance,
            q_options={"task_name": f"product-update-{instance.title}"},
        )

from django.core.management import BaseCommand

from api.products.models import Channel
from api.igb.api.client import get_singleton_client


class Command(BaseCommand):
    help = """
    Refresh availability of MoC channels against the IGB API
    in case they _cease_ support of MoC for that particular board.
    """

    def handle(self, *args, **options):
        moc_channels = Channel.objects.filter(moc_enabled=True)
        igb_client = get_singleton_client()

        for channel in moc_channels:
            if not channel.igb_moc_channel_class:
                continue

            moc_board = igb_client.detail(channel.igb_moc_channel_class)
            if not moc_board:
                channel.igb_moc_channel_class = None

            channel.save()

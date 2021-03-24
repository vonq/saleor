from ...campaign import models
from ..utils.filters import filter_by_query_param
from ..channel import ChannelQsContext

CAMPAIGN_SEARCH_FIELDS = ("titile")


def resolve_campaings(info, query, channel_slug, **_kwargs):
    qs = models.Campaign.objects.all()
    qs = filter_by_query_param(qs, query, CAMPAIGN_SEARCH_FIELDS)
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)

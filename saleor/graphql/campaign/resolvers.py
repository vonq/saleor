from ...campaign import models
from ..utils.filters import filter_by_query_param
from ..channel import ChannelQsContext

CAMPAIGN_SEARCH_FIELDS = ("titile")
JOB_INFO_SEARCH_FIELDS = ("title")


def resolve_campaings(info, query, channel_slug, **_kwargs):
    qs = models.Campaign.objects.all()
    qs = filter_by_query_param(qs, query, CAMPAIGN_SEARCH_FIELDS)
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_job_infos(info, query, channel_slug, **_kwargs):
    qs = models.JobInfo.objects.all()
    qs = filter_by_query_param(qs, query, JOB_INFO_SEARCH_FIELDS)
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)

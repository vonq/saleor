from ...campaign import models
from ..utils.filters import filter_by_query_param

CAMPAIGN_SEARCH_FIELDS = ("titile")
JOB_INFO_SEARCH_FIELDS = ("title")


def resolve_campaings(info, query, **_kwargs):
    qs = models.Campaign.objects.all()
    return filter_by_query_param(qs, query, CAMPAIGN_SEARCH_FIELDS)


def resolve_job_infos(info, query, **_kwargs):
    qs = models.JobInfo.objects.all()
    return filter_by_query_param(qs, query, JOB_INFO_SEARCH_FIELDS)

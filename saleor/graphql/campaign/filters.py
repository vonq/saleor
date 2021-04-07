import django_filters

from ...campaign.models import Campaign, JobInfo
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_query_param


def filter_campaign_title(qs, _, value):
    fields = [
        "title",
    ]
    qs = filter_by_query_param(qs, value, fields)
    return qs


class CampaignFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(method=filter_campaign_title)

    class Meta:
        model = Campaign
        fields = [
            "title",
        ]


class CampaignFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CampaignFilter


def filter_job_info_title(qs, _, value):
    fields = [
        "title",
    ]
    qs = filter_by_query_param(qs, value, fields)
    return qs


class JobInfoFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(method=filter_campaign_title)

    class Meta:
        model = JobInfo
        fields = [
            "title",
        ]


class JobInfoFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = JobInfoFilter

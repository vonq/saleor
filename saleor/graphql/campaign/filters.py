import django_filters

from ...campaign.models import Campaign
from ..core.types import ChannelFilterInputObjectType
from ..utils.filters import filter_by_query_param


def filter_campaign_title(qs, _, value):
    fields = ["title", ]
    qs = filter_by_query_param(qs, value, fields)
    return qs


class CampaignFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(method=filter_campaign_title)

    class Meta:
        model = Campaign
        fields = ["title", ]


class CampaignFilterInput(ChannelFilterInputObjectType):
    class Meta:
        filterset_class = CampaignFilter

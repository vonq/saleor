import graphene

from ..core.types import ChannelSortInputObjectType


class CampaignSortField(graphene.Enum):
    USER = ["user_id"]


class CampaignSortInput(ChannelSortInputObjectType):
    class Meta:
        sort_enum = CampaignSortField
        type_name = "campaigns"


class JobInfoSortField(graphene.Enum):
    CAMPAIGN = ["campaign_id", ]


class JobInfoSortInput(ChannelSortInputObjectType):
    class Meta:
        sort_enum = JobInfoSortField
        type_name = "job_infos"

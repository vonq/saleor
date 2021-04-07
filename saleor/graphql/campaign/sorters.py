import graphene

from ..core.types import SortInputObjectType


class CampaignSortField(graphene.Enum):
    USER = ["user_id"]


class CampaignSortInput(SortInputObjectType):
    class Meta:
        sort_enum = CampaignSortField
        type_name = "campaigns"


class JobInfoSortField(graphene.Enum):
    CAMPAIGN = [
        "campaign_id",
    ]


class JobInfoSortInput(SortInputObjectType):
    class Meta:
        sort_enum = JobInfoSortField
        type_name = "job_infos"

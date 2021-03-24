import graphene

from ..core.types import ChannelSortInputObjectType


class CampaignSortField(graphene.Enum):
    USER = ["user_id"]


class CampaignSortInput(ChannelSortInputObjectType):
    class Meta:
        sort_enum = CampaignSortField
        type_name = "campaigns"

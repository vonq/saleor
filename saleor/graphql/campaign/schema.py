import graphene
from ..core.fields import ChannelContextFilterConnectionField
from .mutations.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignDelete
)
from .types import CampaignType
from .resolvers import resolve_campaings
from .sorters import CampaignSortInput
from .filters import CampaignFilterInput


class CampaignQuery(graphene.ObjectType):
    campaigns = ChannelContextFilterConnectionField(
        CampaignType,
        description="List of campaigns.",
        sort_by=CampaignSortInput(description="Sort campaigns."),
        filter=CampaignFilterInput(description="Filter campaigns.")
    )

    def resolve_campaigns(self, info, query=None, channel=None, **data):
        return resolve_campaings(info, query, channel_slug=None, **data)


class CampaignMutations(graphene.ObjectType):
    # campaign
    campaign_create = CampaignCreate.Field()
    campaign_delete = CampaignDelete.Field()
    campaign_update = CampaignUpdate.Field()

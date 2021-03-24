import graphene
from ..core.fields import ChannelContextFilterConnectionField
from ..channel import ChannelContext
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
    campaign = graphene.Field(
        CampaignType,
        description="Look up a campaign by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the campaign.", required=True
        ),
    )

    def resolve_campaigns(self, info, query=None, channel=None, **data):
        return resolve_campaings(info, query, channel_slug=None, **data)

    def resolve_campaign(self, info, id, channel=None):
        campaign = graphene.Node.get_node_from_global_id(info, id, CampaignType)
        return ChannelContext(node=campaign, channel_slug=channel) if campaign else None


class CampaignMutations(graphene.ObjectType):
    # campaign
    campaign_create = CampaignCreate.Field()
    campaign_delete = CampaignDelete.Field()
    campaign_update = CampaignUpdate.Field()

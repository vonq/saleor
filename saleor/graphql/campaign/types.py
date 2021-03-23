import graphene

from ...campaign.models import Campaign
from ..core.connection import CountableDjangoObjectType


class CampaignType(CountableDjangoObjectType):

    class Meta:
        description = "Represents a campaign data."
        interfaces = [graphene.relay.Node, ]
        model = Campaign

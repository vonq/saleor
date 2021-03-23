import graphene

from .mutations.campaign import (
    CampaignCreate,
    CampaignDelete
)


class CampaignQuery(graphene.ObjectType):
    pass


class CampaignMutations(graphene.ObjectType):
    # campaign
    campaign_create = CampaignCreate.Field()
    campaign_delete = CampaignDelete.Field()

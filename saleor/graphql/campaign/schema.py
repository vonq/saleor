import graphene

from .mutations.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignDelete
)


class CampaignQuery(graphene.ObjectType):
    pass


class CampaignMutations(graphene.ObjectType):
    # campaign
    campaign_create = CampaignCreate.Field()
    campaign_delete = CampaignDelete.Field()
    campaign_update = CampaignUpdate.Field()

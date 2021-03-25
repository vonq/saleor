import graphene
from ..core.fields import ChannelContextFilterConnectionField
from ..channel import ChannelContext
from .mutations.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignDelete
)
from .mutations.job_info import (
    JobInfoCreate,
    JobInfoUpdate,
    JobInfoDelete
)
from .types import CampaignType, JobInfoType
from .resolvers import resolve_campaings, resolve_job_infos
from .sorters import CampaignSortInput, JobInfoSortInput
from .filters import CampaignFilterInput, JobInfoFilterInput


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
    job_infos = ChannelContextFilterConnectionField(
        JobInfoType,
        description="List of job information instances.",
        sort_by=JobInfoSortInput(description="Sort job information."),
        filter=JobInfoFilterInput(description="Filter job information")
    )
    job_info = ChannelContextFilterConnectionField(
        JobInfoType,
        description="Look up a campaign by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the job info instance.", required=True
        ),
    )

    def resolve_campaigns(self, info, query=None, channel=None, **data):
        return resolve_campaings(info, query, channel_slug=None, **data)

    def resolve_campaign(self, info, id, channel=None):
        campaign = graphene.Node.get_node_from_global_id(info, id, CampaignType)
        return ChannelContext(node=campaign, channel_slug=channel) if campaign else None

    def resolve_job_infos(self, info, query=None, channel=None, **data):
        return resolve_job_infos(info, query, channel_slug=None, **data)

    def resolve_job_info(self, info, id, channel=None):
        job_info = graphene.Node.get_node_from_global_id(info, id, JobInfoType)
        return ChannelContext(node=job_info, channel_slug=channel) if job_info else None


class CampaignMutations(graphene.ObjectType):
    # campaign
    campaign_create = CampaignCreate.Field()
    campaign_delete = CampaignDelete.Field()
    campaign_update = CampaignUpdate.Field()
    # job info
    job_info_create = JobInfoCreate.Field()
    job_info_update = JobInfoUpdate.Field()
    job_info_delete = JobInfoDelete.Field()

import graphene

from ..core.fields import FilterInputConnectionField
from .filters import CampaignFilterInput, JobInfoFilterInput
from .mutations.campaign import CampaignCreate, CampaignDelete, CampaignUpdate
from .mutations.job_info import JobInfoCreate, JobInfoDelete, JobInfoUpdate
from .resolvers import resolve_campaings, resolve_job_infos
from .sorters import CampaignSortInput, JobInfoSortInput
from .types import CampaignType, JobInfoType


class CampaignQuery(graphene.ObjectType):
    campaigns = FilterInputConnectionField(
        CampaignType,
        description="List of campaigns.",
        sort_by=CampaignSortInput(description="Sort campaigns."),
        filter=CampaignFilterInput(description="Filter campaigns."),
    )
    campaign = graphene.Field(
        CampaignType,
        description="Look up a campaign by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the campaign.", required=True
        ),
    )
    job_infos = FilterInputConnectionField(
        JobInfoType,
        description="List of job information instances.",
        sort_by=JobInfoSortInput(description="Sort job information."),
        filter=JobInfoFilterInput(description="Filter job information"),
    )
    job_info = FilterInputConnectionField(
        JobInfoType,
        description="Look up a campaign by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the job info instance.", required=True
        ),
    )

    def resolve_campaigns(self, info, query=None, **data):
        return resolve_campaings(info, query, **data)

    def resolve_campaign(self, info, id, channel=None):
        return graphene.Node.get_node_from_global_id(info, id, CampaignType)

    def resolve_job_infos(self, info, query=None, **data):
        return resolve_job_infos(info, query, **data)

    def resolve_job_info(self, info, id, channel=None):
        return graphene.Node.get_node_from_global_id(info, id, JobInfoType)


class CampaignMutations(graphene.ObjectType):
    # campaign
    campaign_create = CampaignCreate.Field()
    campaign_delete = CampaignDelete.Field()
    campaign_update = CampaignUpdate.Field()
    # job info
    job_info_create = JobInfoCreate.Field()
    job_info_update = JobInfoUpdate.Field()
    job_info_delete = JobInfoDelete.Field()

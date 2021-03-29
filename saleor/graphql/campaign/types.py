import graphene
from graphene_federation import key
from graphene_django.types import DjangoObjectType

from ...campaign.models import Campaign, JobInfo
from ..core.connection import CountableDjangoObjectType
from ..account.types import User


@key(fields="id")
class CampaignType(CountableDjangoObjectType):

    user = graphene.Field(User, description="User of the campaign.")

    class Meta:
        description = "Represents a campaign data."
        interfaces = [graphene.relay.Node, ]
        model = Campaign
        only_fields = [
            "title",
            "industry",
            "education",
            "job_function",
            "seniority",
            "country",
        ]

    @staticmethod
    def resolve_user(root, info, **_kwargs):
        return root.user


@key(fields="id")
class JobInfoType(DjangoObjectType):

    campaign = graphene.Field(
        CampaignType, description="Represents campaign of job info instance."
    )

    class Meta:
        description = "Represents a campaign job information data."
        interfaces = [graphene.relay.Node, ]
        model = JobInfo

    @staticmethod
    def resolve_campaign(root, info, **_kwargs):
        return root.campaign

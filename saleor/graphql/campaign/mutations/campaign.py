import graphene

from ....campaign.models import Campaign
from ...account.enums import CountryCodeEnum
from ...core.types.common import CampaignError
from ...core.enums import IndustryEnum, EducationLeavelEnum, SeniorityEnum
from ...core.mutations import ModelMutation, ModelDeleteMutation
from ..types import CampaignType


class CampaignCreateInput(graphene.InputObjectType):
    user = graphene.ID(description="The id of the user.")
    title = graphene.String(required=True, description="Title of job.")
    job_function = graphene.String(required=True, description="Choose from thousands of job functions available in our database.")
    country = CountryCodeEnum(required=True, description="Country.")
    seniority = SeniorityEnum(required=True, description="Position level.")
    industry = IndustryEnum(required=True, description="Industry.")
    education = EducationLeavelEnum(required=True, description="Education level.")


class CampaignCreate(ModelMutation):

    class Arguments:
        input = CampaignCreateInput(required=True, description="Fields required to create campaign.")

    class Meta:
        description = "Create a new campaign."
        model = Campaign
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

    @classmethod
    def get_type_for_model(cls):
        return CampaignType


class CampaignDelete(ModelDeleteMutation):

    class Arguments:
        id = graphene.ID(description="ID of the campaign instance.")

    class Meta:
        description = "Delete a campaign."
        model = Campaign
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

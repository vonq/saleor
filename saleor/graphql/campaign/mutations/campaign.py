import graphene

from ....campaign.models import Campaign
from ...account.enums import CountryCodeEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types.common import CampaignError
from ..enums import EducationLeavelEnum, IndustryEnum, SeniorityEnum
from ..types import CampaignType


class CampaignCreateInput(graphene.InputObjectType):
    title = graphene.String(required=True, description="Title of job.")
    job_function = graphene.String(
        required=True,
        description="Choose from thousands of job functions available in our database.",
    )
    country = CountryCodeEnum(required=True, description="Country.")
    seniority = graphene.NonNull(SeniorityEnum, description="Seniority.")
    industry = graphene.NonNull(IndustryEnum, description="Industry.")
    education = graphene.NonNull(EducationLeavelEnum, description="Education level.")


class CampaignCreate(ModelMutation):
    class Arguments:
        input = CampaignCreateInput(
            required=True, description="Fields required to create campaign."
        )

    class Meta:
        description = "Create a new campaign."
        model = Campaign
        exclude = [
            "user",
        ]
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

    @classmethod
    def get_type_for_model(cls):
        return CampaignType

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        instance.user = info.context.user
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)


class CampaignUpdateInput(graphene.InputObjectType):
    title = graphene.String(description="Title of job.")
    job_function = graphene.String(
        description="Choose from thousands of job functions available in our database."
    )
    country = CountryCodeEnum(description="Country.")
    seniority = SeniorityEnum(description="Industry.")
    industry = IndustryEnum(description="Industry.")
    education = EducationLeavelEnum(description="Education level.")


class CampaignUpdate(CampaignCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a campaign to update.")
        input = CampaignUpdateInput(
            required=True, description="Fields required to update a campaign."
        )

    class Meta:
        description = "Updates an existing campaign."
        model = Campaign
        exclude = [
            "user",
        ]
        error_type_class = CampaignError
        error_type_field = "campaign_errors"


class CampaignDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the campaign instance.")

    class Meta:
        description = "Delete a campaign."
        model = Campaign
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

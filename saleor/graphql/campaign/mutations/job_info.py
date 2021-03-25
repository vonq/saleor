import graphene

from ....campaign.models import JobInfo
from ...core.types.common import CampaignError
from ...core.enums import (
    IndustryEnum,
    EducationLeavelEnum,
    SeniorityEnum,
    PeriodEnum,
    CurrenciesEnum,
    EmploymentTypeEnum
)
from ...core.mutations import ModelMutation, ModelDeleteMutation
from ...channel import ChannelContext


class JobInfoCreateInput(graphene.InputObjectType):
    campaign = graphene.ID(required=True, description="Campaign IDs witch assigned to job info.")
    title = graphene.String(required=True, description="Title of job.")
    seniority = SeniorityEnum(required=True, description="Position level.")
    industry = IndustryEnum(required=True, description="Industry.")
    job_description = graphene.String(required=True, description="Job description.")
    link_to_job_detail_page = graphene.String(required=True, description="Link to job detail page.")
    link_to_job_app_page = graphene.String(required=True, description="Link to the app page.")
    exp_year = graphene.Int(required=True, description="Years of experience.")
    education = EducationLeavelEnum(required=True, description="Education level.")
    hours_per_week = graphene.List(graphene.Int, required=True, description="Hours per week.")
    salary_interval = graphene.List(graphene.Int, required=True, description="Salary interval.")
    contact_info_name = graphene.String(description="Contact info name.")
    contact_phone = graphene.String(description="Contact phone.")
    currency = CurrenciesEnum(required=True, description="Currency.")
    period = PeriodEnum(required=True, description="Period.")
    employment_type = EmploymentTypeEnum(required=True, description="Employment type.")


class JobInfoCreate(ModelMutation):

    class Arguments:
        input = JobInfoCreateInput(required=True, description="Fields required to create job information.")

    class Meta:
        description = "Create a new job info."
        model = JobInfo
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)


class JobInfoUpdateInput(graphene.InputObjectType):
    campaign = graphene.ID(description="Campaign IDs witch assigned to job info.")
    title = graphene.String(description="Title of job.")
    seniority = SeniorityEnum(description="Position level.")
    industry = IndustryEnum(description="Industry.")
    job_description = graphene.String(description="Job description.")
    link_to_job_detail_page = graphene.String(description="Link to job detail page.")
    link_to_job_app_page = graphene.String(description="Link to the app page.")
    exp_year = graphene.Int(description="Years of experience.")
    education = EducationLeavelEnum(description="Education level.")
    hours_per_week = graphene.List(graphene.Int, description="Hours per week.")
    salary_interval = graphene.List(graphene.Int, description="Salary interval.")
    contact_info_name = graphene.String(description="Contact info name.")
    contact_phone = graphene.String(description="Contact phone.")
    currency = CurrenciesEnum(description="Currency.")
    period = PeriodEnum(description="Period.")
    employment_type = EmploymentTypeEnum(description="Employment type.")


class JobInfoUpdate(JobInfoCreate):

    class Arguments:
        id = graphene.ID(required=True, description="ID of a job info instance to update.")
        input = JobInfoUpdateInput(required=True, description="Fields required to create job information.")

    class Meta:
        description = "Updates an existing job information instance."
        model = JobInfo
        error_type_class = CampaignError
        error_type_field = "campaign_errors"


class JobInfoDelete(ModelDeleteMutation):

    class Arguments:
        id = graphene.ID(required=True, description="ID of a job info instance to delete.")

    class Meta:
        description = "Delete a job information instance."
        model = JobInfo
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

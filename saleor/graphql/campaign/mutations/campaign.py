from collections import defaultdict
from typing import Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
import graphene

from ....campaign.models import Campaign
from ....campaign.error_codes import CampaignErrorCode
from ...account.enums import CountryCodeEnum
from ...core.types.common import CampaignError
from ...core.enums import IndustryEnum, EducationLeavelEnum, SeniorityEnum
from ...core.mutations import ModelMutation, ModelDeleteMutation
from ...channel import ChannelContext
from ...utils.validators import check_for_duplicates
from ..types import CampaignType


class CampaignCreateInput(graphene.InputObjectType):
    add_products = graphene.List(
        graphene.NonNull(
            graphene.ID
        ),
        required=False,
        description="List of products IDs witch assigned to products."
    )
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
        exclude = ["user", ]
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

    @classmethod
    def get_type_for_model(cls):
        return CampaignType

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

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

    @classmethod
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        products = cleaned_data.get("add_products")
        if products:
            instance.products.add(*products)


class CampaignUpdateInput(graphene.InputObjectType):
    add_products = graphene.List(
        graphene.NonNull(
            graphene.ID
        ),
        required=False,
        description="List of products IDs witch assigned to products."
    )
    remove_products = graphene.List(
        graphene.NonNull(
            graphene.ID
        ),
        required=False,
        description="List of products IDs witch removed from products."
    )
    title = graphene.String(description="Title of job.")
    job_function = graphene.String(description="Choose from thousands of job functions available in our database.")
    country = CountryCodeEnum(description="Country.")
    seniority = SeniorityEnum(description="Position level.")
    industry = IndustryEnum(description="Industry.")
    education = EducationLeavelEnum(description="Education level.")


class CampaignUpdate(CampaignCreate):

    class Arguments:
        id = graphene.ID(required=True, description="ID of a campaign to update.")
        input = CampaignUpdateInput(required=True, description="Fields required to update a campaign.")

    class Meta:
        description = "Updates an existing campaign."
        model = Campaign
        exclude = ['user', ]
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

    @classmethod
    def check_duplicates(
        cls,
        errors: dict,
        input_data: dict,
        fields: Tuple[str, str, str],
    ):
        """Check if any items are on both input field.

        Raise error if some of items are duplicated.
        """
        error = check_for_duplicates(input_data, *fields)
        if error:
            print(error, flush=True)
            error.code = CampaignErrorCode.DUPLICATED_INPUT_ITEM.value
            error_field = fields[2]
            errors[error_field].append(error)

    @classmethod
    def clean_input(cls, info, instance, data):
        errors = defaultdict(list)
        input_fields = ("add_products", "remove_products", "products", )
        cls.check_duplicates(errors, data, input_fields)
        if errors:
            raise ValidationError(errors)
        cleaned_input = super().clean_input(info, instance, data)
        return cleaned_input

    @classmethod
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        add_products = cleaned_data.get("add_products")
        remove_products = cleaned_data.get("remove_products")
        if add_products:
            instance.products.add(*add_products)
        if remove_products:
            instance.products.remove(*remove_products)


class CampaignDelete(ModelDeleteMutation):

    class Arguments:
        id = graphene.ID(description="ID of the campaign instance.")

    class Meta:
        description = "Delete a campaign."
        model = Campaign
        error_type_class = CampaignError
        error_type_field = "campaign_errors"

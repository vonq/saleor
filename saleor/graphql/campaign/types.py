import graphene
from graphene_federation import key

from ...campaign.models import Campaign
from ..core.connection import CountableDjangoObjectType
from ..core.fields import ChannelContextFilterConnectionField
from ..account.types import User
from ..channel import ChannelQsContext
from ..channel.types import ChannelContextType
from ..product.types import Product


@key(fields="id")
class CampaignType(ChannelContextType, CountableDjangoObjectType):

    products = ChannelContextFilterConnectionField(
        Product, description="List of products this campaign applies to."
    )
    user = graphene.Field(User, description="User of the campaign.")

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
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
    def resolve_products(root, info, **_kwargs):
        qs = root.node.products.all()
        return ChannelQsContext(qs=qs, channel_slug=root.channel_slug)

    @staticmethod
    def resolve_user(root, info, **_kwargs):
        return root.node.user

import graphene

from saleor.graphql.checkout.resolvers import resolve_checkout_lines
from saleor.graphql.checkout.types import Checkout
from saleor.graphql.core.fields import BaseDjangoConnectionField
from vonq.permissions import CheckoutPermissions, remote_permission_required
from saleor.checkout import models


def resolve_checkouts(channel_slug, organization_id):
    queryset = models.Checkout.objects.all()
    if channel_slug:
        queryset = queryset.filter(channel__slug=channel_slug, metadata__orgId=organization_id)
    return queryset


class CheckoutQueries(graphene.ObjectType):
    checkouts = BaseDjangoConnectionField(
        Checkout,
        description="List of checkouts.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )

    @remote_permission_required(CheckoutPermissions.READ_CHECKOUTS)
    def resolve_checkouts(self, info, channel=None, **_kwargs):
        organization_id = info.context.remote_user.organization.metadata['orgId']
        return resolve_checkouts(channel, organization_id)

    @remote_permission_required(CheckoutPermissions.READ_CHECKOUTS)
    def resolve_checkout_lines(self, info, **_kwargs):
        return resolve_checkout_lines()

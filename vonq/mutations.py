import graphene

from saleor.graphql.core.mutations import BaseMutation
from saleor.graphql.core.types.common import AccountError

from vonq.plugins.auth0_plugin import ExternalAccessTokens


class ExternalObtainAccessTokens(BaseMutation):
    """Obtain external access tokens by a custom plugin."""

    id_token = graphene.String(description="The id token")
    access_token = graphene.String(description="The access token, required to authenticate with the remote API")
    refresh_token = graphene.String(
        description="The refresh token, required to re-generate external access token."
    )

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = graphene.JSONString(
            required=True,
            description="The data required by plugin to create authentication data.",
        )

    class Meta:
        description = "Obtain external access tokens for user by custom plugin."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        request = info.context
        plugin_id = data["plugin_id"]
        input_data = data["input"]
        manager = info.context.plugins
        access_tokens_response: ExternalAccessTokens = manager.external_obtain_access_tokens(
            plugin_id, input_data, request
        )
        info.context.refresh_token = access_tokens_response.refresh_token

        return cls(
            id_token=access_tokens_response.id_token,
            access_token=access_tokens_response.access_token,
            refresh_token=access_tokens_response.refresh_token,
        )

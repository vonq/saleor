from dataclasses import dataclass
from typing import Tuple, Optional

import jwt
import requests

from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import ValidationError
from saleor.plugins.base_plugin import (
    BasePlugin,
    ExternalAccessTokens as SaleorExternalAccessToken,
)
from vonq.jwt_utils import (
    verify_access_token,
    get_token_auth_header,
    get_user_from_token,
    create_user_from_token,
)

from django.conf import settings

User = get_user_model()


@dataclass
class ExternalAccessTokens:
    """
    A small class to override Saleor's, because
    we want to include an id token together
    with the access token.
    """

    id_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class Auth0Plugin(BasePlugin):
    """
    A VONQ plugin to allow the auth endpoints
    to work with our Auth0 tenant
    """

    PLUGIN_NAME = "Authenticate with Auth0"
    PLUGIN_ID = "vonq.authentication.auth0"
    PLUGIN_DESCRIPTION = "Description?"
    CONFIGURATION_PER_CHANNEL = False
    CONFIG_STRUCTURE = {}
    DEFAULT_ACTIVE = True

    def external_authentication_url(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:
        """
        Generate a URL to redirect the user to
        in order to complete the authorisation.
        """

        redirect_uri = data["redirect_uri"]

        return {
            "authorizeUrl": f"https://{settings.AUTH0_DOMAIN}/authorize?"
            f"response_type=code&"
            f"audience={settings.API_AUDIENCE}&"
            f"client_id={settings.AUTH0_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=openid+profile+email+offline_access&"
            f"state={data.get('state')}"
        }

    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        """
        Given a code grant, exchange it for access token, id token and
        refresh token. Each code can only be used ONCE.
        """

        resp = requests.post(
            url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "redirect_uri": data["redirect_uri"],
                "code": data["code"],
                "scope": "openid+profile+email+offline_access",
            },
        )

        if not resp.ok:
            raise ValidationError(f"Auth invalid! {resp.content}")

        payload = resp.json()

        return ExternalAccessTokens(
            access_token=payload["access_token"],
            id_token=payload["id_token"],
            refresh_token=payload["refresh_token"],
        )

    def external_refresh(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        """
        Get a new a access/id token given the refresh token.
        """

        refresh_token = data["refreshToken"]
        redirect_uri = data["redirect_uri"]
        resp = requests.post(
            url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            data={
                "grant_type": "authorization_code",
                f"audience={settings.API_AUDIENCE}&"
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": refresh_token,
            },
        )
        if not resp.ok:
            raise ValidationError(f"Auth invalid! {resp.content}")

        payload = resp.json()

        user = get_user_from_token(payload["id_token"])

        return SaleorExternalAccessToken(
            token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            csrf_token=data["state"],
            user=user,
        )

    def external_logout(self, data: dict, request: WSGIRequest, previous_value):
        return_to = data["returnTo"]
        return {
            "logoutUrl": f"https://{settings.AUTH0_DOMAIN}/v2/logout?client_id={settings.AUTH0_CLIENT_ID}&returnTo={return_to}"
        }

    def external_verify(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> Tuple[Optional["User"], dict]:
        """
        Verify a token against the WKS
        """

        token = data["token"]
        verify_access_token(token)
        user = get_user_from_token(token)
        user_payload = jwt.decode(token, options={"verify_signature": False})
        return user, user_payload

    def authenticate_user(
        self, request: WSGIRequest, previous_value
    ) -> Optional["User"]:
        """
        Authenticate a user after verifying the access token

        (This flow is optional and not strictly required when using the web app)
        """
        try:
            token = get_token_auth_header(request)
            verify_access_token(token)
        except ValidationError:
            return None

        try:
            user = get_user_from_token(token)
        except ValidationError:
            user = create_user_from_token(token)
        return user

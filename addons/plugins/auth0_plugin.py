from typing import Tuple, Optional

import jwt
import requests
from auth0.v3.exceptions import TokenValidationError
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import ValidationError
from saleor.plugins.base_plugin import BasePlugin, ExternalAccessTokens


from auth0.v3.authentication.token_verifier import (
    TokenVerifier,
    AsymmetricSignatureVerifier,
)

from django.conf import settings

User = get_user_model()

JWKS_URL = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
ISSUER = f"https://{settings.AUTH0_DOMAIN}/"


def verify_token(token):
    sv = AsymmetricSignatureVerifier(JWKS_URL)
    tv = TokenVerifier(
        signature_verifier=sv, issuer=ISSUER, audience=settings.AUTH0_CLIENT_ID
    )

    try:
        tv.verify(token)
    except TokenValidationError as e:
        raise ValidationError(f"Invalid token! {e}")


def get_user_from_token(token) -> Optional[User]:
    user_id_token = jwt.decode(token, options={"verify_signature": False})
    user_email = user_id_token["email"]
    email_verified = user_id_token["email_verified"]

    if not email_verified:
        raise ValidationError("User email hasn'\t been verified yet.")

    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        raise ValidationError(f"Unknown user {user_email}")

    return user


class Auth0Plugin(BasePlugin):
    PLUGIN_NAME = "Authenticate with Auth0"
    PLUGIN_ID = "vonq.authentication.auth0"
    PLUGIN_DESCRIPTION = ""
    CONFIG_STRUCTURE = None
    DEFAULT_ACTIVE = True

    def external_authentication_url(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:

        return {
            "authorizeUrl": f"https://{settings.AUTH0_DOMAIN}/authorize?"
            f"response_type=code&"
            f"client_id={settings.AUTH0_CLIENT_ID}&"
            f"redirect_uri=https://localhost:9000/callback&"
            f"scope=openid+profile+email+offline_access&"
            f"state={data.get('state')}"
        }

    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        resp = requests.post(
            url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "redirect_uri": "http://localhost:9000/callback",
                "code": data["code"],
            },
        )
        if not resp.ok:
            raise ValidationError(f"Auth invalid! {resp.content}")

        payload = resp.json()

        verify_token(payload["id_token"])

        user = get_user_from_token(payload["id_token"])

        return ExternalAccessTokens(
            token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            csrf_token=data["state"],
            user=user,
        )

    def external_refresh(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        pass

    def external_logout(self, data: dict, request: WSGIRequest, previous_value):
        pass

    def external_verify(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> Tuple[Optional["User"], dict]:
        token = data["token"]

        verify_token(token)
        user = get_user_from_token(token)

        return user, {}

    def authenticate_user(
        self, request: WSGIRequest, previous_value
    ) -> Optional["User"]:
        token = request.META.get("HTTP_AUTHORIZATION", " ").split(" ")[1]

        user = get_user_from_token(token)

        return user

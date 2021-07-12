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

        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        issuer = f"https://{settings.AUTH0_DOMAIN}/"

        sv = AsymmetricSignatureVerifier(jwks_url)
        tv = TokenVerifier(
            signature_verifier=sv, issuer=issuer, audience=settings.AUTH0_CLIENT_ID
        )

        try:
            tv.verify(payload["id_token"])
        except TokenValidationError as e:
            raise ValidationError(f"Invalid token! {e}")

        user_id_token = jwt.decode(
            payload["id_token"], options={"verify_signature": False}
        )
        user_email = user_id_token["email"]
        email_verified = user_id_token["email_verified"]

        if not email_verified:
            raise ValidationError("User email hasn'\t been verified yet.")

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            # TODO: implement a get_or_create!
            raise ValidationError(f"Unknown user {user_email}")

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
        pass

    def authenticate_user(
        self, request: WSGIRequest, previous_value
    ) -> Optional["User"]:
        pass

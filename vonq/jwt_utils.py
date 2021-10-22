from typing import Dict, List, Optional

import jwt
import requests
from authlib.jose import jwt as jose_jwt
from auth0.v3.exceptions import TokenValidationError
from auth0.v3.authentication.token_verifier import (
    TokenVerifier,
    AsymmetricSignatureVerifier,
)
from django.contrib.auth import get_user_model

from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest

from django.conf import settings

JWKS_URL = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
ISSUER = f"https://{settings.AUTH0_DOMAIN}/"
AUDIENCE = settings.API_AUDIENCE
ALGORITHMS = ["RS256"]

User = get_user_model()


class AuthError(Exception):
    pass


class Organization:
    id: str
    name: str
    metadata: Dict[str, str]

    def __init__(self, payload):
        self.id = payload["id"]
        self.metadata = payload["metadata"]
        self.name = payload["name"]


class RemoteUser:
    organization: Organization = None
    email: str
    roles: List[str]

    def __init__(self, payload):
        if payload.get("http://vonq.com/organization"):
            self.organization = Organization(payload["http://vonq.com/organization"])
        self.email = payload.get("http://vonq.com/userinfo")
        self.roles = payload[
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
        ]
        self.permissions = payload.get("permissions", [])


def verify_token(token):
    sv = AsymmetricSignatureVerifier(JWKS_URL)
    tv = TokenVerifier(
        signature_verifier=sv, issuer=ISSUER, audience=settings.AUTH0_CLIENT_ID
    )

    try:
        tv.verify(token)
    except TokenValidationError as e:
        raise ValidationError(f"Invalid token! {e}")


def verify_access_token(token):
    jsonurl = requests.get(JWKS_URL)
    jwks = jsonurl.json()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except:
        raise ValidationError(
            {"code": "invalid_header", "description": "INVALID HEADER"}, 401
        )
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
    if rsa_key:
        try:
            payload = jose_jwt.decode(token, rsa_key)
        except jwt.ExpiredSignatureError:
            raise ValidationError(
                {"code": "token_expired", "description": "token is expired"}, 401
            )
        except jwt.MissingRequiredClaimError:
            raise ValidationError(
                {
                    "code": "invalid_claims",
                    "description": "incorrect claims,"
                    "please check the audience and issuer",
                },
                401,
            )
        except Exception as e:
            raise ValidationError(
                {
                    "code": "invalid_header",
                    "description": "Unable to parse authentication" " token.",
                },
                401,
            )
        else:
            return payload

    raise ValidationError("No RSA key")


def get_token_auth_header(request: "WSGIRequest") -> str:
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization header is expected",
            },
            401,
        )

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with" " Bearer",
            },
            401,
        )
    elif len(parts) == 1:
        raise AuthError(
            {"code": "invalid_header", "description": "Token not found"}, 401
        )
    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must be" " Bearer token",
            },
            401,
        )

    token = parts[1]
    return token


def get_user_from_token(token) -> Optional["User"]:
    """
    #TODO: Do we really need this?
    """
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


def create_user_from_token(token) -> "User":
    """
    #TODO: Do we really need this? Rework if not
    """
    user_id_token = jwt.decode(token, options={"verify_signature": False})
    user_email = user_id_token["email"]
    # This is the auth0 organisation id
    user_org_id = user_id_token.get("org_id")
    # TODO: Improve naming for JMP-Id and Auth0-Id?
    user = User.objects.create(email=user_email, metadata={"org_id": user_org_id})
    return user

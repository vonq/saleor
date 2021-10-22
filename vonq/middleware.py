from django.core.exceptions import ValidationError

from vonq.jwt_utils import RemoteUser, get_token_auth_header, AuthError, \
    verify_access_token


def remote_user(get_response):
    """
    Add the remote user (i.e. the user exposed by the authentication token)
    to the context so that it can be passed around resolvers.
    """
    def _remote_user_middleware(request):
        try:
            token = get_token_auth_header(request)
        except AuthError:
            request.remote_user = None
            return get_response(request)

        try:
            access_token = verify_access_token(token)
        except ValidationError:
            request.remote_user = None
            return get_response(request)

        if access_token.get('owner') and access_token.get('owner') == 'saleor':
            request.remote_user = None
            return get_response(request)

        request.remote_user = RemoteUser(access_token)
        return get_response(request)

    return _remote_user_middleware

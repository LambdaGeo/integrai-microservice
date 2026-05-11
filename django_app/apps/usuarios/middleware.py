from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject

from apps.usuarios.backends import MicroserviceUser
from apps.usuarios.services import get_cached_microservice_data, refresh_cached_user
from microservices.clients import reset_request_auth_token, set_request_auth_token


def get_microservice_user(request):
    username = request.session.get('microservice_user_id')
    if not username:
        return AnonymousUser()

    cache_data = get_cached_microservice_data(username)
    user_data = cache_data.get('user_data')
    profile_data = cache_data.get('profile_data')
    token = cache_data.get('token') or request.session.get('microservice_token')

    if not user_data:
        refreshed_data = refresh_cached_user(username, token)
        if refreshed_data:
            user_data, profile_data = refreshed_data

    if not user_data:
        return AnonymousUser()

    return MicroserviceUser(
        username=str(username),
        user_data=user_data,
        profile_data=profile_data,
        token=token,
    )


class MicroserviceUserMiddleware:
    """
    Keeps request.user compatible with Django for users authenticated by
    the users-service. Must run after AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token_context = set_request_auth_token(request.session.get('microservice_token'))
        if request.session.get('microservice_authenticated'):
            request.user = SimpleLazyObject(lambda: get_microservice_user(request))
        try:
            return self.get_response(request)
        finally:
            reset_request_auth_token(token_context)

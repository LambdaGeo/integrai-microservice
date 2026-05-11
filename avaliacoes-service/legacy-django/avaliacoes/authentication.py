"""DRF authentication backed by the users-service bearer token."""
import json
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework import authentication, exceptions


class UsersServiceAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed("Invalid authorization header")

        auth_request = Request(
            f"{settings.USERS_SERVICE_URL}/api/v1/auth/me",
            method="GET",
            headers={"Authorization": header},
        )

        try:
            with urlopen(auth_request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 401:
                raise exceptions.AuthenticationFailed("Invalid access token") from exc
            raise exceptions.PermissionDenied("Access denied") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise exceptions.AuthenticationFailed("Users service unavailable") from exc

        user = SimpleNamespace(
            id=data.get("id"),
            username=data.get("username"),
            email=data.get("email"),
            is_active=data.get("is_active", False),
            is_staff=data.get("is_staff", False),
            is_superuser=data.get("is_superuser", False),
            is_authenticated=True,
        )
        return user, parts[1]

    def authenticate_header(self, request):
        return self.keyword

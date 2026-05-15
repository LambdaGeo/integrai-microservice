import base64
import json
import os
import time

import requests
from django.core.cache import cache
from django.core.files.storage import default_storage


CACHE_TIMEOUT = int(os.getenv('MICROSERVICE_CACHE_TIMEOUT', '1800'))
CACHE_KEY_USER = 'microservice_user_{}'
CACHE_KEY_PROFILE = 'microservice_profile_{}'
CACHE_KEY_TOKEN = 'microservice_token_{}'
TOKEN_EXPIRY_SKEW_SECONDS = 30
USERS_SERVICE_URL = os.getenv('USERS_SERVICE_URL', 'http://users-service:8000')


def normalize_username(username):
    return ''.join(filter(str.isdigit, str(username or '')))


def auth_headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def is_token_expired(token):
    if not token:
        return True

    try:
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except (IndexError, ValueError, TypeError, json.JSONDecodeError):
        return True

    expires_at = data.get('exp')
    if not expires_at:
        return True

    return expires_at <= time.time() + TOKEN_EXPIRY_SKEW_SECONDS


def response_error(response):
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    detail = payload.get('detail') if isinstance(payload, dict) else None
    return {
        'status_code': response.status_code,
        'detail': detail or response.text or 'Erro no microservice',
    }


def clear_microservice_session(request):
    request.session.pop('microservice_user_id', None)
    request.session.pop('microservice_token', None)
    request.session.pop('microservice_authenticated', None)
    request.session.pop('show_welcome', None)


def uploaded_file_to_profile_photo_url(uploaded_file):
    if not uploaded_file:
        return None

    path = default_storage.save(f'usuarios/fotos/{uploaded_file.name}', uploaded_file)
    return default_storage.url(path)


def cache_microservice_user(username, user_data, profile_data=None, token=None):
    cache.set(CACHE_KEY_USER.format(username), user_data, CACHE_TIMEOUT)
    cache.set(CACHE_KEY_PROFILE.format(username), profile_data, CACHE_TIMEOUT)
    if token:
        cache.set(CACHE_KEY_TOKEN.format(username), token, CACHE_TIMEOUT)


def get_cached_microservice_data(username):
    if not username:
        return {}

    user_data = cache.get(CACHE_KEY_USER.format(username))
    profile_data = cache.get(CACHE_KEY_PROFILE.format(username))
    token = cache.get(CACHE_KEY_TOKEN.format(username))

    if not profile_data and user_data:
        profile_data = user_data.get('profile')

    return {
        'username': username,
        'user_data': user_data,
        'profile_data': profile_data,
        'token': token,
    }


def get_cached_user_with_username(username):
    username = str(username)
    cache_data = get_cached_microservice_data(username)

    if not cache_data.get('user_data') and username.isdigit():
        padded_username = username.zfill(11)
        padded_cache_data = get_cached_microservice_data(padded_username)
        if padded_cache_data.get('user_data'):
            padded_cache_data['username'] = padded_username
            return padded_cache_data

    return cache_data


def login_user(username, password):
    username = normalize_username(username)
    if not username or not password:
        return None

    session = requests.Session()
    token_response = session.post(
        f'{USERS_SERVICE_URL}/api/v1/auth/token',
        data={'username': username, 'password': password},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    if token_response.status_code != 200:
        return None

    token_data = token_response.json()
    token = token_data.get('access_token')
    if not token:
        return None

    user_data, profile_data = fetch_user_bundle(username, token)
    if not user_data:
        return None

    cache_microservice_user(username, user_data, profile_data, token)

    return {
        'username': username,
        'user_data': user_data,
        'profile_data': profile_data,
        'token': token,
    }


def fetch_user_bundle(username, token):
    headers = auth_headers(token)

    user_response = requests.get(
        f'{USERS_SERVICE_URL}/api/v1/usuarios/username/{username}',
        headers=headers,
        timeout=5,
    )
    if user_response.status_code != 200:
        return None, None

    user_data = user_response.json()
    profile_data = None

    profile_response = requests.get(
        f'{USERS_SERVICE_URL}/api/v1/usuarios/profile/me',
        headers=headers,
        timeout=5,
    )
    if profile_response.status_code == 200:
        profile_data = profile_response.json()

    return user_data, profile_data


def refresh_cached_user(username, token):
    if not username or not token:
        return None

    try:
        user_data, profile_data = fetch_user_bundle(username, token)
    except requests.exceptions.RequestException:
        return None

    if not user_data:
        return None

    cache_microservice_user(username, user_data, profile_data, token)
    return user_data, profile_data


def update_user(user_id, token, user_data):
    if not token or not user_id or is_token_expired(token):
        return False, {'status_code': 401, 'detail': 'Sessão expirada'}

    try:
        response = requests.put(
            f'{USERS_SERVICE_URL}/api/v1/usuarios/{user_id}',
            json=user_data,
            headers=auth_headers(token),
            timeout=5,
        )
    except requests.exceptions.RequestException:
        return False, None

    if response.status_code == 200:
        return True, response.json()

    return False, response_error(response)


def save_profile(token, user_id, profile_data):
    if not token or not user_id or is_token_expired(token):
        return False, {'status_code': 401, 'detail': 'Sessão expirada'}

    headers = auth_headers(token)

    try:
        response = requests.put(
            f'{USERS_SERVICE_URL}/api/v1/usuarios/profile/me',
            json=profile_data,
            headers=headers,
            timeout=5,
        )

        if response.status_code == 200:
            return True, response.json()

        if response.status_code == 404:
            create_response = requests.post(
                f'{USERS_SERVICE_URL}/api/v1/usuarios/profile',
                json={**profile_data, 'user_id': user_id},
                headers=headers,
                timeout=5,
            )
            if create_response.status_code in (200, 201):
                return True, create_response.json()
            return False, response_error(create_response)
    except requests.exceptions.RequestException:
        return False, None

    return False, response_error(response)


def create_user_with_profile(user_data, profile_data):
    try:
        response = requests.post(
            f'{USERS_SERVICE_URL}/api/v1/usuarios',
            json=user_data,
            headers={'Content-Type': 'application/json'},
        )

        if response.status_code not in (200, 201):
            return False, response.json().get('detail', 'Erro ao criar usuario')

        created_user = response.json()
        token_data = login_user(user_data['username'], user_data['password'])

        if profile_data and token_data:
            save_profile(
                token=token_data['token'],
                user_id=created_user.get('id'),
                profile_data=profile_data,
            )

        return True, created_user
    except requests.exceptions.RequestException as exc:
        return False, str(exc)

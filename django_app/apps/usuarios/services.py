import os

import requests
from django.core.cache import cache


CACHE_TIMEOUT = 86400
CACHE_KEY_USER = 'microservice_user_{}'
CACHE_KEY_PROFILE = 'microservice_profile_{}'
CACHE_KEY_TOKEN = 'microservice_token_{}'
USERS_SERVICE_URL = os.getenv('USERS_SERVICE_URL', 'http://users-service:8000')


def normalize_username(username):
    return ''.join(filter(str.isdigit, str(username or '')))


def auth_headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


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
    if not token or not user_id:
        return False, None

    try:
        response = requests.put(
            f'{USERS_SERVICE_URL}/api/v1/usuarios/{user_id}',
            json=user_data,
            headers=auth_headers(token),
        )
    except requests.exceptions.RequestException:
        return False, None

    if response.status_code == 200:
        return True, response.json()

    return False, None


def save_profile(token, user_id, profile_data):
    if not token or not user_id:
        return False, None

    headers = auth_headers(token)

    try:
        response = requests.put(
            f'{USERS_SERVICE_URL}/api/v1/usuarios/profile/me',
            json=profile_data,
            headers=headers,
        )

        if response.status_code == 200:
            return True, response.json()

        if response.status_code == 404:
            create_response = requests.post(
                f'{USERS_SERVICE_URL}/api/v1/usuarios/profile',
                json={**profile_data, 'user_id': user_id},
                headers=headers,
            )
            if create_response.status_code in (200, 201):
                return True, create_response.json()
    except requests.exceptions.RequestException:
        return False, None

    return False, None


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

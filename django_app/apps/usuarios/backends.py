import hashlib
import requests
from django.contrib.auth.backends import BaseBackend

from apps.usuarios.services import get_cached_user_with_username, login_user


class MicroserviceUser:
    class _meta:
        class PkField:
            def value_to_string(self, obj):
                return str(obj.pk)

        pk = PkField()
        model_name = 'microserviceuser'
        app_label = 'usuarios'

    def __init__(self, username, user_data, profile_data=None, token=None):
        self.username = username
        self._user_data = user_data or {}
        self._profile_data = profile_data or self._user_data.get('profile')
        self._token = token
        self.pk = username
        self.id = self._user_data.get('id')
        self.password = None

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def email(self):
        return self._user_data.get('email') or f'{self.username}@integrai.ufma.br'

    @property
    def first_name(self):
        nome = self._profile_data.get('nome', '') if self._profile_data else ''
        return nome.split()[0] if nome else ''

    @property
    def last_name(self):
        nome = self._profile_data.get('nome', '') if self._profile_data else ''
        return ' '.join(nome.split()[1:]) if nome else ''

    @property
    def is_active(self):
        return self._user_data.get('is_active', True)

    @property
    def is_staff(self):
        return self._user_data.get('is_staff', False)

    @property
    def is_superuser(self):
        return self._user_data.get('is_superuser', False)

    @property
    def token(self):
        return self._token

    @property
    def profile(self):
        if self._profile_data:
            return MicroserviceProfile(self._profile_data)
        return None

    def __str__(self):
        return self.username

    def __eq__(self, other):
        if isinstance(other, MicroserviceUser):
            return self.username == other.username
        return False

    def __hash__(self):
        return hash(self.username)

    def get_username(self):
        return self.username

    def get_full_name(self):
        if self.profile and self.profile.nome:
            return self.profile.nome
        return self.username

    def get_short_name(self):
        return self.first_name

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return perm in self._user_data.get('permissions', [])

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True
        return self.is_active and self.is_staff

    def get_session_auth_hash(self):
        return hashlib.sha256(
            (self.username + (self._token or 'default_salt')).encode()
        ).hexdigest()

    def get_group_permissions(self, obj=None):
        return set()

    def get_all_permissions(self, obj=None):
        return set(self._user_data.get('permissions', []))

    def natural_key(self):
        return (self.username,)

    def delete(self):
        pass

    def save(self, *args, **kwargs):
        pass


class MicroserviceProfile:
    def __init__(self, profile_data):
        self._data = profile_data or {}

    @property
    def nome(self):
        return self._data.get('nome', '')

    @property
    def area(self):
        return self._data.get('area')

    @property
    def ubs(self):
        return self._data.get('ubs')

    @property
    def foto(self):
        return self._data.get('foto')

    @property
    def primeiro_nome(self):
        nome = self.nome
        return nome.split()[0] if nome else ''

    @property
    def UBS(self):
        return self.ubs

    @property
    def foto_url(self):
        return self.foto or None


class MicroserviceBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            auth_data = login_user(username, password)
        except requests.exceptions.RequestException as exc:
            print(f'Erro ao conectar com users-service: {exc}')
            return None

        if not auth_data:
            return None

        return MicroserviceUser(
            username=auth_data['username'],
            user_data=auth_data['user_data'],
            profile_data=auth_data['profile_data'],
            token=auth_data['token'],
        )

    def get_user(self, user_id):
        cache_data = get_cached_user_with_username(user_id)
        user_data = cache_data.get('user_data')

        if not user_data:
            return None

        return MicroserviceUser(
            username=cache_data.get('username'),
            user_data=user_data,
            profile_data=cache_data.get('profile_data'),
            token=cache_data.get('token'),
        )

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        if user_obj.profile:
            return True
        return user_obj.is_staff or user_obj.is_superuser

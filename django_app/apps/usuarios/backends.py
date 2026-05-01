"""
Backend de autenticação que se conecta ao microservice users-service.
Não persiste dados no banco local - usa cache Django.
"""
import os
import requests
from django.contrib.auth.backends import BaseBackend
from django.core.cache import cache


# ==================== Cache Keys ====================
CACHE_KEY_USER = 'microservice_user_{}'
CACHE_KEY_PROFILE = 'microservice_profile_{}'
CACHE_KEY_TOKEN = 'microservice_token_{}'


class MicroserviceUser:
    """
    Classe proxy que representa o usuário logado.
    Compatível com o sistema de sessão do Django 5.1.
    """
    
    _meta = None
    DoesNotExist = None
    
    def __init__(self, username, user_data, profile_data=None, token=None):
        self.username = username
        self._user_data = user_data or {}
        self._profile_data = profile_data
        self._token = token
        self._is_authenticated = True
        self._state = None
        
        pk_value = self._user_data.get('id')
        if pk_value is None:
            import hashlib
            pk_value = int(hashlib.md5(username.encode()).hexdigest()[:8], 16)
        
        self.pk = pk_value
        self.id = pk_value
    
    # ---------- Propriedades obrigatórias para o Django ----------
           
    @property
    def email(self):
        return self._user_data.get('email') or f"{self.username}@integrai.ufma.br"
    
    @property
    def first_name(self):
        nome = self._user_data.get('nome', '')
        return nome.split()[0] if nome else ''
    
    @property
    def last_name(self):
        nome = self._user_data.get('nome', '')
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
    def is_authenticated(self):
        return self._is_authenticated
    
    @property
    def is_anonymous(self):
        return False
    
    @property
    def token(self):
        return self._token
    
    @property
    def profile(self):
        if self._profile_data:
            return MicroserviceProfile(self._profile_data)
        return None
    
    # ---------- Métodos obrigatórios para o Django ----------
    
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
        return self._user_data.get('nome', self.username)
    
    def get_short_name(self):
        return self.first_name
    
    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return perm in self._user_data.get('permissions', [])
    
    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(p, obj) for p in perm_list)
    
    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True
        return self.is_active and self.is_staff
    
    def get_session_auth_hash(self):
        """
        O Django usa este hash para invalidar sessões após mudança de senha.
        Sem ele, auth.login() pode falhar.
        """
        import hashlib
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
    """
    Classe proxy para o perfil do agente.
    """
    
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
        nome = self._data.get('nome', '')
        return nome.split()[0] if nome else ''
    
    @property 
    def UBS(self):
        """Alias para compatibilidade com templates existentes"""
        return self._data.get('ubs')
    
    @property
    def foto_url(self):
        """Retorna URL da foto se disponível"""
        foto = self._data.get('foto')
        if foto:
            return foto
        return None


class MicroserviceBackend(BaseBackend):
    """
    Backend de autenticação que consulta o microservice users-service.
    Usa cache Django para armazenar dados do usuário.
    """
    
    def __init__(self):
        self.users_service_url = os.getenv(
            'USERS_SERVICE_URL', 
            'http://users-service:8000'
        )
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica o usuário através do microservice.
        """
        if not username or not password:
            return None
            
        # Limpar CPF (remover pontos e traços)
        username = ''.join(filter(str.isdigit, str(username)))
        
        try:
            # Chamar o endpoint de login do microservice
            response = self.session.post(
                f'{self.users_service_url}/api/v1/auth/token',
                data={
                    'username': username,
                    'password': password
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                # Usar dados do usuário retornados pelo login (evita segunda chamada)
                user_data = token_data.get('user')
                
                if access_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {access_token}'
                    })

                    # Buscar dados do usuário pelo username
                    user_response = self.session.get(
                        f'{self.users_service_url}/api/v1/usuarios/username/{username}'
                    )

                    if user_response.status_code != 200:
                        return None

                    user_data = user_response.json()

                    # Buscar perfil — opcional, não bloqueia o login
                    profile_data = None
                    try:
                        profile_response = self.session.get(
                            f'{self.users_service_url}/api/v1/usuarios/profile/me'
                        )
                        if profile_response.status_code == 200:
                            profile_data = profile_response.json()
                    except Exception:
                        pass

                    cache.set(CACHE_KEY_USER.format(username), user_data, 86400)
                    cache.set(CACHE_KEY_PROFILE.format(username), profile_data, 86400)
                    cache.set(CACHE_KEY_TOKEN.format(username), access_token, 86400)

                    return MicroserviceUser(
                        username=username,
                        user_data=user_data,
                        profile_data=profile_data,
                        token=access_token
                    )
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar com users-service: {e}")
            return None
    
    def get_user(self, user_id):
        """
        Recupera o usuário pelo cache.
        """
        # Buscar dados do cache
        user_data = cache.get(CACHE_KEY_USER.format(user_id))
        profile_data = cache.get(CACHE_KEY_PROFILE.format(user_id))
        token = cache.get(CACHE_KEY_TOKEN.format(user_id))
        
        if user_data:
            return MicroserviceUser(
                username=user_id,
                user_data=user_data,
                profile_data=profile_data,
                token=token
            )
        
        # Se não encontrou no cache, retorna None
        return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Verifica permissões do usuário.
        """
        if not user_obj.is_active:
            return False
        
        # Verificar se o usuário tem o perfil de agente
        if hasattr(user_obj, 'profile') and user_obj.profile:
            return True
        
        # Se é staff ou superuser, tem permissões
        if user_obj.is_staff or user_obj.is_superuser:
            return True
        
        return False
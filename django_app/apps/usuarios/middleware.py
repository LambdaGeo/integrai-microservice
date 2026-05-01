from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject


def get_microservice_user(request):
    """
    Retorna um objeto usuário compatível com Django,
    baseado nos dados da sessão e cache do microserviço.
    """
    user_id = request.session.get('microservice_user_id')
    
    if not user_id:
        return AnonymousUser()
    
    # Tenta recuperar do cache
    user_data = cache.get(f'microservice_user_{user_id}')
    token = cache.get(f'microservice_token_{user_id}')
    
    if not user_data:
        return AnonymousUser()
    
    # Cria um objeto usuário simples mas compatível
    user = type('MicroserviceUser', (), {})()
    user.pk = user_data.get('id', 0)
    user.id = user_data.get('id', 0)
    user.username = user_data.get('username', user_id)
    user.email = user_data.get('email', '')
    user.is_active = True
    user.is_authenticated = True
    user.is_anonymous = False
    user.is_staff = False
    user.is_superuser = False
    user.token = token
    
    # Métodos que o Django espera
    user.get_username = lambda: user.username
    user.get_full_name = lambda: user_data.get('nome', user.username)
    user.get_short_name = lambda: user_data.get('nome', '').split()[0] if user_data.get('nome') else user.username
    user.has_perm = lambda perm, obj=None: True
    user.has_perms = lambda perm_list, obj=None: True
    user.has_module_perms = lambda app_label: True
    
    # Atributos para o template
    user._profile_data = cache.get(f'microservice_profile_{user_id}')
    
    return user


class MicroserviceUserMiddleware:
    """
    Middleware que injeta um usuário compatível no request.
    Deve ser colocado DEPOIS do SessionMiddleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Usa SimpleLazyObject para não executar até que seja acessado
        request.user = SimpleLazyObject(lambda: get_microservice_user(request))
        
        response = self.get_response(request)
        return response
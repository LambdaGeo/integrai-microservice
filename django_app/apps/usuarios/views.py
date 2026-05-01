from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
import requests
import os

from apps.usuarios.forms import LoginForms, CadastroForms
from .forms import PerfilUpdateUserForm, PerfilUpdateProfileForm

from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth import login as auth_login, get_user

def microservice_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('microservice_authenticated'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# User = get_user_model()

# URL do microservice
USERS_SERVICE_URL = os.getenv('USERS_SERVICE_URL', 'http://users-service:8000')

# Cache keys (mesmo do backends.py)
CACHE_KEY_USER = 'microservice_user_{}'
CACHE_KEY_PROFILE = 'microservice_profile_{}'
CACHE_KEY_TOKEN = 'microservice_token_{}'


def _get_microservice_cache_data(username):
    """
    Recupera dados do usuário do cache Django.
    """
    if not username:
        return {}
    
    user_data = cache.get(CACHE_KEY_USER.format(username))
    profile_data = cache.get(CACHE_KEY_PROFILE.format(username))
    token = cache.get(CACHE_KEY_TOKEN.format(username))
    
    return {
        'user_data': user_data,
        'profile_data': profile_data,
        'token': token,
    }


def _get_user_from_cache(request):
    """
    Recupera o usuário do cache baseado na sessão.
    """
    username = request.session.get('microservice_user_id')
    if not username:
        return None
    
    cache_data = _get_microservice_cache_data(username)
    user_data = cache_data.get('user_data')
    profile_data = cache_data.get('profile_data')
    token = cache_data.get('token')
    
    if not user_data:
        return None
    
    # Criar objeto usuário simulado
    class SessionUser:
        def __init__(self, data, profile, token):
            self.username = data.get('username', '')
            self.email = data.get('email', '')
            self.first_name = data.get('nome', '').split()[0] if data.get('nome') else ''
            self.last_name = ' '.join(data.get('nome', '').split()[1:]) if data.get('nome') else ''
            self.is_active = data.get('is_active', True)
            self._profile = profile
            self._token = token
        
        @property
        def profile(self):
            if self._profile:
                class SessionProfile:
                    def __init__(self, p):
                        self.nome = p.get('nome', '')
                        self.area = p.get('area')
                        self.ubs = p.get('ubs')
                        self.foto = p.get('foto')
                        self.primeiro_nome = p.get('nome', '').split()[0] if p.get('nome') else ''
                return SessionProfile(self._profile)
            return None
    
    return SessionUser(user_data, profile_data, token)


def _update_profile_in_microservice(request, profile_data):
    """
    Atualiza o perfil do agente no microservice via API.
    """
    username = request.session.get('microservice_user_id')
    cache_data = _get_microservice_cache_data(username)
    token = cache_data.get('token')
    
    if not token:
        return False
    
    try:
        response = requests.put(
            f'{USERS_SERVICE_URL}/api/v1/usuarios/profile/me',
            json=profile_data,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao atualizar perfil no microservice: {e}")
        return False


@login_required
def meu_perfil(request):
    """
    Exibe o perfil do usuário logado.
    Os dados são obtidos do cache Django.
    """
    session_user = _get_user_from_cache(request)
    
    if not session_user:
        messages.error(request, "Sessão expirada. Faça login novamente.")
        return redirect('login')
    
    return render(request, "usuarios/meu_perfil.html", {
        "user": session_user,
        "profile": session_user.profile,
    })


@login_required
def editar_perfil(request):
    """
    Edita o perfil do usuário logado.
    Os dados são sincronizados com o microservice.
    """
    username = request.session.get('microservice_user_id')
    session_data = _get_microservice_cache_data(username)
    user_data = session_data.get('user_data', {})
    profile_data = session_data.get('profile_data', {})
    
    if request.method == "POST":
        # Atualizar dados do usuário
        user_form_data = {
            'email': request.POST.get('email'),
        }
        
        # Atualizar perfil no microservice
        profile_form_data = {
            'nome': request.POST.get('nome'),
            'area': request.POST.get('area'),
            'ubs': request.POST.get('ubs'),
        }
        
        # Chamar API do microservice
        success = _update_profile_in_microservice(request, profile_form_data)
        
        if success:
            # Atualizar sessão local
            request.session['microservice_user_data'].update(user_form_data)
            if profile_data:
                request.session['microservice_profile_data'].update(profile_form_data)
            
            messages.success(request, "Perfil atualizado com sucesso!")
        else:
            messages.error(request, "Erro ao atualizar perfil no microservice.")
        
        return redirect("editar_perfil")
    
    # Preparar dados para o formulário
    class SessionUser:
        def __init__(self, data, profile):
            self.username = data.get('username', '')
            self.email = data.get('email', '')
            self.first_name = data.get('nome', '').split()[0] if data.get('nome') else ''
            self.last_name = ' '.join(data.get('nome', '').split()[1:]) if data.get('nome') else ''
            self.is_active = data.get('is_active', True)
            self._profile = profile
        
        @property
        def profile(self):
            if self._profile:
                class SessionProfile:
                    def __init__(self, p):
                        self.nome = p.get('nome', '')
                        self.area = p.get('area')
                        self.ubs = p.get('ubs')
                        self.foto = p.get('foto')
                return SessionProfile(self._profile)
            return None
    
    session_user = SessionUser(user_data, profile_data)
    
    # Criar forms vazios para compatibilidade (os dados são preenchidos no template)
    form_user = PerfilUpdateUserForm(instance=session_user)
    form_profile = PerfilUpdateProfileForm(instance=session_user.profile if session_user.profile else None)

    return render(request, "usuarios/editar_perfil.html", {
        "form_user": form_user,
        "form_profile": form_profile,
    })
#antigo forma de login
# def login(request):
#     form = LoginForms() # Cria um formulário vazio

#     if request.method == 'POST':
#         form = LoginForms(request.POST) # Preenche com dados

#         if form.is_valid(): # O form.clean() JÁ autenticou o usuário
            
#             # 1. Pegamos o usuário que o próprio formulário autenticou
#             usuario = form.get_user() 
            
#             # 2. Fazemos o login
#             auth.login(request, usuario)

#                 # Limpa todas as mensagens antigas que sobraram na sessão
#             storage = messages.get_messages(request)
#             storage.used = True

#             messages.success(request, f'{usuario.username} logado com sucesso!')
#             request.session['show_welcome'] = True
#             return redirect('index')
        
#         # 3. Se o form for inválido (senha errada, campos em branco),
#         # o 'return render' abaixo mostrará os erros automaticamente.
#         # Você não precisa de um 'else' aqui.

#     return render(request, 'usuarios/login.html', {'form': form})

def login(request):
    form = LoginForms()

    if request.method == 'POST':
        form = LoginForms(request.POST)

        if form.is_valid():
            usuario = form.get_user()

            # 1. PRIMEIRO salva os dados na sessão
            request.session['microservice_user_id'] = usuario.username
            request.session['microservice_token'] = usuario.token
            request.session['microservice_authenticated'] = True
            request.session['show_welcome'] = True
            
            # 2. DEPOIS salva no cache
            cache.set(f'microservice_user_{usuario.username}', usuario._user_data, 86400)
            cache.set(f'microservice_token_{usuario.username}', usuario.token, 86400)

            # 3. NÃO use cycle_key() - isso estava matando a sessão!
            
            # 4. Força salvar a sessão antes do redirect
            request.session.save()
            
            # 5. Mensagem
            storage = messages.get_messages(request)
            storage.used = True
            messages.success(request, 'Login realizado com sucesso!')

            print("🔍 Redirecionando para index...")
            return redirect('index')

    return render(request, 'usuarios/login.html', {'form': form})

def _create_user_in_microservice(user_data, profile_data):
    try:
        # 1. Criar usuário
        response = requests.post(
            f'{USERS_SERVICE_URL}/api/v1/usuarios',
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code not in (200, 201):
            return False, response.json().get('detail', 'Erro ao criar usuário')
        
        usuario_criado = response.json()
        
        # 2. Fazer login para obter token
        token_response = requests.post(
            f'{USERS_SERVICE_URL}/api/v1/auth/token',
            data={
                'username': user_data['username'],
                'password': user_data['password']
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if token_response.status_code != 200:
            # Usuário criado mas sem perfil — ainda é sucesso parcial
            return True, usuario_criado
        
        token = token_response.json().get('access_token')
        
        # 3. Criar perfil com o token
        if profile_data and token:
            requests.post(
                f'{USERS_SERVICE_URL}/api/v1/usuarios/profile',
                json=profile_data,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
        
        return True, usuario_criado
        
    except Exception as e:
        return False, str(e)


def cadastro(request):
    """
    Cadastra novo usuário via microservice.
    """
    form = CadastroForms()

    if request.method == 'POST':
        form = CadastroForms(request.POST, request.FILES)

        if form.is_valid():
            # Preparar dados para o microservice
            username = ''.join(filter(str.isdigit, str(form.cleaned_data['nome_cadastro'])))
            
            user_data = {
                'username': username,
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['senha_1'],
            }
            
            profile_data = {
                'nome': form.cleaned_data['nome_completo'],
                'area': form.cleaned_data.get('area'),
                'ubs': form.cleaned_data.get('ubs'),
            }
            
            # Criar no microservice
            success, result = _create_user_in_microservice(user_data, profile_data)
            
            if success:
                messages.success(request, 'Cadastro efetuado com sucesso! Faça login.')
                return redirect('login')
            else:
                messages.error(request, f'Erro ao cadastrar: {result}')

    # Se o método for GET ou o form for inválido,
    # renderiza a página com o formulário (e seus erros, se houver).
    return render(request, 'usuarios/cadastro.html', {'form': form})


def logout(request):
    # Limpar dados da sessão do microservice
    request.session.pop('microservice_user_id', None)
    request.session.pop('microservice_token', None)
    request.session.pop('microservice_user_data', None)
    request.session.pop('microservice_profile_data', None)
    request.session.pop('show_welcome', None)
    
    auth.logout(request)
    messages.success(request, "Logout efetuado com sucesso!")
    return redirect('login')
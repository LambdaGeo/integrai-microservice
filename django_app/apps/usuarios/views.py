from django.contrib import auth, messages
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render

from apps.usuarios.decorator import login_required_message
from apps.usuarios.forms import (
    CadastroForms,
    LoginForms,
    PerfilUpdateProfileForm,
    PerfilUpdateUserForm,
)
from apps.usuarios.services import (
    cache_microservice_user,
    create_user_with_profile,
    save_profile,
    update_user,
)


@login_required_message
def meu_perfil(request):
    return render(request, 'usuarios/meu_perfil.html', {
        'user': request.user,
        'profile': request.user.profile,
    })


@login_required_message
def editar_perfil(request):
    profile = request.user.profile

    if request.method == 'POST':
        form_user = PerfilUpdateUserForm(request.POST)
        form_profile = PerfilUpdateProfileForm(request.POST, request.FILES)

        if form_user.is_valid() and form_profile.is_valid():
            token = request.user.token or request.session.get('microservice_token')
            username = request.session.get('microservice_user_id')

            user_success, updated_user_data = update_user(
                user_id=request.user.id,
                token=token,
                user_data={'email': form_user.cleaned_data['email']},
            )
            profile_success, updated_profile_data = save_profile(
                token=token,
                user_id=request.user.id,
                profile_data={
                    'nome': form_profile.cleaned_data['nome'],
                    'area': form_profile.cleaned_data.get('area'),
                    'ubs': form_profile.cleaned_data.get('ubs'),
                },
            )

            if user_success and profile_success:
                updated_user_data['profile'] = updated_profile_data
                cache_microservice_user(
                    username=username,
                    user_data=updated_user_data,
                    profile_data=updated_profile_data,
                    token=token,
                )
                messages.success(request, 'Perfil atualizado com sucesso!')
                return redirect('editar_perfil')

            messages.error(request, 'Erro ao atualizar perfil no microservice.')
    else:
        form_user = PerfilUpdateUserForm(initial={
            'email': request.user.email,
        })
        form_profile = PerfilUpdateProfileForm(initial={
            'nome': profile.nome if profile else '',
            'area': profile.area if profile else '',
            'ubs': profile.ubs if profile else '',
        })

    return render(request, 'usuarios/editar_perfil.html', {
        'form_user': form_user,
        'form_profile': form_profile,
    })


def login(request):
    form = LoginForms()

    if request.method == 'POST':
        form = LoginForms(request.POST)
        if form.is_valid():
            usuario = form.get_user()

            cache_microservice_user(
                username=usuario.username,
                user_data=usuario._user_data,
                profile_data=usuario._profile_data,
                token=usuario.token,
            )

            auth_login(request, usuario)
            request.session['microservice_user_id'] = usuario.username
            request.session['microservice_token'] = usuario.token
            request.session['microservice_authenticated'] = True
            request.session['show_welcome'] = True
            request.session.save()

            messages.success(request, 'Login realizado com sucesso!')
            return redirect('index')

    return render(request, 'usuarios/login.html', {'form': form})


def cadastro(request):
    form = CadastroForms()

    if request.method == 'POST':
        form = CadastroForms(request.POST, request.FILES)
        if form.is_valid():
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

            success, result = create_user_with_profile(user_data, profile_data)

            if success:
                messages.success(request, 'Cadastro efetuado com sucesso! Faça login.')
                return redirect('login')

            messages.error(request, f'Erro ao cadastrar: {result}')

    return render(request, 'usuarios/cadastro.html', {'form': form})


def logout(request):
    request.session.pop('microservice_user_id', None)
    request.session.pop('microservice_token', None)
    request.session.pop('microservice_authenticated', None)
    request.session.pop('show_welcome', None)

    auth.logout(request)
    messages.success(request, 'Logout efetuado com sucesso!')
    return redirect('login')

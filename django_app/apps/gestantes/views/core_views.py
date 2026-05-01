# ======================================
# Importações principais do Django
# ======================================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# ======================================
# Importações de apps locais
# ======================================
from apps.usuarios.decorator import login_required_message


# =========================================================
# Função: Home
# Página inicial pública ou redireciona usuário logado
# =========================================================
def home(request):
    # Verifica sessão do microservice
    if request.session.get('microservice_authenticated'):
        return redirect('index')
    return render(request, 'gestantes/core/home.html')


# =========================================================
# Função: Chat
# Página de conversa (template estático)
# =========================================================
@login_required_message
def chat(request):
    return render(request, 'gestantes/core/chat.html')


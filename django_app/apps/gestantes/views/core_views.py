# ======================================
# Importações principais do Django
# ======================================
from django.shortcuts import render, redirect

# ======================================
# Importações de apps locais
# ======================================
from apps.usuarios.decorator import login_required_message


# =========================================================
# Função: Home
# Página inicial pública ou redireciona usuário logado
# =========================================================
def home(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'gestantes/core/home.html')


# =========================================================
# Função: Chat
# Página de conversa (template estático)
# =========================================================
@login_required_message
def chat(request):
    return render(request, 'gestantes/core/chat.html')

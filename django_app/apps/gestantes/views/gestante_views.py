# ======================================
# Importações principais do Django
# ======================================
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

# ======================================
# Importações de apps locais
# ======================================
from apps.gestantes.models import Gestante, ConsentimentoGestante
from apps.gestantes.forms import GestanteForms
from apps.usuarios.decorator import login_required_message
# =========================================================
# Função: Revogar Consentimento
# Cria um registro de consentimento com status "revogado"
# =========================================================
@login_required_message
def revogar_consentimento(request, gestante_id):
    gestante = get_object_or_404(Gestante, id=gestante_id)

    if request.method == 'POST':
        ConsentimentoGestante.objects.create(
            gestante=gestante,
            usuario_id=request.user.id,
            status='revogado'
        )
    return redirect('index')  # Redireciona para a página principal


# =========================================================
# Função: Index
# Lista gestantes do usuário logado e mostra cards
# =========================================================
def index(request):
    if not request.user.is_authenticated:
        return redirect('home')

    show_welcome = request.session.pop('show_welcome', False)
    gestantes = Gestante.objects.filter(usuario_id=request.user.id).order_by("-data_cadastro")
    gestantes = [g for g in gestantes if g.consentimento_ativo]

    return render(request, 'gestantes/crud/painel.html', {
        "cards": gestantes,
        "show_welcome": show_welcome,
    })

# =========================================================
# Função: Buscar Gestantes
# Filtra gestantes pelo nome
# =========================================================
@login_required_message
def buscar(request):
    gestantes = Gestante.objects.filter(usuario_id=request.user.id).order_by("data_cadastro")

    if "buscar" in request.GET:
        nome_a_buscar = request.GET['buscar']
        if nome_a_buscar:
            gestantes = gestantes.filter(nome__icontains=nome_a_buscar)

    return render(request, 'gestantes/crud/painel.html', {"cards": gestantes})


# =========================================================
# Função: Nova Gestante
# Cria gestante e registra consentimento inicial
# =========================================================
@login_required_message
def nova_gestante(request):
    form = GestanteForms()

    if request.method == 'POST':
        form = GestanteForms(request.POST, request.FILES)
        consentimento_aceito = request.POST.get('consentimento_aceito') == 'true'

        if not consentimento_aceito:
            messages.error(request, 'Você precisa aceitar o consentimento para registrar a gestante.')
            # Retorna o form para não perder dados digitados
            return render(request, 'gestantes/crud/acolher.html', {'form': form, 'consentimento_erro': True})

        if form.is_valid():
            gestante = form.save(commit=False)
            gestante.usuario_id = request.user.id
            gestante.save()

            ConsentimentoGestante.objects.create(
                gestante=gestante,
                usuario_id=request.user.id,
                status='aceito'
            )

            messages.success(request, 'Nova gestante cadastrada!')
            return redirect('questionario', gestante_id=gestante.id)

    return render(request, 'gestantes/crud/acolher.html', {'form': form})


# =========================================================
# Função: Editar Gestante
# Permite atualização de dados com consentimento ativo
# =========================================================
@login_required_message
def editar_gestante(request, gestante_id):
    gestante = get_object_or_404(Gestante, id=gestante_id) # Você já busca a gestante aqui

    if not gestante.consentimento_ativo:
        messages.error(request, "Não é possível editar uma gestante com consentimento revogado.")
        return redirect('index')

    form = GestanteForms(instance=gestante)

    if request.method == 'POST':
        form = GestanteForms(request.POST, request.FILES, instance=gestante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gestante editada com sucesso')
            return redirect('index')

    # MUDANÇA AQUI: Passe o objeto 'gestante' completo para o template
    context = {
        'form': form,
        'gestante_id': gestante_id, # Pode manter, mas 'gestante' é melhor
        'gestante': gestante       # <-- ADICIONE ISSO
    }
    # DE: return render(request, 'gestantes/editar.html', {'form': form, 'gestante_id': gestante_id})
    return render(request, 'gestantes/crud/editar.html', context) # Use o novo caminho do template

# =========================================================
# Função: Deletar Gestante
# Remove registro de gestante
# =========================================================
@login_required_message
def deletar_gestante(request, gestante_id):
    gestante = get_object_or_404(Gestante, id=gestante_id) # Use get_object_or_404
    gestante.delete()
    messages.success(request, 'Deleção feita com sucesso!')
    return redirect('index')

# ======================================
# Importações principais do Django
# ======================================
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from apps.usuarios.decorator import login_required_message

# ======================================
# Importações de apps locais
# ======================================
from apps.gestantes.models import Gestante, Avaliacao
from apps.gestantes.forms import AvaliacaoForm
from apps.gestantes import services # Importa a camada de serviço
from django.http import JsonResponse

from apps.gestantes.services import predicao_api_esta_online

from apps.gestantes.services import gerar_token

# =========================================================
# Função: Detalhes da Gestante
# Mostra informações e evolução de riscos
# =========================================================
@login_required_message
def gestante(request, gestante_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Usuário não logado')
        return redirect('login')

    gestante = get_object_or_404(Gestante, pk=gestante_id)
    avaliacoes = Avaliacao.objects.filter(gestante=gestante).order_by('-data_aplicacao')[:2]

    ultima_avaliacao = avaliacoes[0] if len(avaliacoes) > 0 else None
    penultima_avaliacao = avaliacoes[1] if len(avaliacoes) > 1 else None

    # Chama a camada de serviço para fazer o trabalho sujo
    riscos, evolucao_riscos_dict = services.obter_dados_risco(
        ultima_avaliacao, 
        penultima_avaliacao
    )

    nome_usuario = request.user.profile.primeiro_nome 
    
    token = gerar_token(nome_usuario)

    context = {
        "gestante": gestante,
        "ultima_avaliacao": ultima_avaliacao,
        "penultima_avaliacao": penultima_avaliacao,
        "riscos": riscos,
        "evolucao_riscos_dict": evolucao_riscos_dict,
        "token": token
    }

    return render(request, 'gestantes/avaliacao/detalhe.html', context)


# =========================================================
# Função: Avaliação
# Cria nova avaliação associada à gestante
# =========================================================
@login_required_message
def avaliacao(request, gestante_id):
    gestante = get_object_or_404(Gestante, id=gestante_id)

    if not gestante.consentimento_ativo:
        messages.error(request, "Não é possível avaliar uma gestante com consentimento revogado.")
        return redirect('index')

    # 🚨 Checa API antes de mostrar o formulário
    if not predicao_api_esta_online():
        messages.error(request, "O serviço de predição está indisponível no momento. Tente mais tarde")
        return redirect('gestante', gestante_id)
    
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            questionario = form.save(gestante=gestante)
            messages.success(request, "Avaliação registrada com sucesso.")
            return redirect(reverse('gestante', args=[gestante_id]))
    else:
        form = AvaliacaoForm()

    return render(request, 'gestantes/avaliacao/questionario.html', {'form': form, 'gestante': gestante})

@login_required_message
def avaliacao_status(request, gestante_id):
    tipo = request.GET.get("tipo", "sintese")  # llm como padrão

    ultima_avaliacao = (
        Avaliacao.objects
        .filter(gestante_id=gestante_id)
        .order_by('-data_aplicacao')
        .first()
    )

    if not ultima_avaliacao:
        return JsonResponse({"status": "NONE", "status_text": "Sem avaliações"})

    # Mapeia o atributo correto
    atributo_status = {
        "sintese": "status_processamento_llm",
        "pilulas": "status_processamento_pills",
    }.get(tipo)

    # Em caso de tipo inválido:
    if atributo_status is None:
        return JsonResponse({"status": "INVALID", "status_text": "Tipo desconhecido"})

    status = getattr(ultima_avaliacao, atributo_status)

    status_texts = {
        "PENDING": "Em breve, a MarIA irá preparar tudo para você.",
        "PROCESSING": "A MarIA está processando as informações da gestante.",
        "COMPLETED": "A MarIA já analisou os resultados!",
        "FAILED": "A MarIA teve uma dificuldade ao processar a avaliação. Tente novamente daqui a pouco."
    }

    return JsonResponse({
        "status": status,
        "status_text": status_texts.get(status, "")
    })





def api_predicao_status(request):
    return JsonResponse({"online": predicao_api_esta_online()})

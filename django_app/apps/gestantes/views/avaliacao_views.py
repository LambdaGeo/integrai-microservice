# ======================================
# Importações principais do Django
# ======================================
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from apps.usuarios.decorator import login_required_message

# ======================================
# Importações de apps locais
# ======================================
from apps.gestantes import services
from django.http import JsonResponse

from apps.gestantes.services import predicao_api_esta_online
from apps.gestantes.services import gerar_token
from apps.gestantes.views.gestante_views import _get_gestante_fhir
from microservices.clients import avaliacoes_client


class AvaliacaoForm(forms.Form):
    corrimento_vaginal = forms.BooleanField(required=False, label="Corrimento vaginal frequente?")
    periodontite_carie = forms.BooleanField(required=False, label="Cárie e/ou periodontite?")
    hipertensao_gestacao = forms.BooleanField(required=False, label="Hipertensão na gestação?")
    diabetes_gestacao = forms.BooleanField(required=False, label="Diabetes na gestação?")
    estresse_gestacao = forms.BooleanField(required=False, label="Estresse durante gestação?")
    historico_familiar_alergia = forms.BooleanField(required=False, label="Histórico familiar de alergia?")
    consumo_bebidas_adocadas = forms.BooleanField(required=False, label="Consumo de bebidas adoçadas?")
    consumo_ultraprocessados = forms.BooleanField(required=False, label="Consumo de ultraprocessados?")
    consumo_alcool = forms.BooleanField(required=False, label="Consumo de álcool?")
    fumante_gestacao = forms.BooleanField(required=False, label="Fumante?")


def _listar_avaliacoes(gestante_id):
    avaliacoes = avaliacoes_client.list_avaliacoes(params={"gestante": gestante_id})
    return sorted(
        avaliacoes,
        key=lambda avaliacao: avaliacao.get("data_aplicacao") or "",
        reverse=True,
    )


# =========================================================
# Função: Detalhes da Gestante
# Mostra informações e evolução de riscos
# =========================================================
@login_required_message
def gestante(request, gestante_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Usuário não logado')
        return redirect('login')

    gestante = _get_gestante_fhir(gestante_id)
    if not gestante:
        messages.error(request, "Gestante não encontrada.")
        return redirect('index')

    avaliacoes = _listar_avaliacoes(gestante_id)[:2]

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
    gestante = _get_gestante_fhir(gestante_id)
    if not gestante:
        messages.error(request, "Gestante não encontrada.")
        return redirect('index')

    if not gestante.get('consentimento_ativo', True):
        messages.error(request, "Não é possível avaliar uma gestante com consentimento revogado.")
        return redirect('index')

    # 🚨 Checa API antes de mostrar o formulário
    if not predicao_api_esta_online():
        messages.error(request, "O serviço de predição está indisponível no momento. Tente mais tarde")
        return redirect('gestante', gestante_id)
    
    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            payload = {"gestante": gestante_id, **form.cleaned_data}
            questionario = avaliacoes_client.create_avaliacao(payload)
            if questionario:
                messages.success(request, "Avaliação registrada com sucesso.")
                return redirect(reverse('gestante', args=[gestante_id]))
            messages.error(request, "Erro ao registrar avaliação no avaliacoes-service.")
    else:
        form = AvaliacaoForm()

    return render(request, 'gestantes/avaliacao/questionario.html', {'form': form, 'gestante': gestante})


@login_required_message
def avaliacao_status(request, gestante_id):
    tipo = request.GET.get("tipo", "sintese")

    ultima_avaliacao = next(iter(_listar_avaliacoes(gestante_id)), None)

    if not ultima_avaliacao:
        return JsonResponse({"status": "NONE", "status_text": "Sem avaliações"})

    atributo_status = {
        "sintese": "status_processamento_llm",
        "pilulas": "status_processamento_pills",
    }.get(tipo)

    if atributo_status is None:
        return JsonResponse({"status": "INVALID", "status_text": "Tipo desconhecido"})

    status = ultima_avaliacao.get(atributo_status)

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

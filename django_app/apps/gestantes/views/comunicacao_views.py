# ======================================
# Importações principais do Django
# ======================================
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

import hmac
import hashlib
from django.conf import settings

# ======================================
# Importações de apps locais
# ======================================
from apps.gestantes.models import Gestante, Avaliacao, Pilula

from apps.gestantes.literals import NOMES_FATORES
from apps.gestantes.services import gerar_token

import time


def resumo_riscos_api(request, gestante_id):
    gestante = get_object_or_404(Gestante, id=gestante_id)
    avaliacao = Avaliacao.objects.filter(gestante=gestante).order_by('-data_aplicacao').first()

    return JsonResponse({
        "sintese": avaliacao.llm_sintese if avaliacao and avaliacao.llm_sintese else ""
    })

# =========================================================
# Função: Comunica
# Mostra pílulas de comunicação
# =========================================================
def comunica(request, gestante_id):
    # Busca a gestante
    gestante = get_object_or_404(Gestante, pk=gestante_id)

    # Opcional: pega a avaliação mais recente da gestante
    avaliacao = Avaliacao.objects.filter(gestante=gestante).order_by('-data_aplicacao').first()



    top_fatores = avaliacao.top_fatores if avaliacao else []

    fatores_traduzidos = [NOMES_FATORES.get(f, f) for f in top_fatores]


    

    nome_usuario = request.user.profile.primeiro_nome 
    
    token = gerar_token(nome_usuario)
    

    return render(request, "gestantes/comunicacao/comunica.html", {
        "gestante": gestante,
        "sintese": avaliacao.llm_sintese if avaliacao else "",
        "top_fatores": ", ".join(fatores_traduzidos),
        "token": token
    })


def pilulas(request, gestante_id):
    # Busca a gestante
    gestante = get_object_or_404(Gestante, pk=gestante_id)

    # Opcional: pega a avaliação mais recente da gestante
    avaliacao = Avaliacao.objects.filter(gestante=gestante).order_by('-data_aplicacao').first()

    # Busca todas as pílulas da avaliação
    pilulas_qs = Pilula.objects.filter(avaliacao=avaliacao).order_by('semana_num', 'data_geracao')

    # Constrói a lista de pílulas com atributo 'disponivel'
    agora = timezone.now()
    pilulas = []
    for p in pilulas_qs:
        pilulas.append({
            "id": p.id,
            "titulo": p.titulo,
            "conteudo": p.conteudo,
            "status": p.status,
            "semana_num": p.semana_num,
            "semana_ord": p.semana_ord,
            "data_range": p.periodo_envio,
            "data_inicio_envio": p.data_inicio_envio,
           # "disponivel": p.data_inicio_envio <= agora if p.data_inicio_envio else False
            "disponivel": True
        })


    return render(request, "gestantes/comunicacao/pilulas.html", {
        "gestante": gestante,
        "pilulas": pilulas,
    })


# =========================================================
# Função: Atualizar Status da Pílula
# Marca pílula como enviada/pendente
# =========================================================
from django.http import JsonResponse

@login_required
def atualizar_status_pilula(request, pilula_id):
    pilula = get_object_or_404(Pilula, pk=pilula_id)

    if request.method == 'POST':
        enviada = 'enviada' if 'enviada' in request.POST else 'pendente'
        pilula.status = enviada
        pilula.save()

        # Se for AJAX → devolve JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'status': pilula.status
            })

    # Se não for AJAX → redirect normal
    return redirect(request.META.get('HTTP_REFERER', 'home'))

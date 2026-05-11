import json
from django.utils.text import slugify

import requests
import logging
from django.conf import settings
# DESABILITADO: Modelos migrados para microservice gestantes-service
# from apps.gestantes.models import Avaliacao, Pilula

from apps.gestantes.literals import PILLS_PADRAO
from apps.gestantes.literals import EXPLICACAO_SEM_RISCO

import re
import random

# Configura um logger para este módulo
logger = logging.getLogger(__name__)

from apps.gestantes.literals import NOMES_FATORES


import jwt
import datetime

def gerar_token(usuario_nome: str):
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

    payload = {
        "usuario": usuario_nome,
        "exp": exp
    }

    token = jwt.encode(payload, settings.CHAINLIT_SECRET, algorithm="HS256")
    return token


def predicao_api_esta_online() -> bool:
    """Verifica se a API de predição está respondendo."""
    try:
        response = requests.get(settings.R_API_HEALTHCHECK_URL, timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _classificar_risco(prob):
    """Função auxiliar privada para classificar risco."""
    if prob >= 70:
        return "🚨", "text-danger"
    elif prob >= 31:
        return "⚠️", "text-warning"
    else:
        return "✅", "text-success"

def _processar_resultado_avaliacao(resultado_json):
    """Converte o JSON de resultado em um dicionário Python."""
    if isinstance(resultado_json, str):
        try:
            return json.loads(resultado_json)
        except json.JSONDecodeError:
            return {}
    return resultado_json or {}

def obter_dados_risco(ultima_avaliacao, penultima_avaliacao):
    resultado_atual = _processar_resultado_avaliacao(
        (ultima_avaliacao or {}).get("resultado_integralidade_saude")
    )
    resultado_anterior = _processar_resultado_avaliacao(
        (penultima_avaliacao or {}).get("resultado_integralidade_saude")
    )

    riscos = _montar_riscos(resultado_atual)
    evolucao = _montar_evolucao(resultado_atual, resultado_anterior)
    return riscos, evolucao


def _montar_riscos(resultado):
    if not resultado or resultado.get("prob_integralidade") is None:
        return {}

    fatores = [
        NOMES_FATORES.get(fator, fator)
        for fator in resultado.get("top_fatores", []) or []
    ]

    return {
        "integralidade": {
            "valor": round(float(resultado["prob_integralidade"]), 1),
            "fatores": fatores,
        },
        "outros": [
            {"nome": "Asma", "valor": round(float(resultado.get("prob_asma", 0)), 1)},
            {"nome": "Obesidade", "valor": round(float(resultado.get("prob_obesidade", 0)), 1)},
            {"nome": "Cárie", "valor": round(float(resultado.get("prob_carie", 0)), 1)},
            {"nome": "Alergia", "valor": round(float(resultado.get("prob_alergia", 0)), 1)},
        ],
    }


def _montar_evolucao(resultado_atual, resultado_anterior):
    if not resultado_atual or not resultado_anterior:
        return {}
    atual = resultado_atual.get("prob_integralidade")
    anterior = resultado_anterior.get("prob_integralidade")
    if atual is None or anterior is None:
        return {}
    return {
        "integralidade": {
            "delta": round(float(atual) - float(anterior), 1),
            "valor_atual": round(float(atual), 1),
            "valor_anterior": round(float(anterior), 1),
        }
    }

# DESABILITADO: Função que depende de modelo local Avaliacao
# Todas as funções abaixo foram comentadas pois usam o modelo Avaliacao
# que foi migrado para o microservice gestantes-service.
# Use a API do microservice ao invés.

# def chamar_api_de_risco(avaliacao_instance):
#     """
#     Monta o payload, envia para a API R e retorna os resultados.
#     """
#     pass

# def processar_risco_avaliacao(avaliacao_id):
#     """
#     Função "wrapper" que busca a avaliação, chama a API 
#     e salva o resultado.
#     """
#     pass

# def gerar_pilulas(avaliacao):
#     """
#     Consulta a API /pills usando os fatores da avaliação
#     e salva/atualiza as pílulas no banco.
#     """
#     pass

# def gerar_sintese_llm(avaliacao):
#     """
#     Se não houver fatores negativos, retorna explicação e pílulas padrão,
#     sem chamar a API 'maria_api'.
#     Se houver fatores, envia para API e retorna o conteúdo gerado.
#     """
#     pass

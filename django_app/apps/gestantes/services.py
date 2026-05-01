import json
from django.utils.text import slugify

import requests
import logging
from django.conf import settings
from apps.gestantes.models import Avaliacao, Pilula

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
    """
    Processa as avaliações e retorna os dicionários de 
    riscos e evolução.
    """
    riscos = {}
    evolucao_riscos_dict = {}

    if not ultima_avaliacao:
        return riscos, evolucao_riscos_dict

    # ------------------------------
    # Processamento da última avaliação
    # ------------------------------
    resultado = _processar_resultado_avaliacao(
        getattr(ultima_avaliacao, "resultado_integralidade_saude", {})
    )

    prob_integralidade = round(resultado.get("prob_integralidade", 0))
    icone_int, classe_int = _classificar_risco(prob_integralidade)
    
    fatores_traduzidos = [NOMES_FATORES.get(f, f) for f in resultado.get("top_fatores", [])]
    
    riscos["integralidade"] = {
        "nome": "Integralidade",
        "valor": prob_integralidade,
        "fatores": fatores_traduzidos,
        "icone": icone_int,
        "classe": classe_int,
        "slug": "integralidade",
    }

    outros = []
    for chave, nome in [
        ("prob_asma", "Asma"),
        ("prob_obesidade", "Obesidade"),
        ("prob_carie", "Cárie"),
        ("prob_alergia", "Alergia"),
    ]:
        valor = round(resultado.get(chave, 0))
        icone, classe = _classificar_risco(valor)
        outros.append({
            "nome": nome, "valor": valor, "icone": icone, 
            "classe": classe, "slug": slugify(nome),
        })
    
    outros = sorted(outros, key=lambda r: r["valor"], reverse=True)
    riscos["outros"] = outros

    # ------------------------------
    # Processamento da evolução
    # ------------------------------
    if penultima_avaliacao:
        resultado_ant = _processar_resultado_avaliacao(
            getattr(penultima_avaliacao, "resultado_integralidade_saude", {})
        )

        anterior = round(resultado_ant.get("prob_integralidade", 0))
        atual = prob_integralidade
        delta = atual - anterior

        if delta > 0:
            direcao, seta = "📈", "↑"
        elif delta < 0:
            direcao, seta = "📉", "↓"
        else:
            direcao, seta = "➡️", "="

        evolucao_riscos_dict["integralidade"] = {
            "nome": "Integralidade", "anterior": anterior, "atual": atual,
            "delta": delta, "direcao": direcao, "seta": seta,
            "icone": icone_int, "classe": classe_int, "slug": "integralidade",
        }
    
    return riscos, evolucao_riscos_dict


def chamar_api_de_risco(avaliacao_instance):
    """
    Monta o payload, envia para a API R e retorna os resultados.
    """
    gestante = avaliacao_instance.gestante

    payload = {
        # Dados da avaliação
        #'peso_atual': avaliacao_instance.peso_atual or 0,
        #'idade_gestacional': avaliacao_instance.idade_gestacional or 0,
        #'consultas_prenatal': avaliacao_instance.consultas_prenatal or 0,
        'corrimento_vaginal': avaliacao_instance.corrimento_vaginal or False,
        'periodontite_carie': avaliacao_instance.periodontite_carie or False,
        'hipertensao_gestacao': avaliacao_instance.hipertensao_gestacao or False,
        'diabetes_gestacao': avaliacao_instance.diabetes_gestacao or False,
        'estresse_gestacao': avaliacao_instance.estresse_gestacao or False,
        'historico_familiar_alergia': avaliacao_instance.historico_familiar_alergia or False,
        'consumo_bebidas_adocadas': avaliacao_instance.consumo_bebidas_adocadas or False,
        'consumo_ultraprocessados': avaliacao_instance.consumo_ultraprocessados or False,
        'consumo_alcool': avaliacao_instance.consumo_alcool or False,
        'fumante_gestacao': avaliacao_instance.fumante_gestacao or False,

        # Dados derivados da gestante
        'imc_pre_gestacional': gestante.imc if gestante else 0,
        'idade_gestante': gestante.idade if gestante else 0,
        #'vulnerabilidade_social': gestante.vulnerabilidade_social if gestante else False,
    }

    # Pega a URL do settings.py
    api_url = settings.R_API_URL
    #api_url = 'http://r_api:8000/predict'

    try:
        logger.info(f"📤 Enviando payload para API R (Avaliação ID: {avaliacao_instance.id}):\n{json.dumps(payload, indent=2)}")
        response = requests.post(api_url, json=payload, timeout=20)
        response.raise_for_status()
        logger.info(f"✅ API R respondeu para Avaliação ID: {avaliacao_instance.id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ ERRO AO CHAMAR A API R (Avaliação ID: {avaliacao_instance.id}): {e}")
        return {}

def processar_risco_avaliacao(avaliacao_id):
    """
    Função "wrapper" que busca a avaliação, chama a API 
    e salva o resultado.
    """
    try:
        avaliacao = Avaliacao.objects.get(id=avaliacao_id)
        
        # Chama a função de API
        resultados_api = chamar_api_de_risco(avaliacao)
        
        # Salva o resultado
        if resultados_api:
            avaliacao.resultado_integralidade_saude = resultados_api
            avaliacao.save(update_fields=['resultado_integralidade_saude'])
            logger.info(f"💾 Resultado da API salvo para Avaliação ID: {avaliacao.id}")

    except Avaliacao.DoesNotExist:
        logger.error(f"Tentativa de processar risco para Avaliação ID {avaliacao_id} que não existe.")
    except Exception as e:
        logger.error(f"Erro inesperado ao processar risco para Avaliação ID {avaliacao_id}: {e}")

def gerar_pilulas(avaliacao: Avaliacao):
    """
    Consulta a API /pills usando os fatores da avaliação
    e salva/atualiza as pílulas no banco.
    """

    week_pills = []
    top_fatores = avaliacao.top_fatores or []

    # Se não tiver fatores, nada a fazer
    if not top_fatores:
        week_pills = random.sample(PILLS_PADRAO, 4)
        #logging.info("Avaliação sem fatores negativos — nenhuma pílula gerada.")
    else:
        # ------------------------------
        # 1. Chama API /pills
        # ------------------------------
        base_url = getattr(settings, "MARIA_API_URL", "http://maria_api:8000")
        url = f"{base_url}/pills"

        payload = {"factors": top_fatores}

        try:
            response = requests.post(url, json=payload, timeout=600)
            logging.info(f"Resposta API /pills: {response.json()}")
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as e:
            raise RuntimeError(f"Erro ao chamar API /pills: {e}")

        week_pills = data.get("week_pills", [])

    # ------------------------------
    # 2. Salva pílulas no banco
    # ------------------------------
    for i, item in enumerate(week_pills, start=1):

        fator = item.get("fator")
        conteudo = item.get("pill")

        # nome amigável, se existir no dict
        titulo_traduzido = NOMES_FATORES.get(fator, fator)

        pilula, created = Pilula.objects.update_or_create(
            avaliacao=avaliacao,
            semana_num=i,
            titulo=titulo_traduzido,
            defaults={"conteudo": conteudo},
        )

        logging.info(f"Pílula {'criada' if created else 'atualizada'}: {pilula}")

    
def gerar_sintese_llm(avaliacao: Avaliacao):
    """
    Se não houver fatores negativos, retorna explicação e pílulas padrão,
    sem chamar a API 'maria_api'.
    Se houver fatores, envia para API e retorna o conteúdo gerado.
    """

    top_fatores = avaliacao.top_fatores or []
    #print ("quantos fatores", top_fatores, not top_fatores)

    # -------------------------------------------
    # 🟣 CASO NÃO EXISTAM FATORES → NÃO CHAMA API
    # -------------------------------------------
    if top_fatores == []:

        return {
            "sintese": EXPLICACAO_SEM_RISCO,
            "fontes": [],
            "factors": [],
        }

    # -------------------------------------------
    # 🟣 SE EXISTIREM FATORES → CHAMA A API MARIA
    # -------------------------------------------
    base_url = getattr(settings, "MARIA_API_URL", "http://maria_api:8000")
    url = f"{base_url}/explanation"

    payload = {"factors": top_fatores}

    try:
        response = requests.post(url, json=payload, timeout=600)
        logging.error(response.json())
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Erro ao chamar API maria_api: {e}")
    
    explicacao = data.get("explanation", {})
    explicacao = re.sub(r"\([^)]*\)", "", explicacao)

    fontes = data.get("sources", [])
    factors = data.get("factors", [])

    return {
        "sintese": explicacao,
        "fontes": fontes,
        "factors": factors,
    }
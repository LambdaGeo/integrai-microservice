from django_rq import job
from apps.gestantes import services
from apps.gestantes.models import Avaliacao, Pilula

import logging

from apps.gestantes.literals import NOMES_FATORES

def gerar_pilulas(avaliacao: Avaliacao, week_pills: list):
    """
    week_pills é a lista retornada pela API, no formato:
    [
        {"fator": "vagdischarge", "pill": "texto da pílula"},
        {"fator": "blockupf2", "pill": "texto da pílula"},
    ]
    """
    for i, item in enumerate(week_pills, start=1):
        # Traduz o fator para nome amigável usando o dicionário
        titulo_traduzido = NOMES_FATORES.get(item["fator"], item["fator"])

        # Cria ou atualiza a pílula
        pilula, created = Pilula.objects.update_or_create(
            avaliacao=avaliacao,
            semana_num=i,
            titulo=titulo_traduzido,
            defaults={"conteudo": item["pill"]}
        )
        logging.info(f"Pílula {'criada' if created else 'atualizada'}: {pilula}")

@job
def gerar_sintese_llm_task(avaliacao_id: int):
    """
    Executa em background a chamada à API 'maria_api' para gerar a síntese.
    """
    avaliacao = Avaliacao.objects.get(id=avaliacao_id)
    avaliacao.status_processamento_llm = "PROCESSING"
    avaliacao.save(update_fields=["status_processamento_llm"])
   
    try:
        resultado = services.gerar_sintese_llm(avaliacao)
        avaliacao.llm_sintese = resultado["sintese"]
        avaliacao.status_processamento_llm = "COMPLETED"
        avaliacao.save()
        
        # Cria/atualiza as pílulas somente se a API retornou dados
        #if resultado.get("week_pills"):
        #    gerar_pilulas(avaliacao, resultado["week_pills"])

    except Exception as e:
        avaliacao.llm_sintese = f"Erro ao gerar síntese: {e}"
        avaliacao.status_processamento_llm = "FAILED"
        avaliacao.save()
        logging.error(f"Erro ao gerar síntese para Avaliacao {avaliacao_id}: {e}")


@job
def gerar_pilulas_task(avaliacao_id: int):
    """
    Executa em background a geração das pílulas.
    """
    avaliacao = Avaliacao.objects.get(id=avaliacao_id)

    # Se quiser controlar status no futuro
    avaliacao.status_processamento_pills = "PROCESSING"
    avaliacao.save(update_fields=["status_processamento_pills"])

    try:
        # Chama a função que consulta a API e salva as pílulas no banco
        services.gerar_pilulas(avaliacao)

        avaliacao.status_processamento_pills = "COMPLETED"
        avaliacao.save(update_fields=["status_processamento_pills"])

    except Exception as e:
        avaliacao.status_processamento_pills = "FAILED"
        avaliacao.save(update_fields=["status_processamento_pills"])
        
        logging.error(
            f"Erro ao gerar pílulas para Avaliacao {avaliacao_id}: {e}",
            exc_info=True
        )

    

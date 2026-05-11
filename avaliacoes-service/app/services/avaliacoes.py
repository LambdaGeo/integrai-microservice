"""
Avaliacoes domain services.
"""
from datetime import date
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Avaliacao


settings = get_settings()

EXT_PESO = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-peso-pre"
EXT_ALTURA = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-altura"

QUESTIONARIO_FIELDS = [
    "corrimento_vaginal",
    "periodontite_carie",
    "hipertensao_gestacao",
    "diabetes_gestacao",
    "estresse_gestacao",
    "consumo_bebidas_adocadas",
    "historico_familiar_alergia",
    "consumo_ultraprocessados",
    "consumo_alcool",
    "fumante_gestacao",
]


async def calcular_e_salvar_risco(
    db: Session,
    avaliacao: Avaliacao,
    access_token: str | None = None,
) -> dict[str, Any]:
    payload = await montar_payload_predicao(avaliacao, access_token=access_token)
    resultado = await chamar_api_predicao(payload)
    avaliacao.resultado_integralidade_saude = resultado
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)
    return resultado


async def montar_payload_predicao(
    avaliacao: Avaliacao,
    access_token: str | None = None,
) -> dict[str, Any]:
    patient = await buscar_patient(avaliacao.gestante, access_token=access_token)
    idade = calcular_idade(patient.get("birthDate"))
    imc = calcular_imc(patient)

    if idade is None or imc is None:
        raise ValueError("Paciente sem dados suficientes para calcular idade da gestante e IMC pré-gestacional.")

    payload = {field: bool(getattr(avaliacao, field)) for field in QUESTIONARIO_FIELDS}
    payload["imc_pre_gestacional"] = imc
    payload["idade_gestante"] = idade
    return payload


async def buscar_patient(gestante_id: int, access_token: str | None = None) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else None
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{settings.GESTANTES_SERVICE_URL.rstrip('/')}/fhir/Patient/{gestante_id}",
            headers=headers,
        )
    response.raise_for_status()
    data = response.json()
    if not data or data.get("resourceType") == "OperationOutcome":
        raise ValueError(f"Gestante {gestante_id} não encontrada no gestantes-service.")
    return data


async def chamar_api_predicao(payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(settings.R_API_URL, json=payload)
    response.raise_for_status()
    return response.json()


def calcular_idade(data_nascimento: str | None) -> int | None:
    if not data_nascimento:
        return None
    nascimento = date.fromisoformat(data_nascimento)
    hoje = date.today()
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))


def calcular_imc(patient: dict[str, Any]) -> float | None:
    peso = fhir_extension(patient, EXT_PESO, "valueInteger")
    altura = fhir_extension(patient, EXT_ALTURA, "valueDecimal")
    if not peso or not altura:
        return None
    return round(float(peso) / (float(altura) ** 2), 2)


def fhir_extension(patient: dict[str, Any], url: str, value_key: str) -> Any:
    for extension in patient.get("extension", []) or []:
        if extension.get("url") == url:
            return extension.get(value_key)
    return None

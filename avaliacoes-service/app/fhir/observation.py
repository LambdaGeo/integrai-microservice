"""
FHIR Observation helpers for Avaliacoes.
"""
import json
from datetime import datetime
from typing import Any

from app.models import Avaliacao


FHIR_SYSTEM = "https://integrai.ufma.br/fhir/CodeSystem/avaliacao-gestacional"
OBSERVATION_CODE = "avaliacao-gestacional"
EXT_RESULTADO = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-resultado-integralidade-saude"
EXT_STATUS_LLM = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-status-processamento-llm"
EXT_STATUS_PILLS = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-status-processamento-pills"
EXT_LLM_SINTESE = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-llm-sintese"

COMPONENTS = {
    "peso_atual": {"display": "Peso atual", "value": "valueQuantity", "unit": "kg", "code": "kg"},
    "idade_gestacional": {"display": "Idade gestacional em semanas", "value": "valueInteger"},
    "consultas_prenatal": {"display": "Quantidade de consultas pre-natal", "value": "valueInteger"},
    "corrimento_vaginal": {"display": "Corrimento vaginal frequente", "value": "valueBoolean"},
    "periodontite_carie": {"display": "Carie e/ou periodontite", "value": "valueBoolean"},
    "hipertensao_gestacao": {"display": "Hipertensao na gestacao", "value": "valueBoolean"},
    "diabetes_gestacao": {"display": "Diabetes na gestacao", "value": "valueBoolean"},
    "estresse_gestacao": {"display": "Estresse durante gestacao", "value": "valueBoolean"},
    "historico_familiar_alergia": {"display": "Historico familiar de alergia", "value": "valueBoolean"},
    "consumo_bebidas_adocadas": {"display": "Consumo de bebidas adocadas", "value": "valueBoolean"},
    "consumo_ultraprocessados": {"display": "Consumo de ultraprocessados", "value": "valueBoolean"},
    "consumo_alcool": {"display": "Consumo de alcool", "value": "valueBoolean"},
    "fumante_gestacao": {"display": "Fumante na gestacao", "value": "valueBoolean"},
}


def avaliacao_to_fhir_observation(instance: Avaliacao) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "resourceType": "Observation",
        "id": str(instance.id),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "survey",
                        "display": "Survey",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": FHIR_SYSTEM,
                    "code": OBSERVATION_CODE,
                    "display": "Avaliacao gestacional",
                }
            ],
            "text": "Avaliacao gestacional",
        },
        "subject": {"reference": f"Patient/{instance.gestante}"},
        "component": [],
        "extension": [
            {"url": EXT_STATUS_LLM, "valueString": instance.status_processamento_llm},
            {"url": EXT_STATUS_PILLS, "valueString": instance.status_processamento_pills},
        ],
    }

    if instance.data_aplicacao:
        observation["effectiveDateTime"] = instance.data_aplicacao.isoformat()
        observation["issued"] = instance.data_aplicacao.isoformat()

    if instance.resultado_integralidade_saude is not None:
        observation["extension"].append(
            {"url": EXT_RESULTADO, "valueString": json.dumps(instance.resultado_integralidade_saude)}
        )

    if instance.llm_sintese:
        observation["extension"].append({"url": EXT_LLM_SINTESE, "valueString": instance.llm_sintese})

    for field, config in COMPONENTS.items():
        value = getattr(instance, field, None)
        if value is None:
            continue

        component: dict[str, Any] = {
            "code": {
                "coding": [{"system": FHIR_SYSTEM, "code": field, "display": config["display"]}],
                "text": config["display"],
            }
        }
        if config["value"] == "valueQuantity":
            component["valueQuantity"] = {
                "value": value,
                "unit": config["unit"],
                "system": "http://unitsofmeasure.org",
                "code": config["code"],
            }
        else:
            component[config["value"]] = value
        observation["component"].append(component)

    return observation


def fhir_observation_to_avaliacao(fhir_data: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {}

    reference = (fhir_data.get("subject") or {}).get("reference")
    if reference and reference.startswith("Patient/"):
        data["gestante"] = int(reference.split("/", 1)[1])

    if fhir_data.get("effectiveDateTime"):
        data["data_aplicacao"] = datetime.fromisoformat(fhir_data["effectiveDateTime"].replace("Z", "+00:00"))

    for component in fhir_data.get("component", []) or []:
        field = component_code(component)
        if field in COMPONENTS:
            data[field] = component_value(component)

    for extension in fhir_data.get("extension", []) or []:
        url = extension.get("url")
        if url == EXT_STATUS_LLM:
            data["status_processamento_llm"] = extension.get("valueString") or "PENDING"
        elif url == EXT_STATUS_PILLS:
            data["status_processamento_pills"] = extension.get("valueString") or "PENDING"
        elif url == EXT_LLM_SINTESE:
            data["llm_sintese"] = extension.get("valueString")
        elif url == EXT_RESULTADO and extension.get("valueString"):
            data["resultado_integralidade_saude"] = json.loads(extension["valueString"])

    return data


def component_code(component: dict[str, Any]) -> str | None:
    for coding in component.get("code", {}).get("coding", []) or []:
        if coding.get("system") == FHIR_SYSTEM:
            return coding.get("code")
    return None


def component_value(component: dict[str, Any]) -> Any:
    if "valueBoolean" in component:
        return component["valueBoolean"]
    if "valueInteger" in component:
        return component["valueInteger"]
    if "valueQuantity" in component:
        return (component["valueQuantity"] or {}).get("value")
    if "valueString" in component:
        return component["valueString"]
    return None

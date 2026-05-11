import json
import logging
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)

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


def calcular_e_salvar_risco(avaliacao, access_token=None):
    payload = _montar_payload_predicao(avaliacao, access_token=access_token)
    resultado = _chamar_api_predicao(payload)
    avaliacao.resultado_integralidade_saude = resultado
    avaliacao.save(update_fields=["resultado_integralidade_saude"])
    return resultado


def _montar_payload_predicao(avaliacao, access_token=None):
    patient = _buscar_patient(avaliacao.gestante, access_token=access_token)
    idade = _calcular_idade(patient.get("birthDate"))
    imc = _calcular_imc(patient)

    if idade is None or imc is None:
        raise ValueError("Patient sem dados suficientes para calcular idade gestante e IMC pre-gestacional.")

    payload = {field: bool(getattr(avaliacao, field)) for field in QUESTIONARIO_FIELDS}
    payload["imc_pre_gestacional"] = imc
    payload["idade_gestante"] = idade
    return payload


def _buscar_patient(gestante_id, access_token=None):
    url = f"{settings.GESTANTES_SERVICE_URL.rstrip('/')}/fhir/Patient/{gestante_id}"
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else None
    data = _request_json("GET", url, headers=headers)
    if not data or data.get("resourceType") == "OperationOutcome":
        raise ValueError(f"Gestante {gestante_id} nao encontrada no gestantes-service.")
    return data


def _chamar_api_predicao(payload):
    return _request_json("POST", settings.R_API_URL, payload)


def _request_json(method, url, payload=None, headers=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = Request(
        url,
        data=body,
        method=method,
        headers=request_headers,
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.exception("Erro ao chamar %s %s", method, url)
        raise RuntimeError(f"Erro ao chamar {url}: {exc}") from exc


def _calcular_idade(data_nascimento):
    if not data_nascimento:
        return None
    nascimento = date.fromisoformat(data_nascimento)
    hoje = date.today()
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))


def _calcular_imc(patient):
    peso = _fhir_extension(patient, EXT_PESO, "valueInteger")
    altura = _fhir_extension(patient, EXT_ALTURA, "valueDecimal")
    if not peso or not altura:
        return None
    return round(float(peso) / (float(altura) ** 2), 2)


def _fhir_extension(patient, url, value_key):
    for extension in patient.get("extension", []) or []:
        if extension.get("url") == url:
            return extension.get(value_key)
    return None

"""
Cliente para comunicação entre microservices.
"""
import json
import os
import requests
from contextvars import ContextVar
from typing import Optional, Dict, Any, List


_request_auth_token = ContextVar("microservice_auth_token", default=None)


def set_request_auth_token(token: Optional[str]):
    return _request_auth_token.set(token)


def reset_request_auth_token(token_context):
    _request_auth_token.reset(token_context)


FHIR_SYSTEM = "https://integrai.ufma.br/fhir/CodeSystem/avaliacao-gestacional"
OBSERVATION_CODE = "avaliacao-gestacional"
EXT_RESULTADO = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-resultado-integralidade-saude"
EXT_STATUS_LLM = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-status-processamento-llm"
EXT_STATUS_PILLS = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-status-processamento-pills"
EXT_LLM_SINTESE = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-llm-sintese"

AVALIACAO_COMPONENTS = {
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


class BaseServiceClient:
    """Classe base para comunicação entre serviços."""
    
    def __init__(self, service_url: str):
        self.base_url = service_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.last_error = None

    def set_bearer_token(self, token: str) -> None:
        self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{self.base_url}{endpoint}"
        self.last_error = None
        try:
            headers = None
            token = _request_auth_token.get()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            response = self.session.request(method, url, json=data, params=params, headers=headers)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            self.last_error = self._extract_error(e)
            print(f"Erro na requisição {method} {url}: {e}")
            return None

    def _extract_error(self, error: requests.exceptions.RequestException) -> Optional[str]:
        response = getattr(error, "response", None)
        if response is None or not response.content:
            return None
        try:
            payload = response.json()
        except ValueError:
            return response.text

        if payload.get("resourceType") == "OperationOutcome":
            issues = payload.get("issue") or []
            if issues:
                return issues[0].get("diagnostics")

        detail = payload.get("detail")
        if isinstance(detail, list) and detail:
            first = detail[0]
            if isinstance(first, dict):
                return first.get("msg")
        if isinstance(detail, str):
            return detail
        return None


class UsersServiceClient(BaseServiceClient):
    """Cliente para o serviço de usuários."""
    
    def __init__(self):
        url = os.getenv('USERS_SERVICE_URL', 'http://localhost:8000')
        super().__init__(url)

    def health(self) -> Optional[Dict]:
        return self._request('GET', '/health')

    def login(self, username: str, password: str) -> Optional[Dict]:
        response = self.session.post(
            f'{self.base_url}/api/v1/auth/token',
            data={'username': username, 'password': password},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        try:
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get('access_token')
            if access_token:
                self.set_bearer_token(access_token)
            return token_data
        except requests.exceptions.RequestException as e:
            self.last_error = self._extract_error(e)
            print(f"Erro na requisição POST {self.base_url}/api/v1/auth/token: {e}")
            return None

    def get_usuario(self, usuario_id: int) -> Optional[Dict]:
        return self._request('GET', f'/api/v1/usuarios/{usuario_id}')
    
    def list_usuarios(self, params: Optional[Dict] = None) -> List[Dict]:
        result = self._request('GET', '/api/v1/usuarios', params=params)
        return result if result else []
    
    def get_agente(self, agente_id: int) -> Optional[Dict]:
        return self._request('GET', f'/api/v1/usuarios/{agente_id}')
    
    def list_agentes(self, params: Optional[Dict] = None) -> List[Dict]:
        result = self._request('GET', '/api/v1/usuarios', params=params)
        return result if result else []


class GestantesServiceClient(BaseServiceClient):
    """Cliente para o serviço de gestantes."""
    
    def __init__(self):
        url = os.getenv('GESTANTES_SERVICE_URL', 'http://localhost:8001')
        super().__init__(url)

    def health(self) -> Optional[Dict]:
        return self._request('GET', '/health')
    
    def get_gestante(self, gestante_id: int) -> Optional[Dict]:
        return self._request('GET', f'/api/v1/gestantes/{gestante_id}')
    
    def list_gestantes(self, params: Optional[Dict] = None) -> List[Dict]:
        result = self._request('GET', '/api/v1/gestantes', params=params)
        return result if result else []
    
    def create_gestante(self, data: Dict) -> Optional[Dict]:
        return self._request('POST', '/api/v1/gestantes', data=data)
    
    def update_gestante(self, gestante_id: int, data: Dict) -> Optional[Dict]:
        return self._request('PUT', f'/api/v1/gestantes/{gestante_id}', data=data)

    def delete_gestante(self, gestante_id: int) -> Optional[Dict]:
        return self._request('DELETE', f'/api/v1/gestantes/{gestante_id}')
    
    def get_consentimento(self, consentimento_id: int) -> Optional[Dict]:
        return self._request('GET', f'/api/v1/consentimentos/{consentimento_id}')
    
    def list_consentimentos(self, params: Optional[Dict] = None) -> List[Dict]:
        result = self._request('GET', '/api/v1/consentimentos', params=params)
        return result if result else []

    def create_consentimento(self, data: Dict) -> Optional[Dict]:
        return self._request('POST', '/api/v1/consentimentos', data=data)

    def update_consentimento(self, consentimento_id: int, data: Dict) -> Optional[Dict]:
        return self._request('PUT', f'/api/v1/consentimentos/{consentimento_id}', data=data)


class AvaliacoesServiceClient(BaseServiceClient):
    """Cliente para o serviço de avaliações."""
    
    def __init__(self):
        url = os.getenv('AVALIACOES_SERVICE_URL', 'http://localhost:8002')
        super().__init__(url)
    
    def get_avaliacao(self, avaliacao_id: int) -> Optional[Dict]:
        observation = self._request('GET', f'/fhir/Observation/{avaliacao_id}')
        return self._observation_to_avaliacao(observation) if observation else None
    
    def list_avaliacoes(self, params: Optional[Dict] = None) -> List[Dict]:
        fhir_params = self._avaliacao_params_to_fhir(params or {})
        bundle = self._request('GET', '/fhir/Observation', params=fhir_params)
        entries = (bundle or {}).get('entry', [])
        return [
            self._observation_to_avaliacao(entry.get('resource'))
            for entry in entries
            if entry.get('resource')
        ]
    
    def create_avaliacao(self, data: Dict) -> Optional[Dict]:
        observation = self._avaliacao_to_observation(data)
        created = self._request('POST', '/fhir/Observation', data=observation)
        return self._observation_to_avaliacao(created) if created else None
    
    def get_pilula(self, pilula_id: int) -> Optional[Dict]:
        return self._request('GET', f'/api/pilulas/{pilula_id}/')
    
    def list_pilulas(self, params: Optional[Dict] = None) -> List[Dict]:
        result = self._request('GET', '/api/pilulas/', params=params)
        return result if result else []
    
    def marcar_pilula_enviada(self, pilula_id: int) -> Optional[Dict]:
        return self._request('POST', f'/api/pilulas/{pilula_id}/marcar_enviada/')


    def _avaliacao_params_to_fhir(self, params: Dict) -> Dict:
        fhir_params = {}
        if params.get('gestante'):
            fhir_params['subject'] = f"Patient/{params['gestante']}"
        if params.get('_count'):
            fhir_params['_count'] = params['_count']
        return fhir_params

    def _avaliacao_to_observation(self, data: Dict) -> Dict:
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "survey",
                    "display": "Survey",
                }]
            }],
            "code": {
                "coding": [{
                    "system": FHIR_SYSTEM,
                    "code": OBSERVATION_CODE,
                    "display": "Avaliacao gestacional",
                }],
                "text": "Avaliacao gestacional",
            },
            "subject": {"reference": f"Patient/{data['gestante']}"},
            "component": [],
        }

        extensions = []
        if data.get("status_processamento_llm"):
            extensions.append({"url": EXT_STATUS_LLM, "valueString": data["status_processamento_llm"]})
        if data.get("status_processamento_pills"):
            extensions.append({"url": EXT_STATUS_PILLS, "valueString": data["status_processamento_pills"]})
        if data.get("llm_sintese"):
            extensions.append({"url": EXT_LLM_SINTESE, "valueString": data["llm_sintese"]})
        if data.get("resultado_integralidade_saude") is not None:
            extensions.append({
                "url": EXT_RESULTADO,
                "valueString": json.dumps(data["resultado_integralidade_saude"]),
            })
        if extensions:
            observation["extension"] = extensions

        for field, config in AVALIACAO_COMPONENTS.items():
            if field not in data or data[field] is None:
                continue

            component = {
                "code": {
                    "coding": [{
                        "system": FHIR_SYSTEM,
                        "code": field,
                        "display": config["display"],
                    }],
                    "text": config["display"],
                }
            }
            if config["value"] == "valueQuantity":
                component["valueQuantity"] = {
                    "value": data[field],
                    "unit": config["unit"],
                    "system": "http://unitsofmeasure.org",
                    "code": config["code"],
                }
            else:
                component[config["value"]] = data[field]
            observation["component"].append(component)

        return observation

    def _observation_to_avaliacao(self, observation: Optional[Dict]) -> Optional[Dict]:
        if not observation or observation.get("resourceType") == "OperationOutcome":
            return None

        avaliacao = {
            "id": self._as_int(observation.get("id")),
            "gestante": self._subject_id(observation),
            "data_aplicacao": observation.get("effectiveDateTime") or observation.get("issued"),
            "resultado_integralidade_saude": None,
            "status_processamento_llm": "PENDING",
            "status_processamento_pills": "PENDING",
            "llm_sintese": None,
        }

        for component in observation.get("component", []) or []:
            field = self._component_code(component)
            if field in AVALIACAO_COMPONENTS:
                avaliacao[field] = self._component_value(component)

        for extension in observation.get("extension", []) or []:
            url = extension.get("url")
            if url == EXT_STATUS_LLM:
                avaliacao["status_processamento_llm"] = extension.get("valueString") or "PENDING"
            elif url == EXT_STATUS_PILLS:
                avaliacao["status_processamento_pills"] = extension.get("valueString") or "PENDING"
            elif url == EXT_LLM_SINTESE:
                avaliacao["llm_sintese"] = extension.get("valueString")
            elif url == EXT_RESULTADO and extension.get("valueString"):
                try:
                    avaliacao["resultado_integralidade_saude"] = json.loads(extension["valueString"])
                except json.JSONDecodeError:
                    avaliacao["resultado_integralidade_saude"] = None

        return avaliacao

    def _subject_id(self, observation: Dict) -> Optional[int]:
        reference = (observation.get("subject") or {}).get("reference")
        if not reference:
            return None
        return self._as_int(reference.removeprefix("Patient/"))

    def _component_code(self, component: Dict) -> Optional[str]:
        for coding in component.get("code", {}).get("coding", []) or []:
            if coding.get("system") == FHIR_SYSTEM:
                return coding.get("code")
        return None

    def _component_value(self, component: Dict) -> Any:
        if "valueBoolean" in component:
            return component["valueBoolean"]
        if "valueInteger" in component:
            return component["valueInteger"]
        if "valueQuantity" in component:
            return (component["valueQuantity"] or {}).get("value")
        if "valueString" in component:
            return component["valueString"]
        return None

    def _as_int(self, value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


# Instâncias globais
users_client = UsersServiceClient()
gestantes_client = GestantesServiceClient()
avaliacoes_client = AvaliacoesServiceClient()

"""
Cliente para comunicação entre microservices.
"""
import os
import requests
from typing import Optional, Dict, Any, List


class BaseServiceClient:
    """Classe base para comunicação entre serviços."""
    
    def __init__(self, service_url: str):
        self.base_url = service_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def set_bearer_token(self, token: str) -> None:
        self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, json=data, params=params)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição {method} {url}: {e}")
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
            print(f"Erro na requisiÃ§Ã£o POST {self.base_url}/api/v1/auth/token: {e}")
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
        return self._request('GET', f'/api/avaliacoes/{avaliacao_id}/')
    
    def list_avaliacoes(self, params: Optional[Dict] = None) -> List[Dict]:
        result = self._request('GET', '/api/avaliacoes/', params=params)
        return result if result else []
    
    def create_avaliacao(self, data: Dict) -> Optional[Dict]:
        return self._request('POST', '/api/avaliacoes/', data=data)
    
    def get_pilula(self, pilula_id: int) -> Optional[Dict]:
        return self._request('GET', f'/api/pilulas/{pilula_id}/')
    
    def list_pilulas(self, params: Optional[Dict] = None) -> List[Dict]:
        result = self._request('GET', '/api/pilulas/', params=params)
        return result if result else []
    
    def marcar_pilula_enviada(self, pilula_id: int) -> Optional[Dict]:
        return self._request('POST', f'/api/pilulas/{pilula_id}/marcar_enviada/')


# Instâncias globais
users_client = UsersServiceClient()
gestantes_client = GestantesServiceClient()
avaliacoes_client = AvaliacoesServiceClient()

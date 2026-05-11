# Integrai - Arquitetura de Microservices

Este projeto foi refatorado de uma aplicação monolítica Django para uma arquitetura de microservices.

## Visão Geral

A aplicação foi separada em 3 serviços independentes:

```
microservices/
├── users-service/        # Porta 8000 - Gerenciamento de usuários e autenticação
├── gestantes-service/    # Porta 8001 - Gerenciamento de gestantes
├── avaliacoes-service/   # Porta 8002 - Avaliações e Pílulas de Conhecimento
├── docker-compose.yml   # Orquestração dos serviços
└── clients.py          # Cliente para comunicação entre serviços
```

## Serviços

### 1. Users Service (Porta 8000)
- **Responsabilidade**: Gerenciamento de usuários, autenticação e perfis de agentes
- **Modelos**: `Usuario`, `AgenteProfile`
- **Endpoints**: `/api/usuarios/`, `/api/agentes/`

### 2. Gestantes Service (Porta 8001)
- **Responsabilidade**: Cadastro e gerenciamento de gestantes
- **Modelos**: `Gestante`, `ConsentimentoGestante`
- **Endpoints**: `/api/gestantes/`, `/api/consentimentos/`

### 3. Avaliacoes Service (Porta 8002)
- **Responsabilidade**: Avaliações de saúde, processamento LLM e pílulas de conhecimento
- **Modelos**: `Avaliacao`, `Pilula`
- **Endpoints**: `/api/avaliacoes/`, `/api/pilulas/`

## Configuração

### Variáveis de Ambiente

Cada serviço requer as seguintes variáveis de ambiente:

```env
SECRET_KEY=sua-chave-secreta
DEBUG=True
DB_NAME=nome_do_banco
DB_USER=postgres
DB_PASSWORD=senha_postgres
DB_HOST=localhost
DB_PORT=5432
```

### URLs de Comunicação Entre Serviços

```env
USERS_SERVICE_URL=http://localhost:8000
GESTANTES_SERVICE_URL=http://localhost:8001
AVALIACOES_SERVICE_URL=http://localhost:8002
```

## Executando com Docker

```bash
cd microservices
docker-compose up -d
```

Isso irá iniciar:
- PostgreSQL (porta 5432)
- Redis (porta 6379)
- Users Service (porta 8000)
- Gestantes Service (porta 8001)
- Avaliacoes Service (porta 8002)

## Executando Localmente

```bash
# Users Service
cd microservices/users-service
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Gestantes Service (outro terminal)
cd microservices/gestantes-service
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001

# Avaliacoes Service (outro terminal)
cd microservices/avaliacoes-service
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8002
```

## Comunicação Entre Serviços

O arquivo `clients.py` fornece clientes Python para comunicação entre serviços:

```python
from clients import users_client, gestantes_client, avaliacoes_client

# Buscar gestante
gestante = gestantes_client.get_gestante(1)

# Listar avaliações
avaliacoes = avaliacoes_client.list_avaliacoes({'gestante': 1})

# Buscar usuário
usuario = users_client.get_usuario(1)
```

## API REST

Cada serviço expõe uma API RESTful com os seguintes endpoints:

### Users Service
- `GET /api/usuarios/` - Listar usuários
- `POST /api/usuarios/` - Criar usuário
- `GET /api/usuarios/{id}/` - Detalhar usuário
- `PUT /api/usuarios/{id}/` - Atualizar usuário
- `DELETE /api/usuarios/{id}/` - Deletar usuário

### Gestantes Service
- `GET /api/gestantes/` - Listar gestantes
- `POST /api/gestantes/` - Criar gestante
- `GET /api/gestantes/{id}/` - Detalhar gestante
- `PUT /api/gestantes/{id}/` - Atualizar gestante
- `DELETE /api/gestantes/{id}/` - Deletar gestante

### Avaliacoes Service
- `GET /api/avaliacoes/` - Listar avaliações
- `POST /api/avaliacoes/` - Criar avaliação
- `GET /api/avaliacoes/{id}/` - Detalhar avaliação
- `GET /api/pilulas/` - Listar pílulas
- `POST /api/pilulas/{id}/marcar_enviada/` - Marcar pílula como enviada

## Banco de Dados

Cada serviço possui seu próprio banco de dados PostgreSQL:
- `users_db` - Dados de usuários
- `gestantes_db` - Dados de gestantes
- `avaliacoes_db` - Dados de avaliações

## Filas de Tarefas

O serviço de avaliações utiliza Redis + RQ para processamento assíncrono de:
- Geração de síntese LLM
- Criação de pílulas de conhecimento
- Envio de notificações

## Considerações

1. **Autenticação**: O `users-service` centraliza a emissão e validação dos tokens de acesso
2. **Consistência de Dados**: Comunicação síncrona entre serviços para garantir consistência
3. **Escalabilidade**: Cada serviço pode ser escalado independentemente, respeitando suas dependências HTTP
4. **Monitoramento**: Recomenda-se adicionar logging e métricas (Prometheus, Grafana)

## Limitações metodológicas

- **Acoplamento por introspecção de token**: o `gestantes-service` valida o Bearer token por chamada HTTP ao endpoint `GET /api/v1/auth/me` do `users-service`, em vez de validar localmente o JWT com uma chave compartilhada. Essa abordagem simplifica a centralização da autenticação no protótipo, mas cria dependência direta de disponibilidade: se o `users-service` estiver indisponível, os endpoints protegidos do `gestantes-service` também ficam indisponíveis para validação de autenticação. Portanto, a independência operacional entre os microsserviços fica parcialmente limitada.

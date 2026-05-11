# users-service

API de gerenciamento de usuários e autenticação em FastAPI, com suporte FHIR R4 para Patient e Practitioner.

## Implementação ativa

- A implementação ativa está em `app/` e usa FastAPI.
- A implementação Django anterior foi preservada em `legacy-django/` apenas como referência histórica.
- O serviço possui Dockerfile próprio e deve ser executado como unidade independente.

## Microsserviço

- Contexto de domínio: usuários, autenticação e perfil de agente.
- Persistência própria: banco PostgreSQL `users_db`.
- Comunicação externa: API REST HTTP, JWT e fachada FHIR R4.
- Porta interna padrão: `8000`.
- Porta exposta no host pelo compose raiz: `8003`.

## Executar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Executar com Docker

No diretório raiz do projeto:

```bash
docker compose up --build users-service
```

O `docker-compose.yml` raiz sobe também o banco isolado `users-db`, exposto em `5434` no host e `5432` na rede Docker.

## Endpoints principais

- `GET /health`
- `POST /api/v1/auth/token`
- `GET /api/v1/usuarios`
- `GET /api/v1/usuarios/{id}`
- `GET /fhir/metadata`
- `GET /fhir/Patient`
- `GET /fhir/Practitioner`

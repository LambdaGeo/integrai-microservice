# users-service

API de gerenciamento de usuarios e autenticacao em FastAPI, com suporte FHIR R4 para Patient e Practitioner.

## Implementacao ativa

- A implementacao ativa esta em `app/` e usa FastAPI.
- A implementacao Django anterior foi preservada em `legacy-django/` apenas como referencia historica.
- O servico possui Dockerfile proprio e deve ser executado como unidade independente.

## Microservico

- Contexto de dominio: usuarios, autenticacao e perfil de agente.
- Persistencia propria: banco PostgreSQL `users_db`.
- Comunicacao externa: API REST HTTP, JWT e fachada FHIR R4.
- Porta interna padrao: `8000`.
- Porta exposta no host pelo compose raiz: `8003`.

## Executar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Executar com Docker

No diretorio raiz do projeto:

```bash
docker compose up --build users-service
```

O `docker-compose.yml` raiz sobe tambem o banco isolado `users-db`, exposto em `5434` no host e `5432` na rede Docker.

## Endpoints principais

- `GET /health`
- `POST /api/v1/auth/token`
- `GET /api/v1/usuarios`
- `GET /api/v1/usuarios/{id}`
- `GET /fhir/metadata`
- `GET /fhir/Patient`
- `GET /fhir/Practitioner`

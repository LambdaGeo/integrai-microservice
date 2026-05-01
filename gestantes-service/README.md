# gestantes-service

API de gerenciamento de gestantes em FastAPI, com suporte FHIR R4 (Patient).

## Implementacao ativa

- A implementacao ativa deste servico esta em `app/` e usa FastAPI.
- A implementacao Django anterior foi preservada em `legacy-django/` apenas como referencia historica.
- O servico possui Dockerfile proprio e deve ser executado como unidade independente.

## Decisoes de interoperabilidade

- Conformidade FHIR: validada com `fhir.resources==8.2.0`.
- Regras de negocio: isoladas em `app/services/gestantes.py`.
- Perfil local de `Patient`: `https://integrai.ufma.br/fhir/StructureDefinition/GestantePatient`.
- Extensoes usadas no `Patient` para dados de dominio:
  - peso pre-gestacional
  - altura
  - vulnerabilidade social
  - usuario responsavel (`usuario_id`)
- Regra de consistencia:
  - `POST /fhir/Patient` exige os campos de dominio nas extensoes (sem defaults implicitos).
  - `PUT /fhir/Patient/{id}` permite payload parcial, mas valida o estado final combinado.
- Erros dos endpoints FHIR sao retornados como `OperationOutcome`.
- O `CapabilityStatement` declara recurso, perfil, interacoes e parametros de busca suportados.

## Microservico

- Contexto de dominio: gestantes e consentimentos.
- Persistencia propria: banco PostgreSQL `gestantes_db`.
- Comunicacao externa: API REST HTTP e fachada FHIR R4.
- Porta padrao interna: `8001`.

## Executar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Executar com Docker

No diretorio raiz do projeto:

```bash
docker compose up --build gestantes-service
```

O `docker-compose.yml` raiz sobe tambem o banco isolado `gestantes-db`, exposto em `5433` no host e `5432` na rede Docker.

## Endpoints principais

- `GET /health`
- `GET /api/v1/gestantes`
- `POST /api/v1/gestantes`
- `GET /api/v1/consentimentos`
- `POST /api/v1/consentimentos`

## FHIR (minimo)

- `GET /fhir/metadata`
- `GET /fhir/Patient`
- `GET /fhir/Patient/{id}`
- `POST /fhir/Patient`
- `PUT /fhir/Patient/{id}`
- `DELETE /fhir/Patient/{id}`

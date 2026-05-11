# gestantes-service

API de gerenciamento de gestantes em FastAPI, com suporte FHIR R4 (Patient).

## Implementação ativa

- A implementação ativa deste serviço está em `app/` e usa FastAPI.
- A implementação Django anterior foi preservada em `legacy-django/` apenas como referência histórica.
- O serviço possui Dockerfile próprio e deve ser executado como unidade independente.

## Decisões de interoperabilidade

- Conformidade FHIR: validada com `fhir.resources==8.2.0`.
- Regras de negócio: isoladas em `app/services/gestantes.py`.
- Perfil local de `Patient`: `https://integrai.ufma.br/fhir/StructureDefinition/GestantePatient`.
- Extensões usadas no `Patient` para dados de domínio:
  - peso pré-gestacional
  - altura
  - vulnerabilidade social
  - usuário responsável (`usuario_id`)
- Regra de consistência:
  - `POST /fhir/Patient` exige os campos de domínio nas extensões (sem defaults implícitos).
  - `PUT /fhir/Patient/{id}` permite payload parcial, mas valida o estado final combinado.
- Erros dos endpoints FHIR são retornados como `OperationOutcome`.
- O `CapabilityStatement` declara recurso, perfil, interações e parâmetros de busca suportados.

## Microsserviço

- Contexto de domínio: gestantes e consentimentos.
- Persistência própria: banco PostgreSQL `gestantes_db`.
- Comunicação externa: API REST HTTP e fachada FHIR R4.
- Porta padrão interna: `8001`.

## Limitação metodológica

- A autenticação dos endpoints protegidos usa introspecção de token: o `gestantes-service` encaminha o Bearer token para `GET /api/v1/auth/me` no `users-service`. Isso não é validação local do JWT com chave compartilhada. Como consequência, a indisponibilidade do `users-service` impede a validação de usuários e torna os endpoints protegidos do `gestantes-service` indisponíveis. Essa decisão simplifica o protótipo, mas aumenta o acoplamento entre serviços e deve ser considerada uma limitação da arquitetura avaliada.

## Executar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Executar com Docker

No diretório raiz do projeto:

```bash
docker compose up --build gestantes-service
```

O `docker-compose.yml` raiz sobe também o banco isolado `gestantes-db`, exposto em `5433` no host e `5432` na rede Docker.

## Endpoints principais

- `GET /health`
- `GET /api/v1/gestantes`
- `POST /api/v1/gestantes`
- `GET /api/v1/consentimentos`
- `POST /api/v1/consentimentos`

## FHIR (mínimo)

- `GET /fhir/metadata`
- `GET /fhir/Patient`
- `GET /fhir/Patient/{id}`
- `POST /fhir/Patient`
- `PUT /fhir/Patient/{id}`
- `DELETE /fhir/Patient/{id}`

# avaliacoes-service

FastAPI para gerenciamento de avaliacoes e pilulas de conhecimento, com fachada FHIR R4.

Estrutura alinhada aos demais microservices FastAPI do projeto:

- `app/main.py` - entrypoint FastAPI
- `app/models/` - modelos SQLAlchemy
- `app/routers/` - endpoints REST por recurso
- `app/fhir/` - fachada e conversores FHIR R4
- `app/services/` - regras de dominio e integrações externas
- `legacy-django/` - implementacao Django anterior preservada como referencia

Rotas principais:

- `GET /health`
- `GET /api/health`
- `GET|POST /fhir/Observation`
- `GET|PUT|DELETE /fhir/Observation/{id}`
- `GET|POST /api/avaliacoes/`
- `GET|POST /api/pilulas/`
- `POST /api/pilulas/{id}/marcar_enviada/`

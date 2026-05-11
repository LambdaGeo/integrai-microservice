"""
FHIR R4 endpoints.
"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import false
from sqlalchemy.orm import Session

from app.auth import authorized_gestante_ids, can_access_gestante, require_authenticated_user
from app.config import get_settings
from app.database import get_db
from app.fhir.observation import avaliacao_to_fhir_observation, fhir_observation_to_avaliacao
from app.models import Avaliacao
from app.services.avaliacoes import calcular_e_salvar_risco

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fhir", tags=["FHIR"])
settings = get_settings()


def operation_outcome(
    status_code: int,
    diagnostics: str = "",
    *,
    code: str = "processing",
    severity: str = "error",
) -> JSONResponse:
    content: dict[str, Any] = {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": severity, "code": code}],
    }
    if diagnostics:
        content["issue"][0]["diagnostics"] = diagnostics
    return JSONResponse(status_code=status_code, content=content, media_type="application/fhir+json")


@router.get("/Observation")
async def list_observations(
    fhir_id: Optional[int] = Query(None, alias="_id"),
    subject: Optional[str] = Query(None),
    patient: Optional[str] = Query(None),
    _count: Optional[int] = Query(None, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    access_token = current_user.get("access_token")

    if fhir_id is not None:
        avaliacao = db.query(Avaliacao).filter(Avaliacao.id == fhir_id).first()
        if not avaliacao:
            return operation_outcome(status.HTTP_404_NOT_FOUND, code="not-found")
        if not await can_access_gestante(avaliacao.gestante, access_token):
            return operation_outcome(status.HTTP_404_NOT_FOUND, code="not-found")
        return avaliacao_to_fhir_observation(avaliacao)

    allowed_ids = await authorized_gestante_ids(access_token)
    query = db.query(Avaliacao).filter(Avaliacao.gestante.in_(allowed_ids))

    subject_filter = subject or patient
    if subject_filter:
        gestante_id = subject_filter.removeprefix("Patient/")
        if not await can_access_gestante(gestante_id, access_token):
            query = query.filter(false())
        else:
            query = query.filter(Avaliacao.gestante == int(gestante_id))

    query = query.order_by(Avaliacao.gestante, Avaliacao.data_aplicacao)
    if _count:
        query = query.limit(_count)

    entries = [
        {"resource": avaliacao_to_fhir_observation(avaliacao), "fullUrl": f"Observation/{avaliacao.id}"}
        for avaliacao in query.all()
    ]
    return {"resourceType": "Bundle", "type": "searchset", "total": len(entries), "entry": entries}


@router.get("/Observation/{observation_id}")
async def get_observation(
    observation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    avaliacao = db.query(Avaliacao).filter(Avaliacao.id == observation_id).first()
    if not avaliacao or not await can_access_gestante(avaliacao.gestante, current_user.get("access_token")):
        return operation_outcome(status.HTTP_404_NOT_FOUND, code="not-found")
    return avaliacao_to_fhir_observation(avaliacao)


@router.post("/Observation", status_code=status.HTTP_201_CREATED)
async def create_observation(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    access_token = current_user.get("access_token")
    try:
        data = fhir_observation_to_avaliacao(body)
    except (TypeError, ValueError) as exc:
        return operation_outcome(status.HTTP_400_BAD_REQUEST, str(exc), code="invalid")

    if not data.get("gestante"):
        return operation_outcome(status.HTTP_400_BAD_REQUEST, "subject Patient reference is required", code="invalid")

    if not await can_access_gestante(data.get("gestante"), access_token):
        return operation_outcome(status.HTTP_403_FORBIDDEN, "Access denied", code="forbidden")

    avaliacao = Avaliacao(**data)
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)

    try:
        await calcular_e_salvar_risco(db, avaliacao, access_token=access_token)
    except Exception:
        logger.exception("Erro ao calcular risco da avaliacao %s", avaliacao.id)

    return avaliacao_to_fhir_observation(avaliacao)


@router.put("/Observation/{observation_id}")
async def update_observation(
    observation_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    access_token = current_user.get("access_token")
    avaliacao = db.query(Avaliacao).filter(Avaliacao.id == observation_id).first()
    if not avaliacao or not await can_access_gestante(avaliacao.gestante, access_token):
        return operation_outcome(status.HTTP_404_NOT_FOUND, code="not-found")

    try:
        data = fhir_observation_to_avaliacao(body)
    except (TypeError, ValueError) as exc:
        return operation_outcome(status.HTTP_400_BAD_REQUEST, str(exc), code="invalid")

    if data.get("gestante") and not await can_access_gestante(data["gestante"], access_token):
        return operation_outcome(status.HTTP_403_FORBIDDEN, "Access denied", code="forbidden")

    for key, value in data.items():
        setattr(avaliacao, key, value)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao_to_fhir_observation(avaliacao)


@router.delete("/Observation/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(
    observation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    avaliacao = db.query(Avaliacao).filter(Avaliacao.id == observation_id).first()
    if not avaliacao or not await can_access_gestante(avaliacao.gestante, current_user.get("access_token")):
        return operation_outcome(status.HTTP_404_NOT_FOUND, code="not-found")
    db.delete(avaliacao)
    db.commit()
    return None


@router.get("/Questionnaire")
async def list_questionnaires(current_user: dict = Depends(require_authenticated_user)):
    return {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}


@router.get("/QuestionnaireResponse")
async def list_questionnaire_responses(current_user: dict = Depends(require_authenticated_user)):
    return {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}


@router.get("/metadata")
async def metadata(current_user: dict = Depends(require_authenticated_user)):
    return capability_statement()


@router.get("")
async def fhir_root(current_user: dict = Depends(require_authenticated_user)):
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "fhirVersion": "4.0.1",
        "format": ["json"],
    }


def capability_statement() -> dict[str, Any]:
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-04-26",
        "kind": "instance",
        "software": {"name": settings.APP_NAME, "version": settings.APP_VERSION},
        "fhirVersion": "4.0.1",
        "format": ["json", "application/fhir+json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Observation",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                        ],
                    },
                    {"type": "Questionnaire", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                    {
                        "type": "QuestionnaireResponse",
                        "interaction": [{"code": "read"}, {"code": "search-type"}, {"code": "create"}],
                    },
                ],
            }
        ],
    }

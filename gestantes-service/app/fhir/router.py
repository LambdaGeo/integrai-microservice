"""
FHIR R4 endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.auth import can_access_usuario, is_admin_user, require_authenticated_user
from app.database import get_db
from app.fhir.patient import (
    GESTANTE_PATIENT_PROFILE,
    fhir_patient_to_gestante,
    gestante_to_fhir_patient,
    match_identifier,
)
from app.models.gestante import Gestante
from app.services.gestantes import validar_regras_gestante

router = APIRouter(prefix="/fhir", tags=["FHIR"])
settings = get_settings()


def operation_outcome(
    status_code: int,
    diagnostics: str,
    *,
    code: str = "processing",
    severity: str = "error",
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": severity,
                    "code": code,
                    "diagnostics": diagnostics,
                }
            ],
        },
        media_type="application/fhir+json",
    )


@router.get("/metadata")
async def capability_statement():
    return {
        "resourceType": "CapabilityStatement",
        "id": "integrai-gestantes-fhir",
        "url": "https://integrai.ufma.br/fhir/CapabilityStatement/gestantes-service",
        "version": settings.APP_VERSION,
        "name": "IntegraiGestantesFhirServer",
        "title": "Integrai Gestantes Service FHIR API",
        "status": "active",
        "kind": "instance",
        "date": "2026-04-28",
        "publisher": "Integrai UFMA",
        "description": "FHIR R4 facade for the Integrai Gestantes Service, exposing pregnant women as Patient resources.",
        "software": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
        "implementation": {
            "description": "FastAPI service for gestantes domain data",
            "url": "http://localhost:8001/fhir",
        },
        "fhirVersion": "4.0.1",
        "format": ["json", "application/fhir+json"],
        "rest": [
            {
                "mode": "server",
                "documentation": "Minimal FHIR R4 REST API for the Patient resource in the gestantes bounded context.",
                "security": {
                    "cors": True,
                    "description": "Autenticação via Bearer token é exigida para os endpoints FHIR protegidos.",
                },
                "resource": [
                    {
                        "type": "Patient",
                        "profile": GESTANTE_PATIENT_PROFILE,
                        "documentation": "Gestante represented as a FHIR Patient with local extensions for domain fields.",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "delete"},
                        ],
                        "searchParam": [
                            {
                                "name": "name",
                                "type": "string",
                                "documentation": "Search by gestante name.",
                            },
                            {
                                "name": "identifier",
                                "type": "token",
                                "documentation": "Search by local gestante identifier or phone digits.",
                            },
                            {
                                "name": "_count",
                                "type": "number",
                                "documentation": "Maximum number of results returned.",
                            },
                        ],
                    }
                ],
            }
        ],
    }


@router.get("/Patient")
async def search_patients(
    name: Optional[str] = Query(None),
    identifier: Optional[str] = Query(None),
    _count: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    query = db.query(Gestante)
    if not is_admin_user(current_user):
        query = query.filter(Gestante.usuario_id == current_user.get("id"))
    if name:
        query = query.filter(Gestante.nome.ilike(f"%{name}%"))

    candidates = query.limit(_count).all()
    patients = candidates
    if identifier:
        patients = [item for item in candidates if match_identifier(item, identifier)]

    entries = [
        {
            "fullUrl": f"Patient/{gestante.id}",
            "resource": gestante_to_fhir_patient(gestante),
            "search": {"mode": "match"},
        }
        for gestante in patients
    ]

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries,
    }


@router.get("/Patient/{patient_id}")
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    gestante = db.query(Gestante).filter(Gestante.id == patient_id).first()
    if not gestante or not can_access_usuario(current_user, gestante.usuario_id):
        return operation_outcome(status.HTTP_404_NOT_FOUND, "Patient não encontrado", code="not-found")
    return gestante_to_fhir_patient(gestante)


@router.post("/Patient", status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    try:
        mapped = fhir_patient_to_gestante(body, require_domain_fields=True)
    except ValueError as exc:
        return operation_outcome(status.HTTP_400_BAD_REQUEST, f"FHIR Patient inválido: {exc}", code="invalid")

    try:
        validar_regras_gestante(mapped["data_nascimento"], int(mapped["peso"]), float(mapped["altura"]))
    except ValueError as exc:
        return operation_outcome(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), code="business-rule")

    if not is_admin_user(current_user):
        mapped["usuario_id"] = current_user.get("id")

    gestante = Gestante(**mapped)
    db.add(gestante)
    db.commit()
    db.refresh(gestante)
    return gestante_to_fhir_patient(gestante)


@router.put("/Patient/{patient_id}")
async def update_patient(
    patient_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    gestante = db.query(Gestante).filter(Gestante.id == patient_id).first()
    if not gestante or not can_access_usuario(current_user, gestante.usuario_id):
        return operation_outcome(status.HTTP_404_NOT_FOUND, "Patient não encontrado", code="not-found")

    try:
        mapped = fhir_patient_to_gestante(body, require_domain_fields=False)
    except ValueError as exc:
        return operation_outcome(status.HTTP_400_BAD_REQUEST, f"FHIR Patient inválido: {exc}", code="invalid")

    final_nome = mapped["nome"] if mapped["nome"] is not None else gestante.nome
    final_data_nascimento = (
        mapped["data_nascimento"] if mapped["data_nascimento"] is not None else gestante.data_nascimento
    )
    final_telefone = mapped["telefone"] if mapped["telefone"] is not None else gestante.telefone
    final_peso = mapped["peso"] if mapped["peso"] is not None else gestante.peso
    final_altura = mapped["altura"] if mapped["altura"] is not None else gestante.altura
    final_vulnerabilidade = (
        mapped["vulnerabilidade_social"]
        if mapped["vulnerabilidade_social"] is not None
        else gestante.vulnerabilidade_social
    )
    final_usuario_id = mapped["usuario_id"] if mapped["usuario_id"] is not None else gestante.usuario_id
    if not is_admin_user(current_user):
        final_usuario_id = gestante.usuario_id
    final_foto = mapped["foto"] if mapped["foto"] is not None else gestante.foto

    try:
        validar_regras_gestante(final_data_nascimento, int(final_peso), float(final_altura))
    except ValueError as exc:
        return operation_outcome(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc), code="business-rule")

    gestante.nome = final_nome
    gestante.data_nascimento = final_data_nascimento
    gestante.telefone = final_telefone
    gestante.peso = final_peso
    gestante.altura = final_altura
    gestante.vulnerabilidade_social = final_vulnerabilidade
    gestante.usuario_id = final_usuario_id
    gestante.foto = final_foto
    db.commit()
    db.refresh(gestante)
    return gestante_to_fhir_patient(gestante)


@router.delete("/Patient/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    gestante = db.query(Gestante).filter(Gestante.id == patient_id).first()
    if not gestante or not can_access_usuario(current_user, gestante.usuario_id):
        return operation_outcome(status.HTTP_404_NOT_FOUND, "Patient não encontrado", code="not-found")

    db.delete(gestante)
    db.commit()
    return None

"""
FHIR R4 endpoints for the Users Service.

This service exposes community health agents as Practitioner resources.
Patients are exposed by gestantes-service, where the assisted person belongs
to the domain model.
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.database import get_db
from app.fhir.practitioner import agenteprofile_to_fhir_practitioner, fhir_practitioner_to_agenteprofile
from app.models.usuario import AgenteProfile, Usuario

router = APIRouter(prefix="/fhir", tags=["FHIR"])


@router.get("/metadata")
async def fhir_metadata():
    """FHIR CapabilityStatement for the users bounded context."""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-05-11",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json", "application/fhir+json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Practitioner",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                        ],
                        "searchParam": [
                            {
                                "name": "name",
                                "type": "string",
                                "documentation": "Search by agent name.",
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


@router.get("/Practitioner")
async def search_practitioners(
    name: Optional[str] = Query(None, description="Practitioner name"),
    _count: int = Query(20, ge=1, le=200, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Search for Practitioner resources."""
    query = db.query(AgenteProfile)

    if name:
        query = query.filter(AgenteProfile.nome.like(f"%{name}%"))

    profiles = query.limit(_count).all()
    entries = [
        {
            "fullUrl": f"Practitioner/{profile.id}",
            "resource": json.loads(agenteprofile_to_fhir_practitioner(profile).json()),
            "search": {"mode": "match"},
        }
        for profile in profiles
    ]

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries,
    }


@router.get("/Practitioner/{practitioner_id}")
async def get_practitioner(
    practitioner_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Get Practitioner by ID."""
    profile = db.query(AgenteProfile).filter(AgenteProfile.id == practitioner_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practitioner not found")

    return json.loads(agenteprofile_to_fhir_practitioner(profile).json())


@router.post("/Practitioner", status_code=status.HTTP_201_CREATED)
async def create_practitioner(
    body: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Create a new Practitioner resource."""
    from fhir.resources.practitioner import Practitioner
    from pydantic import ValidationError

    try:
        practitioner = Practitioner(**body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid FHIR Practitioner: {exc}",
        ) from exc

    profile_data = fhir_practitioner_to_agenteprofile(practitioner)
    existing = db.query(AgenteProfile).filter(AgenteProfile.user_id == profile_data["user_id"]).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Practitioner already exists")

    db_profile = AgenteProfile(**profile_data)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    return json.loads(agenteprofile_to_fhir_practitioner(db_profile).json())

"""
FHIR Router - FHIR R4 endpoints
"""
from typing import Optional, List
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, AgenteProfile
from app.fhir.patient import usuario_to_fhir_patient, fhir_patient_to_usuario
from app.fhir.practitioner import agenteprofile_to_fhir_practitioner, fhir_practitioner_to_agenteprofile
from app.auth import get_current_active_user
from app.schemas import UsuarioCreate
from app.auth import get_password_hash

router = APIRouter(prefix="/fhir", tags=["FHIR"])


# ==================== FHIR Capability Statement ====================

@router.get("/metadata")
async def fhir_metadata():
    """
    FHIR Capability Statement (metadata)
    """
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-01-01",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {
                    "type": "Patient",
                    "interaction": [
                        {"code": "read"},
                        {"code": "search-type"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"}
                    ]
                },
                {
                    "type": "Practitioner",
                    "interaction": [
                        {"code": "read"},
                        {"code": "search-type"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"}
                    ]
                }
            ]
        }]
    }


# ==================== Patient Endpoints ====================

@router.get("/Patient")
async def search_patients(
    identifier: Optional[str] = Query(None, description="Patient identifier (CPF)"),
    active: Optional[bool] = Query(None, description="Patient is active"),
    _count: Optional[int] = Query(20, description="Number of results"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Search for Patient resources
    """
    query = db.query(Usuario)
    
    if identifier:
        query = query.filter(Usuario.username.like(f"%{identifier}%"))
    if active is not None:
        query = query.filter(Usuario.is_active == active)
    
    usuarios = query.limit(_count).all()
    
    # Build FHIR Bundle
    entries = []
    for usuario in usuarios:
        patient = usuario_to_fhir_patient(usuario)
        entries.append({
            "fullUrl": f"Patient/{usuario.id}",
            "resource": json.loads(patient.json()),
            "search": {"mode": "match"}
        })
    
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries
    }


@router.get("/Patient/{patient_id}")
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Get Patient by ID
    """
    usuario = db.query(Usuario).filter(Usuario.id == patient_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    patient = usuario_to_fhir_patient(usuario)
    return json.loads(patient.json())


@router.post("/Patient", status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Create new Patient resource
    """
    from fhir.resources.patient import Patient
    from pydantic import ValidationError
    
    try:
        patient = Patient(**body)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid FHIR Patient: {str(e)}"
        )
    
    # Convert to Usuario
    usuario_data = fhir_patient_to_usuario(patient, "changeme")  # Password required
    
    # Check if exists
    existing = db.query(Usuario).filter(Usuario.username == usuario_data["username"]).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient already exists"
        )
    
    # Create
    db_usuario = Usuario(
        username=usuario_data["username"],
        email=usuario_data.get("email"),
        hashed_password=get_password_hash(usuario_data["password"])
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    
    return json.loads(usuario_to_fhir_patient(db_usuario).json())


@router.put("/Patient/{patient_id}")
async def update_patient(
    patient_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Update Patient resource
    """
    from fhir.resources.patient import Patient
    from pydantic import ValidationError
    
    try:
        patient = Patient(**body)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid FHIR Patient: {str(e)}"
        )
    
    usuario = db.query(Usuario).filter(Usuario.id == patient_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Update fields
    if patient.telecom:
        for telecom in patient.telecom:
            if telecom.system == "email":
                usuario.email = telecom.value
    
    if patient.active is not None:
        usuario.is_active = patient.active
    
    db.commit()
    db.refresh(usuario)
    
    return json.loads(usuario_to_fhir_patient(usuario).json())


@router.delete("/Patient/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Delete Patient (soft delete)
    """
    usuario = db.query(Usuario).filter(Usuario.id == patient_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    usuario.is_active = False
    db.commit()
    
    return None


# ==================== Practitioner Endpoints ====================

@router.get("/Practitioner")
async def search_practitioners(
    name: Optional[str] = Query(None, description="Practitioner name"),
    active: Optional[bool] = Query(None, description="Practitioner is active"),
    _count: Optional[int] = Query(20, description="Number of results"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Search for Practitioner resources
    """
    query = db.query(AgenteProfile)
    
    if name:
        query = query.filter(AgenteProfile.nome.like(f"%{name}%"))
    
    profiles = query.limit(_count).all()
    
    # Build FHIR Bundle
    entries = []
    for profile in profiles:
        practitioner = agenteprofile_to_fhir_practitioner(profile)
        entries.append({
            "fullUrl": f"Practitioner/{profile.id}",
            "resource": json.loads(practitioner.json()),
            "search": {"mode": "match"}
        })
    
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries
    }


@router.get("/Practitioner/{practitioner_id}")
async def get_practitioner(
    practitioner_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Get Practitioner by ID
    """
    profile = db.query(AgenteProfile).filter(AgenteProfile.id == practitioner_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner not found"
        )
    
    practitioner = agenteprofile_to_fhir_practitioner(profile)
    return json.loads(practitioner.json())


@router.post("/Practitioner", status_code=status.HTTP_201_CREATED)
async def create_practitioner(
    body: dict,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Create new Practitioner resource
    """
    from fhir.resources.practitioner import Practitioner
    from pydantic import ValidationError
    
    try:
        practitioner = Practitioner(**body)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid FHIR Practitioner: {str(e)}"
        )
    
    profile_data = fhir_practitioner_to_agenteprofile(practitioner)
    
    # Check if exists
    existing = db.query(AgenteProfile).filter(AgenteProfile.user_id == profile_data["user_id"]).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Practitioner already exists"
        )
    
    # Create
    db_profile = AgenteProfile(**profile_data)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return json.loads(agenteprofile_to_fhir_practitioner(db_profile).json())
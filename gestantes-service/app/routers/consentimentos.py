"""
Consentimentos CRUD endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.gestante import ConsentimentoGestante, Gestante
from app.schemas import ConsentimentoCreate, ConsentimentoResponse, ConsentimentoUpdate

router = APIRouter(prefix="/consentimentos", tags=["Consentimentos"])


@router.get("", response_model=list[ConsentimentoResponse])
async def list_consentimentos(
    gestante_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(ConsentimentoGestante)
    if gestante_id is not None:
        query = query.filter(ConsentimentoGestante.gestante_id == gestante_id)
    if status_filter:
        query = query.filter(ConsentimentoGestante.status == status_filter)
    return query.order_by(ConsentimentoGestante.data_registro.desc()).offset(skip).limit(limit).all()


@router.get("/{consentimento_id}", response_model=ConsentimentoResponse)
async def get_consentimento(consentimento_id: int, db: Session = Depends(get_db)):
    consentimento = db.query(ConsentimentoGestante).filter(ConsentimentoGestante.id == consentimento_id).first()
    if not consentimento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consentimento nao encontrado")
    return consentimento


@router.post("", response_model=ConsentimentoResponse, status_code=status.HTTP_201_CREATED)
async def create_consentimento(payload: ConsentimentoCreate, db: Session = Depends(get_db)):
    gestante = db.query(Gestante).filter(Gestante.id == payload.gestante_id).first()
    if not gestante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestante nao encontrada")

    consentimento = ConsentimentoGestante(**payload.model_dump())
    db.add(consentimento)
    db.commit()
    db.refresh(consentimento)
    return consentimento


@router.put("/{consentimento_id}", response_model=ConsentimentoResponse)
async def update_consentimento(
    consentimento_id: int,
    payload: ConsentimentoUpdate,
    db: Session = Depends(get_db),
):
    consentimento = db.query(ConsentimentoGestante).filter(ConsentimentoGestante.id == consentimento_id).first()
    if not consentimento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consentimento nao encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(consentimento, field, value)

    db.commit()
    db.refresh(consentimento)
    return consentimento


@router.delete("/{consentimento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consentimento(consentimento_id: int, db: Session = Depends(get_db)):
    consentimento = db.query(ConsentimentoGestante).filter(ConsentimentoGestante.id == consentimento_id).first()
    if not consentimento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consentimento nao encontrado")

    db.delete(consentimento)
    db.commit()
    return None


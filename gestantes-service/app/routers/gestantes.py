"""
Gestantes CRUD endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.gestante import Gestante
from app.schemas import GestanteCreate, GestanteResponse, GestanteUpdate
from app.services.gestantes import validar_regras_gestante

router = APIRouter(prefix="/gestantes", tags=["Gestantes"])


@router.get("", response_model=list[GestanteResponse])
async def list_gestantes(
    nome: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    vulnerabilidade_social: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Gestante)
    if nome:
        query = query.filter(Gestante.nome.ilike(f"%{nome}%"))
    if usuario_id is not None:
        query = query.filter(Gestante.usuario_id == usuario_id)
    if vulnerabilidade_social is not None:
        query = query.filter(Gestante.vulnerabilidade_social == vulnerabilidade_social)
    return query.order_by(Gestante.data_cadastro.desc()).offset(skip).limit(limit).all()


@router.get("/{gestante_id}", response_model=GestanteResponse)
async def get_gestante(gestante_id: int, db: Session = Depends(get_db)):
    gestante = db.query(Gestante).filter(Gestante.id == gestante_id).first()
    if not gestante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestante nao encontrada")
    return gestante


@router.post("", response_model=GestanteResponse, status_code=status.HTTP_201_CREATED)
async def create_gestante(payload: GestanteCreate, db: Session = Depends(get_db)):
    validar_regras_gestante(payload.data_nascimento, payload.peso, payload.altura)
    gestante = Gestante(**payload.model_dump())
    db.add(gestante)
    db.commit()
    db.refresh(gestante)
    return gestante


@router.put("/{gestante_id}", response_model=GestanteResponse)
async def update_gestante(gestante_id: int, payload: GestanteUpdate, db: Session = Depends(get_db)):
    gestante = db.query(Gestante).filter(Gestante.id == gestante_id).first()
    if not gestante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestante nao encontrada")

    updates = payload.model_dump(exclude_unset=True)
    final_data_nascimento = updates.get("data_nascimento", gestante.data_nascimento)
    final_peso = updates.get("peso", gestante.peso)
    final_altura = updates.get("altura", gestante.altura)
    validar_regras_gestante(final_data_nascimento, final_peso, final_altura)

    for field, value in updates.items():
        setattr(gestante, field, value)

    db.commit()
    db.refresh(gestante)
    return gestante


@router.delete("/{gestante_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gestante(gestante_id: int, db: Session = Depends(get_db)):
    gestante = db.query(Gestante).filter(Gestante.id == gestante_id).first()
    if not gestante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestante nao encontrada")

    db.delete(gestante)
    db.commit()
    return None

"""
Consentimentos CRUD endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.audit import registrar_auditoria
from app.auth import can_access_usuario, is_admin_user, require_authenticated_user
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
    current_user: dict = Depends(require_authenticated_user),
):
    query = db.query(ConsentimentoGestante)
    if not is_admin_user(current_user):
        query = query.join(Gestante).filter(Gestante.usuario_id == current_user.get("id"))
    if gestante_id is not None:
        query = query.filter(ConsentimentoGestante.gestante_id == gestante_id)
    if status_filter:
        query = query.filter(ConsentimentoGestante.status == status_filter)
    return query.order_by(ConsentimentoGestante.data_registro.desc()).offset(skip).limit(limit).all()


@router.get("/{consentimento_id}", response_model=ConsentimentoResponse)
async def get_consentimento(
    consentimento_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    consentimento = db.query(ConsentimentoGestante).filter(ConsentimentoGestante.id == consentimento_id).first()
    if not consentimento or not can_access_usuario(current_user, consentimento.gestante.usuario_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consentimento não encontrado")
    return consentimento


@router.post("", response_model=ConsentimentoResponse, status_code=status.HTTP_201_CREATED)
async def create_consentimento(
    payload: ConsentimentoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    gestante = db.query(Gestante).filter(Gestante.id == payload.gestante_id).first()
    if not gestante or not can_access_usuario(current_user, gestante.usuario_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gestante não encontrada")

    data = payload.model_dump()
    if not is_admin_user(current_user):
        data["usuario_id"] = current_user.get("id")
    consentimento = ConsentimentoGestante(**data)
    db.add(consentimento)
    db.commit()
    db.refresh(consentimento)
    await registrar_auditoria(
        current_user,
        "consentimento.criado",
        "consentimento",
        consentimento.id,
        "Consentimento registrado.",
        {"gestante_id": consentimento.gestante_id, "status": consentimento.status},
    )
    return consentimento


@router.put("/{consentimento_id}", response_model=ConsentimentoResponse)
async def update_consentimento(
    consentimento_id: int,
    payload: ConsentimentoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    consentimento = db.query(ConsentimentoGestante).filter(ConsentimentoGestante.id == consentimento_id).first()
    if not consentimento or not can_access_usuario(current_user, consentimento.gestante.usuario_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consentimento não encontrado")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(consentimento, field, value)

    db.commit()
    db.refresh(consentimento)
    if updates:
        await registrar_auditoria(
            current_user,
            "consentimento.atualizado",
            "consentimento",
            consentimento.id,
            "Consentimento atualizado.",
            {"campos": sorted(updates.keys()), "gestante_id": consentimento.gestante_id},
        )
    return consentimento


@router.delete("/{consentimento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consentimento(
    consentimento_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    consentimento = db.query(ConsentimentoGestante).filter(ConsentimentoGestante.id == consentimento_id).first()
    if not consentimento or not can_access_usuario(current_user, consentimento.gestante.usuario_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consentimento não encontrado")

    db.delete(consentimento)
    db.commit()
    await registrar_auditoria(
        current_user,
        "consentimento.excluido",
        "consentimento",
        consentimento_id,
        "Consentimento excluído.",
    )
    return None

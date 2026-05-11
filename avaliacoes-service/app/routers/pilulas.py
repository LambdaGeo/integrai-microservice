"""
Pilulas CRUD endpoints.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.auth import authorized_gestante_ids, can_access_gestante, require_authenticated_user
from app.database import get_db
from app.models import Avaliacao, Pilula
from app.schemas import PilulaCreate, PilulaUpdate

router = APIRouter(prefix="/pilulas", tags=["Pílulas"])


def pilula_to_dict(pilula: Pilula) -> dict:
    return {
        "id": pilula.id,
        "avaliacao": pilula.avaliacao_id,
        "avaliacao_id": pilula.avaliacao_id,
        "avaliacao_gestante": f"Gestante {pilula.avaliacao.gestante}",
        "titulo": pilula.titulo,
        "conteudo": pilula.conteudo,
        "semana_num": pilula.semana_num,
        "semana_ord": pilula.semana_ord,
        "data_geracao": pilula.data_geracao,
        "data_envio": pilula.data_envio,
        "status": pilula.status,
        "periodo_envio": pilula.periodo_envio,
    }


@router.get("/")
async def list_pilulas(
    avaliacao: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    allowed_ids = await authorized_gestante_ids(current_user.get("access_token"))
    query = (
        db.query(Pilula)
        .join(Pilula.avaliacao)
        .options(joinedload(Pilula.avaliacao))
        .filter(Avaliacao.gestante.in_(allowed_ids))
    )
    if avaliacao is not None:
        query = query.filter(Pilula.avaliacao_id == avaliacao)
    if status_filter:
        query = query.filter(Pilula.status == status_filter)
    pilulas = query.order_by(Pilula.avaliacao_id, Pilula.semana_num, Pilula.data_geracao).all()
    return [pilula_to_dict(item) for item in pilulas]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_pilula(
    payload: PilulaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    data = payload.model_dump(by_alias=True)
    avaliacao = db.query(Avaliacao).filter(Avaliacao.id == data["avaliacao_id"]).first()
    if not avaliacao or not await can_access_gestante(avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    pilula = Pilula(**data)
    db.add(pilula)
    db.commit()
    db.refresh(pilula)
    return pilula_to_dict(pilula)


@router.get("/{pilula_id}/")
async def get_pilula(
    pilula_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    pilula = db.query(Pilula).options(joinedload(Pilula.avaliacao)).filter(Pilula.id == pilula_id).first()
    if not pilula or not await can_access_gestante(pilula.avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pílula não encontrada")
    return pilula_to_dict(pilula)


@router.put("/{pilula_id}/")
async def update_pilula(
    pilula_id: int,
    payload: PilulaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    pilula = db.query(Pilula).options(joinedload(Pilula.avaliacao)).filter(Pilula.id == pilula_id).first()
    if not pilula or not await can_access_gestante(pilula.avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pílula não encontrada")

    updates = payload.model_dump(exclude_unset=True, by_alias=True)
    if updates.get("avaliacao_id"):
        nova_avaliacao = db.query(Avaliacao).filter(Avaliacao.id == updates["avaliacao_id"]).first()
        if not nova_avaliacao or not await can_access_gestante(nova_avaliacao.gestante, current_user.get("access_token")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    for field, value in updates.items():
        setattr(pilula, field, value)
    db.commit()
    db.refresh(pilula)
    return pilula_to_dict(pilula)


@router.delete("/{pilula_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pilula(
    pilula_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    pilula = db.query(Pilula).options(joinedload(Pilula.avaliacao)).filter(Pilula.id == pilula_id).first()
    if not pilula or not await can_access_gestante(pilula.avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pílula não encontrada")
    db.delete(pilula)
    db.commit()
    return None


@router.post("/{pilula_id}/marcar_enviada/")
async def marcar_pilula_enviada(
    pilula_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    pilula = db.query(Pilula).options(joinedload(Pilula.avaliacao)).filter(Pilula.id == pilula_id).first()
    if not pilula or not await can_access_gestante(pilula.avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pílula não encontrada")
    pilula.status = "enviada"
    pilula.data_envio = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pilula)
    return pilula_to_dict(pilula)

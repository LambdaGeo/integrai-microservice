"""
Avaliacoes CRUD endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import authorized_gestante_ids, can_access_gestante, require_authenticated_user
from app.database import get_db
from app.models import Avaliacao
from app.schemas import AvaliacaoCreate, AvaliacaoUpdate

router = APIRouter(prefix="/avaliacoes", tags=["Avaliacoes"])


def avaliacao_to_dict(avaliacao: Avaliacao) -> dict:
    return {
        "id": avaliacao.id,
        "gestante": avaliacao.gestante,
        "gestante_nome": f"Gestante {avaliacao.gestante}",
        "data_aplicacao": avaliacao.data_aplicacao,
        "peso_atual": avaliacao.peso_atual,
        "idade_gestacional": avaliacao.idade_gestacional,
        "consultas_prenatal": avaliacao.consultas_prenatal,
        "corrimento_vaginal": avaliacao.corrimento_vaginal,
        "periodontite_carie": avaliacao.periodontite_carie,
        "hipertensao_gestacao": avaliacao.hipertensao_gestacao,
        "diabetes_gestacao": avaliacao.diabetes_gestacao,
        "estresse_gestacao": avaliacao.estresse_gestacao,
        "historico_familiar_alergia": avaliacao.historico_familiar_alergia,
        "consumo_bebidas_adocadas": avaliacao.consumo_bebidas_adocadas,
        "consumo_ultraprocessados": avaliacao.consumo_ultraprocessados,
        "consumo_alcool": avaliacao.consumo_alcool,
        "fumante_gestacao": avaliacao.fumante_gestacao,
        "resultado_integralidade_saude": avaliacao.resultado_integralidade_saude,
        "status_processamento_llm": avaliacao.status_processamento_llm,
        "status_processamento_pills": avaliacao.status_processamento_pills,
        "llm_sintese": avaliacao.llm_sintese,
        "ganho_peso": None,
        "top_fatores_str": avaliacao.top_fatores_str,
    }


@router.get("/")
async def list_avaliacoes(
    gestante: Optional[int] = Query(None),
    status_processamento_llm: Optional[str] = Query(None),
    status_processamento_pills: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    allowed_ids = await authorized_gestante_ids(current_user.get("access_token"))
    query = db.query(Avaliacao).filter(Avaliacao.gestante.in_(allowed_ids))
    if gestante is not None:
        if gestante not in allowed_ids:
            return []
        query = query.filter(Avaliacao.gestante == gestante)
    if status_processamento_llm:
        query = query.filter(Avaliacao.status_processamento_llm == status_processamento_llm)
    if status_processamento_pills:
        query = query.filter(Avaliacao.status_processamento_pills == status_processamento_pills)
    avaliacoes = query.order_by(Avaliacao.gestante, Avaliacao.data_aplicacao).all()
    return [avaliacao_to_dict(item) for item in avaliacoes]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_avaliacao(
    payload: AvaliacaoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    if not await can_access_gestante(payload.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    avaliacao = Avaliacao(**payload.model_dump())
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao_to_dict(avaliacao)


@router.get("/{avaliacao_id}/")
async def get_avaliacao(
    avaliacao_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    avaliacao = db.query(Avaliacao).filter(Avaliacao.id == avaliacao_id).first()
    if not avaliacao or not await can_access_gestante(avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return avaliacao_to_dict(avaliacao)


@router.put("/{avaliacao_id}/")
async def update_avaliacao(
    avaliacao_id: int,
    payload: AvaliacaoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    avaliacao = db.query(Avaliacao).filter(Avaliacao.id == avaliacao_id).first()
    if not avaliacao or not await can_access_gestante(avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("gestante") and not await can_access_gestante(updates["gestante"], current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in updates.items():
        setattr(avaliacao, field, value)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao_to_dict(avaliacao)


@router.delete("/{avaliacao_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avaliacao(
    avaliacao_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_authenticated_user),
):
    avaliacao = db.query(Avaliacao).filter(Avaliacao.id == avaliacao_id).first()
    if not avaliacao or not await can_access_gestante(avaliacao.gestante, current_user.get("access_token")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(avaliacao)
    db.commit()
    return None

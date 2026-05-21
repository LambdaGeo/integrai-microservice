from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.audit import record_audit_log
from app.auth import get_current_active_user
from app.database import get_db
from app.models.usuario import AuditLog, Usuario
from app.schemas import AuditLogCreate, AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Auditoria"])


def is_admin_user(user: Usuario) -> bool:
    return bool(user.is_staff or user.is_superuser)


def ensure_admin_user(user: Usuario) -> None:
    if not is_admin_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    actor_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Lista eventos de auditoria. Restrito a administradores."""
    ensure_admin_user(current_user)
    query = db.query(AuditLog)

    if actor_id is not None:
        query = query.filter(AuditLog.actor_id == actor_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    payload: AuditLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Registra um evento de auditoria para o usuário autenticado."""
    return record_audit_log(
        db,
        actor=current_user,
        action=payload.action,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        description=payload.description,
        detalhes=payload.detalhes,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

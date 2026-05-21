from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.usuario import AuditLog, Usuario


def record_audit_log(
    db: Session,
    *,
    actor: Optional[Usuario],
    action: str,
    resource_type: str,
    resource_id: Optional[str | int] = None,
    description: Optional[str] = None,
    detalhes: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        description=description,
        detalhes=detalhes,
        ip_address=ip_address,
        user_agent=user_agent[:255] if user_agent else None,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

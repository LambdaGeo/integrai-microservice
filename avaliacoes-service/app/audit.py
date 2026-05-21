from typing import Any, Optional

import httpx

from app.config import get_settings

settings = get_settings()


async def registrar_auditoria(
    current_user: dict,
    action: str,
    resource_type: str,
    resource_id: Optional[int | str] = None,
    description: Optional[str] = None,
    detalhes: Optional[dict[str, Any]] = None,
) -> None:
    token = current_user.get("access_token")
    if not token:
        return

    payload = {
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id is not None else None,
        "description": description,
        "detalhes": detalhes or {},
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{settings.USERS_SERVICE_URL.rstrip('/')}/api/v1/audit",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError as exc:
        print(f"Erro ao registrar auditoria: {exc}")

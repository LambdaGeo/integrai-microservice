"""
Authentication and authorization dependencies backed by users-service and
gestantes-service.
"""
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings


security = HTTPBearer(auto_error=False)
settings = get_settings()


async def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                f"{settings.USERS_SERVICE_URL.rstrip('/')}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {credentials.credentials}"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de usuários indisponível",
        ) from exc

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    user = response.json()
    user["access_token"] = credentials.credentials
    return user


async def authorized_gestante_ids(access_token: str | None, count: int = 200) -> list[int]:
    if not access_token:
        return []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.GESTANTES_SERVICE_URL.rstrip('/')}/fhir/Patient",
                params={"_count": count},
                headers={"Authorization": f"Bearer {access_token}"},
            )
    except httpx.HTTPError:
        return []

    if response.status_code >= 400:
        return []

    try:
        bundle = response.json()
    except ValueError:
        return []

    ids: list[int] = []
    for entry in bundle.get("entry", []) or []:
        resource_id = (entry.get("resource") or {}).get("id")
        try:
            ids.append(int(resource_id))
        except (TypeError, ValueError):
            continue
    return ids


async def can_access_gestante(gestante_id: int | str | None, access_token: str | None) -> bool:
    try:
        parsed_id = int(gestante_id)
    except (TypeError, ValueError):
        return False
    return parsed_id in await authorized_gestante_ids(access_token)

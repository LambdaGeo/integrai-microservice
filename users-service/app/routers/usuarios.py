"""
Router de usuários - endpoints CRUD.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit import record_audit_log
from app.auth import get_current_active_user, get_password_hash
from app.database import get_db
from app.models.usuario import AgenteProfile, Usuario
from app.schemas import (
    AgenteProfileCreate,
    AgenteProfileResponse,
    AgenteProfileUpdate,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
    UsuarioWithProfileResponse,
)

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def is_admin_user(user: Usuario) -> bool:
    return bool(user.is_staff or user.is_superuser)


def ensure_admin_user(user: Usuario) -> None:
    if not is_admin_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )


def collect_usuario_changes(usuario: Usuario, usuario_update: UsuarioUpdate) -> dict:
    changes = {}
    for field in ("email", "is_active", "is_staff", "is_superuser"):
        value = getattr(usuario_update, field)
        if value is not None and getattr(usuario, field) != value:
            changes[field] = {"antes": getattr(usuario, field), "depois": value}
    return changes


@router.get("/profile/me", response_model=AgenteProfileResponse)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Retorna o perfil do usuário autenticado."""
    profile = db.query(AgenteProfile).filter(AgenteProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )
    return profile


@router.post("/profile", response_model=AgenteProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile: AgenteProfileCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Cria o perfil do usuário autenticado."""
    existing = db.query(AgenteProfile).filter(AgenteProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Perfil já existe para este usuário",
        )

    db_profile = AgenteProfile(
        user_id=current_user.id,
        nome=profile.nome,
        area=profile.area,
        ubs=profile.ubs,
        foto=profile.foto,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    record_audit_log(
        db,
        actor=current_user,
        action="perfil.criado",
        resource_type="agente_profile",
        resource_id=db_profile.id,
        description="Perfil de agente criado.",
        detalhes={"user_id": current_user.id},
    )
    return db_profile


@router.put("/profile/me", response_model=AgenteProfileResponse)
async def update_my_profile(
    profile_update: AgenteProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Atualiza o perfil do usuário autenticado."""
    profile = db.query(AgenteProfile).filter(AgenteProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )

    updates = profile_update.model_dump(exclude_unset=True)
    if profile_update.nome is not None:
        profile.nome = profile_update.nome
    if profile_update.area is not None:
        profile.area = profile_update.area
    if profile_update.ubs is not None:
        profile.ubs = profile_update.ubs
    if profile_update.foto is not None:
        profile.foto = profile_update.foto

    db.commit()
    db.refresh(profile)
    if updates:
        record_audit_log(
            db,
            actor=current_user,
            action="perfil.atualizado",
            resource_type="agente_profile",
            resource_id=profile.id,
            description="Perfil de agente atualizado.",
            detalhes={"campos": sorted(updates.keys())},
        )
    return profile


@router.get("", response_model=List[UsuarioResponse])
async def list_usuarios(
    skip: int = 0,
    limit: int = 20,
    is_active: Optional[bool] = None,
    is_staff: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Lista usuários com paginação. Restrito a administradores."""
    ensure_admin_user(current_user)
    query = db.query(Usuario)

    if is_active is not None:
        query = query.filter(Usuario.is_active == is_active)
    if is_staff is not None:
        query = query.filter(Usuario.is_staff == is_staff)

    return query.offset(skip).limit(limit).all()


@router.get("/cpf/{cpf}", response_model=UsuarioWithProfileResponse)
async def get_usuario_by_cpf(
    cpf: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Busca usuário por CPF."""
    cpf = "".join(filter(str.isdigit, cpf))
    if not is_admin_user(current_user) and current_user.username != cpf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    usuario = db.query(Usuario).filter(Usuario.username == cpf).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioWithProfileResponse)
async def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Busca usuário por ID."""
    if not is_admin_user(current_user) and current_user.id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario


@router.get("/username/{username}", response_model=UsuarioWithProfileResponse)
async def get_usuario_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Busca usuário por username/CPF."""
    if not is_admin_user(current_user) and current_user.username != username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return usuario


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
):
    """Cria um novo usuário."""
    existing = db.query(Usuario).filter(Usuario.username == usuario.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já cadastrado")

    if usuario.email:
        existing_email = db.query(Usuario).filter(Usuario.email == usuario.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")

    db_usuario = Usuario(
        username=usuario.username,
        email=usuario.email,
        hashed_password=get_password_hash(usuario.password),
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    record_audit_log(
        db,
        actor=None,
        action="usuario.criado",
        resource_type="usuario",
        resource_id=db_usuario.id,
        description="Usuário criado pelo cadastro.",
        detalhes={"username": db_usuario.username, "email": db_usuario.email},
    )
    return db_usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Atualiza usuário. Campos de permissão são restritos a administradores."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    if not is_admin_user(current_user) and current_user.id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

    permission_fields = (
        usuario_update.is_active is not None
        or usuario_update.is_staff is not None
        or usuario_update.is_superuser is not None
    )
    if permission_fields and not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem alterar permissões",
        )

    removing_own_admin_access = (
        current_user.id == usuario_id
        and (
            usuario_update.is_active is False
            or usuario_update.is_staff is False
            or usuario_update.is_superuser is False
        )
    )
    if removing_own_admin_access:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido remover o próprio acesso administrativo",
        )

    changes = collect_usuario_changes(usuario, usuario_update)

    if usuario_update.email is not None:
        usuario.email = usuario_update.email
    if usuario_update.is_active is not None:
        usuario.is_active = usuario_update.is_active
    if usuario_update.is_staff is not None:
        usuario.is_staff = usuario_update.is_staff
    if usuario_update.is_superuser is not None:
        usuario.is_superuser = usuario_update.is_superuser

    db.commit()
    db.refresh(usuario)
    if changes:
        record_audit_log(
            db,
            actor=current_user,
            action="usuario.atualizado",
            resource_type="usuario",
            resource_id=usuario.id,
            description="Usuário atualizado.",
            detalhes={"campos": changes},
        )
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Desativa usuário. Restrito a administradores."""
    ensure_admin_user(current_user)
    if current_user.id == usuario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido desativar o próprio usuário",
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    usuario.is_active = False
    db.commit()
    record_audit_log(
        db,
        actor=current_user,
        action="usuario.desativado",
        resource_type="usuario",
        resource_id=usuario.id,
        description="Usuário desativado.",
        detalhes={"username": usuario.username},
    )
    return None

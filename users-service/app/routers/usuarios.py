"""
Usuários Router - CRUD endpoints
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, AgenteProfile
from app.schemas import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse,
    AgenteProfileCreate, AgenteProfileUpdate, AgenteProfileResponse,
    UsuarioWithProfileResponse
)
from app.auth import get_current_active_user, get_password_hash

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


# ==================== AgenteProfile Endpoints ====================

@router.get("/profile/me", response_model=AgenteProfileResponse)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get current user's profile"""
    profile = db.query(AgenteProfile).filter(AgenteProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )
    return profile


@router.post("/profile", response_model=AgenteProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile: AgenteProfileCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Create profile for current user"""
    # Check if profile already exists
    existing = db.query(AgenteProfile).filter(AgenteProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Perfil já existe para este usuário"
        )
    
    # Create profile
    db_profile = AgenteProfile(
        user_id=current_user.id,
        nome=profile.nome,
        area=profile.area,
        ubs=profile.ubs,
        foto=profile.foto
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_profile


@router.put("/profile/me", response_model=AgenteProfileResponse)
async def update_my_profile(
    profile_update: AgenteProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Update current user's profile"""
    profile = db.query(AgenteProfile).filter(AgenteProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )
    
    # Update fields
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
    
    return profile


# ==================== Usuario Endpoints ====================

@router.get("", response_model=List[UsuarioResponse])
async def list_usuarios(
    skip: int = 0,
    limit: int = 20,
    is_active: Optional[bool] = None,
    is_staff: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """List all usuários with pagination"""
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
    current_user: Usuario = Depends(get_current_active_user)
):
    """Buscar usuário por CPF (username)"""
    # Garante que o CPF tenha apenas dígitos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    usuario = db.query(Usuario).filter(Usuario.username == cpf).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return usuario

@router.get("/{usuario_id}", response_model=UsuarioWithProfileResponse)
async def get_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get usuario by ID"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return usuario

@router.get("/username/{username}", response_model=UsuarioWithProfileResponse)
async def get_usuario_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get usuario by username (CPF)"""
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return usuario

@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    # current_user: Usuario = Depends(get_current_active_user)
):
    """Create new usuario"""
    # Check if username already exists
    existing = db.query(Usuario).filter(Usuario.username == usuario.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já cadastrado"
        )
    
    # Check if email already exists
    if usuario.email:
        existing_email = db.query(Usuario).filter(Usuario.email == usuario.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )
    
    # Create usuario
    db_usuario = Usuario(
        username=usuario.username,
        email=usuario.email,
        hashed_password=get_password_hash(usuario.password)
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    
    return db_usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Update usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Update fields
    if usuario_update.email is not None:
        usuario.email = usuario_update.email
    if usuario_update.is_active is not None:
        usuario.is_active = usuario_update.is_active
    
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Delete usuario (soft delete - deactivate)"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Soft delete - just deactivate
    usuario.is_active = False
    db.commit()
    
    return None


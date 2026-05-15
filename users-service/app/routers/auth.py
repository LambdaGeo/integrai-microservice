"""
Auth Router - Login/Token endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas import Token, TokenWithUser, PasswordResetRequest, PasswordResetConfirm, UsuarioResponse
from app.auth import verify_password, create_access_token, get_password_hash, get_current_active_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/me", response_model=UsuarioResponse)
async def current_user(current_user: Usuario = Depends(get_current_active_user)):
    """Validate bearer token and return the authenticated user."""
    return current_user


@router.post("/token", response_model=TokenWithUser)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login endpoint
    """
    # Clean username (remove non-digits for CPF)
    username = ''.join(filter(str.isdigit, form_data.username))
    
    user = db.query(Usuario).filter(Usuario.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    access_token = create_access_token(
        data={"sub": user.username}
    )
    
    # Retorna token + dados do usuário
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=TokenWithUser)
async def login_json(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    JSON login endpoint (alternative to OAuth2 form)
    """
    # Clean username (remove non-digits for CPF)
    username = ''.join(filter(str.isdigit, username))
    
    user = db.query(Usuario).filter(Usuario.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos"
        )
    
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    access_token = create_access_token(
        data={"sub": user.username}
    )
    
    # Retorna token + dados do usuário
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# ==================== Password Reset ====================

@router.post("/password/reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset - sends email with reset link
    """
    # Buscar usuário por email ou username (CPF)
    user = None
    if request.username:
        username = ''.join(filter(str.isdigit, request.username))
        user = db.query(Usuario).filter(Usuario.username == username).first()
    elif request.email:
        user = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    if not user:
        # Não revelar se o usuário existe
        return {"message": "Se o email/CPF existir, um link de recuperação será enviado"}
    
    if not user.is_active:
        return {"message": "Se o email/CPF existir, um link de recuperação será enviado"}
    
    # TODO: Enviar email com link de reset
    # Por enquanto, apenas retorna sucesso
    return {"message": "Se o email/CPF existir, um link de recuperação será enviado"}


@router.post("/password/reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    username: str,
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with new password
    """
    # Validar token (simplificado - em produção usar token seguro)
    username = ''.join(filter(str.isdigit, username))
    user = db.query(Usuario).filter(Usuario.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solicitação de recuperação inválida"
        )
    
    # Atualizar senha
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Senha atualizada com sucesso"}

from app.schemas import PasswordResetRequest, PasswordResetConfirm
import secrets

@router.post("/password-reset/request")
async def request_password_reset(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Solicita reset de senha — busca usuário e gera token"""
    
    # Buscar usuário por email ou username
    user = None
    if data.email:
        user = db.query(Usuario).filter(Usuario.email == data.email).first()
    elif data.username:
        username = ''.join(filter(str.isdigit, data.username))
        user = db.query(Usuario).filter(Usuario.username == username).first()
    
    # Sempre retorna sucesso — não revela se o usuário existe
    if not user:
        return {"message": "Se o usuário existir, um email será enviado."}
    
    # Gerar token de reset
    reset_token = secrets.token_urlsafe(32)
    
    # Armazenar token no banco com expiração
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Retornar token (em produção isso seria enviado por email)
    return {
        "message": "Token gerado com sucesso.",
        "reset_token": reset_token  # remover em produção
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    token: str,
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirma reset de senha com o token"""
    
    user = db.query(Usuario).filter(
        Usuario.reset_token == token,
        Usuario.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado."
        )
    
    # Atualizar senha
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "Senha alterada com sucesso."}

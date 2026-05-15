"""
Usuario Schemas - Pydantic models for API
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ==================== Auth Schemas ====================

class Token(BaseModel):
    access_token: str
    token_type: str





class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(..., description="CPF do usuário")
    password: str = Field(..., description="Senha")


class PasswordResetRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None


class PasswordResetConfirm(BaseModel):
    new_password: str = Field(..., min_length=8)


# ==================== Usuario Schemas ====================

class UsuarioBase(BaseModel):
    username: str = Field(..., max_length=11)
    email: Optional[EmailStr] = None


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)


class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UsuarioResponse(UsuarioBase):
    id: int
    is_active: bool
    is_staff: bool
    is_superuser: bool
    date_joined: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class TokenWithUser(Token):
    """Token response including user data"""
    user: Optional[UsuarioResponse] = None
# ==================== AgenteProfile Schemas ====================

class AgenteProfileBase(BaseModel):
    nome: str = Field(..., max_length=150)
    area: Optional[str] = Field(None, max_length=100)
    ubs: Optional[str] = Field(None, max_length=100)


class AgenteProfileCreate(AgenteProfileBase):
    user_id: int
    foto: Optional[str] = None


class AgenteProfileUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=150)
    area: Optional[str] = Field(None, max_length=100)
    ubs: Optional[str] = Field(None, max_length=100)
    foto: Optional[str] = None


class AgenteProfileResponse(AgenteProfileBase):
    id: int
    user_id: int
    foto: Optional[str] = None
    primeiro_nome: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Usuario with Profile ====================

class UsuarioWithProfileResponse(UsuarioResponse):
    profile: Optional[AgenteProfileResponse] = None
    
    class Config:
        from_attributes = True

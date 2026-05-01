"""
Usuario Model - SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(11), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    date_joined = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Reset de senha
    reset_token = Column(String(100), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    profile = relationship("AgenteProfile", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, username={self.username})>"


class AgenteProfile(Base):
    """AgenteProfile - Perfil de Agente de Saúde"""
    __tablename__ = "agente_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    nome = Column(String(150), nullable=False)
    foto = Column(String(500), nullable=True)  # ImageField path
    area = Column(String(100), nullable=True)
    ubs = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("Usuario", back_populates="profile")
    
    @property
    def primeiro_nome(self) -> str:
        return self.nome.split()[0] if self.nome else ""
    
    def __repr__(self):
        return f"<AgenteProfile(id={self.id}, nome={self.nome})>"
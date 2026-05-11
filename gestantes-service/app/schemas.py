"""
Pydantic schemas for Gestantes Service.
"""
from datetime import date, datetime
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.gestantes import validar_regras_gestante

class GestanteBase(BaseModel):
    nome: str = Field(..., max_length=100)
    data_nascimento: date
    peso: int = Field(..., ge=30, le=200)
    altura: float = Field(..., ge=1.0, le=2.5)
    telefone: Optional[str] = Field(None, max_length=20)
    vulnerabilidade_social: bool = False
    foto: Optional[str] = None
    usuario_id: Optional[int] = None

    @field_validator("telefone")
    @classmethod
    def normalize_phone(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        digits = re.sub(r"\D", "", value)
        if digits.startswith("55") and len(digits) in (12, 13):
            return f"+{digits}"
        if len(digits) in (10, 11):
            return f"+55{digits}"
        raise ValueError("Telefone inválido. Informe DDD com 10 ou 11 dígitos.")

    @model_validator(mode="after")
    def validate_business_rules(self):
        validar_regras_gestante(self.data_nascimento, self.peso, self.altura)
        return self


class GestanteCreate(GestanteBase):
    pass


class GestanteUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    data_nascimento: Optional[date] = None
    peso: Optional[int] = Field(None, ge=30, le=200)
    altura: Optional[float] = Field(None, ge=1.0, le=2.5)
    telefone: Optional[str] = Field(None, max_length=20)
    vulnerabilidade_social: Optional[bool] = None
    foto: Optional[str] = None
    usuario_id: Optional[int] = None

    @field_validator("telefone")
    @classmethod
    def normalize_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = re.sub(r"\D", "", value)
        if digits.startswith("55") and len(digits) in (12, 13):
            return f"+{digits}"
        if len(digits) in (10, 11):
            return f"+55{digits}"
        raise ValueError("Telefone inválido. Informe DDD com 10 ou 11 dígitos.")

    @model_validator(mode="after")
    def validate_optional_business_rules(self):
        if (
            self.data_nascimento is not None
            and self.peso is not None
            and self.altura is not None
        ):
            validar_regras_gestante(self.data_nascimento, self.peso, self.altura)
        return self


class GestanteResponse(GestanteBase):
    id: int
    data_cadastro: datetime
    imc: Optional[float] = None
    idade: int
    imc_classificacao: str
    telefone_whatsapp: Optional[str] = None
    consentimento_ativo: bool = True

    class Config:
        from_attributes = True


class ConsentimentoBase(BaseModel):
    gestante_id: int
    usuario_id: Optional[int] = None
    status: str = Field(..., pattern="^(aceito|revogado)$")
    motivo_revogacao: Optional[str] = None


class ConsentimentoCreate(ConsentimentoBase):
    pass


class ConsentimentoUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(aceito|revogado)$")
    motivo_revogacao: Optional[str] = None


class ConsentimentoResponse(ConsentimentoBase):
    id: int
    data_registro: datetime

    class Config:
        from_attributes = True

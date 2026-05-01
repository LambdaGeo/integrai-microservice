"""
Gestantes models.
"""
from datetime import date, datetime
import re

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Gestante(Base):
    __tablename__ = "gestantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    peso: Mapped[int] = mapped_column(Integer, nullable=False)
    altura: Mapped[float] = mapped_column(Float, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vulnerabilidade_social: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    foto: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    consentimentos: Mapped[list["ConsentimentoGestante"]] = relationship(
        back_populates="gestante",
        cascade="all, delete-orphan",
    )

    @property
    def imc(self) -> float | None:
        if self.altura and self.altura > 0:
            return round(self.peso / (self.altura ** 2), 2)
        return None

    @property
    def idade(self) -> int:
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    @property
    def imc_classificacao(self) -> str:
        imc = self.imc
        if imc is None:
            return "Altura ou peso invalidos"
        if imc < 18.5:
            return "Baixo peso"
        if imc <= 24.9:
            return "Adequado"
        return "Excesso de peso"

    @property
    def telefone_whatsapp(self) -> str | None:
        if not self.telefone:
            return None
        return re.sub(r"\D", "", self.telefone)


class ConsentimentoGestante(Base):
    __tablename__ = "consentimentos_gestante"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gestante_id: Mapped[int] = mapped_column(ForeignKey("gestantes.id"), nullable=False, index=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    motivo_revogacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    gestante: Mapped[Gestante] = relationship(back_populates="consentimentos")

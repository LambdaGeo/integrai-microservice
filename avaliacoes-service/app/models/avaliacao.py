"""
Avaliacoes models.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Avaliacao(Base):
    __tablename__ = "avaliacoes_avaliacao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gestante: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    data_aplicacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
    )
    peso_atual: Mapped[float | None] = mapped_column(Float, nullable=True)
    idade_gestacional: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consultas_prenatal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corrimento_vaginal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    periodontite_carie: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hipertensao_gestacao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    diabetes_gestacao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estresse_gestacao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    historico_familiar_alergia: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consumo_bebidas_adocadas: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consumo_ultraprocessados: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consumo_alcool: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fumante_gestacao: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resultado_integralidade_saude: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status_processamento_llm: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    status_processamento_pills: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    llm_sintese: Mapped[str | None] = mapped_column(Text, nullable=True)

    pilulas: Mapped[list["Pilula"]] = relationship(
        back_populates="avaliacao",
        cascade="all, delete-orphan",
        order_by=lambda: (Pilula.semana_num, Pilula.data_geracao),
    )

    @property
    def top_fatores(self) -> list[str]:
        if not self.resultado_integralidade_saude:
            return []
        return self.resultado_integralidade_saude.get("top_fatores", [])

    @property
    def top_fatores_str(self) -> str:
        return ", ".join(self.top_fatores)


class Pilula(Base):
    __tablename__ = "avaliacoes_pilula"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    avaliacao_id: Mapped[int] = mapped_column(
        ForeignKey("avaliacoes_avaliacao.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    conteudo: Mapped[str | None] = mapped_column(Text, nullable=True)
    semana_num: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_geracao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
    )
    data_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="pendente", nullable=False)

    avaliacao: Mapped[Avaliacao] = relationship(back_populates="pilulas")

    @property
    def data_inicio_envio(self) -> datetime | None:
        if not self.data_geracao or not self.semana_num:
            return None
        return self.data_geracao + timedelta(days=(self.semana_num - 1) * 7)

    @property
    def periodo_envio(self) -> str | None:
        inicio = self.data_inicio_envio
        if not inicio:
            return None
        fim = inicio + timedelta(days=6)
        mes = inicio.strftime("%B").capitalize()
        return f"{inicio.day} a {fim.day} de {mes}"

    @property
    def semana_ord(self) -> str | None:
        if not self.semana_num:
            return None
        return f"{self.semana_num}a"

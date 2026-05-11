"""
Pydantic schemas for Avaliacoes Service.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


STATUS_LLM = ("PENDING", "PROCESSING", "COMPLETED", "FAILED")
STATUS_PILULA = ("aguardando", "pendente", "enviada", "lida")


class AvaliacaoBase(BaseModel):
    gestante: int
    peso_atual: float | None = None
    idade_gestacional: int | None = Field(None, ge=0)
    consultas_prenatal: int | None = Field(None, ge=0)
    corrimento_vaginal: bool = False
    periodontite_carie: bool = False
    hipertensao_gestacao: bool = False
    diabetes_gestacao: bool = False
    estresse_gestacao: bool = False
    historico_familiar_alergia: bool = False
    consumo_bebidas_adocadas: bool = False
    consumo_ultraprocessados: bool = False
    consumo_alcool: bool = False
    fumante_gestacao: bool = False
    resultado_integralidade_saude: dict[str, Any] | None = None
    status_processamento_llm: str = "PENDING"
    status_processamento_pills: str = "PENDING"
    llm_sintese: str | None = None


class AvaliacaoCreate(AvaliacaoBase):
    pass


class AvaliacaoUpdate(BaseModel):
    gestante: int | None = None
    data_aplicacao: datetime | None = None
    peso_atual: float | None = None
    idade_gestacional: int | None = Field(None, ge=0)
    consultas_prenatal: int | None = Field(None, ge=0)
    corrimento_vaginal: bool | None = None
    periodontite_carie: bool | None = None
    hipertensao_gestacao: bool | None = None
    diabetes_gestacao: bool | None = None
    estresse_gestacao: bool | None = None
    historico_familiar_alergia: bool | None = None
    consumo_bebidas_adocadas: bool | None = None
    consumo_ultraprocessados: bool | None = None
    consumo_alcool: bool | None = None
    fumante_gestacao: bool | None = None
    resultado_integralidade_saude: dict[str, Any] | None = None
    status_processamento_llm: str | None = None
    status_processamento_pills: str | None = None
    llm_sintese: str | None = None


class AvaliacaoResponse(AvaliacaoBase):
    id: int
    gestante_nome: str
    data_aplicacao: datetime
    ganho_peso: float | None = None
    top_fatores_str: str = ""

    model_config = ConfigDict(from_attributes=True)


class PilulaBase(BaseModel):
    avaliacao: int = Field(alias="avaliacao_id")
    titulo: str = Field(..., max_length=200)
    conteudo: str | None = None
    semana_num: int | None = Field(None, ge=1)
    data_envio: datetime | None = None
    status: str = "pendente"

    model_config = ConfigDict(populate_by_name=True)


class PilulaCreate(PilulaBase):
    pass


class PilulaUpdate(BaseModel):
    avaliacao: int | None = Field(None, alias="avaliacao_id")
    titulo: str | None = Field(None, max_length=200)
    conteudo: str | None = None
    semana_num: int | None = Field(None, ge=1)
    data_envio: datetime | None = None
    status: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class PilulaResponse(PilulaBase):
    id: int
    avaliacao_gestante: str
    data_geracao: datetime
    semana_ord: str | None = None
    periodo_envio: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

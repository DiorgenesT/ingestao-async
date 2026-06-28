import uuid
from datetime import datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel

from app.models.job import StatusJob


class SubmeterUrlRequest(BaseModel):
    url: AnyHttpUrl
    nome: str


class ResumoDataset(BaseModel):
    linhas: int
    colunas: list[str]
    tamanho_bytes: int
    tempo_processamento_segundos: float
    processado_em: str
    url: str | None = None

    model_config = {"from_attributes": True, "extra": "allow"}


class JobResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    status: StatusJob
    tentativas: int
    erro: str | None
    criado_em: datetime
    atualizado_em: datetime
    nome: str | None = None
    resumo: ResumoDataset | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_job(cls, job: Any) -> "JobResponse":
        resumo = None
        if job.dataset is not None:
            resumo = ResumoDataset.model_validate(job.dataset.resumo)
        nome = job.dataset.nome if job.dataset else job.payload.get("nome")
        return cls(
            id=job.id,
            tipo=job.tipo,
            status=job.status,
            tentativas=job.tentativas,
            erro=job.erro,
            criado_em=job.criado_em,
            atualizado_em=job.atualizado_em,
            nome=nome,
            resumo=resumo,
        )


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str


class ListaJobsResponse(BaseModel):
    items: list[JobResponse]
    total: int

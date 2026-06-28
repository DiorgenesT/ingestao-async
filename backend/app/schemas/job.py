import uuid
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel

from app.models.job import StatusJob


class SubmeterUrlRequest(BaseModel):
    url: AnyHttpUrl
    nome: str


class JobResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    status: StatusJob
    tentativas: int
    erro: str | None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str


class ListaJobsResponse(BaseModel):
    items: list[JobResponse]
    total: int

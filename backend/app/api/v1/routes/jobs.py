import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import usuario_atual
from app.core.config import settings
from app.core.database import get_session_dep
from app.models.user import Usuario
from app.schemas.job import JobResponse, JobSubmitResponse, ListaJobsResponse, SubmeterUrlRequest
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/url", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submeter_url(
    body: SubmeterUrlRequest,
    session: AsyncSession = Depends(get_session_dep),
    usuario: Usuario = Depends(usuario_atual),
) -> JobSubmitResponse:
    job_id = await JobService(session, usuario.id).submeter_url(str(body.url), body.nome)
    return JobSubmitResponse(job_id=job_id, status="pendente")


@router.post("/csv", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submeter_csv(
    arquivo: UploadFile,
    nome: str = Form(...),
    session: AsyncSession = Depends(get_session_dep),
    usuario: Usuario = Depends(usuario_atual),
) -> JobSubmitResponse:
    conteudo = await arquivo.read()
    if len(conteudo) > settings.UPLOAD_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite de {settings.UPLOAD_MAX_BYTES // (1024 * 1024)} MB",
        )
    job_id = await JobService(session, usuario.id).submeter_csv(conteudo, nome)
    return JobSubmitResponse(job_id=job_id, status="pendente")


@router.get("", response_model=ListaJobsResponse)
async def listar_jobs(
    limite: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_session_dep),
    usuario: Usuario = Depends(usuario_atual),
) -> ListaJobsResponse:
    items, total = await JobService(session, usuario.id).listar_jobs(limite, offset)
    return ListaJobsResponse(
        items=[JobResponse.model_validate(j) for j in items],
        total=total,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def buscar_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session_dep),
    usuario: Usuario = Depends(usuario_atual),
) -> JobResponse:
    job = await JobService(session, usuario.id).buscar_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job nao encontrado")
    return JobResponse.model_validate(job)

import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.job import Job
from app.queue.postgres_queue import FilaPostgres


class JobService:
    def __init__(self, session: AsyncSession, usuario_id: uuid.UUID) -> None:
        self._session = session
        self._usuario_id = usuario_id
        self._fila = FilaPostgres(session=session, usuario_id=usuario_id)

    async def submeter_url(self, url: str, nome: str) -> str:
        return await self._fila.enfileirar(
            tipo="url",
            payload={"url": url, "nome": nome},
        )

    async def submeter_csv(self, conteudo: bytes, nome: str) -> str:
        """
        Salva o arquivo em disco e enfileira o caminho.
        Em producao, substituir pelo upload para object storage (S3/R2).
        """
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        nome_arquivo = f"{uuid.uuid4()}.csv"
        caminho = upload_dir / nome_arquivo
        caminho.write_bytes(conteudo)

        return await self._fila.enfileirar(
            tipo="csv",
            payload={"caminho": str(caminho), "nome": nome},
        )

    async def listar_jobs(self, limite: int = 20, offset: int = 0) -> tuple[list[Job], int]:
        stmt = (
            select(Job)
            .where(Job.usuario_id == self._usuario_id)
            .options(selectinload(Job.dataset))
            .order_by(Job.criado_em.desc())
            .limit(limite)
            .offset(offset)
        )
        count_stmt = select(func.count()).select_from(Job).where(Job.usuario_id == self._usuario_id)
        items = list((await self._session.execute(stmt)).scalars().all())
        total: int = (await self._session.execute(count_stmt)).scalar() or 0
        return items, total

    async def deletar_job(self, job_id: uuid.UUID) -> bool:
        stmt = select(Job).where(Job.id == job_id, Job.usuario_id == self._usuario_id)
        job = (await self._session.execute(stmt)).scalar_one_or_none()
        if job is None:
            return False
        await self._session.delete(job)
        return True

    async def buscar_job(self, job_id: uuid.UUID) -> Job | None:
        stmt = (
            select(Job)
            .where(Job.id == job_id, Job.usuario_id == self._usuario_id)
            .options(selectinload(Job.dataset))
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

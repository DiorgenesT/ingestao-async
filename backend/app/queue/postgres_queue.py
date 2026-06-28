import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.job import Job, StatusJob
from app.queue.interface import FilaInterface, MensagemFila


class FilaPostgres(FilaInterface):
    """
    Implementacao de fila robusta sobre Postgres.

    Usa SELECT ... FOR UPDATE SKIP LOCKED para garantir que dois workers
    nunca processem o mesmo job simultaneamente, sem locks de aplicacao
    ou infra adicional.

    Para migrar para AWS SQS: substituir por FilaSQS que implementa
    FilaInterface. Nenhum codigo de negocio ou do worker precisa mudar.
    """

    def __init__(self, session: AsyncSession, usuario_id: uuid.UUID | None = None) -> None:
        self._session = session
        self._usuario_id = usuario_id or uuid.uuid4()

    async def enfileirar(self, tipo: str, payload: dict[str, Any]) -> str:
        job = Job(
            tipo=tipo,
            payload=payload,
            status=StatusJob.PENDENTE,
            tentativas=0,
            max_tentativas=settings.JOB_MAX_TENTATIVAS,
            usuario_id=self._usuario_id,
        )
        self._session.add(job)
        await self._session.flush()
        return str(job.id)

    async def receber(self, limite: int = 1) -> list[MensagemFila]:
        agora = datetime.now(UTC)
        visibility_ate = agora + timedelta(seconds=settings.JOB_VISIBILITY_TIMEOUT_SEGUNDOS)

        # SKIP LOCKED garante que workers concorrentes nunca peguem o mesmo job.
        # locked_until permite reprocessamento automatico se o worker morrer.
        stmt = (
            select(Job)
            .where(
                Job.status.in_([StatusJob.PENDENTE, StatusJob.FALHOU]),
                (Job.locked_until.is_(None)) | (Job.locked_until <= agora),
            )
            .order_by(Job.criado_em)
            .limit(limite)
            .with_for_update(skip_locked=True)
        )
        resultado = await self._session.execute(stmt)
        jobs = list(resultado.scalars().all())

        mensagens: list[MensagemFila] = []
        for job in jobs:
            job.status = StatusJob.PROCESSANDO
            job.locked_until = visibility_ate
            mensagens.append(
                MensagemFila(
                    id=str(job.id),
                    tipo=job.tipo,
                    payload=job.payload,
                    tentativas=job.tentativas,
                    recibo=str(job.id),
                )
            )
        await self._session.flush()
        return mensagens

    async def confirmar(self, recibo: str) -> None:
        """Equivalente ao DeleteMessage do SQS."""
        await self._session.execute(
            update(Job)
            .where(Job.id == uuid.UUID(recibo))
            .values(
                status=StatusJob.CONCLUIDO,
                locked_until=None,
                atualizado_em=datetime.now(UTC),
            )
        )

    async def rejeitar(self, recibo: str, erro: str) -> None:
        """
        Registra falha com backoff exponencial.
        Nao chamar DeleteMessage no SQS equivale a deixar a mensagem
        retornar automaticamente apos o VisibilityTimeout.
        """
        stmt = select(Job).where(Job.id == uuid.UUID(recibo)).with_for_update()
        resultado = await self._session.execute(stmt)
        job = resultado.scalar_one()

        job.tentativas += 1
        job.erro = erro
        job.atualizado_em = datetime.now(UTC)

        if job.tentativas >= job.max_tentativas:
            job.status = StatusJob.MORTO
            job.locked_until = None
        else:
            # Backoff exponencial: 60s, 120s, 240s, ...
            espera = settings.JOB_BACKOFF_BASE_SEGUNDOS * (2 ** (job.tentativas - 1))
            job.status = StatusJob.FALHOU
            job.locked_until = datetime.now(UTC) + timedelta(seconds=espera)

        await self._session.flush()

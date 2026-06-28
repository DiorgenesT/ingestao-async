"""
Testes de integracao da FilaPostgres.
Requerem banco de dados real (postgres rodando em localhost:5432).

Cada operacao usa sua propria sessao que commita ao sair do bloco.
Isso espelha o uso real: uma sessao por request, operacoes autonomas.
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.core.database import get_session
from app.core.security import gerar_hash_senha
from app.models.job import Job, StatusJob
from app.models.user import Usuario
from app.queue.interface import FilaInterface, MensagemFila
from app.queue.postgres_queue import FilaPostgres

pytestmark = pytest.mark.usefixtures("banco_de_teste")


@pytest.fixture(scope="module")
async def usuario_id() -> uuid.UUID:
    """Cria um usuario no banco uma vez por modulo para os testes de fila."""
    uid = uuid.uuid4()
    async with get_session() as session:
        session.add(
            Usuario(
                id=uid,
                email=f"fila-{uid}@test.com",
                hash_senha=gerar_hash_senha("senha123"),
            )
        )
    return uid


async def _enfileirar(uid: uuid.UUID, tipo: str, payload: dict) -> str:  # type: ignore[type-arg]
    async with get_session() as session:
        return await FilaPostgres(session, uid).enfileirar(tipo, payload)


async def _receber(uid: uuid.UUID, limite: int = 1) -> list[MensagemFila]:
    async with get_session() as session:
        return await FilaPostgres(session, uid).receber(limite)


async def _confirmar(uid: uuid.UUID, recibo: str) -> None:
    async with get_session() as session:
        await FilaPostgres(session, uid).confirmar(recibo)


async def _rejeitar(uid: uuid.UUID, recibo: str, erro: str) -> None:
    async with get_session() as session:
        await FilaPostgres(session, uid).rejeitar(recibo, erro)


async def _buscar_job(job_id: str) -> Job | None:
    async with get_session() as session:
        return await session.get(Job, uuid.UUID(job_id))


# ---------------------------------------------------------------------------
# Testes de contrato de interface
# ---------------------------------------------------------------------------


def test_fila_postgres_implementa_interface() -> None:
    assert issubclass(FilaPostgres, FilaInterface)


def test_mensagem_fila_tem_campos_obrigatorios() -> None:
    msg = MensagemFila(
        id=str(uuid.uuid4()),
        tipo="csv",
        payload={"arquivo": "dados.csv"},
        tentativas=0,
    )
    assert msg.tipo == "csv"
    assert msg.tentativas == 0
    assert msg.recibo == ""


# ---------------------------------------------------------------------------
# Testes de comportamento
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enfileirar_cria_job_pendente(usuario_id: uuid.UUID) -> None:
    job_id = await _enfileirar(usuario_id, "csv", {"arquivo": "dados.csv"})

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status == StatusJob.PENDENTE
    assert job.payload == {"arquivo": "dados.csv"}
    assert job.tentativas == 0

    # limpeza: confirmar para nao poluir outros testes
    msgs = await _receber(usuario_id)
    target = next((m for m in msgs if m.id == job_id), None)
    if target:
        await _confirmar(usuario_id, target.recibo)


@pytest.mark.asyncio
async def test_receber_aplica_visibility_timeout_e_muda_status(
    usuario_id: uuid.UUID,
) -> None:
    job_id = await _enfileirar(usuario_id, "csv", {"seq": 1})
    msgs = await _receber(usuario_id)
    target = next(m for m in msgs if m.id == job_id)

    assert target.tipo == "csv"
    assert target.recibo != ""

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status == StatusJob.PROCESSANDO
    assert job.locked_until is not None
    assert job.locked_until > datetime.now(timezone.utc)

    # limpeza
    await _confirmar(usuario_id, target.recibo)


@pytest.mark.asyncio
async def test_confirmar_marca_job_como_concluido(usuario_id: uuid.UUID) -> None:
    job_id = await _enfileirar(usuario_id, "csv", {})
    msgs = await _receber(usuario_id)
    target = next(m for m in msgs if m.id == job_id)

    await _confirmar(usuario_id, target.recibo)

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status == StatusJob.CONCLUIDO
    assert job.locked_until is None


@pytest.mark.asyncio
async def test_rejeitar_incrementa_tentativas_e_aplica_backoff(
    usuario_id: uuid.UUID,
) -> None:
    job_id = await _enfileirar(usuario_id, "csv", {})
    msgs = await _receber(usuario_id)
    target = next(m for m in msgs if m.id == job_id)

    await _rejeitar(usuario_id, target.recibo, "timeout ao processar")

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.tentativas == 1
    assert job.status == StatusJob.FALHOU
    assert job.erro == "timeout ao processar"
    assert job.locked_until is not None
    assert job.locked_until > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_rejeitar_apos_max_tentativas_envia_para_dead_letter(
    usuario_id: uuid.UUID,
) -> None:
    job_id = await _enfileirar(usuario_id, "csv", {})

    # Simula tentativas ja realizadas diretamente no banco
    async with get_session() as session:
        job = await session.get(Job, uuid.UUID(job_id))
        assert job is not None
        job.tentativas = job.max_tentativas - 1

    msgs = await _receber(usuario_id)
    target = next(m for m in msgs if m.id == job_id)
    await _rejeitar(usuario_id, target.recibo, "falha final")

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status == StatusJob.MORTO
    assert job.locked_until is None


@pytest.mark.asyncio
async def test_job_com_backoff_nao_aparece_antes_do_timeout(
    usuario_id: uuid.UUID,
) -> None:
    """Job rejeitado com backoff nao deve ser reprocessado imediatamente."""
    job_id = await _enfileirar(usuario_id, "csv", {})
    msgs = await _receber(usuario_id)
    target = next(m for m in msgs if m.id == job_id)
    await _rejeitar(usuario_id, target.recibo, "falha temporaria")

    # Tentativa imediata de receber: job em backoff nao deve aparecer
    msgs2 = await _receber(usuario_id, limite=20)
    ids = [m.id for m in msgs2]
    assert job_id not in ids, "Job em backoff foi reprocessado antes do timeout"


@pytest.mark.asyncio
async def test_skip_locked_dois_workers_nao_pegam_o_mesmo_job(
    usuario_id: uuid.UUID,
) -> None:
    """
    Dois workers concorrentes devem pegar jobs distintos.
    SELECT FOR UPDATE SKIP LOCKED e o mecanismo que garante isso
    sem lock de aplicacao ou infra adicional.
    """
    id1 = await _enfileirar(usuario_id, "csv", {"w": 1})
    id2 = await _enfileirar(usuario_id, "csv", {"w": 2})

    # Duas sessoes abertas simultaneamente: cada uma pega um job diferente
    async with get_session() as s1:
        async with get_session() as s2:
            f1 = FilaPostgres(session=s1, usuario_id=usuario_id)
            f2 = FilaPostgres(session=s2, usuario_id=usuario_id)
            msgs1 = await f1.receber(limite=1)
            msgs2 = await f2.receber(limite=1)

            ids_recebidos = {m.id for m in msgs1} | {m.id for m in msgs2}

    assert id1 in ids_recebidos
    assert id2 in ids_recebidos
    assert len(ids_recebidos) == 2, "Workers pegaram o mesmo job (corrida de dados)"

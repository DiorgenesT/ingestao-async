"""
Testes de integracao do worker.
Requerem banco de dados real.
"""

import uuid
from pathlib import Path
from typing import Any

import pytest
import respx
from httpx import Response
from sqlalchemy import select, update

from app.core.database import get_session
from app.core.security import gerar_hash_senha
from app.models.dataset import Dataset
from app.models.job import Job, StatusJob
from app.models.user import Usuario
from app.queue.postgres_queue import FilaPostgres
from app.worker.main import processar_uma_vez

pytestmark = pytest.mark.usefixtures("banco_de_teste")


@pytest.fixture(autouse=True, scope="module")
async def limpar_jobs_pendentes() -> None:
    async with get_session() as session:
        await session.execute(
            update(Job)
            .where(Job.status.in_([StatusJob.PENDENTE, StatusJob.FALHOU, StatusJob.PROCESSANDO]))
            .values(status=StatusJob.MORTO)
        )


@pytest.fixture(scope="module")
async def usuario_id() -> uuid.UUID:
    uid = uuid.uuid4()
    async with get_session() as session:
        session.add(
            Usuario(
                id=uid,
                email=f"worker-{uid}@test.com",
                hash_senha=gerar_hash_senha("senha123"),
            )
        )
    return uid


async def _enfileirar(uid: uuid.UUID, tipo: str, payload: dict[str, Any]) -> str:
    async with get_session() as session:
        return await FilaPostgres(session, uid).enfileirar(tipo, payload)


async def _buscar_job(job_id: str) -> Job | None:
    async with get_session() as session:
        return await session.get(Job, uuid.UUID(job_id))


async def _buscar_dataset(job_id: str) -> Dataset | None:
    async with get_session() as session:
        result = await session.execute(select(Dataset).where(Dataset.job_id == uuid.UUID(job_id)))
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_processa_job_csv_com_sucesso(usuario_id: uuid.UUID, tmp_path: Path) -> None:
    csv_file = tmp_path / "dados.csv"
    csv_file.write_text("nome,valor\nalfa,10\nbeta,20\n")

    job_id = await _enfileirar(
        usuario_id,
        "csv",
        {"caminho": str(csv_file), "nome": "Dataset CSV"},
    )

    processados = await processar_uma_vez()
    assert processados >= 1

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status == StatusJob.CONCLUIDO

    dataset = await _buscar_dataset(job_id)
    assert dataset is not None
    assert dataset.resumo["linhas"] == 2
    assert "nome" in dataset.resumo["colunas"]


@pytest.mark.asyncio
@respx.mock
async def test_worker_processa_job_url_com_sucesso(usuario_id: uuid.UUID) -> None:
    csv_content = "produto,preco\ncafe,5.0\npao,3.5\n"
    url = "http://dados-test.gov.br/dataset.csv"
    respx.get(url).mock(return_value=Response(200, text=csv_content))

    job_id = await _enfileirar(
        usuario_id,
        "url",
        {"url": url, "nome": "Dataset URL"},
    )

    processados = await processar_uma_vez()
    assert processados >= 1

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status == StatusJob.CONCLUIDO

    dataset = await _buscar_dataset(job_id)
    assert dataset is not None
    assert dataset.resumo["linhas"] == 2
    assert "produto" in dataset.resumo["colunas"]


@pytest.mark.asyncio
@respx.mock
async def test_worker_rejeita_job_url_com_erro_http(usuario_id: uuid.UUID) -> None:
    url = "http://servidor-404.test/dados.csv"
    respx.get(url).mock(return_value=Response(404))

    job_id = await _enfileirar(
        usuario_id,
        "url",
        {"url": url, "nome": "Dataset Invalido"},
    )

    await processar_uma_vez()

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status in (StatusJob.FALHOU, StatusJob.MORTO)
    assert job.erro is not None


@pytest.mark.asyncio
async def test_worker_rejeita_tipo_desconhecido(usuario_id: uuid.UUID) -> None:
    job_id = await _enfileirar(
        usuario_id,
        "xml",
        {"arquivo": "dados.xml"},
    )

    await processar_uma_vez()

    job = await _buscar_job(job_id)
    assert job is not None
    assert job.status in (StatusJob.FALHOU, StatusJob.MORTO)
    assert job.erro is not None

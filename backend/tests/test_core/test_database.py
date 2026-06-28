import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import NullPool

from app.core.database import engine, get_session

pytestmark = pytest.mark.usefixtures("banco_de_teste")


def test_engine_usa_nullpool() -> None:
    assert isinstance(engine.pool, NullPool)


@pytest.mark.asyncio
async def test_sessao_conecta_e_executa_query() -> None:
    async with get_session() as session:
        assert isinstance(session, AsyncSession)
        resultado = await session.execute(text("SELECT 1 AS valor"))
        assert resultado.scalar() == 1


@pytest.mark.asyncio
async def test_sessao_faz_rollback_em_excecao() -> None:
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
            raise RuntimeError("falha simulada")
    except RuntimeError:
        pass
    # Confirma que consegue abrir nova sessao apos rollback
    async with get_session() as session:
        resultado = await session.execute(text("SELECT 2 AS valor"))
        assert resultado.scalar() == 2

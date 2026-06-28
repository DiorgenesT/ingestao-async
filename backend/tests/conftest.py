import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Variáveis de ambiente devem ser definidas ANTES de qualquer import da app,
# pois config.py cria o objeto settings no momento do import.
_test_db_url = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/ingestao_async_test",
)
os.environ.setdefault("DATABASE_URL", _test_db_url)
os.environ.setdefault("SECRET_KEY", "chave-de-teste-com-pelo-menos-32-caracteres-ok")
os.environ.setdefault("ENVIRONMENT", "test")

from app.models import Base  # noqa: E402 - deve vir apos os setdefault acima

_test_engine = create_async_engine(_test_db_url, poolclass=NullPool, echo=False)
_TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
async def banco_de_teste() -> None:
    """
    Cria as tabelas no banco de teste uma vez por sessao.
    Use este fixture em testes que precisam do banco via:
        pytestmark = pytest.mark.usefixtures("banco_de_teste")
    """
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield  # type: ignore[misc]
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()

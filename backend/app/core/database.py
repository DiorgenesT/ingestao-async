from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# NullPool obrigatorio: o pool e gerenciado pelo Supavisor (porta 6543).
# Criar pool proprio aqui causaria esgotamento de conexoes no free tier do Supabase.
# prepared_statement_cache_size=0 obrigatorio: Supavisor em modo transaction
# nao suporta prepared statements (erro DuplicatePreparedStatementError).
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=settings.ENVIRONMENT == "development",
    connect_args={"statement_cache_size": 0},
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session_dep() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI para injecao de sessao via Depends()."""
    async with get_session() as session:
        yield session

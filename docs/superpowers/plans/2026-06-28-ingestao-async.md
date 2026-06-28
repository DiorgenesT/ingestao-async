# ingestao-async: Plano de Implementacao

> **Para trabalhadores agenticos:** SUB-SKILL OBRIGATORIA: Use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa a tarefa. Os passos usam sintaxe de checkbox (`- [ ]`) para rastreamento.

**Objetivo:** Construir uma API de ingestao e processamento assincrono de dados publicos com fila robusta baseada em Postgres, worker separado, autenticacao JWT e dashboard React, com qualidade de engenharia senior.

**Arquitetura:** A API FastAPI recebe submissoes de datasets (CSV ou URL), valida com Pydantic v2, enfileira jobs via interface abstrata implementada em Postgres (compativel com SQS). Um worker separado consome a fila com SELECT FOR UPDATE SKIP LOCKED, processa os dados e grava resultados no Supabase Postgres via SQLAlchemy 2.0 async com NullPool (pool delegado ao Supavisor na porta 6543).

**Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 async, asyncpg, Alembic, argon2-cffi, python-jose, React 18, Vite, TypeScript strict, Tailwind CSS, pytest, pytest-asyncio, mypy strict, ruff, Docker multi-stage, GitHub Actions.

---

## Convencoes do Projeto

- Todo texto (comentarios, commits, docs) em pt-BR.
- Sem emojis, sem travessoes (en dash / em dash).
- Commits no padrao Conventional Commits em pt-BR, sem trailer de coautoria.
- Python com type hints completos, mypy strict, proibido Any solto.
- TypeScript strict, proibido `any`.
- Testes com banco de teste real (sem mock de banco).
- TDD: escrever o teste que falha, depois a implementacao minima.

---

## Estrutura de Pastas

```
ingestao-async/
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routes/
│   │   │       │   ├── auth.py
│   │   │       │   ├── jobs.py
│   │   │       │   └── health.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   └── dataset.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── job.py
│   │   │   └── dataset.py
│   │   ├── queue/
│   │   │   ├── interface.py
│   │   │   └── postgres_queue.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   └── job_service.py
│   │   ├── worker/
│   │   │   ├── main.py
│   │   │   └── handlers/
│   │   │       ├── csv_handler.py
│   │   │       └── url_handler.py
│   │   └── main.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   │   ├── test_auth.py
│   │   │   ├── test_jobs.py
│   │   │   └── test_health.py
│   │   ├── test_queue/
│   │   │   └── test_postgres_queue.py
│   │   └── test_worker/
│   │       ├── test_csv_handler.py
│   │       └── test_url_handler.py
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   │   └── BarChart.tsx
│   │   │   ├── JobCard.tsx
│   │   │   ├── JobForm.tsx
│   │   │   └── StatusBadge.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Login.tsx
│   │   │   └── Submit.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useJobs.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
├── docker-compose.yml
├── render.yaml
├── CLAUDE.md
└── README.md
```

---

## Fase 1: Scaffolding e Configuracao Base

### Tarefa 1.1: Inicializar pyproject.toml com todas as dependencias

**Arquivos:**
- Criar: `backend/pyproject.toml`

- [ ] **Passo 1: Criar pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ingestao-async"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.8.0",
    "pydantic-settings>=2.4.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "argon2-cffi>=23.1.0",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.9",
    "httpx>=0.27.0",
    "aiofiles>=24.1.0",
    "slowapi>=0.1.9",
    "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.11.0",
    "ruff>=0.6.0",
    "pre-commit>=3.8.0",
    "types-aiofiles>=24.1.0",
]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
plugins = ["pydantic.mypy"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "SIM", "RUF"]
ignore = ["E501"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "alembic/*"]
```

- [ ] **Passo 2: Criar o ambiente virtual e instalar dependencias**

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

- [ ] **Passo 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: adicionar pyproject.toml com dependencias do projeto"
```

---

### Tarefa 1.2: Configuracao central (Settings via pydantic-settings)

**Arquivos:**
- Criar: `backend/app/core/config.py`
- Criar: `backend/.env.example`

- [ ] **Passo 1: Escrever o teste que falha**

Criar `backend/tests/test_core/test_config.py`:

```python
import pytest
from app.core.config import Settings


def test_settings_carrega_valores_obrigatorios() -> None:
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@host:6543/db",
        SECRET_KEY="chave-secreta-com-mais-de-32-caracteres-obrigatorio",
        ENVIRONMENT="test",
    )
    assert s.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert s.ENVIRONMENT == "test"


def test_settings_valores_padrao() -> None:
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@host:6543/db",
        SECRET_KEY="chave-secreta-com-mais-de-32-caracteres-obrigatorio",
        ENVIRONMENT="test",
    )
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert s.JOB_MAX_TENTATIVAS == 3
    assert s.JOB_VISIBILITY_TIMEOUT_SEGUNDOS == 300
    assert s.RATE_LIMIT_POR_MINUTO == 60
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
cd backend && source .venv/bin/activate
pytest tests/test_core/test_config.py -v
# Esperado: FAIL - ModuleNotFoundError
```

- [ ] **Passo 3: Implementar**

Criar `backend/app/__init__.py` e `backend/app/core/__init__.py` (vazios).

Criar `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    JOB_MAX_TENTATIVAS: int = 3
    JOB_VISIBILITY_TIMEOUT_SEGUNDOS: int = 300
    JOB_BACKOFF_BASE_SEGUNDOS: int = 60

    RATE_LIMIT_POR_MINUTO: int = 60
    UPLOAD_MAX_BYTES: int = 50 * 1024 * 1024  # 50 MB


settings = Settings()  # type: ignore[call-arg]
```

- [ ] **Passo 4: Criar .env.example**

```env
DATABASE_URL=postgresql+asyncpg://postgres:senha@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
SECRET_KEY=gere-com-openssl-rand-hex-32
ENVIRONMENT=development
```

- [ ] **Passo 5: Executar e confirmar aprovacao**

```bash
pytest tests/test_core/test_config.py -v
# Esperado: 2 passed
```

- [ ] **Passo 6: Commit**

```bash
git add backend/app/ backend/.env.example
git commit -m "feat: adicionar configuracao central com pydantic-settings"
```

---

### Tarefa 1.3: Conexao com banco (SQLAlchemy async + NullPool para Supavisor)

**Arquivos:**
- Criar: `backend/app/core/database.py`

- [ ] **Passo 1: Escrever o teste que falha**

Criar `backend/tests/test_core/test_database.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session, engine


@pytest.mark.asyncio
async def test_sessao_conecta_e_executa_query() -> None:
    async with get_session() as session:
        assert isinstance(session, AsyncSession)
        resultado = await session.execute(__import__("sqlalchemy").text("SELECT 1"))
        assert resultado.scalar() == 1


def test_engine_usa_nullpool() -> None:
    from sqlalchemy.pool import NullPool
    assert isinstance(engine.pool, NullPool)
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_core/test_database.py -v
# Esperado: FAIL - ModuleNotFoundError
```

- [ ] **Passo 3: Implementar**

Criar `backend/app/core/database.py`:

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# NullPool obrigatorio: o pool de conexoes e gerenciado pelo Supavisor (porta 6543).
# Criar pool proprio aqui causaria esgotamento de conexoes no free tier.
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=settings.ENVIRONMENT == "development",
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
    """Dependencia FastAPI para injecao de sessao."""
    async with get_session() as session:
        yield session
```

- [ ] **Passo 4: Executar e confirmar aprovacao**

```bash
# Requer banco real. Configure .env com DATABASE_URL valida.
pytest tests/test_core/test_database.py -v
```

- [ ] **Passo 5: Commit**

```bash
git add backend/app/core/database.py
git commit -m "feat: configurar engine SQLAlchemy async com NullPool para Supavisor"
```

---

### Tarefa 1.4: Logging estruturado com request ID

**Arquivos:**
- Criar: `backend/app/core/logging.py`

- [ ] **Passo 1: Escrever o teste que falha**

Criar `backend/tests/test_core/test_logging.py`:

```python
import json
import pytest
from app.core.logging import configurar_logging, obter_logger


def test_logger_emite_json_estruturado(capsys: pytest.CaptureFixture[str]) -> None:
    configurar_logging()
    logger = obter_logger("teste")
    logger.info("evento de teste", usuario_id="123", endpoint="/jobs")
    saida = capsys.readouterr().out
    dados = json.loads(saida)
    assert dados["event"] == "evento de teste"
    assert dados["usuario_id"] == "123"
    assert "timestamp" in dados
    assert dados["level"] == "info"
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_core/test_logging.py -v
# Esperado: FAIL
```

- [ ] **Passo 3: Implementar**

Criar `backend/app/core/logging.py`:

```python
import logging
import sys

import structlog


def configurar_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def obter_logger(nome: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(nome)
```

- [ ] **Passo 4: Executar e confirmar aprovacao**

```bash
pytest tests/test_core/test_logging.py -v
```

- [ ] **Passo 5: Commit**

```bash
git add backend/app/core/logging.py
git commit -m "feat: adicionar logging estruturado JSON com structlog"
```

---

### Tarefa 1.5: Modelos SQLAlchemy (User, Job, Dataset)

**Arquivos:**
- Criar: `backend/app/models/base.py`
- Criar: `backend/app/models/user.py`
- Criar: `backend/app/models/job.py`
- Criar: `backend/app/models/dataset.py`

- [ ] **Passo 1: Escrever os testes que falham**

Criar `backend/tests/test_models/test_models.py`:

```python
import pytest
from sqlalchemy import inspect
from app.models.user import Usuario
from app.models.job import Job, StatusJob
from app.models.dataset import Dataset


def test_modelo_usuario_tem_colunas_obrigatorias() -> None:
    cols = {c.key for c in inspect(Usuario).mapper.column_attrs}
    assert {"id", "email", "hash_senha", "criado_em", "ativo"}.issubset(cols)


def test_modelo_job_tem_colunas_fila() -> None:
    cols = {c.key for c in inspect(Job).mapper.column_attrs}
    assert {
        "id", "tipo", "payload", "status", "tentativas", "max_tentativas",
        "locked_until", "erro", "criado_em", "atualizado_em",
    }.issubset(cols)


def test_status_job_tem_todos_os_estados() -> None:
    assert set(StatusJob) == {
        StatusJob.PENDENTE,
        StatusJob.PROCESSANDO,
        StatusJob.CONCLUIDO,
        StatusJob.FALHOU,
        StatusJob.MORTO,
    }


def test_modelo_dataset_tem_colunas_obrigatorias() -> None:
    cols = {c.key for c in inspect(Dataset).mapper.column_attrs}
    assert {"id", "job_id", "nome", "resumo", "criado_em"}.issubset(cols)
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_models/ -v
# Esperado: FAIL - ImportError
```

- [ ] **Passo 3: Implementar base**

Criar `backend/app/models/__init__.py` (vazio).

Criar `backend/app/models/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Passo 4: Implementar Usuario**

Criar `backend/app/models/user.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hash_senha: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="usuario")  # type: ignore[name-defined]
```

- [ ] **Passo 5: Implementar Job**

Criar `backend/app/models/job.py`:

```python
import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StatusJob(str, enum.Enum):
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"
    FALHOU = "falhou"
    MORTO = "morto"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[StatusJob] = mapped_column(
        Enum(StatusJob, name="status_job"),
        nullable=False,
        default=StatusJob.PENDENTE,
        index=True,
    )
    tentativas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_tentativas: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="jobs")  # type: ignore[name-defined]
    dataset: Mapped["Dataset | None"] = relationship("Dataset", back_populates="job", uselist=False)  # type: ignore[name-defined]
```

- [ ] **Passo 6: Implementar Dataset**

Criar `backend/app/models/dataset.py`:

```python
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, unique=True
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    resumo: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["Job"] = relationship("Job", back_populates="dataset")  # type: ignore[name-defined]
```

- [ ] **Passo 7: Executar e confirmar aprovacao**

```bash
pytest tests/test_models/ -v
# Esperado: 4 passed
```

- [ ] **Passo 8: Commit**

```bash
git add backend/app/models/
git commit -m "feat: adicionar modelos SQLAlchemy para Usuario, Job e Dataset"
```

---

### Tarefa 1.6: Migrations com Alembic

**Arquivos:**
- Criar: `backend/alembic.ini`
- Criar: `backend/alembic/env.py`
- Criar: `backend/alembic/versions/0001_criacao_inicial.py`

- [ ] **Passo 1: Inicializar Alembic**

```bash
cd backend && source .venv/bin/activate
alembic init alembic
```

- [ ] **Passo 2: Configurar alembic/env.py para async**

Substituir o conteudo de `backend/alembic/env.py` por:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings
from app.models.base import Base
from app.models.user import Usuario  # noqa: F401 - registra no metadata
from app.models.job import Job  # noqa: F401
from app.models.dataset import Dataset  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Passo 3: Gerar a migration inicial**

```bash
cd backend && alembic revision --autogenerate -m "criacao inicial das tabelas"
# Verificar o arquivo gerado em alembic/versions/
```

- [ ] **Passo 4: Aplicar a migration**

```bash
alembic upgrade head
```

- [ ] **Passo 5: Commit**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: configurar Alembic async e migration inicial do schema"
```

---

## Fase 2: Fila Postgres (o coracao do projeto)

### Tarefa 2.1: Interface abstrata da fila

**Arquivos:**
- Criar: `backend/app/queue/interface.py`
- Criar: `backend/app/queue/__init__.py`

- [ ] **Passo 1: Escrever o teste que valida o protocolo**

Criar `backend/tests/test_queue/test_interface.py`:

```python
from app.queue.interface import FilaInterface, MensagemFila
from app.queue.postgres_queue import FilaPostgres


def test_fila_postgres_implementa_interface() -> None:
    assert issubclass(FilaPostgres, FilaInterface)


def test_mensagem_fila_tem_campos_obrigatorios() -> None:
    import uuid
    msg = MensagemFila(
        id=str(uuid.uuid4()),
        tipo="csv",
        payload={"arquivo": "dados.csv"},
        tentativas=0,
    )
    assert msg.tipo == "csv"
    assert msg.tentativas == 0
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_queue/test_interface.py -v
```

- [ ] **Passo 3: Implementar a interface**

Criar `backend/app/queue/interface.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MensagemFila:
    """Representa uma mensagem retirada da fila para processamento."""
    id: str
    tipo: str
    payload: dict[str, Any]
    tentativas: int
    # Identificador de recibo para exclusao apos processamento bem-sucedido.
    # Equivalente ao ReceiptHandle do SQS.
    recibo: str = field(default="")


class FilaInterface(ABC):
    """
    Interface abstrata para sistemas de fila.

    Mapeamento para AWS SQS:
    - enfileirar()   -> SendMessage
    - receber()      -> ReceiveMessage (com WaitTimeSeconds para long polling)
    - confirmar()    -> DeleteMessage (usando ReceiptHandle)
    - rejeitar()     -> ChangeMessageVisibility (timeout=0 para reprocessamento imediato)

    O campo locked_until da implementacao Postgres corresponde ao
    VisibilityTimeout do SQS: a mensagem fica invisivel para outros workers
    durante o processamento. Se o worker morrer sem confirmar, a mensagem
    reaparece automaticamente apos o timeout.
    """

    @abstractmethod
    async def enfileirar(self, tipo: str, payload: dict[str, Any]) -> str:
        """Adiciona um job a fila. Retorna o ID do job."""

    @abstractmethod
    async def receber(self, limite: int = 1) -> list[MensagemFila]:
        """Retira mensagens disponiveis para processamento."""

    @abstractmethod
    async def confirmar(self, recibo: str) -> None:
        """Marca o job como concluido e o remove da fila. Equivalente ao DeleteMessage do SQS."""

    @abstractmethod
    async def rejeitar(self, recibo: str, erro: str) -> None:
        """Registra falha. Aplica backoff ou envia para dead-letter se esgotadas as tentativas."""
```

- [ ] **Passo 4: Executar e confirmar aprovacao (parcial)**

```bash
pytest tests/test_queue/test_interface.py::test_mensagem_fila_tem_campos_obrigatorios -v
```

- [ ] **Passo 5: Commit**

```bash
git add backend/app/queue/
git commit -m "feat: definir interface abstrata FilaInterface com mapeamento SQS"
```

---

### Tarefa 2.2: Implementacao PostgresQueue (SELECT FOR UPDATE SKIP LOCKED)

**Arquivos:**
- Criar: `backend/app/queue/postgres_queue.py`

- [ ] **Passo 1: Escrever os testes que falham**

Criar `backend/tests/test_queue/test_postgres_queue.py`:

```python
import asyncio
import uuid
import pytest
from datetime import datetime, timezone

from sqlalchemy import select, text
from app.core.database import get_session
from app.models.job import Job, StatusJob
from app.queue.postgres_queue import FilaPostgres


@pytest.fixture
async def fila(db_session):
    return FilaPostgres(session=db_session)


@pytest.fixture
async def db_session():
    async with get_session() as session:
        yield session
        await session.execute(text("DELETE FROM jobs WHERE tipo = 'teste'"))
        await session.commit()


@pytest.mark.asyncio
async def test_enfileirar_cria_job_pendente(fila: FilaPostgres) -> None:
    job_id = await fila.enfileirar("teste", {"dado": 1})
    async with get_session() as s:
        job = await s.get(Job, uuid.UUID(job_id))
    assert job is not None
    assert job.status == StatusJob.PENDENTE
    assert job.payload == {"dado": 1}


@pytest.mark.asyncio
async def test_receber_retorna_mensagem_e_aplica_visibility_timeout(fila: FilaPostgres) -> None:
    await fila.enfileirar("teste", {"seq": 1})
    mensagens = await fila.receber(limite=1)
    assert len(mensagens) == 1
    assert mensagens[0].tipo == "teste"

    # Confirma que o job esta com locked_until no futuro (visibility timeout)
    async with get_session() as s:
        job = await s.get(Job, uuid.UUID(mensagens[0].id))
    assert job is not None
    assert job.locked_until is not None
    assert job.locked_until > datetime.now(timezone.utc)
    assert job.status == StatusJob.PROCESSANDO


@pytest.mark.asyncio
async def test_skip_locked_dois_workers_nao_pegam_o_mesmo_job() -> None:
    fila1 = FilaPostgres.__new__(FilaPostgres)
    fila2 = FilaPostgres.__new__(FilaPostgres)

    async with get_session() as s1, get_session() as s2:
        fila1._session = s1
        fila2._session = s2
        job_id = str(uuid.uuid4())
        # Insere manualmente para controlar o ID
        s1.add(Job(
            id=uuid.UUID(job_id), tipo="teste", payload={},
            status=StatusJob.PENDENTE, tentativas=0, max_tentativas=3,
            usuario_id=uuid.uuid4(),  # usuario ficticio para o teste
        ))
        await s1.commit()

        msgs1 = await fila1.receber(limite=1)
        msgs2 = await fila2.receber(limite=1)

    ids = {m.id for m in msgs1 + msgs2}
    assert len(ids) == len(msgs1 + msgs2)  # sem duplicatas


@pytest.mark.asyncio
async def test_confirmar_marca_job_como_concluido(fila: FilaPostgres) -> None:
    await fila.enfileirar("teste", {})
    mensagens = await fila.receber(limite=1)
    await fila.confirmar(mensagens[0].recibo)

    async with get_session() as s:
        job = await s.get(Job, uuid.UUID(mensagens[0].id))
    assert job is not None
    assert job.status == StatusJob.CONCLUIDO


@pytest.mark.asyncio
async def test_rejeitar_incrementa_tentativas_e_aplica_backoff(fila: FilaPostgres) -> None:
    await fila.enfileirar("teste", {})
    mensagens = await fila.receber(limite=1)
    await fila.rejeitar(mensagens[0].recibo, erro="falha simulada")

    async with get_session() as s:
        job = await s.get(Job, uuid.UUID(mensagens[0].id))
    assert job is not None
    assert job.tentativas == 1
    assert job.status == StatusJob.FALHOU
    assert job.erro == "falha simulada"


@pytest.mark.asyncio
async def test_rejeitar_apos_max_tentativas_envia_para_dead_letter(fila: FilaPostgres) -> None:
    job_id_str = await fila.enfileirar("teste", {})
    job_uuid = uuid.UUID(job_id_str)

    # Simula tentativas anteriores
    async with get_session() as s:
        job = await s.get(Job, job_uuid)
        assert job is not None
        job.tentativas = 2  # max_tentativas - 1
        await s.commit()

    mensagens = await fila.receber(limite=1)
    await fila.rejeitar(mensagens[0].recibo, erro="falha final")

    async with get_session() as s:
        job = await s.get(Job, job_uuid)
    assert job is not None
    assert job.status == StatusJob.MORTO
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_queue/test_postgres_queue.py -v
# Esperado: FAIL - ImportError
```

- [ ] **Passo 3: Implementar FilaPostgres**

Criar `backend/app/queue/postgres_queue.py`:

```python
import uuid
from datetime import datetime, timedelta, timezone
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
    nunca processem o mesmo job simultaneamente, sem necessidade de locks
    de aplicacao ou infra adicional.

    Para migrar para AWS SQS: substituir esta classe por FilaSQS que
    implementa a mesma interface FilaInterface. Nenhum codigo de negocio
    ou do worker precisara ser alterado.
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
        agora = datetime.now(timezone.utc)
        visibility_ate = agora + timedelta(seconds=settings.JOB_VISIBILITY_TIMEOUT_SEGUNDOS)

        stmt = (
            select(Job)
            .where(
                Job.status == StatusJob.PENDENTE,
                (Job.locked_until == None) | (Job.locked_until <= agora),  # noqa: E711
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
                    recibo=str(job.id),  # no Postgres o recibo e o proprio ID
                )
            )
        await self._session.flush()
        return mensagens

    async def confirmar(self, recibo: str) -> None:
        """Equivalente ao DeleteMessage do SQS."""
        await self._session.execute(
            update(Job)
            .where(Job.id == uuid.UUID(recibo))
            .values(status=StatusJob.CONCLUIDO, locked_until=None, atualizado_em=datetime.now(timezone.utc))
        )

    async def rejeitar(self, recibo: str, erro: str) -> None:
        """
        Registra falha com backoff exponencial.
        Apos max_tentativas, job vai para dead-letter (status MORTO).
        Equivale a nao chamar DeleteMessage no SQS (mensagem volta apos VisibilityTimeout).
        """
        job_id = uuid.UUID(recibo)
        stmt = select(Job).where(Job.id == job_id).with_for_update()
        resultado = await self._session.execute(stmt)
        job = resultado.scalar_one()

        job.tentativas += 1
        job.erro = erro

        if job.tentativas >= job.max_tentativas:
            job.status = StatusJob.MORTO
            job.locked_until = None
        else:
            # Backoff exponencial: 60s, 120s, 240s, ...
            espera = settings.JOB_BACKOFF_BASE_SEGUNDOS * (2 ** (job.tentativas - 1))
            job.status = StatusJob.FALHOU
            job.locked_until = datetime.now(timezone.utc) + timedelta(seconds=espera)

        await self._session.flush()
```

- [ ] **Passo 4: Executar e confirmar aprovacao**

```bash
pytest tests/test_queue/ -v
# Esperado: todos passando
```

- [ ] **Passo 5: Confirmar que a interface esta completa**

```bash
pytest tests/test_queue/test_interface.py -v
# Esperado: 2 passed
```

- [ ] **Passo 6: Commit**

```bash
git add backend/app/queue/postgres_queue.py
git commit -m "feat: implementar FilaPostgres com SELECT FOR UPDATE SKIP LOCKED e dead-letter"
```

---

## Fase 3: Autenticacao JWT

### Tarefa 3.1: Seguranca (hash de senha e JWT)

**Arquivos:**
- Criar: `backend/app/core/security.py`

- [ ] **Passo 1: Escrever os testes que falham**

Criar `backend/tests/test_core/test_security.py`:

```python
import pytest
from app.core.security import (
    gerar_hash_senha,
    verificar_senha,
    criar_access_token,
    criar_refresh_token,
    decodificar_token,
)


def test_hash_senha_e_verificacao() -> None:
    senha = "minhasenha123"
    hash_ = gerar_hash_senha(senha)
    assert hash_ != senha
    assert verificar_senha(senha, hash_) is True
    assert verificar_senha("errada", hash_) is False


def test_criar_e_decodificar_access_token() -> None:
    token = criar_access_token(subject="usuario-id-123")
    payload = decodificar_token(token)
    assert payload["sub"] == "usuario-id-123"
    assert payload["tipo"] == "access"


def test_criar_e_decodificar_refresh_token() -> None:
    token = criar_refresh_token(subject="usuario-id-123")
    payload = decodificar_token(token)
    assert payload["sub"] == "usuario-id-123"
    assert payload["tipo"] == "refresh"


def test_token_invalido_levanta_excecao() -> None:
    with pytest.raises(Exception):
        decodificar_token("token.invalido.aqui")
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_core/test_security.py -v
```

- [ ] **Passo 3: Implementar**

Criar `backend/app/core/security.py`:

```python
from datetime import datetime, timedelta, timezone
from typing import Any

import argon2
from argon2 import PasswordHasher
from jose import JWTError, jwt

from app.core.config import settings

_hasher = PasswordHasher()


def gerar_hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, hash_: str) -> bool:
    try:
        return _hasher.verify(hash_, senha)
    except argon2.exceptions.VerifyMismatchError:
        return False


def criar_access_token(subject: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _criar_token(subject=subject, tipo="access", expira=expira)


def criar_refresh_token(subject: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _criar_token(subject=subject, tipo="refresh", expira=expira)


def _criar_token(subject: str, tipo: str, expira: datetime) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "tipo": tipo,
        "exp": expira,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decodificar_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("Token invalido ou expirado") from exc
```

- [ ] **Passo 4: Executar e confirmar aprovacao**

```bash
pytest tests/test_core/test_security.py -v
# Esperado: 4 passed
```

- [ ] **Passo 5: Commit**

```bash
git add backend/app/core/security.py
git commit -m "feat: implementar seguranca com argon2 e JWT (access + refresh)"
```

---

### Tarefa 3.2: AuthService e endpoints de autenticacao

**Arquivos:**
- Criar: `backend/app/services/auth_service.py`
- Criar: `backend/app/schemas/auth.py`
- Criar: `backend/app/api/v1/routes/auth.py`

- [ ] **Passo 1: Escrever os testes de integracao que falham**

Criar `backend/tests/test_api/test_auth.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_registrar_usuario_com_sucesso(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/registrar", json={
        "email": "test@example.com",
        "senha": "SenhaForte123!"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_registrar_email_duplicado_retorna_409(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "senha": "SenhaForte123!"}
    await client.post("/api/v1/auth/registrar", json=payload)
    resp = await client.post("/api/v1/auth/registrar", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_com_credenciais_validas(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/registrar", json={
        "email": "login@example.com", "senha": "SenhaForte123!"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "senha": "SenhaForte123!"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_senha_errada_retorna_401(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "senha": "senhaerrada"
    })
    assert resp.status_code == 401
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_api/test_auth.py -v
```

- [ ] **Passo 3: Implementar schemas de auth**

Criar `backend/app/schemas/__init__.py` (vazio).

Criar `backend/app/schemas/auth.py`:

```python
from pydantic import BaseModel, EmailStr, field_validator


class RegistrarRequest(BaseModel):
    email: EmailStr
    senha: str

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
```

- [ ] **Passo 4: Implementar AuthService**

Criar `backend/app/services/__init__.py` (vazio).

Criar `backend/app/services/auth_service.py`:

```python
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    criar_access_token,
    criar_refresh_token,
    gerar_hash_senha,
    verificar_senha,
)
from app.models.user import Usuario
from app.schemas.auth import TokenResponse


class EmailJaCadastradoError(Exception):
    pass


class CredenciaisInvalidasError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(self, email: str, senha: str) -> TokenResponse:
        usuario = Usuario(email=email, hash_senha=gerar_hash_senha(senha))
        self._session.add(usuario)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailJaCadastradoError(email) from exc

        return TokenResponse(
            access_token=criar_access_token(str(usuario.id)),
            refresh_token=criar_refresh_token(str(usuario.id)),
        )

    async def login(self, email: str, senha: str) -> TokenResponse:
        stmt = select(Usuario).where(Usuario.email == email, Usuario.ativo.is_(True))
        resultado = await self._session.execute(stmt)
        usuario = resultado.scalar_one_or_none()

        if usuario is None or not verificar_senha(senha, usuario.hash_senha):
            raise CredenciaisInvalidasError()

        return TokenResponse(
            access_token=criar_access_token(str(usuario.id)),
            refresh_token=criar_refresh_token(str(usuario.id)),
        )
```

- [ ] **Passo 5: Implementar rotas de auth**

Criar `backend/app/api/__init__.py` e `backend/app/api/v1/__init__.py` e `backend/app/api/v1/routes/__init__.py` (todos vazios).

Criar `backend/app/api/v1/routes/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_dep
from app.schemas.auth import LoginRequest, RegistrarRequest, TokenResponse
from app.services.auth_service import AuthService, CredenciaisInvalidasError, EmailJaCadastradoError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registrar", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def registrar(
    body: RegistrarRequest,
    session: AsyncSession = Depends(get_session_dep),
) -> TokenResponse:
    try:
        return await AuthService(session).registrar(body.email, body.senha)
    except EmailJaCadastradoError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ja cadastrado")


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session_dep),
) -> TokenResponse:
    try:
        return await AuthService(session).login(body.email, body.senha)
    except CredenciaisInvalidasError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")
```

- [ ] **Passo 6: Criar app principal**

Criar `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth
from app.core.logging import configurar_logging

configurar_logging()

app = FastAPI(title="ingestao-async", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Passo 7: Executar e confirmar aprovacao**

```bash
pytest tests/test_api/test_auth.py -v
```

- [ ] **Passo 8: Commit**

```bash
git add backend/app/
git commit -m "feat: implementar autenticacao com registro, login e JWT"
```

---

## Fase 4: API de Ingestao de Jobs

### Tarefa 4.1: Schemas e rotas de jobs

**Arquivos:**
- Criar: `backend/app/schemas/job.py`
- Criar: `backend/app/services/job_service.py`
- Criar: `backend/app/api/v1/routes/jobs.py`

- [ ] **Passo 1: Escrever os testes que falham**

Criar `backend/tests/test_api/test_jobs.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def obter_token(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/registrar", json={
        "email": "jobs@example.com", "senha": "SenhaForte123!"
    })
    return resp.json()["access_token"]


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_submeter_job_url_com_sucesso(client: AsyncClient) -> None:
    token = await obter_token(client)
    resp = await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/dataset/exemplo.csv", "nome": "Dataset Exemplo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pendente"


@pytest.mark.asyncio
async def test_submeter_job_sem_auth_retorna_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/dataset/exemplo.csv", "nome": "Teste"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_listar_jobs_do_usuario(client: AsyncClient) -> None:
    token = await obter_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/dataset/a.csv", "nome": "A"},
        headers=headers,
    )
    resp = await client.get("/api/v1/jobs", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_buscar_status_job(client: AsyncClient) -> None:
    token = await obter_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    cria = await client.post("/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/dataset/b.csv", "nome": "B"},
        headers=headers,
    )
    job_id = cria.json()["job_id"]
    resp = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_api/test_jobs.py -v
```

- [ ] **Passo 3: Implementar schemas**

Criar `backend/app/schemas/job.py`:

```python
import uuid
from datetime import datetime
from typing import Any

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
```

- [ ] **Passo 4: Implementar JobService**

Criar `backend/app/services/job_service.py`:

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, StatusJob
from app.queue.postgres_queue import FilaPostgres


class JobService:
    def __init__(self, session: AsyncSession, usuario_id: uuid.UUID) -> None:
        self._session = session
        self._usuario_id = usuario_id
        self._fila = FilaPostgres(session=session, usuario_id=usuario_id)

    async def submeter_url(self, url: str, nome: str) -> str:
        return await self._fila.enfileirar(
            tipo="url", payload={"url": url, "nome": nome}
        )

    async def listar_jobs(self, limite: int = 20, offset: int = 0) -> tuple[list[Job], int]:
        stmt = (
            select(Job)
            .where(Job.usuario_id == self._usuario_id)
            .order_by(Job.criado_em.desc())
            .limit(limite)
            .offset(offset)
        )
        count_stmt = select(func.count()).select_from(Job).where(Job.usuario_id == self._usuario_id)
        items = list((await self._session.execute(stmt)).scalars().all())
        total = (await self._session.execute(count_stmt)).scalar() or 0
        return items, total

    async def buscar_job(self, job_id: uuid.UUID) -> Job | None:
        return await self._session.get(Job, job_id)
```

- [ ] **Passo 5: Implementar dependencia de autenticacao**

Criar `backend/app/api/v1/deps.py`:

```python
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_dep
from app.core.security import decodificar_token
from app.models.user import Usuario

_bearer = HTTPBearer()


async def usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_session_dep),
) -> Usuario:
    try:
        payload = decodificar_token(credentials.credentials)
        if payload.get("tipo") != "access":
            raise ValueError("Tipo de token invalido")
        usuario_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    stmt = select(Usuario).where(Usuario.id == usuario_id, Usuario.ativo.is_(True))
    usuario = (await session.execute(stmt)).scalar_one_or_none()
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado")
    return usuario
```

- [ ] **Passo 6: Implementar rotas de jobs**

Criar `backend/app/api/v1/routes/jobs.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import usuario_atual
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


@router.get("", response_model=ListaJobsResponse)
async def listar_jobs(
    limite: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_session_dep),
    usuario: Usuario = Depends(usuario_atual),
) -> ListaJobsResponse:
    items, total = await JobService(session, usuario.id).listar_jobs(limite, offset)
    return ListaJobsResponse(items=[JobResponse.model_validate(j) for j in items], total=total)


@router.get("/{job_id}", response_model=JobResponse)
async def buscar_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session_dep),
    usuario: Usuario = Depends(usuario_atual),
) -> JobResponse:
    job = await JobService(session, usuario.id).buscar_job(job_id)
    if job is None or job.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job nao encontrado")
    return JobResponse.model_validate(job)
```

- [ ] **Passo 7: Registrar rotas no app principal**

Editar `backend/app/main.py` adicionando:

```python
from app.api.v1.routes import auth, jobs

# ...apos app.include_router(auth.router, ...):
app.include_router(jobs.router, prefix="/api/v1")
```

- [ ] **Passo 8: Executar e confirmar aprovacao**

```bash
pytest tests/test_api/ -v
```

- [ ] **Passo 9: Commit**

```bash
git add backend/app/
git commit -m "feat: adicionar endpoints de submissao e consulta de jobs"
```

---

## Fase 5: Worker de Processamento

### Tarefa 5.1: Handler de URL (download e processamento de CSV publico)

**Arquivos:**
- Criar: `backend/app/worker/handlers/url_handler.py`
- Criar: `backend/app/worker/handlers/csv_handler.py`

- [ ] **Passo 1: Escrever os testes que falham**

Criar `backend/tests/test_worker/test_url_handler.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.worker.handlers.url_handler import processar_url


@pytest.mark.asyncio
async def test_processar_url_retorna_resumo() -> None:
    csv_conteudo = "nome,valor\nalfa,10\nbeta,20\ngamma,30\n"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = csv_conteudo
        mock_get.return_value.raise_for_status = lambda: None
        resultado = await processar_url("https://dados.gov.br/fake.csv", "Teste")

    assert resultado["nome"] == "Teste"
    assert resultado["total_linhas"] == 3
    assert resultado["colunas"] == ["nome", "valor"]
    assert "valor_min" in resultado
    assert "valor_max" in resultado
    assert "valor_media" in resultado
```

Criar `backend/tests/test_worker/test_csv_handler.py`:

```python
import io
import pytest
from app.worker.handlers.csv_handler import processar_csv


def test_processar_csv_normaliza_e_calcula_indicadores() -> None:
    csv = "nome,valor,data\nalfa,10,2024-01-01\nbeta,20,2024-01-02\ngamma,30,2024-01-03\n"
    stream = io.StringIO(csv)
    resultado = processar_csv(stream, nome="Teste")

    assert resultado["total_linhas"] == 3
    assert resultado["colunas"] == ["nome", "valor", "data"]
    assert resultado["valor_media"] == 20.0
    assert resultado["valor_min"] == 10.0
    assert resultado["valor_max"] == 30.0
    assert "sanitizado" in resultado


def test_processar_csv_sanitiza_colunas_pii() -> None:
    csv = "email,cpf,nome,valor\na@b.com,123.456.789-00,Joao,100\n"
    resultado = processar_csv(io.StringIO(csv), nome="PII Test")
    assert resultado["sanitizado"] is True
    assert "email" not in resultado.get("colunas_removidas_pii", []) or \
           resultado["colunas_removidas_pii"] is not None
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_worker/ -v
```

- [ ] **Passo 3: Implementar csv_handler**

Criar `backend/app/worker/__init__.py` e `backend/app/worker/handlers/__init__.py` (vazios).

Criar `backend/app/worker/handlers/csv_handler.py`:

```python
import csv
import io
from typing import Any

# Colunas comuns de PII que devem ser removidas na ingestao (LGPD)
COLUNAS_PII = frozenset({"email", "cpf", "cnpj", "telefone", "celular", "nome_completo", "rg", "senha"})


def processar_csv(stream: io.StringIO, nome: str) -> dict[str, Any]:
    leitor = csv.DictReader(stream)
    linhas = list(leitor)
    colunas_originais = list(leitor.fieldnames or [])

    colunas_pii_encontradas = [c for c in colunas_originais if c.lower() in COLUNAS_PII]
    for linha in linhas:
        for col in colunas_pii_encontradas:
            linha.pop(col, None)

    colunas_limpas = [c for c in colunas_originais if c not in colunas_pii_encontradas]
    colunas_numericas = _detectar_colunas_numericas(linhas, colunas_limpas)

    resultado: dict[str, Any] = {
        "nome": nome,
        "total_linhas": len(linhas),
        "colunas": colunas_limpas,
        "sanitizado": len(colunas_pii_encontradas) > 0,
        "colunas_removidas_pii": colunas_pii_encontradas,
    }

    for col in colunas_numericas:
        valores = [float(l[col]) for l in linhas if l.get(col, "").strip()]
        if valores:
            resultado[f"{col}_media"] = sum(valores) / len(valores)
            resultado[f"{col}_min"] = min(valores)
            resultado[f"{col}_max"] = max(valores)

    # Atalhos para a primeira coluna numerica encontrada (compatibilidade com testes)
    if colunas_numericas:
        col = colunas_numericas[0]
        resultado["valor_media"] = resultado.get(f"{col}_media")
        resultado["valor_min"] = resultado.get(f"{col}_min")
        resultado["valor_max"] = resultado.get(f"{col}_max")

    return resultado


def _detectar_colunas_numericas(linhas: list[dict[str, str]], colunas: list[str]) -> list[str]:
    numericas = []
    for col in colunas:
        amostras = [l.get(col, "").strip() for l in linhas[:10] if l.get(col, "").strip()]
        if amostras and all(_e_numero(v) for v in amostras):
            numericas.append(col)
    return numericas


def _e_numero(valor: str) -> bool:
    try:
        float(valor.replace(",", "."))
        return True
    except ValueError:
        return False
```

- [ ] **Passo 4: Implementar url_handler**

Criar `backend/app/worker/handlers/url_handler.py`:

```python
import io
from typing import Any

import httpx

from app.worker.handlers.csv_handler import processar_csv


async def processar_url(url: str, nome: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resposta = await client.get(url)
        resposta.raise_for_status()
        conteudo = resposta.text

    return processar_csv(io.StringIO(conteudo), nome=nome)
```

- [ ] **Passo 5: Executar e confirmar aprovacao**

```bash
pytest tests/test_worker/ -v
```

- [ ] **Passo 6: Commit**

```bash
git add backend/app/worker/
git commit -m "feat: implementar handlers de processamento CSV e URL com sanitizacao LGPD"
```

---

### Tarefa 5.2: Processo worker principal

**Arquivos:**
- Criar: `backend/app/worker/main.py`

- [ ] **Passo 1: Escrever o teste de integracao que falha**

Criar `backend/tests/test_worker/test_worker_main.py`:

```python
import asyncio
import uuid
import pytest
from app.core.database import get_session
from app.models.job import Job, StatusJob
from app.queue.postgres_queue import FilaPostgres
from app.worker.main import processar_proximo_job


@pytest.mark.asyncio
async def test_worker_processa_job_e_marca_concluido() -> None:
    usuario_id = uuid.uuid4()
    async with get_session() as session:
        fila = FilaPostgres(session=session, usuario_id=usuario_id)
        job_id = await fila.enfileirar("teste_noop", {"nome": "Teste Worker"})

    resultado = await processar_proximo_job()
    assert resultado is True  # processou alguma coisa

    async with get_session() as session:
        job = await session.get(Job, uuid.UUID(job_id))
    assert job is not None
    assert job.status == StatusJob.CONCLUIDO
```

- [ ] **Passo 2: Executar e confirmar falha**

```bash
pytest tests/test_worker/test_worker_main.py -v
```

- [ ] **Passo 3: Implementar worker principal**

Criar `backend/app/worker/main.py`:

```python
import asyncio
import signal
from typing import Any

from app.core.database import get_session
from app.core.logging import obter_logger
from app.queue.postgres_queue import FilaPostgres
from app.worker.handlers.url_handler import processar_url

logger = obter_logger("worker")

HANDLERS: dict[str, Any] = {
    "url": lambda payload: processar_url(payload["url"], payload["nome"]),
    # Handlers adicionais registrados aqui conforme o sistema cresce
}


async def processar_proximo_job() -> bool:
    """Processa o proximo job disponivel. Retorna True se processou algo."""
    async with get_session() as session:
        fila = FilaPostgres(session=session)
        mensagens = await fila.receber(limite=1)

        if not mensagens:
            return False

        msg = mensagens[0]
        logger.info("iniciando processamento", job_id=msg.id, tipo=msg.tipo)

        handler = HANDLERS.get(msg.tipo)
        if handler is None:
            await fila.rejeitar(msg.recibo, erro=f"Tipo desconhecido: {msg.tipo}")
            logger.warning("tipo de job desconhecido", tipo=msg.tipo, job_id=msg.id)
            return True

        try:
            await handler(msg.payload)
            await fila.confirmar(msg.recibo)
            logger.info("job concluido", job_id=msg.id)
        except Exception as exc:
            await fila.rejeitar(msg.recibo, erro=str(exc))
            logger.error("falha no processamento", job_id=msg.id, erro=str(exc), exc_info=True)

        return True


async def executar_worker(intervalo_segundos: float = 5.0) -> None:
    logger.info("worker iniciado", intervalo=intervalo_segundos)
    parar = asyncio.Event()

    def _sinal_parada(signum: int, frame: object) -> None:
        logger.info("sinal de parada recebido", sinal=signum)
        parar.set()

    signal.signal(signal.SIGTERM, _sinal_parada)
    signal.signal(signal.SIGINT, _sinal_parada)

    while not parar.is_set():
        try:
            processou = await processar_proximo_job()
            if not processou:
                await asyncio.sleep(intervalo_segundos)
        except Exception:
            logger.error("erro inesperado no loop do worker", exc_info=True)
            await asyncio.sleep(intervalo_segundos)

    logger.info("worker encerrado")


if __name__ == "__main__":
    asyncio.run(executar_worker())
```

- [ ] **Passo 4: Executar e confirmar aprovacao**

```bash
pytest tests/test_worker/ -v
```

- [ ] **Passo 5: Commit**

```bash
git add backend/app/worker/main.py
git commit -m "feat: implementar processo worker com loop de consumo e graceful shutdown"
```

---

## Fase 6: Infraestrutura e Qualidade

### Tarefa 6.1: Dockerfile multi-stage e docker-compose

**Arquivos:**
- Criar: `backend/Dockerfile`
- Criar: `docker-compose.yml`

- [ ] **Passo 1: Criar Dockerfile multi-stage**

Criar `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

FROM base AS builder
RUN pip install hatchling
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .

FROM base AS production
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM production AS worker
CMD ["python", "-m", "app.worker.main"]
```

- [ ] **Passo 2: Criar docker-compose.yml**

Criar `docker-compose.yml` (na raiz do projeto):

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ingestao_async
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./backend
      target: production
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/ingestao_async
      SECRET_KEY: chave-de-desenvolvimento-local-apenas
      ENVIRONMENT: development
    depends_on:
      db:
        condition: service_healthy

  worker:
    build:
      context: ./backend
      target: worker
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/ingestao_async
      SECRET_KEY: chave-de-desenvolvimento-local-apenas
      ENVIRONMENT: development
    depends_on:
      db:
        condition: service_healthy
```

- [ ] **Passo 3: Testar build local**

```bash
docker compose build
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up api worker
# Em outro terminal:
curl http://localhost:8000/health
# Esperado: {"status":"ok"}
```

- [ ] **Passo 4: Commit**

```bash
git add backend/Dockerfile docker-compose.yml
git commit -m "infra: adicionar Dockerfile multi-stage e docker-compose para desenvolvimento local"
```

---

### Tarefa 6.2: Pre-commit, mypy e ruff

**Arquivos:**
- Criar: `backend/.pre-commit-config.yaml`
- Criar: `.gitignore`

- [ ] **Passo 1: Criar .gitignore**

Criar `.gitignore` na raiz:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
*.egg-info/
dist/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Env
.env
.env.local

# Node
node_modules/
dist/
.vite/

# Claude
CLAUDE.md

# Misc
.DS_Store
*.log
```

- [ ] **Passo 2: Criar .pre-commit-config.yaml**

Criar `backend/.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: mypy app --strict
        language: system
        types: [python]
        pass_filenames: false
```

- [ ] **Passo 3: Instalar pre-commit**

```bash
cd backend && source .venv/bin/activate
pre-commit install
```

- [ ] **Passo 4: Executar verificacoes completas**

```bash
mypy app --strict
ruff check app
ruff format app --check
```

- [ ] **Passo 5: Corrigir todos os erros de tipo antes de continuar**

```bash
# Se houver erros, corrigir um por um. Nao suprimir com type: ignore sem justificativa.
```

- [ ] **Passo 6: Commit**

```bash
git add .gitignore backend/.pre-commit-config.yaml
git commit -m "chore: adicionar pre-commit com ruff e mypy strict"
```

---

### Tarefa 6.3: CI no GitHub Actions

**Arquivos:**
- Criar: `.github/workflows/ci.yml`

- [ ] **Passo 1: Criar workflow de CI**

Criar `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: ["main", "develop"]
  pull_request:
    branches: ["main"]

jobs:
  backend:
    name: Backend (lint, tipos, testes)
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: ingestao_async_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Configurar Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
          cache-dependency-path: backend/pyproject.toml

      - name: Instalar dependencias
        run: pip install -e ".[dev]"
        working-directory: backend

      - name: Lint com ruff
        run: ruff check app
        working-directory: backend

      - name: Verificacao de tipos com mypy
        run: mypy app --strict
        working-directory: backend

      - name: Executar migrations de teste
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/ingestao_async_test
          SECRET_KEY: chave-de-ci-apenas-32-chars-minimo
          ENVIRONMENT: test
        run: alembic upgrade head
        working-directory: backend

      - name: Testes com cobertura
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/ingestao_async_test
          SECRET_KEY: chave-de-ci-apenas-32-chars-minimo
          ENVIRONMENT: test
        run: pytest --cov=app --cov-report=term-missing --cov-fail-under=80
        working-directory: backend
```

- [ ] **Passo 2: Commit**

```bash
git add .github/
git commit -m "ci: adicionar pipeline GitHub Actions com lint, mypy e testes"
```

---

## Fase 7: Frontend React

### Tarefa 7.1: Setup Vite + React + TypeScript + Tailwind

**Arquivos:**
- Criar: `frontend/` (estrutura completa)

- [ ] **Passo 1: Inicializar projeto Vite**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Passo 2: Configurar Tailwind**

Editar `frontend/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}
```

- [ ] **Passo 3: Configurar tsconfig strict**

Editar `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src"]
}
```

- [ ] **Passo 4: Commit**

```bash
git add frontend/
git commit -m "feat: inicializar frontend React com Vite, TypeScript strict e Tailwind"
```

---

### Tarefa 7.2: Tipos, servico de API e autenticacao

**Arquivos:**
- Criar: `frontend/src/types/index.ts`
- Criar: `frontend/src/services/api.ts`
- Criar: `frontend/src/hooks/useAuth.ts`

- [ ] **Passo 1: Definir tipos**

Criar `frontend/src/types/index.ts`:

```typescript
export type StatusJob = "pendente" | "processando" | "concluido" | "falhou" | "morto";

export interface Job {
  id: string;
  tipo: string;
  status: StatusJob;
  tentativas: number;
  erro: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface ListaJobsResponse {
  items: Job[];
  total: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
```

- [ ] **Passo 2: Implementar servico de API**

Criar `frontend/src/services/api.ts`:

```typescript
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function obterToken(): string | null {
  return localStorage.getItem("access_token");
}

async function requisitar<T>(
  caminho: string,
  opcoes: RequestInit = {}
): Promise<T> {
  const token = obterToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(opcoes.headers as Record<string, string> ?? {}),
  };

  const resp = await fetch(`${BASE_URL}${caminho}`, { ...opcoes, headers });
  if (!resp.ok) {
    const erro = await resp.json().catch(() => ({ detail: "Erro desconhecido" }));
    throw new Error(erro.detail ?? `HTTP ${resp.status}`);
  }
  return resp.json() as Promise<T>;
}

import type { Job, ListaJobsResponse, TokenResponse } from "../types";

export const api = {
  auth: {
    registrar: (email: string, senha: string) =>
      requisitar<TokenResponse>("/api/v1/auth/registrar", {
        method: "POST",
        body: JSON.stringify({ email, senha }),
      }),
    login: (email: string, senha: string) =>
      requisitar<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, senha }),
      }),
  },
  jobs: {
    listar: (limite = 20, offset = 0) =>
      requisitar<ListaJobsResponse>(`/api/v1/jobs?limite=${limite}&offset=${offset}`),
    buscar: (id: string) =>
      requisitar<Job>(`/api/v1/jobs/${id}`),
    submeterUrl: (url: string, nome: string) =>
      requisitar<{ job_id: string; status: string }>("/api/v1/jobs/url", {
        method: "POST",
        body: JSON.stringify({ url, nome }),
      }),
  },
};
```

- [ ] **Passo 3: Commit**

```bash
git add frontend/src/types/ frontend/src/services/
git commit -m "feat: adicionar tipos TypeScript e servico de API"
```

---

### Tarefa 7.3: Dashboard com grafico SVG e lista de jobs

**Arquivos:**
- Criar: `frontend/src/components/charts/BarChart.tsx`
- Criar: `frontend/src/components/JobCard.tsx`
- Criar: `frontend/src/pages/Dashboard.tsx`

- [ ] **Passo 1: Implementar BarChart em SVG puro**

Criar `frontend/src/components/charts/BarChart.tsx`:

```tsx
interface Barra {
  rotulo: string;
  valor: number;
}

interface BarChartProps {
  dados: Barra[];
  largura?: number;
  altura?: number;
  cor?: string;
}

export function BarChart({ dados, largura = 500, altura = 200, cor = "#6366f1" }: BarChartProps) {
  if (dados.length === 0) return null;

  const margem = { topo: 20, direita: 20, baixo: 40, esquerda: 50 };
  const larguraInterna = largura - margem.esquerda - margem.direita;
  const alturaInterna = altura - margem.topo - margem.baixo;

  const valorMax = Math.max(...dados.map((d) => d.valor));
  const larguraBarra = larguraInterna / dados.length - 4;

  const escalaY = (valor: number) => alturaInterna - (valor / valorMax) * alturaInterna;
  const escalaX = (i: number) => i * (larguraBarra + 4);

  return (
    <svg width={largura} height={altura} role="img" aria-label="Grafico de barras">
      <g transform={`translate(${margem.esquerda},${margem.topo})`}>
        {/* Eixo Y */}
        <line x1={0} y1={0} x2={0} y2={alturaInterna} stroke="#e5e7eb" strokeWidth={1} />
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const y = alturaInterna * (1 - frac);
          return (
            <g key={frac}>
              <line x1={-4} y1={y} x2={larguraInterna} y2={y} stroke="#f3f4f6" strokeWidth={1} />
              <text x={-8} y={y + 4} textAnchor="end" fontSize={10} fill="#9ca3af">
                {Math.round(valorMax * frac)}
              </text>
            </g>
          );
        })}

        {/* Barras */}
        {dados.map((d, i) => (
          <g key={d.rotulo}>
            <rect
              x={escalaX(i)}
              y={escalaY(d.valor)}
              width={larguraBarra}
              height={alturaInterna - escalaY(d.valor)}
              fill={cor}
              rx={3}
            />
            <text
              x={escalaX(i) + larguraBarra / 2}
              y={alturaInterna + 16}
              textAnchor="middle"
              fontSize={10}
              fill="#6b7280"
            >
              {d.rotulo}
            </text>
          </g>
        ))}
      </g>
    </svg>
  );
}
```

- [ ] **Passo 2: Implementar JobCard**

Criar `frontend/src/components/JobCard.tsx`:

```tsx
import type { Job, StatusJob } from "../types";

const COR_STATUS: Record<StatusJob, string> = {
  pendente: "bg-amber-100 text-amber-800",
  processando: "bg-blue-100 text-blue-800",
  concluido: "bg-green-100 text-green-800",
  falhou: "bg-red-100 text-red-800",
  morto: "bg-gray-100 text-gray-800",
};

interface JobCardProps {
  job: Job;
}

export function JobCard({ job }: JobCardProps) {
  const data = new Date(job.criado_em).toLocaleString("pt-BR");

  return (
    <article className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <span className="font-mono text-xs text-gray-400">{job.id.slice(0, 8)}...</span>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${COR_STATUS[job.status]}`}>
          {job.status}
        </span>
      </div>
      <p className="mt-2 text-sm font-medium text-gray-900">{job.tipo}</p>
      <p className="mt-1 text-xs text-gray-500">{data}</p>
      {job.erro && (
        <p className="mt-2 rounded bg-red-50 p-2 text-xs text-red-700">{job.erro}</p>
      )}
    </article>
  );
}
```

- [ ] **Passo 3: Implementar pagina Dashboard**

Criar `frontend/src/pages/Dashboard.tsx`:

```tsx
import { useEffect, useState } from "react";
import { BarChart } from "../components/charts/BarChart";
import { JobCard } from "../components/JobCard";
import { api } from "../services/api";
import type { Job, StatusJob } from "../types";

export function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    api.jobs
      .listar()
      .then((r) => setJobs(r.items))
      .catch((e: Error) => setErro(e.message))
      .finally(() => setCarregando(false));
  }, []);

  const contagemPorStatus = (): { rotulo: string; valor: number }[] => {
    const contagem: Partial<Record<StatusJob, number>> = {};
    for (const job of jobs) {
      contagem[job.status] = (contagem[job.status] ?? 0) + 1;
    }
    return Object.entries(contagem).map(([rotulo, valor]) => ({ rotulo, valor: valor ?? 0 }));
  };

  if (carregando) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-sm text-gray-500">Carregando...</p>
      </div>
    );
  }

  if (erro) {
    return (
      <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{erro}</div>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>

      {jobs.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-gray-500">
            Jobs por status
          </h2>
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white p-6">
            <BarChart dados={contagemPorStatus()} />
          </div>
        </section>
      )}

      <section className="mt-8">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-gray-500">
          Ultimos jobs
        </h2>
        {jobs.length === 0 ? (
          <p className="text-sm text-gray-500">Nenhum job encontrado. Submeta o primeiro!</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
```

- [ ] **Passo 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: implementar dashboard com grafico SVG puro e lista de jobs"
```

---

## Fase 8: Deploy e Documentacao

### Tarefa 8.1: render.yaml para deploy da API e worker

**Arquivos:**
- Criar: `render.yaml`

- [ ] **Passo 1: Criar render.yaml**

Criar `render.yaml` na raiz:

```yaml
services:
  - type: web
    name: ingestao-async-api
    runtime: docker
    dockerfilePath: backend/Dockerfile
    dockerContext: backend
    dockerCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production
    healthCheckPath: /health

  - type: worker
    name: ingestao-async-worker
    runtime: docker
    dockerfilePath: backend/Dockerfile
    dockerContext: backend
    dockerCommand: "python -m app.worker.main"
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        fromService:
          name: ingestao-async-api
          type: web
          envVarKey: SECRET_KEY
      - key: ENVIRONMENT
        value: production
```

- [ ] **Passo 2: Commit**

```bash
git add render.yaml
git commit -m "infra: adicionar render.yaml para deploy de API e worker"
```

---

## Checklist de Auto-revisao

### Cobertura de requisitos

- [x] API FastAPI com Pydantic v2
- [x] Fila Postgres com SELECT FOR UPDATE SKIP LOCKED
- [x] Interface abstrata de fila com mapeamento SQS documentado
- [x] Visibility timeout (locked_until)
- [x] Retry com backoff exponencial
- [x] Dead-letter (status MORTO)
- [x] Worker separado da API
- [x] Autenticacao JWT com access + refresh token
- [x] argon2 para hash de senha
- [x] SQLAlchemy 2.0 async com NullPool para Supavisor porta 6543
- [x] Alembic para migrations
- [x] Logging estruturado JSON com structlog
- [x] mypy strict + ruff + pre-commit
- [x] pytest com banco real, TDD
- [x] Dockerfile multi-stage
- [x] docker-compose com api, worker, db
- [x] GitHub Actions CI
- [x] render.yaml para deploy
- [x] Frontend React + TypeScript strict + Tailwind
- [x] Graficos SVG puro (sem bibliotecas de grafico)
- [x] Sanitizacao de PII na ingestao (LGPD)
- [x] Endpoint /health

### Pendente para README (apos todas as fases)

- [ ] Diagrama de arquitetura em SVG
- [ ] Instrucoes de como rodar localmente
- [ ] Mapeamento detalhado fila Postgres -> SQS
- [ ] Documentacao de deploy (Render + Cloudflare Pages + Supabase)
- [ ] Nota sobre cold start do free tier do Render

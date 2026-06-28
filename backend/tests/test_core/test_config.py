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
    assert s.JOB_VISIBILITY_TIMEOUT_SEGUNDOS == 3600
    assert s.RATE_LIMIT_POR_MINUTO == 60

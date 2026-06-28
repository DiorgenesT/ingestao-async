from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

_hasher = PasswordHasher()


def gerar_hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, hash_: str) -> bool:
    try:
        return _hasher.verify(hash_, senha)
    except VerifyMismatchError:
        return False


def criar_access_token(subject: str) -> str:
    expira = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _criar_token(subject=subject, tipo="access", expira=expira)


def criar_refresh_token(subject: str) -> str:
    expira = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _criar_token(subject=subject, tipo="refresh", expira=expira)


def _criar_token(subject: str, tipo: str, expira: datetime) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "tipo": tipo,
        "exp": expira,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decodificar_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("Token invalido ou expirado") from exc

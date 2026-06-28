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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    stmt = select(Usuario).where(Usuario.id == usuario_id, Usuario.ativo.is_(True))
    usuario = (await session.execute(stmt)).scalar_one_or_none()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario

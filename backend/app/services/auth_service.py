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

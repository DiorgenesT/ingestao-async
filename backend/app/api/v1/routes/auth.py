from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_dep
from app.schemas.auth import LoginRequest, RegistrarRequest, TokenResponse
from app.services.auth_service import (
    AuthService,
    CredenciaisInvalidasError,
    EmailJaCadastradoError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registrar", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def registrar(
    body: RegistrarRequest,
    session: AsyncSession = Depends(get_session_dep),
) -> TokenResponse:
    try:
        return await AuthService(session).registrar(body.email, body.senha)
    except EmailJaCadastradoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ja cadastrado",
        ) from None


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session_dep),
) -> TokenResponse:
    try:
        return await AuthService(session).login(body.email, body.senha)
    except CredenciaisInvalidasError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

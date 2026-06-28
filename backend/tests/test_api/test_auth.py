"""
Testes de integracao dos endpoints de autenticacao.
Requerem banco de dados real.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.usefixtures("banco_de_teste")


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c  # type: ignore[misc]


@pytest.mark.asyncio
async def test_registrar_usuario_retorna_tokens(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/registrar",
        json={"email": "novo@example.com", "senha": "SenhaForte123!"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_registrar_email_duplicado_retorna_409(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "senha": "SenhaForte123!"}
    await client.post("/api/v1/auth/registrar", json=payload)
    resp = await client.post("/api/v1/auth/registrar", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_registrar_senha_curta_retorna_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/registrar",
        json={"email": "curta@example.com", "senha": "123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_com_credenciais_validas(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/registrar",
        json={"email": "login@example.com", "senha": "SenhaForte123!"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "senha": "SenhaForte123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_senha_errada_retorna_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/registrar",
        json={"email": "senha-errada@example.com", "senha": "SenhaForte123!"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "senha-errada@example.com", "senha": "senhaerrada"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_usuario_inexistente_retorna_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "naoexiste@example.com", "senha": "qualquer123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_healthcheck(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

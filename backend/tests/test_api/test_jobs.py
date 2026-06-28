"""
Testes de integracao dos endpoints de jobs.
Requerem banco de dados real.
"""

import io

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.usefixtures("banco_de_teste")


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c  # type: ignore[misc]


async def _registrar_e_obter_token(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/v1/auth/registrar",
        json={"email": email, "senha": "SenhaForte123!"},
    )
    return str(resp.json()["access_token"])


# ---------------------------------------------------------------------------
# Submissao de URL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submeter_url_retorna_202_com_job_id(client: AsyncClient) -> None:
    token = await _registrar_e_obter_token(client, "url-user@test.com")
    resp = await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/dataset/exemplo.csv", "nome": "Dataset Teste"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pendente"


@pytest.mark.asyncio
async def test_submeter_url_sem_autenticacao_retorna_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/dataset/exemplo.csv", "nome": "Teste"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_submeter_url_invalida_retorna_422(client: AsyncClient) -> None:
    token = await _registrar_e_obter_token(client, "url-invalida@test.com")
    resp = await client.post(
        "/api/v1/jobs/url",
        json={"url": "nao-e-uma-url", "nome": "Teste"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Submissao de CSV
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submeter_csv_retorna_202_com_job_id(client: AsyncClient) -> None:
    token = await _registrar_e_obter_token(client, "csv-user@test.com")
    csv_bytes = b"nome,valor\nalfa,10\nbeta,20\n"
    resp = await client.post(
        "/api/v1/jobs/csv",
        files={"arquivo": ("dados.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"nome": "Meu Dataset"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pendente"


@pytest.mark.asyncio
async def test_submeter_csv_sem_autenticacao_retorna_401(client: AsyncClient) -> None:
    csv_bytes = b"nome,valor\nalfa,10\n"
    resp = await client.post(
        "/api/v1/jobs/csv",
        files={"arquivo": ("dados.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"nome": "Teste"},
    )
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Listagem e consulta
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_listar_jobs_retorna_apenas_jobs_do_usuario(client: AsyncClient) -> None:
    token_a = await _registrar_e_obter_token(client, "lista-a@test.com")
    token_b = await _registrar_e_obter_token(client, "lista-b@test.com")

    # Usuario A cria um job
    await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/a.csv", "nome": "Job A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Usuario B lista: nao deve ver o job do A
    resp = await client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_listar_jobs_retorna_jobs_proprios(client: AsyncClient) -> None:
    token = await _registrar_e_obter_token(client, "lista-proprios@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/x.csv", "nome": "Job X"},
        headers=headers,
    )
    await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/y.csv", "nome": "Job Y"},
        headers=headers,
    )

    resp = await client.get("/api/v1/jobs", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_buscar_job_por_id(client: AsyncClient) -> None:
    token = await _registrar_e_obter_token(client, "busca@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    cria = await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/b.csv", "nome": "Job B"},
        headers=headers,
    )
    job_id = cria.json()["job_id"]

    resp = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert data["status"] == "pendente"
    assert data["tipo"] in ("url", "csv")


@pytest.mark.asyncio
async def test_buscar_job_de_outro_usuario_retorna_404(client: AsyncClient) -> None:
    token_a = await _registrar_e_obter_token(client, "dono@test.com")
    token_b = await _registrar_e_obter_token(client, "intruso@test.com")

    cria = await client.post(
        "/api/v1/jobs/url",
        json={"url": "https://dados.gov.br/c.csv", "nome": "Job C"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    job_id = cria.json()["job_id"]

    resp = await client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_buscar_job_inexistente_retorna_404(client: AsyncClient) -> None:
    token = await _registrar_e_obter_token(client, "job-404@test.com")
    resp = await client.get(
        "/api/v1/jobs/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404

import csv
import io
import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.queue.interface import MensagemFila


class UrlHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def processar(self, mensagem: MensagemFila) -> dict[str, Any]:
        url: str = mensagem.payload["url"]
        nome: str = mensagem.payload.get("nome", "dataset")

        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            conteudo = response.text

        reader = csv.DictReader(io.StringIO(conteudo))
        linhas = list(reader)

        resumo: dict[str, Any] = {
            "linhas": len(linhas),
            "colunas": list(linhas[0].keys()) if linhas else [],
            "url": url,
        }

        self._session.add(
            Dataset(
                job_id=uuid.UUID(mensagem.id),
                nome=nome,
                resumo=resumo,
            )
        )
        return resumo

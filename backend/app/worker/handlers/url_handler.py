import csv
import io
import time
import uuid
from datetime import datetime, timezone
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

        inicio = time.monotonic()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            conteudo = response.text

        tamanho_bytes = len(response.content)
        reader = csv.DictReader(io.StringIO(conteudo))
        linhas = list(reader)
        tempo_segundos = round(time.monotonic() - inicio, 2)

        resumo: dict[str, Any] = {
            "linhas": len(linhas),
            "colunas": list(linhas[0].keys()) if linhas else [],
            "url": url,
            "tamanho_bytes": tamanho_bytes,
            "tempo_processamento_segundos": tempo_segundos,
            "processado_em": datetime.now(timezone.utc).isoformat(),
        }

        self._session.add(
            Dataset(
                job_id=uuid.UUID(mensagem.id),
                nome=nome,
                resumo=resumo,
            )
        )
        return resumo

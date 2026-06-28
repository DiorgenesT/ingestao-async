import csv
import io
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.queue.interface import MensagemFila

_TIMEOUT = httpx.Timeout(connect=30.0, read=3600.0, write=30.0, pool=30.0)


class UrlHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def processar(self, mensagem: MensagemFila) -> dict[str, Any]:
        url: str = mensagem.payload["url"]
        nome: str = mensagem.payload.get("nome", "dataset")

        inicio = time.monotonic()
        tamanho_bytes = 0
        contagem_linhas = 0
        colunas: list[str] = []

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()
                buffer = io.StringIO()
                cabecalho_lido = False

                async for chunk in response.aiter_text(chunk_size=65536):
                    tamanho_bytes += len(chunk.encode())
                    buffer.write(chunk)

                    buffer.seek(0)
                    reader = csv.reader(buffer)

                    if not cabecalho_lido:
                        try:
                            colunas = next(reader)
                            cabecalho_lido = True
                        except StopIteration:
                            buffer.seek(0, 2)
                            continue

                    for _ in reader:
                        contagem_linhas += 1

                    # manter apenas o trecho incompleto da ultima linha
                    resto = buffer.read()
                    buffer = io.StringIO()
                    if not resto.endswith("\n"):
                        ultima_quebra = resto.rfind("\n")
                        if ultima_quebra != -1:
                            buffer.write(resto[ultima_quebra + 1:])
                    buffer.seek(0, 2)

        tempo_segundos = round(time.monotonic() - inicio, 2)

        resumo: dict[str, Any] = {
            "linhas": contagem_linhas,
            "colunas": colunas,
            "url": url,
            "tamanho_bytes": tamanho_bytes,
            "tempo_processamento_segundos": tempo_segundos,
            "processado_em": datetime.now(UTC).isoformat(),
        }

        self._session.add(
            Dataset(
                job_id=uuid.UUID(mensagem.id),
                nome=nome,
                resumo=resumo,
            )
        )
        return resumo

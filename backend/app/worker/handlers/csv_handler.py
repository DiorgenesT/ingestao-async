import csv
import os
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.queue.interface import MensagemFila


class CsvHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def processar(self, mensagem: MensagemFila) -> dict[str, Any]:
        caminho: str = mensagem.payload["caminho"]
        nome: str = mensagem.payload.get("nome", "dataset")

        inicio = time.monotonic()
        tamanho_bytes = os.path.getsize(caminho)

        with open(caminho, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            linhas = list(reader)

        tempo_segundos = round(time.monotonic() - inicio, 2)

        resumo: dict[str, Any] = {
            "linhas": len(linhas),
            "colunas": list(linhas[0].keys()) if linhas else [],
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

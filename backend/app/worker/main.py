import asyncio
import signal
from typing import Any

from app.core.config import settings
from app.core.database import get_session
from app.core.logging import obter_logger
from app.queue.interface import MensagemFila
from app.queue.postgres_queue import FilaPostgres
from app.worker.handlers.csv_handler import CsvHandler
from app.worker.handlers.url_handler import UrlHandler

_logger = obter_logger("worker")

_HANDLERS: dict[str, type[Any]] = {
    "csv": CsvHandler,
    "url": UrlHandler,
}

_continuar_executando = True


def _registrar_sinais() -> None:
    def _parar(signum: int, frame: Any) -> None:
        global _continuar_executando
        _continuar_executando = False
        _logger.info("sinal recebido, encerrando", sinal=signum)

    signal.signal(signal.SIGTERM, _parar)
    signal.signal(signal.SIGINT, _parar)


async def _processar_mensagem(msg: MensagemFila) -> None:
    handler_cls = _HANDLERS.get(msg.tipo)
    if handler_cls is None:
        async with get_session() as session:
            await FilaPostgres(session=session).rejeitar(
                msg.recibo, f"Tipo de job desconhecido: {msg.tipo}"
            )
        _logger.warning("tipo desconhecido", tipo=msg.tipo, job_id=msg.id)
        return

    try:
        async with get_session() as session:
            fila = FilaPostgres(session=session)
            handler = handler_cls(session)
            await handler.processar(msg)
            await fila.confirmar(msg.recibo)
        _logger.info("job concluido", job_id=msg.id, tipo=msg.tipo)
    except Exception as exc:
        async with get_session() as session:
            await FilaPostgres(session=session).rejeitar(msg.recibo, str(exc))
        _logger.error("job falhou", job_id=msg.id, tipo=msg.tipo, erro=str(exc))


async def processar_uma_vez() -> int:
    """Recebe e processa um lote de jobs. Retorna quantos foram recebidos."""
    async with get_session() as session:
        fila = FilaPostgres(session=session)
        mensagens = await fila.receber(limite=settings.WORKER_BATCH_SIZE)

    for msg in mensagens:
        await _processar_mensagem(msg)

    return len(mensagens)


async def executar() -> None:
    _registrar_sinais()
    _logger.info("worker iniciado", batch_size=settings.WORKER_BATCH_SIZE)

    while _continuar_executando:
        processados = await processar_uma_vez()
        if processados == 0:
            await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SEGUNDOS)


if __name__ == "__main__":
    asyncio.run(executar())

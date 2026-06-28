from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configurar_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def obter_logger(nome: str) -> Any:
    # Vincula o nome do logger como campo de contexto em todos os eventos.
    # Retorna Any porque structlog nao expoe um tipo concreto para BoundLogger
    # quando configurado com PrintLoggerFactory + make_filtering_bound_logger.
    return structlog.get_logger().bind(logger=nome)

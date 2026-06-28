import json

import pytest

from app.core.logging import configurar_logging, obter_logger


def test_logger_emite_json_estruturado(capsys: pytest.CaptureFixture[str]) -> None:
    configurar_logging()
    logger = obter_logger("teste")
    logger.info("evento de teste", usuario_id="123", endpoint="/jobs")

    saida = capsys.readouterr().out
    dados = json.loads(saida)
    assert dados["event"] == "evento de teste"
    assert dados["usuario_id"] == "123"
    assert "timestamp" in dados
    assert dados["level"] == "info"

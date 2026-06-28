from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MensagemFila:
    """Representa uma mensagem retirada da fila para processamento."""

    id: str
    tipo: str
    payload: dict[str, Any]
    tentativas: int
    # Identificador de recibo para exclusao apos processamento bem-sucedido.
    # Equivalente ao ReceiptHandle do SQS.
    recibo: str = field(default="")


class FilaInterface(ABC):
    """
    Interface abstrata para sistemas de fila.

    Mapeamento para AWS SQS:
      enfileirar()  -> SendMessage
      receber()     -> ReceiveMessage (WaitTimeSeconds para long polling)
      confirmar()   -> DeleteMessage (usando ReceiptHandle)
      rejeitar()    -> nao chamar DeleteMessage; a mensagem volta apos VisibilityTimeout

    O campo locked_until da implementacao Postgres corresponde ao VisibilityTimeout
    do SQS: a mensagem fica invisivel para outros workers durante o processamento.
    Se o worker morrer sem confirmar, ela reaparece automaticamente apos o timeout.

    Para migrar para SQS: implementar FilaSQS com esta mesma interface.
    Zero mudancas no worker ou no codigo de negocio.
    """

    @abstractmethod
    async def enfileirar(self, tipo: str, payload: dict[str, Any]) -> str:
        """Adiciona um job a fila. Retorna o ID do job criado."""

    @abstractmethod
    async def receber(self, limite: int = 1) -> list[MensagemFila]:
        """Retira mensagens disponiveis para processamento, aplicando visibility timeout."""

    @abstractmethod
    async def confirmar(self, recibo: str) -> None:
        """Marca o job como concluido. Equivalente ao DeleteMessage do SQS."""

    @abstractmethod
    async def rejeitar(self, recibo: str, erro: str) -> None:
        """
        Registra falha no job.
        Aplica backoff exponencial e reenfileira; apos max_tentativas, envia para dead-letter.
        """

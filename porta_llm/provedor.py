"""O combinado que todo adaptador segue. A casca só conhece esta interface."""

from abc import ABC, abstractmethod

from porta_llm.pedido import Pedido
from porta_llm.resposta import Resposta


class Provedor(ABC):
    # O modelo configurado. Vai no log quando a LLM nem chegou a responder.
    modelo: str

    @abstractmethod
    async def enviar(self, pedido: Pedido) -> Resposta:
        """Manda o pedido e traz a resposta: o texto, o modelo que respondeu e os tokens.

        Quando falha, levanta ErroLLM com o motivo: fora_do_ar (a casca tenta de novo),
        chave_errada ou pedido_recusado (a casca para na hora).
        """

    async def fechar(self) -> None:
        """Fecha as conexões. Quem não tem nada para fechar não precisa mudar."""

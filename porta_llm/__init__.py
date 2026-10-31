"""A Porta da LLM: o único lugar que chama uma LLM.

As peças entram aqui conforme forem construídas (ficha 08, passos 2 a 5).
"""

from porta_llm.erro_llm import ErroLLM
from porta_llm.fala import Fala
from porta_llm.pedido import Pedido
from porta_llm.porta import PortaLLM
from porta_llm.provedor import Provedor
from porta_llm.resposta import Resposta

__all__ = ["ErroLLM", "Fala", "Pedido", "PortaLLM", "Provedor", "Resposta"]

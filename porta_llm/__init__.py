"""A Porta da LLM: o único lugar que chama uma LLM.

Uso: porta = criar_porta(), e depois await porta.chamar(Pedido(...)). Veja o README.
"""

from porta_llm.config_llm import ConfigLLM
from porta_llm.erro_llm import ErroLLM
from porta_llm.fala import Fala
from porta_llm.montar import criar_porta
from porta_llm.pedido import Pedido
from porta_llm.porta import PortaLLM
from porta_llm.provedor import Provedor
from porta_llm.provedor_openai import ProvedorOpenAI
from porta_llm.resposta import Resposta

__all__ = [
    "ConfigLLM",
    "ErroLLM",
    "Fala",
    "Pedido",
    "PortaLLM",
    "Provedor",
    "ProvedorOpenAI",
    "Resposta",
    "criar_porta",
]

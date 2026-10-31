"""A montagem: lê a configuração, escolhe o adaptador e entrega a Porta pronta."""

import asyncio

import httpx

from porta_llm.config_llm import ConfigLLM
from porta_llm.porta import PortaLLM
from porta_llm.provedor_openai import ProvedorOpenAI

# O LLM_FORMATO e o adaptador de cada um. Um adaptador novo (o do Claude, por exemplo) entra aqui.
ADAPTADORES = {"openai": ProvedorOpenAI}


def criar_porta(
    config: ConfigLLM | None = None,
    cliente: httpx.AsyncClient | None = None,
    dormir=asyncio.sleep,
) -> PortaLLM:
    """Quem usa chama só criar_porta(). O cliente e o dormir existem para os testes trocarem
    a internet pelo servidor de mentira e as pausas pelo dormir de mentira."""
    config = config or ConfigLLM()
    adaptador = ADAPTADORES.get(config.formato)
    if adaptador is None:
        raise ValueError(
            f"LLM_FORMATO desconhecido: {config.formato!r}. Os que existem: {', '.join(ADAPTADORES)}"
        )
    provedor = adaptador(url=config.url, modelo=config.modelo, chave=config.chave.get_secret_value(), cliente=cliente)
    return PortaLLM(provedor, dormir=dormir)

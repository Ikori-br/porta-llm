"""A montagem: lê a configuração, escolhe o adaptador e entrega a Porta pronta."""

from porta_llm.config_llm import ConfigLLM
from porta_llm.porta import PortaLLM
from porta_llm.provedor_openai import ProvedorOpenAI

# O LLM_FORMATO e o adaptador de cada um. Um adaptador novo (o do Claude, por exemplo) entra aqui.
ADAPTADORES = {"openai": ProvedorOpenAI}


def criar_porta(config: ConfigLLM | None = None) -> PortaLLM:
    config = config or ConfigLLM()
    adaptador = ADAPTADORES.get(config.formato)
    if adaptador is None:
        raise ValueError(
            f"LLM_FORMATO desconhecido: {config.formato!r}. Os que existem: {', '.join(ADAPTADORES)}"
        )
    provedor = adaptador(url=config.url, modelo=config.modelo, chave=config.chave.get_secret_value())
    return PortaLLM(provedor)

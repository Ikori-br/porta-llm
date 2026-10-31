import os
from pathlib import Path

import pytest

# O .env de teste, com a chave falsa.
ENV_DE_TESTE = Path(__file__).parent / "env_de_teste"
CHAVE_FALSA = "chave-de-teste"


@pytest.fixture
def anyio_backend():
    # Os testes assíncronos rodam com o asyncio, o mesmo que a Porta usa de verdade.
    return "asyncio"


@pytest.fixture
def ambiente_limpo(monkeypatch):
    """Tira do ambiente qualquer LLM_ do computador de quem roda os testes."""
    for nome in list(os.environ):
        if nome.startswith("LLM_"):
            monkeypatch.delenv(nome)
    return monkeypatch

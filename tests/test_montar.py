"""Teste 4 do desenho (ficha 08): a montagem, o criar_porta()."""

import pytest

from porta_llm import ConfigLLM, PortaLLM, ProvedorOpenAI, criar_porta
from tests.conftest import CHAVE_FALSA, ENV_DE_TESTE


@pytest.fixture(autouse=True)
def _limpo(ambiente_limpo):
    return ambiente_limpo


def test_4_openai_monta_a_porta_com_o_provedor_openai():
    porta = criar_porta(ConfigLLM(_env_file=ENV_DE_TESTE))
    assert isinstance(porta, PortaLLM)
    provedor = porta._provedor
    assert isinstance(provedor, ProvedorOpenAI)
    assert provedor.modelo == "modelo-de-teste"
    assert provedor._endereco == "https://api.exemplo.com/chat/completions"


def test_4_sem_config_le_do_ambiente(ambiente_limpo):
    ambiente_limpo.setenv("LLM_MODELO", "deepseek-v4-pro")
    ambiente_limpo.setenv("LLM_CHAVE", CHAVE_FALSA)
    porta = criar_porta()
    assert porta._provedor.modelo == "deepseek-v4-pro"


def test_4_formato_desconhecido_da_erro_claro_ao_ligar(ambiente_limpo):
    ambiente_limpo.setenv("LLM_FORMATO", "claude")
    ambiente_limpo.setenv("LLM_CHAVE", CHAVE_FALSA)
    with pytest.raises(ValueError) as erro:
        criar_porta()
    assert "LLM_FORMATO" in str(erro.value)
    assert "openai" in str(erro.value)
    assert CHAVE_FALSA not in str(erro.value)

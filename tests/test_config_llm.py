"""Teste 3 do desenho (ficha 08): a ConfigLLM.

Usa o .env de teste, com a chave falsa. A chave de verdade nunca entra nos testes.
"""

import pytest
from pydantic import ValidationError

from porta_llm import ConfigLLM
from tests.conftest import CHAVE_FALSA, ENV_DE_TESTE


@pytest.fixture(autouse=True)
def _limpo(ambiente_limpo):
    return ambiente_limpo


def test_3_le_as_quatro_variaveis_do_env_de_teste():
    config = ConfigLLM(_env_file=ENV_DE_TESTE)
    assert config.formato == "openai"
    assert config.url == "https://api.exemplo.com"
    assert config.modelo == "modelo-de-teste"
    assert config.chave.get_secret_value() == CHAVE_FALSA


def test_3_le_das_variaveis_de_ambiente_como_o_docker_entrega(ambiente_limpo):
    ambiente_limpo.setenv("LLM_MODELO", "deepseek-v4-pro")
    ambiente_limpo.setenv("LLM_CHAVE", CHAVE_FALSA)
    config = ConfigLLM()
    assert config.modelo == "deepseek-v4-pro"
    assert config.chave.get_secret_value() == CHAVE_FALSA


def test_3_so_com_a_chave_usa_os_padroes(ambiente_limpo):
    ambiente_limpo.setenv("LLM_CHAVE", CHAVE_FALSA)
    config = ConfigLLM()
    assert config.formato == "openai"
    assert config.url == "https://api.deepseek.com"
    assert config.modelo == "deepseek-flash"


@pytest.mark.parametrize("chave", [None, ""], ids=["sem_a_chave", "chave_vazia"])
def test_3_sem_a_chave_da_um_erro_claro(ambiente_limpo, chave):
    ambiente_limpo.setenv("LLM_MODELO", "deepseek-flash")
    if chave is not None:
        ambiente_limpo.setenv("LLM_CHAVE", chave)
    with pytest.raises(ValidationError) as erro:
        ConfigLLM()
    assert "falta a LLM_CHAVE" in str(erro.value)


def test_3_a_chave_nao_aparece_quando_a_config_e_impressa():
    config = ConfigLLM(_env_file=ENV_DE_TESTE)
    assert CHAVE_FALSA not in repr(config)
    assert CHAVE_FALSA not in str(config)
    assert CHAVE_FALSA not in str(config.chave)

"""Teste 1 do desenho (ficha 08): a Resposta."""

import pytest
from pydantic import BaseModel, ValidationError

from porta_llm import Resposta


class Exemplo(BaseModel):
    nota: int


def test_1_resposta_guarda_o_que_veio_com_os_padroes():
    resposta = Resposta(texto='{"nota": 4}', modelo="deepseek-flash", tokens_entrada=1200, tokens_saida=80)
    assert resposta.texto == '{"nota": 4}'
    assert resposta.modelo == "deepseek-flash"
    assert (resposta.tokens_entrada, resposta.tokens_saida) == (1200, 80)
    assert resposta.dados is None
    assert resposta.tempo_ms == 0
    assert resposta.tentativas == 1


def test_1_resposta_guarda_o_objeto_conferido():
    resposta = Resposta(
        texto='{"nota": 4}',
        modelo="deepseek-flash",
        tokens_entrada=1200,
        tokens_saida=80,
        dados=Exemplo(nota=4),
        tempo_ms=2300,
        tentativas=2,
    )
    assert isinstance(resposta.dados, Exemplo)
    assert resposta.dados.nota == 4
    assert resposta.tentativas == 2


def test_1_resposta_recusa_tokens_negativos():
    with pytest.raises(ValidationError):
        Resposta(texto="oi", modelo="deepseek-flash", tokens_entrada=-1, tokens_saida=0)


def test_1_texto_e_dados_da_resposta_nao_aparecem_quando_ela_e_impressa():
    resposta = Resposta(
        texto="a pessoa parece insegura",
        modelo="deepseek-flash",
        tokens_entrada=1,
        tokens_saida=1,
        dados=Exemplo(nota=4),
    )
    assert "insegura" not in repr(resposta)
    assert "nota=4" not in repr(resposta)

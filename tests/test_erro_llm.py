"""Teste 2 do desenho (ficha 08): o ErroLLM."""

import pytest

from porta_llm import ErroLLM


def test_2_leva_o_motivo_e_o_detalhe():
    erro = ErroLLM("fora_do_ar", "http_503")
    assert erro.motivo == "fora_do_ar"
    assert erro.detalhe == "http_503"
    assert str(erro) == "fora_do_ar: http_503"


def test_2_o_detalhe_e_opcional():
    erro = ErroLLM("resposta_invalida")
    assert erro.detalhe == ""
    assert str(erro) == "resposta_invalida"


@pytest.mark.parametrize("motivo", ["fora_do_ar", "chave_errada", "pedido_recusado", "resposta_invalida"])
def test_2_aceita_os_quatro_motivos(motivo):
    assert ErroLLM(motivo).motivo == motivo


def test_2_recusa_motivo_que_nao_existe():
    with pytest.raises(ValueError):
        ErroLLM("caiu")


@pytest.mark.parametrize(
    "detalhe",
    ["Bearer chave-de-teste", "chave-de-teste", "texto com espaço", "a" * 31],
    ids=["cabecalho_com_a_chave", "a_chave_sozinha", "texto_com_espaco", "longo_demais"],
)
def test_2_o_detalhe_so_aceita_um_codigo_curto(detalhe):
    # O detalhe é um código como http_503. Nem a chave nem um pedaço da resposta cabem nele.
    with pytest.raises(ValueError):
        ErroLLM("chave_errada", detalhe)

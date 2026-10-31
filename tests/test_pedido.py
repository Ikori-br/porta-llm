"""Teste 1 do desenho (ficha 08): o Pedido."""

import pytest
from pydantic import BaseModel, ValidationError

from porta_llm import Fala, Pedido

FALAS = [
    Fala(papel="system", texto="as instruções"),
    Fala(papel="user", texto="a resposta da pessoa"),
]


class Exemplo(BaseModel):
    nota: int


def test_1_pedido_certo_com_os_padroes():
    pedido = Pedido(agente="interprete", falas=FALAS)
    assert pedido.temperatura == 0
    assert pedido.tamanho_maximo == 500
    assert pedido.formato is None
    assert pedido.etiquetas == {}


def test_1_pedido_certo_com_tudo():
    pedido = Pedido(
        agente="condutor",
        falas=FALAS,
        temperatura=0.7,
        tamanho_maximo=300,
        formato=Exemplo,
        etiquetas={"conversa": "c12"},
    )
    assert pedido.temperatura == 0.7
    assert pedido.tamanho_maximo == 300
    assert pedido.formato is Exemplo
    assert pedido.etiquetas == {"conversa": "c12"}


@pytest.mark.parametrize(
    "campos",
    [
        {"falas": []},
        {"temperatura": -0.1},
        {"temperatura": 2.1},
        {"tamanho_maximo": 0},
        {"agente": ""},
        {"formato": dict},
        {"etiquetas": {"nome com espaço": "c12"}},
    ],
    ids=[
        "lista_de_falas_vazia",
        "temperatura_abaixo_de_0",
        "temperatura_acima_de_2",
        "tamanho_zero",
        "agente_sem_nome",
        "formato_que_nao_e_do_pydantic",
        "etiqueta_que_quebraria_o_log",
    ],
)
def test_1_pedido_recusa(campos):
    with pytest.raises(ValidationError):
        Pedido(**{"agente": "interprete", "falas": FALAS, **campos})


def test_1_texto_das_falas_nao_aparece_quando_o_pedido_e_impresso():
    pedido = Pedido(agente="interprete", falas=FALAS)
    assert "resposta da pessoa" not in repr(pedido)
    assert "instruções" not in repr(pedido)

"""Teste 1 do desenho (ficha 08): a Fala."""

import pytest
from pydantic import ValidationError

from porta_llm import Fala


@pytest.mark.parametrize("papel", ["system", "user", "assistant"])
def test_1_fala_aceita_os_tres_papeis(papel):
    assert Fala(papel=papel, texto="oi").papel == papel


def test_1_fala_recusa_papel_que_nao_existe():
    with pytest.raises(ValidationError):
        Fala(papel="robo", texto="oi")


def test_1_texto_da_fala_nao_aparece_quando_ela_e_impressa():
    # Se alguém escrever a Fala no log sem querer, o que a pessoa disse não vaza.
    fala = Fala(papel="user", texto="no outro dia já penso no plano B")
    assert "plano B" not in repr(fala)
    assert "plano B" not in str(fala)

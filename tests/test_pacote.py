"""Teste 0: o esqueleto. O pacote instala com o nome e a versão certos, e dá para importar."""

from importlib.metadata import version


def test_0_o_pacote_instala_e_importa():
    import porta_llm  # noqa: F401  (se o import falhar, o teste falha)

    assert version("porta-llm") == "0.1.0"

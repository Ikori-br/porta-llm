"""Testes 5 a 16 do desenho (ficha 08): a casca, a PortaLLM.

Sem rede, sem chave e sem custo: o Provedor de mentira fica no lugar da LLM, e o
dormir de mentira anota as pausas sem esperar.
"""

import logging

import pytest

from porta_llm import ErroLLM, Fala, Pedido, PortaLLM
from tests.dormir_de_mentira import DormirDeMentira
from tests.formato_de_exemplo import JSON_CERTO, FormatoDeExemplo
from tests.provedor_de_mentira import Demora, ProvedorDeMentira

pytestmark = pytest.mark.anyio

FALAS = [
    Fala(papel="system", texto="Você é o Intérprete. Responda só com o JSON."),
    Fala(papel="user", texto="No dia fico chateado, mas no outro já penso no plano B."),
]


def pedido(formato=None, **campos) -> Pedido:
    return Pedido(agente="interprete", falas=FALAS, formato=formato, etiquetas={"conversa": "c12"}, **campos)


def montar(*roteiro):
    """A casca com o Provedor de mentira e o dormir de mentira. O limite de 30 s vira 0,05 s."""
    provedor = ProvedorDeMentira(*roteiro)
    dormir = DormirDeMentira()
    return PortaLLM(provedor, dormir=dormir, tempo_limite=0.05), provedor, dormir


def linhas(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == "porta-llm"]


@pytest.fixture(autouse=True)
def log_da_porta(caplog):
    caplog.set_level(logging.INFO, logger="porta-llm")


# 5. Responde de primeira


async def test_5_responde_de_primeira(caplog):
    porta, provedor, dormir = montar("oi, tudo bem?")
    resposta = await porta.chamar(pedido())
    assert resposta.texto == "oi, tudo bem?"
    assert (resposta.tokens_entrada, resposta.tokens_saida) == (100, 20)
    assert resposta.modelo == "modelo-de-mentira"
    assert resposta.tentativas == 1
    assert resposta.tempo_ms >= 0
    assert dormir.pausas == []
    assert len(provedor.pedidos) == 1
    assert len(linhas(caplog)) == 1
    assert "evento=llm_respondeu" in linhas(caplog)[0]


# 6. Cai uma vez e depois responde


async def test_6_cai_uma_vez_e_depois_responde(caplog):
    porta, provedor, dormir = montar(ErroLLM("fora_do_ar", "http_503"), "oi")
    resposta = await porta.chamar(pedido())
    assert resposta.texto == "oi"
    assert resposta.tentativas == 2
    assert dormir.pausas == [2]
    eventos = linhas(caplog)
    assert "evento=llm_falhou" in eventos[0] and "detalhe=http_503" in eventos[0]
    assert "evento=llm_respondeu" in eventos[1] and "tentativa=2" in eventos[1]


# 7. Cai 3 vezes


async def test_7_cai_3_vezes_e_desiste(caplog):
    porta, provedor, dormir = montar(
        ErroLLM("fora_do_ar", "http_503"),
        ErroLLM("fora_do_ar", "rede"),
        ErroLLM("fora_do_ar", "http_429"),
    )
    with pytest.raises(ErroLLM) as erro:
        await porta.chamar(pedido())
    assert erro.value.motivo == "fora_do_ar"
    assert erro.value.detalhe == "http_429"
    assert dormir.pausas == [2, 5]
    assert len(provedor.pedidos) == 3
    eventos = linhas(caplog)
    assert len(eventos) == 3
    assert "evento=llm_falhou" in eventos[0]
    assert "evento=llm_falhou" in eventos[1]
    assert "evento=llm_desistiu" in eventos[2] and "motivo=fora_do_ar" in eventos[2]


# 8. Demora mais que o limite


async def test_8_demorar_mais_que_o_limite_conta_como_falha(caplog):
    porta, provedor, dormir = montar(Demora(1), "agora foi")
    resposta = await porta.chamar(pedido())
    assert resposta.texto == "agora foi"
    assert resposta.tentativas == 2
    assert dormir.pausas == [2]
    assert "detalhe=tempo_esgotado" in linhas(caplog)[0]


# 9 e 10. Chave errada e pedido recusado: erro na hora


@pytest.mark.parametrize(
    "erro_do_provedor",
    [ErroLLM("chave_errada", "http_401"), ErroLLM("pedido_recusado", "http_400")],
    ids=["9_chave_errada", "10_pedido_recusado"],
)
async def test_9_e_10_erro_na_hora_sem_tentar_de_novo(caplog, erro_do_provedor):
    porta, provedor, dormir = montar(erro_do_provedor)
    with pytest.raises(ErroLLM) as erro:
        await porta.chamar(pedido())
    assert erro.value.motivo == erro_do_provedor.motivo
    assert len(provedor.pedidos) == 1
    assert dormir.pausas == []
    eventos = linhas(caplog)
    assert len(eventos) == 1
    assert "evento=llm_recusou" in eventos[0] and f"motivo={erro_do_provedor.motivo}" in eventos[0]


# 11. JSON quebrado e depois certo


async def test_11_json_quebrado_e_depois_certo(caplog):
    porta, provedor, dormir = montar('{"capturas": [{"item": ', JSON_CERTO)
    resposta = await porta.chamar(pedido(formato=FormatoDeExemplo))
    assert isinstance(resposta.dados, FormatoDeExemplo)
    assert resposta.dados.capturas[0].valor == 4
    assert resposta.tentativas == 2
    assert dormir.pausas == []
    # O segundo pedido é o primeiro com uma fala a mais no fim, dizendo o que veio errado.
    primeiro, segundo = provedor.pedidos
    assert segundo.falas[:-1] == primeiro.falas
    assert segundo.falas[-1].papel == "user"
    assert "JSON" in segundo.falas[-1].texto
    eventos = linhas(caplog)
    assert "evento=llm_json_invalido" in eventos[0] and "problema=json_quebrado" in eventos[0]
    assert "evento=llm_respondeu" in eventos[1]


# 12. JSON quebrado duas vezes


async def test_12_json_quebrado_duas_vezes_desiste(caplog):
    porta, provedor, dormir = montar("isso não é JSON", "nem isso")
    with pytest.raises(ErroLLM) as erro:
        await porta.chamar(pedido(formato=FormatoDeExemplo))
    assert erro.value.motivo == "resposta_invalida"
    assert len(provedor.pedidos) == 2
    eventos = linhas(caplog)
    assert len(eventos) == 2
    assert "evento=llm_desistiu" in eventos[1] and "motivo=resposta_invalida" in eventos[1]


# 13. Falta um campo ou o tipo está errado


@pytest.mark.parametrize(
    "json_errado, campo",
    [
        ('{"capturas": [{"item": "frustracao", "valor": 4, "trecho": "x"}]}', "capturas.0.certeza"),
        ('{"capturas": [{"item": "frustracao", "valor": "quatro", "trecho": "x", "certeza": "alta"}]}', "capturas.0.valor"),
        ('{"capturas": [{"item": "frustracao", "valor": 9, "trecho": "x", "certeza": "alta"}]}', "capturas.0.valor"),
        ('{"outra_coisa": 1}', "capturas"),
    ],
    ids=["falta_a_certeza", "valor_em_texto", "valor_fora_de_1_a_5", "falta_tudo"],
)
async def test_13_campo_errado_pede_de_novo_dizendo_qual(caplog, json_errado, campo):
    porta, provedor, dormir = montar(json_errado, JSON_CERTO)
    resposta = await porta.chamar(pedido(formato=FormatoDeExemplo))
    assert isinstance(resposta.dados, FormatoDeExemplo)
    assert campo in provedor.pedidos[1].falas[-1].texto
    assert f"campos={campo}" in linhas(caplog)[0]


# 14. Resposta vazia


@pytest.mark.parametrize("formato", [FormatoDeExemplo, None], ids=["com_formato", "sem_formato"])
async def test_14_resposta_vazia_pede_de_novo(caplog, formato):
    porta, provedor, dormir = montar("   ", JSON_CERTO)
    resposta = await porta.chamar(pedido(formato=formato))
    assert resposta.texto == JSON_CERTO
    assert len(provedor.pedidos) == 2
    assert "problema=vazia" in linhas(caplog)[0]


# 15. Sem formato


async def test_15_sem_formato_devolve_o_texto_sem_conferir(caplog):
    porta, provedor, dormir = montar("Que bom! E quando o aperto é com dinheiro, como fica?")
    resposta = await porta.chamar(pedido(temperatura=0.7))
    assert resposta.texto.startswith("Que bom!")
    assert resposta.dados is None
    assert provedor.pedidos[0].temperatura == 0.7


# 16. O log


async def test_16_o_log_nao_tem_nada_da_conversa(caplog):
    valor_recusado = "a pessoa disse que é insegura"
    json_com_valor_recusado = (
        '{"capturas": [{"item": "frustracao", "valor": "' + valor_recusado + '", "trecho": "x", "certeza": "alta"}]}'
    )
    porta, provedor, dormir = montar(ErroLLM("fora_do_ar", "http_503"), json_com_valor_recusado, JSON_CERTO)
    await porta.chamar(pedido(formato=FormatoDeExemplo))
    eventos = linhas(caplog)
    # Uma linha por tentativa, cada uma com a etiqueta da conversa.
    assert len(eventos) == 3
    assert all("conversa=c12" in linha for linha in eventos)
    tudo = caplog.text
    for fala in FALAS:
        assert fala.texto not in tudo
    assert "plano B" not in tudo
    assert "insegura" not in tudo
    assert "frustracao" not in tudo


async def test_16_etiqueta_com_nome_de_campo_fixo_nao_troca_o_campo(caplog):
    porta, provedor, dormir = montar("oi")
    pedido_com_etiqueta = Pedido(agente="interprete", falas=FALAS, etiquetas={"agente": "outro", "conversa": "c12"})
    await porta.chamar(pedido_com_etiqueta)
    linha = linhas(caplog)[0]
    assert "agente=interprete" in linha
    assert "agente=outro" not in linha


async def test_fechar_fecha_o_provedor():
    porta, provedor, dormir = montar()
    await porta.fechar()
    assert provedor.fechado

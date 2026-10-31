"""Testes 17 a 20 do desenho (ficha 08): o adaptador do formato da OpenAI.

Sem internet e sem a chave de verdade: o servidor de mentira fica no lugar do DeepSeek.
"""

import json

import httpx
import pytest

from porta_llm import ErroLLM, Fala, Pedido, ProvedorOpenAI
from tests.formato_de_exemplo import JSON_CERTO, FormatoDeExemplo
from tests.servidor_de_mentira import ServidorDeMentira, erro_http, responde

pytestmark = pytest.mark.anyio

CHAVE = "chave-de-teste"
FALAS = [
    Fala(papel="system", texto="Você é o Intérprete. Responda só com o JSON."),
    Fala(papel="assistant", texto="Quando rola frustração, como você costuma reagir?"),
    Fala(papel="user", texto="No dia fico chateado, mas no outro já penso no plano B."),
]


def montar(*roteiro, url="https://api.deepseek.com"):
    servidor = ServidorDeMentira(*roteiro)
    provedor = ProvedorOpenAI(url=url, modelo="deepseek-flash", chave=CHAVE, cliente=servidor.cliente())
    return provedor, servidor


def pedido(formato=None) -> Pedido:
    return Pedido(agente="interprete", falas=FALAS, temperatura=0, tamanho_maximo=500, formato=formato)


# 17. O pedido sai no formato da OpenAI


@pytest.mark.parametrize("url", ["https://api.deepseek.com", "https://api.deepseek.com/"], ids=["sem_barra", "com_barra"])
async def test_17_pedido_vai_para_o_endereco_certo_com_a_chave_no_cabecalho(url):
    provedor, servidor = montar(responde("oi"), url=url)
    await provedor.enviar(pedido())
    enviado = servidor.pedidos[0]
    assert enviado.method == "POST"
    assert str(enviado.url) == "https://api.deepseek.com/chat/completions"
    assert enviado.headers["authorization"] == f"Bearer {CHAVE}"
    # A chave vai só no cabeçalho, nunca no endereço.
    assert CHAVE not in str(enviado.url)


async def test_17_corpo_do_pedido_no_formato_da_openai():
    provedor, servidor = montar(responde("oi"))
    await provedor.enviar(pedido())
    corpo = json.loads(servidor.pedidos[0].content)
    assert corpo["model"] == "deepseek-flash"
    assert corpo["messages"] == [{"role": f.papel, "content": f.texto} for f in FALAS]
    assert corpo["temperature"] == 0
    assert corpo["max_tokens"] == 500
    assert "response_format" not in corpo


async def test_17_pede_json_so_quando_tem_formato():
    provedor, servidor = montar(responde(JSON_CERTO))
    await provedor.enviar(pedido(formato=FormatoDeExemplo))
    corpo = json.loads(servidor.pedidos[0].content)
    assert corpo["response_format"] == {"type": "json_object"}


def test_17_o_cliente_de_verdade_espera_mais_que_os_30_s_da_casca():
    # O httpx desiste em 5 s se ninguém disser nada. Quem corta em 30 s é a casca.
    provedor = ProvedorOpenAI(url="https://api.deepseek.com", modelo="deepseek-flash", chave=CHAVE)
    assert provedor._cliente.timeout.read > 30


# 18. Lê a resposta


async def test_18_le_o_texto_o_modelo_e_os_tokens():
    provedor, servidor = montar(responde(JSON_CERTO, tokens=(1200, 80), modelo="deepseek-flash-2"))
    resposta = await provedor.enviar(pedido(formato=FormatoDeExemplo))
    assert resposta.texto == JSON_CERTO
    assert resposta.modelo == "deepseek-flash-2"
    assert (resposta.tokens_entrada, resposta.tokens_saida) == (1200, 80)
    # Conferir o JSON é com a casca, não com o adaptador.
    assert resposta.dados is None


# 19. Traduz os erros


@pytest.mark.parametrize(
    "roteiro, motivo, detalhe",
    [
        (erro_http(401), "chave_errada", "http_401"),
        (erro_http(403), "chave_errada", "http_403"),
        (erro_http(400), "pedido_recusado", "http_400"),
        (erro_http(402), "pedido_recusado", "http_402"),
        (erro_http(404), "pedido_recusado", "http_404"),
        (erro_http(422), "pedido_recusado", "http_422"),
        (erro_http(429), "fora_do_ar", "http_429"),
        (erro_http(500), "fora_do_ar", "http_500"),
        (erro_http(503), "fora_do_ar", "http_503"),
        (httpx.ConnectError("sem rede"), "fora_do_ar", "rede"),
        (httpx.ReadTimeout("demorou"), "fora_do_ar", "tempo_esgotado"),
    ],
    ids=[
        "401_chave_errada",
        "403_sem_permissao",
        "400_pedido_invalido",
        "402_sem_saldo",
        "404_modelo_ou_endereco_errado",
        "422_parametro_invalido",
        "429_pedidos_demais",
        "500_erro_no_servidor",
        "503_sobrecarregado",
        "rede_caiu",
        "tempo_esgotado",
    ],
)
async def test_19_traduz_os_erros(roteiro, motivo, detalhe):
    provedor, servidor = montar(roteiro)
    with pytest.raises(ErroLLM) as erro:
        await provedor.enviar(pedido())
    assert erro.value.motivo == motivo
    assert erro.value.detalhe == detalhe
    # Nem a chave nem a mensagem do servidor (que repete o fim da chave) saem no erro.
    assert CHAVE not in str(erro.value)
    assert "****" not in str(erro.value)


# 20. Resposta 200 sem o texto no lugar


@pytest.mark.parametrize(
    "resposta_estranha",
    [
        httpx.Response(200, json={"model": "deepseek-flash", "choices": [{"message": {"role": "assistant", "content": None}}]}),
        httpx.Response(200, json={"model": "deepseek-flash", "choices": []}),
        httpx.Response(200, json={"algo": "diferente"}),
        httpx.Response(200, text="<html>não é JSON</html>"),
        httpx.Response(
            200,
            json={
                "model": 123,
                "choices": [{"message": {"content": 5}}],
                "usage": {"prompt_tokens": "muitos", "completion_tokens": -3},
            },
        ),
    ],
    ids=["texto_nulo", "sem_escolhas", "corpo_diferente", "corpo_que_nao_e_json", "tipos_estranhos"],
)
async def test_20_resposta_200_sem_texto_vira_resposta_vazia(resposta_estranha):
    provedor, servidor = montar(resposta_estranha)
    resposta = await provedor.enviar(pedido())
    assert resposta.texto == ""
    assert resposta.modelo == "deepseek-flash"
    assert (resposta.tokens_entrada, resposta.tokens_saida) == (0, 0)


async def test_fechar_fecha_o_cliente():
    provedor, servidor = montar()
    await provedor.fechar()
    assert provedor._cliente.is_closed

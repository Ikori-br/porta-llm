"""Teste 21 do desenho (ficha 08): a Porta inteira, sem rede.

A montagem, a casca e o adaptador de verdade, juntos. Só três coisas são de mentira:
o servidor (no lugar do DeepSeek), o dormir (para não esperar as pausas) e o .env de
teste (com a chave falsa).
"""

import json
import logging

import pytest

from porta_llm import ConfigLLM, Fala, Pedido, criar_porta
from tests.conftest import CHAVE_FALSA, ENV_DE_TESTE
from tests.dormir_de_mentira import DormirDeMentira
from tests.formato_de_exemplo import JSON_CERTO, FormatoDeExemplo
from tests.servidor_de_mentira import ServidorDeMentira, erro_http, responde

pytestmark = pytest.mark.anyio

FALAS = [
    Fala(papel="system", texto="Você é o Intérprete. Responda só com o JSON das capturas."),
    Fala(papel="assistant", texto="Quando rola frustração, como você costuma reagir?"),
    Fala(papel="user", texto="No dia fico chateado, mas no outro já penso no plano B."),
]


async def test_21_cai_depois_json_quebrado_depois_certo(ambiente_limpo, caplog):
    caplog.set_level(logging.INFO, logger="porta-llm")
    servidor = ServidorDeMentira(
        erro_http(503),                      # 1ª: o DeepSeek está sobrecarregado
        responde('{"capturas": [{"item": '),  # 2ª: responde, mas o JSON veio quebrado
        responde(JSON_CERTO),                # 3ª: responde certo
    )
    dormir = DormirDeMentira()
    porta = criar_porta(ConfigLLM(_env_file=ENV_DE_TESTE), cliente=servidor.cliente(), dormir=dormir)

    resposta = await porta.chamar(
        Pedido(agente="interprete", falas=FALAS, formato=FormatoDeExemplo, etiquetas={"conversa": "c12"})
    )

    # A Porta entrega o objeto conferido.
    assert isinstance(resposta.dados, FormatoDeExemplo)
    assert resposta.dados.capturas[0].item == "frustracao"
    assert resposta.tentativas == 3
    assert dormir.pausas == [2]

    # O que chegou no servidor: a chave do .env de teste no cabeçalho, e o terceiro pedido
    # com uma fala a mais, dizendo que o JSON veio quebrado.
    assert len(servidor.pedidos) == 3
    assert all(p.headers["authorization"] == f"Bearer {CHAVE_FALSA}" for p in servidor.pedidos)
    assert str(servidor.pedidos[0].url) == "https://api.exemplo.com/chat/completions"
    primeiro = json.loads(servidor.pedidos[0].content)
    terceiro = json.loads(servidor.pedidos[2].content)
    assert primeiro["model"] == "modelo-de-teste"
    assert terceiro["messages"][:-1] == primeiro["messages"]
    assert "JSON" in terceiro["messages"][-1]["content"]

    # O log: uma linha por tentativa, com a etiqueta da conversa.
    eventos = [r.getMessage() for r in caplog.records if r.name == "porta-llm"]
    assert len(eventos) == 3
    assert "evento=llm_falhou" in eventos[0] and "detalhe=http_503" in eventos[0]
    assert "evento=llm_json_invalido" in eventos[1]
    assert "evento=llm_respondeu" in eventos[2]
    assert all("conversa=c12" in linha for linha in eventos)

    # A chave e a conversa não aparecem em lugar nenhum: nem no log, nem na Resposta impressa.
    for lugar in (caplog.text, repr(resposta), str(resposta)):
        assert CHAVE_FALSA not in lugar
        assert "plano B" not in lugar
        assert "frustracao" not in lugar

    await porta.fechar()

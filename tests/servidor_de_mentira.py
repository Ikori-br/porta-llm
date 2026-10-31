"""O servidor de mentira: fica no lugar da internet e da API da LLM nos testes do adaptador.

Usa o httpx.MockTransport, que já vem no httpx: em vez de mandar o pedido pela rede, o
httpx entrega o pedido aqui. O servidor segue um roteiro, uma resposta por pedido:
- uma resposta HTTP pronta (as funções responde e erro_http, abaixo);
- um erro do httpx, como a rede caindo.

Anota cada pedido que chegou, para o teste conferir o que o adaptador mandou.
"""

import httpx


def responde(texto, tokens=(1200, 80), modelo="deepseek-flash") -> httpx.Response:
    """Uma resposta da LLM, no formato da OpenAI."""
    return httpx.Response(
        200,
        json={
            "id": "chamada-8f2c",
            "model": modelo,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": texto}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": tokens[0], "completion_tokens": tokens[1], "total_tokens": sum(tokens)},
        },
    )


def erro_http(status: int) -> httpx.Response:
    # Uma mensagem parecida com a do DeepSeek, que repete o fim da chave. Ela não pode sair do adaptador.
    return httpx.Response(status, json={"error": {"message": "Authentication Fails, your api key: ****este is invalid"}})


class ServidorDeMentira:
    def __init__(self, *roteiro):
        self._roteiro = list(roteiro)
        self.pedidos: list[httpx.Request] = []

    def cliente(self) -> httpx.AsyncClient:
        """Um cliente do httpx que fala com este servidor, e não com a internet."""
        return httpx.AsyncClient(transport=httpx.MockTransport(self._atender))

    def _atender(self, pedido: httpx.Request) -> httpx.Response:
        self.pedidos.append(pedido)
        if not self._roteiro:
            raise AssertionError("o roteiro acabou: chegaram mais pedidos do que o teste esperava")
        passo = self._roteiro.pop(0)
        if isinstance(passo, Exception):
            raise passo
        return passo

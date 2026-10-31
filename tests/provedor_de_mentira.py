"""O Provedor de mentira: fica no lugar do adaptador e da LLM nos testes da casca.

Segue um roteiro, um passo por tentativa:
- um texto: a LLM responde esse texto;
- um ErroLLM: a tentativa falha com esse erro;
- Demora(segundos): a LLM demora, e depois responde.

Anota cada pedido que recebeu, para o teste conferir o que a casca mandou.
"""

import asyncio

from porta_llm import ErroLLM, Pedido, Provedor, Resposta


class Demora:
    def __init__(self, segundos: float, texto: str = "respondi tarde"):
        self.segundos = segundos
        self.texto = texto


class ProvedorDeMentira(Provedor):
    modelo = "modelo-de-mentira"

    def __init__(self, *roteiro):
        self._roteiro = list(roteiro)
        self.pedidos: list[Pedido] = []
        self.fechado = False

    async def enviar(self, pedido: Pedido) -> Resposta:
        self.pedidos.append(pedido)
        if not self._roteiro:
            raise AssertionError("o roteiro acabou: a casca tentou mais vezes do que o teste esperava")
        passo = self._roteiro.pop(0)
        if isinstance(passo, ErroLLM):
            raise passo
        if isinstance(passo, Demora):
            await asyncio.sleep(passo.segundos)
            passo = passo.texto
        return Resposta(texto=passo, modelo=self.modelo, tokens_entrada=100, tokens_saida=20)

    async def fechar(self) -> None:
        self.fechado = True

"""A casca da Porta: o que é igual para qualquer LLM.

Espera até 30 s, tenta de novo até 3 vezes (pausas de 2 e 5 s), para na hora com chave
errada ou pedido recusado, confere a resposta e pede de novo uma vez, e escreve uma
linha de log por tentativa. Quem fala com a LLM de verdade é o Provedor.
"""

import asyncio
import re
import time

from pydantic import BaseModel, ValidationError

from porta_llm.erro_llm import ErroLLM
from porta_llm.fala import Fala
from porta_llm.pedido import Pedido
from porta_llm.provedor import Provedor
from porta_llm.registro import Registro
from porta_llm.resposta import Resposta

# Um pedaço do caminho de um campo só vai para o log se for um nome simples ou uma posição.
# O resto (uma chave inventada pela LLM, por exemplo) vira "?".
NOME_SIMPLES = re.compile(r"^[a-z_][a-z0-9_]{0,30}$")


class PortaLLM:
    TENTATIVAS = 3
    PAUSAS = (2, 5)

    def __init__(self, provedor: Provedor, dormir=asyncio.sleep, tempo_limite: float = 30, registro: Registro | None = None):
        self._provedor = provedor
        self._dormir = dormir
        self._tempo_limite = tempo_limite
        self._registro = registro or Registro()

    async def chamar(self, pedido: Pedido) -> Resposta:
        """Manda o pedido e devolve a resposta conferida, ou levanta ErroLLM com o motivo."""
        inicio = time.monotonic()
        contagem = _Contagem()

        resposta, ms = await self._enviar(pedido, contagem)
        dados, problema, campos = self._conferir(pedido, resposta)

        if problema:
            # Pede de novo uma vez, juntando no fim uma fala que diz o que veio errado.
            self._anotar_resposta(self._registro.aviso, "llm_json_invalido", pedido, resposta, contagem, ms, problema, campos)
            correcao = Fala(papel="user", texto=_texto_da_correcao(pedido, problema, campos))
            pedido_de_novo = pedido.model_copy(update={"falas": [*pedido.falas, correcao]})
            resposta, ms = await self._enviar(pedido_de_novo, contagem)
            dados, problema, campos = self._conferir(pedido, resposta)
            if problema:
                self._anotar_resposta(self._registro.erro, "llm_desistiu", pedido, resposta, contagem, ms, problema, campos, motivo="resposta_invalida")
                raise ErroLLM("resposta_invalida", problema)

        self._anotar_resposta(self._registro.info, "llm_respondeu", pedido, resposta, contagem, ms)
        return resposta.model_copy(
            update={"dados": dados, "tempo_ms": _ms_desde(inicio), "tentativas": contagem.total}
        )

    async def fechar(self) -> None:
        await self._provedor.fechar()

    async def _enviar(self, pedido: Pedido, contagem: "_Contagem") -> tuple[Resposta, int]:
        """Até 3 tentativas. Devolve a resposta e quanto tempo levou a tentativa que deu certo."""
        for vez in range(1, self.TENTATIVAS + 1):
            contagem.total += 1
            inicio = time.monotonic()
            try:
                resposta = await asyncio.wait_for(self._provedor.enviar(pedido), self._tempo_limite)
                return resposta, _ms_desde(inicio)
            except TimeoutError:
                erro = ErroLLM("fora_do_ar", "tempo_esgotado")
            except ErroLLM as recebido:
                erro = recebido

            campos = self._campos(pedido, self._provedor.modelo, contagem, _ms_desde(inicio))
            if erro.motivo != "fora_do_ar":
                # Chave errada ou pedido recusado: tentar de novo não adianta.
                self._registro.erro("llm_recusou", **campos, motivo=erro.motivo, detalhe=erro.detalhe)
                raise erro
            if vez == self.TENTATIVAS:
                self._registro.erro("llm_desistiu", **campos, motivo=erro.motivo, detalhe=erro.detalhe)
                raise erro
            self._registro.aviso("llm_falhou", **campos, detalhe=erro.detalhe)
            await self._dormir(self.PAUSAS[vez - 1])
        raise AssertionError("não chega aqui")

    @staticmethod
    def _conferir(pedido: Pedido, resposta: Resposta) -> tuple[BaseModel | None, str | None, list[str]]:
        """Devolve o objeto conferido, ou o problema (vazia, json_quebrado ou campos_errados) e os campos."""
        if not resposta.texto.strip():
            return None, "vazia", []
        if pedido.formato is None:
            return None, None, []
        try:
            return pedido.formato.model_validate_json(resposta.texto), None, []
        except ValidationError as erro:
            if any(e["type"] == "json_invalid" for e in erro.errors()):
                return None, "json_quebrado", []
            # Só o caminho de cada campo errado. O erro do Pydantic traz o valor que veio, e esse não sai daqui.
            return None, "campos_errados", sorted({_caminho(e["loc"]) for e in erro.errors()})

    def _anotar_resposta(self, escrever, evento, pedido, resposta, contagem, ms, problema=None, campos=(), motivo=None) -> None:
        escrever(
            evento,
            **self._campos(pedido, resposta.modelo, contagem, ms),
            tokens_entrada=resposta.tokens_entrada,
            tokens_saida=resposta.tokens_saida,
            motivo=motivo,
            problema=problema,
            campos=",".join(campos) or None,
        )

    @staticmethod
    def _campos(pedido: Pedido, modelo: str, contagem: "_Contagem", ms: int) -> dict:
        fixos = {"agente": pedido.agente, "modelo": modelo, "tentativa": contagem.total, "tempo_ms": ms}
        # As etiquetas vêm antes, e uma etiqueta com o nome de um campo fixo não troca o campo.
        reservados = {"evento", "agente", "modelo", "tentativa", "tempo_ms", "tokens_entrada", "tokens_saida",
                      "motivo", "detalhe", "problema", "campos"}
        etiquetas = {nome: valor for nome, valor in pedido.etiquetas.items() if nome not in reservados}
        return {**fixos, **etiquetas}


class _Contagem:
    """Quantas tentativas já foram, somando o pedir de novo."""

    def __init__(self):
        self.total = 0


def _ms_desde(inicio: float) -> int:
    return int((time.monotonic() - inicio) * 1000)


def _caminho(loc: tuple) -> str:
    partes = [str(p) if isinstance(p, int) or NOME_SIMPLES.match(str(p)) else "?" for p in loc]
    return ".".join(partes) or "tudo"


def _texto_da_correcao(pedido: Pedido, problema: str, campos: list[str]) -> str:
    if problema == "vazia":
        o_que = "veio vazia"
    elif problema == "json_quebrado":
        o_que = "não veio em JSON válido"
    else:
        o_que = "veio com estes campos faltando ou errados: " + ", ".join(campos)
    if pedido.formato is None:
        return f"A sua resposta anterior {o_que}. Responda de novo."
    return f"A sua resposta anterior {o_que}. Responda de novo só com o JSON, no formato pedido."

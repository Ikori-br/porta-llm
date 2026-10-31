"""O adaptador do formato da OpenAI, com o httpx.

Serve para quem fala nesse formato: o DeepSeek, o Gemini, a OpenAI, a Maritaca e o Ollama.
Só sabe mandar o pedido e trazer a resposta. Tentar de novo e conferir o JSON é com a casca.
"""

import httpx

from porta_llm.erro_llm import ErroLLM
from porta_llm.pedido import Pedido
from porta_llm.provedor import Provedor
from porta_llm.resposta import Resposta

# O httpx desiste em 5 s se ninguém disser nada. A LLM pode levar mais, e quem corta em 30 s
# é a casca. Este limite é só uma rede de segurança.
TEMPO_DO_CLIENTE = httpx.Timeout(40.0)


class ProvedorOpenAI(Provedor):
    def __init__(self, url: str, modelo: str, chave: str, cliente: httpx.AsyncClient | None = None):
        self.modelo = modelo
        self._endereco = url.rstrip("/") + "/chat/completions"
        self._chave = chave
        self._cliente = cliente or httpx.AsyncClient(timeout=TEMPO_DO_CLIENTE)

    async def enviar(self, pedido: Pedido) -> Resposta:
        corpo = {
            "model": self.modelo,
            "messages": [{"role": fala.papel, "content": fala.texto} for fala in pedido.falas],
            "temperature": pedido.temperatura,
            "max_tokens": pedido.tamanho_maximo,
        }
        if pedido.formato is not None:
            corpo["response_format"] = {"type": "json_object"}

        # "from None": o erro do httpx não vai junto, para nada do pedido escapar no ErroLLM.
        try:
            http = await self._cliente.post(
                self._endereco, json=corpo, headers={"Authorization": f"Bearer {self._chave}"}
            )
        except httpx.TimeoutException:
            raise ErroLLM("fora_do_ar", "tempo_esgotado") from None
        except httpx.TransportError:
            raise ErroLLM("fora_do_ar", "rede") from None

        if http.status_code in (401, 403):
            raise ErroLLM("chave_errada", f"http_{http.status_code}")
        if http.status_code == 429 or http.status_code >= 500:
            raise ErroLLM("fora_do_ar", f"http_{http.status_code}")
        if http.status_code != 200:
            # 400, 402 (sem saldo no DeepSeek), 404, 422 e o resto: tentar de novo não adianta.
            raise ErroLLM("pedido_recusado", f"http_{http.status_code}")
        return self._ler(http)

    async def fechar(self) -> None:
        await self._cliente.aclose()

    def _ler(self, http: httpx.Response) -> Resposta:
        """Tira o texto, o modelo e os tokens. Se o texto não estiver no lugar, volta vazio, e a casca pede de novo."""
        try:
            corpo = http.json()
        except ValueError:
            corpo = {}
        if not isinstance(corpo, dict):
            corpo = {}
        try:
            texto = corpo["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            texto = ""
        uso = corpo.get("usage") or {}
        return Resposta(
            texto=texto if isinstance(texto, str) else "",
            modelo=corpo.get("model") or self.modelo,
            tokens_entrada=uso.get("prompt_tokens") or 0,
            tokens_saida=uso.get("completion_tokens") or 0,
        )

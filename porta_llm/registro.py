"""O log da Porta: uma linha por acontecimento, no formato chave=valor.

É o mesmo Registro do conector-telegram e do motor, sem o configurar_logs: numa
biblioteca, quem configura o log (o formato, o horário e o nível) é o projeto que usa.

Nunca passe para cá a chave, o texto das falas, o texto da resposta nem os valores que
vieram errados.
"""

import json
import logging


class Registro:
    def __init__(self, nome: str = "porta-llm"):
        self._log = logging.getLogger(nome)

    def info(self, evento: str, **campos) -> None:
        self._escrever(logging.INFO, evento, campos)

    def aviso(self, evento: str, **campos) -> None:
        self._escrever(logging.WARNING, evento, campos)

    def erro(self, evento: str, **campos) -> None:
        self._escrever(logging.ERROR, evento, campos)

    def _escrever(self, nivel: int, evento: str, campos: dict) -> None:
        partes = [f"evento={evento}"]
        partes += [f"{chave}={_valor(valor)}" for chave, valor in campos.items() if valor is not None]
        self._log.log(nivel, " ".join(partes))


def _valor(valor) -> str:
    texto = str(valor)
    # Valores com espaço, aspas ou quebra de linha vão entre aspas, para a linha continuar legível.
    if not texto or any(c in texto for c in ' "=\n\r\t'):
        return json.dumps(texto, ensure_ascii=False)
    return texto

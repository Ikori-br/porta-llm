"""O que quem usa entrega à Porta: as falas e como a LLM deve responder."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from porta_llm.fala import Fala

# O nome de uma etiqueta vira um nome no log (conversa=c12): só letras minúsculas, números e "_".
NOME_DE_ETIQUETA = r"^[a-z][a-z0-9_]*$"


class Pedido(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Só um nome para o log, como "interprete". A Porta não sabe o que ele é.
    agente: str = Field(min_length=1)
    falas: list[Fala] = Field(min_length=1)
    # O quanto a resposta varia. Com 0, ela fica mais previsível.
    temperatura: float = Field(default=0, ge=0, le=2)
    # O máximo de tokens da resposta, que também limita o custo.
    tamanho_maximo: int = Field(default=500, gt=0)
    # Um modelo do Pydantic. Com ele, a Porta pede JSON e confere cada campo. Sem ele, volta só o texto.
    formato: type[BaseModel] | None = None
    # Vão em toda linha do log, como conversa=c12. Nunca ponha texto da conversa aqui.
    etiquetas: dict[str, str] = Field(default_factory=dict)

    @field_validator("etiquetas")
    @classmethod
    def _nomes_simples(cls, etiquetas: dict[str, str]) -> dict[str, str]:
        for nome in etiquetas:
            if not re.match(NOME_DE_ETIQUETA, nome):
                raise ValueError(f"o nome da etiqueta precisa ser simples, como conversa: {nome!r}")
        return etiquetas

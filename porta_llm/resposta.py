"""O que a Porta devolve: o texto, o objeto conferido e quanto custou em tokens e tempo."""

from pydantic import BaseModel, ConfigDict, Field


class Resposta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # repr=False no texto e nos dados: o que a LLM respondeu não aparece quando a Resposta é impressa.
    texto: str = Field(repr=False)
    # O modelo que respondeu de verdade, como a LLM informou.
    modelo: str
    tokens_entrada: int = Field(ge=0)
    tokens_saida: int = Field(ge=0)
    # O objeto já conferido, quando o pedido tinha formato.
    dados: BaseModel | None = Field(default=None, repr=False)
    # Quanto tempo levou, somando todas as tentativas.
    tempo_ms: int = Field(default=0, ge=0)
    tentativas: int = Field(default=1, ge=1)

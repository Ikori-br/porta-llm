"""O formato de exemplo: um formato pequeno, parecido com o das capturas do Intérprete.

O formato de verdade é do motor. Este serve só para testar a conferência do JSON.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Captura(BaseModel):
    item: str
    valor: int = Field(ge=1, le=5)
    trecho: str
    certeza: Literal["baixa", "media", "alta"]


class FormatoDeExemplo(BaseModel):
    capturas: list[Captura]


# Uma resposta certa nesse formato.
JSON_CERTO = (
    '{"capturas": [{"item": "frustracao", "valor": 4,'
    ' "trecho": "no outro dia já penso no plano B", "certeza": "alta"}]}'
)

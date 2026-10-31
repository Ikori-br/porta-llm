"""Uma mensagem da lista que vai para a LLM."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Fala(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # system: as instruções. user: o que a pessoa disse. assistant: o que o bot já respondeu.
    papel: Literal["system", "user", "assistant"]
    # repr=False: o texto não aparece quando a Fala é impressa, para não vazar no log por engano.
    texto: str = Field(repr=False)

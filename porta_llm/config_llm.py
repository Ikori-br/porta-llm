"""A configuração da Porta, lida das variáveis LLM_ de quem usa.

No servidor, quem entrega essas variáveis é o Docker Compose, a partir do .env.
Para testar, dá para apontar um arquivo: ConfigLLM(_env_file="caminho/do/arquivo").
"""

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigLLM(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    # Qual adaptador usar.
    formato: str = "openai"
    # O endereço da API.
    url: str = "https://api.deepseek.com"
    modelo: str = "deepseek-flash"
    # Segredo: só no .env do servidor. O SecretStr mostra ********** quando a configuração é impressa.
    chave: SecretStr | None = None

    @model_validator(mode="after")
    def _tem_chave(self) -> "ConfigLLM":
        if self.chave is None or not self.chave.get_secret_value():
            raise ValueError("falta a LLM_CHAVE. Ela fica só no .env do servidor")
        return self

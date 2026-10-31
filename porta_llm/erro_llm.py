"""O único erro da Porta. O motivo diz o que aconteceu, e quem usa decide o que fazer."""

import re


class ErroLLM(Exception):
    MOTIVOS = ("fora_do_ar", "chave_errada", "pedido_recusado", "resposta_invalida")
    # O detalhe é um código curto, como http_503 ou tempo_esgotado. Assim não cabe nele
    # a chave, o texto das falas nem um pedaço da resposta.
    DETALHE = r"^[a-z0-9_]{0,30}$"

    def __init__(self, motivo: str, detalhe: str = ""):
        if motivo not in self.MOTIVOS:
            raise ValueError(f"motivo desconhecido: {motivo}. Os motivos são: {', '.join(self.MOTIVOS)}")
        if not re.match(self.DETALHE, detalhe):
            raise ValueError("o detalhe precisa ser um código curto, como http_503")
        self.motivo = motivo
        self.detalhe = detalhe
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)

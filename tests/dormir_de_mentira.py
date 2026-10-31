"""O dormir de mentira: fica no lugar do asyncio.sleep. Anota as pausas sem esperar."""


class DormirDeMentira:
    def __init__(self):
        self.pausas: list[float] = []

    async def __call__(self, segundos: float) -> None:
        self.pausas.append(segundos)

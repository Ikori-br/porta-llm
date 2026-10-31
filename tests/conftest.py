import pytest


@pytest.fixture
def anyio_backend():
    # Os testes assíncronos rodam com o asyncio, o mesmo que a Porta usa de verdade.
    return "asyncio"

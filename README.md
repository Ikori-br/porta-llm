# porta-llm

A Porta da LLM: o único lugar que chama uma LLM. Quem usa entrega um pedido pronto (as falas, a temperatura e o formato esperado) e recebe a resposta já conferida. No caminho, a Porta espera, tenta de novo quando a LLM falha, confere o JSON e escreve uma linha de log por tentativa.

É uma **biblioteca de Python**: o projeto que usa instala e importa, e ela roda dentro dele. Nasceu para o motor do chatbot Ikori, mas não sabe nada dele, e serve para qualquer projeto.

> **Em construção.** Etapa 1: as peças estão prontas (passos 1 a 5). Faltam o teste do caminho completo e o envio para o GitHub. O desenho está na ficha 08 do projeto.

```
 quem usa (o motor, por exemplo)
      │ Pedido
      ▼
 PortaLLM ──────── a casca: espera até 30 s, tenta de novo até 3 vezes,
      │            confere o JSON e escreve o log
      ▼
 Provedor ──────── a interface: manda o pedido e traz a resposta
      │
      ▼
 ProvedorOpenAI ── fala no formato da OpenAI, com o httpx
      │
      ▼
 a LLM (DeepSeek, Gemini, OpenAI, Maritaca, Ollama...)
```

## Como usar

```python
from porta_llm import Fala, Pedido, criar_porta

porta = criar_porta()  # lê LLM_FORMATO, LLM_URL, LLM_MODELO e LLM_CHAVE do ambiente

resposta = await porta.chamar(Pedido(
    agente="interprete",
    falas=[
        Fala(papel="system", texto="Você é o Intérprete... Responda só com o JSON."),
        Fala(papel="user", texto="No dia fico chateado, mas no outro já penso no plano B."),
    ],
    temperatura=0,
    tamanho_maximo=500,
    formato=Capturas,              # um modelo do Pydantic, de quem usa
    etiquetas={"conversa": "c12"},
))

resposta.dados          # o objeto Capturas, já conferido
resposta.texto          # o texto que a LLM devolveu
resposta.modelo         # o modelo que respondeu
resposta.tokens_entrada, resposta.tokens_saida
resposta.tempo_ms, resposta.tentativas

await porta.fechar()    # quando o projeto desliga
```

### O pedido

| Campo | O que é | Padrão |
|---|---|---|
| `agente` | Um nome para o log, como `interprete`. A Porta não sabe o que ele é | obrigatório |
| `falas` | A lista que vai para a LLM. Cada `Fala` tem o papel e o texto. O papel é `system` (as instruções), `user` (o que a pessoa disse) ou `assistant` (o que o bot já respondeu) | obrigatório, pelo menos uma |
| `temperatura` | O quanto a resposta varia, de 0 a 2. Com 0, ela fica mais previsível | 0 |
| `tamanho_maximo` | O máximo de tokens da resposta, que também limita o custo | 500 |
| `formato` | Um modelo do Pydantic. Com ele, a Porta pede a resposta em JSON e confere cada campo | nenhum: volta só o texto |
| `etiquetas` | Pares que vão em toda linha do log, como `conversa=c12`. Nunca ponha texto da conversa aqui | nenhuma |

- **Com formato, a Porta pede a resposta em JSON.** O DeepSeek e a OpenAI exigem que a palavra "json" apareça nas instruções. Isso fica com quem escreve as instruções.
- **A temperatura vem de quem chama.** A Porta só repassa.

## Configuração

A Porta lê as variáveis `LLM_` do ambiente de quem usa. No servidor, quem entrega essas variáveis é o Docker Compose, a partir do `.env`. Para testar, dá para apontar um arquivo: `ConfigLLM(_env_file="caminho/do/arquivo")`.

| Variável | O que é | Padrão |
|---|---|---|
| `LLM_FORMATO` | Qual adaptador usar | `openai` |
| `LLM_URL` | O endereço da API | `https://api.deepseek.com` |
| `LLM_MODELO` | O modelo | `deepseek-flash` |
| `LLM_CHAVE` | A chave da API. **Segredo:** só no `.env` do servidor. Nunca vai para o GitHub nem para o log | obrigatória |

## Quando algo dá errado

| O que aconteceu | O que a Porta faz |
|---|---|
| A LLM demorou mais de 30 s, a rede caiu, ou a LLM respondeu 429 (pedidos demais) ou 5xx (fora do ar) | Tenta de novo, até 3 vezes no total, com uma pausa de 2 s e depois de 5 s. Se as 3 falharem, dá `ErroLLM` com o motivo `fora_do_ar` |
| 401 ou 403: a chave está errada | `ErroLLM` com o motivo `chave_errada` na hora, sem tentar de novo |
| 400, 404 ou 422: o pedido foi recusado (um modelo que não existe, por exemplo) | `ErroLLM` com o motivo `pedido_recusado` na hora, sem tentar de novo |
| O JSON veio quebrado, vazio, faltando campo ou com um tipo errado | Pede de novo uma vez, dizendo à LLM quais campos vieram errados. Se errar de novo, dá `ErroLLM` com o motivo `resposta_invalida` |

- **Um erro só, com o motivo.** O `ErroLLM` tem o `motivo` (um dos quatro acima) e o `detalhe` (como `http_503`). Quem usa decide o que fazer com cada motivo.
- **O pior caso:** um pedido pode levar uns 97 s (3 tentativas de 30 s e as pausas), e o dobro se o JSON vier errado.

## O que a Porta nunca faz

- Não sabe nada de quem usa: nem do motor, nem dos questionários, nem do método.
- Não guarda nada em banco. Ela devolve os tokens e o tempo, e quem usa decide se guarda.
- Não escreve no log a chave, o texto das falas, o texto da resposta nem os valores que vieram errados.
- Não configura o log de quem usa: ela só escreve no logger `porta-llm`.

## As peças

Um objeto por arquivo, cada um com uma responsabilidade. As peças recebem as ferramentas quando são criadas, e é isso que permite testar cada uma com ferramentas de mentira.

| Objeto | Arquivo | Responsável por |
|---|---|---|
| PortaLLM | `porta_llm/porta.py` | A casca: esperar, tentar de novo, conferir o JSON e escrever o log |
| Provedor | `porta_llm/provedor.py` | A interface que todo adaptador segue |
| ProvedorOpenAI | `porta_llm/provedor_openai.py` | Falar no formato da OpenAI, com o httpx |
| Fala, Pedido, Resposta | `porta_llm/fala.py`, `porta_llm/pedido.py`, `porta_llm/resposta.py` | Os formatos do que entra e do que sai |
| ErroLLM | `porta_llm/erro_llm.py` | O único erro da Porta, com o motivo |
| ConfigLLM | `porta_llm/config_llm.py` | Ler as variáveis `LLM_` do `.env` |
| Montagem | `porta_llm/montar.py` | `criar_porta()`: escolher o adaptador e entregar a Porta pronta |
| Registro | `porta_llm/registro.py` | Escrever o log no formato `chave=valor` |

## Logs

Uma linha por tentativa, no formato `chave=valor` (o mesmo do conector-telegram e do motor), no logger `porta-llm`. As linhas caem no log de quem usa:

```
2026-10-31T14:02:11Z AVISO porta-llm evento=llm_falhou agente=interprete modelo=deepseek-flash tentativa=1 motivo=http_503 tempo_ms=812 conversa=c12
2026-10-31T14:02:16Z INFO porta-llm evento=llm_respondeu agente=interprete modelo=deepseek-flash tentativa=2 tokens_entrada=1200 tokens_saida=80 tempo_ms=2300 conversa=c12
```

| Evento | Nível | Quando |
|---|---|---|
| `llm_respondeu` | INFO | Deu certo: os tokens e o tempo |
| `llm_falhou` | AVISO | Uma tentativa falhou e a Porta vai tentar de novo: o motivo e o tempo |
| `llm_json_invalido` | AVISO | O JSON veio errado e a Porta vai pedir de novo: os nomes dos campos errados |
| `llm_desistiu` | ERRO | Acabaram as tentativas: `fora_do_ar` ou `resposta_invalida` |
| `llm_recusou` | ERRO | Chave errada ou pedido recusado: o motivo e o código HTTP |

## Testes

Nenhum teste usa a internet, a chave de verdade ou uma LLM, e nenhum custa nada. No lugar delas entram peças de mentira:

| De mentira | No lugar de |
|---|---|
| Provedor de mentira | O adaptador e a LLM, nos testes da casca |
| Servidor de mentira (`httpx.MockTransport`) | A internet e a API, nos testes do adaptador |
| Dormir de mentira | As pausas de 2 e 5 s, para o teste não esperar |
| Formato de exemplo | O formato de quem usa, para testar a conferência do JSON |
| `.env` de teste | A chave de verdade. A chave falsa é procurada no log e nos erros |

Cada objeto tem o seu arquivo de teste, e os números nos nomes dos testes são os da ficha 08. Para rodar:

```
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

No GitHub, os testes rodam sozinhos a cada envio (`.github/workflows/testes.yml`).

## Como instalar num projeto

Fica para a etapa 3, junto com o motor: o repositório é privado, e o Docker precisa de uma forma de baixá-lo sem guardar segredo no GitHub.

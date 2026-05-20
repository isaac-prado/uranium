# Uranium

Pipeline multi-agente de **Engenharia de Software 3.0** que valida o fluxo de desenvolvimento assistido por IA. Orquestra agentes especializados via **LangGraph** com observabilidade via **LangSmith**.

## Arquitetura

```
START → IntentRefiner → [Clarification ↔ IntentRefiner]* → Developer → Validator → [Developer]* → TestGenerator → END
```

| Agente            | Responsabilidade                                  |
| ----------------- | ------------------------------------------------- |
| **IntentRefiner** | Converte solicitação em intent estruturada        |
| **Clarification** | Resolve ambiguidades (respostas simuladas na POC) |
| **Developer**     | Gera artefatos de desenvolvimento                 |
| **Validator**     | Valida artefatos vs critérios de aceitação        |
| **TestGenerator** | Gera plano e casos de teste                       |

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Conta [OpenRouter](https://openrouter.ai/) (LLM)
- Conta [LangSmith](https://smith.langchain.com/) (observabilidade, opcional)

## Configuração

```bash
cp .env.example .env
# Edite .env com suas chaves
uv sync
```

Variáveis principais:

| Variável                   | Descrição                                   |
| -------------------------- | ------------------------------------------- |
| `OPENROUTER_API_KEY`       | Chave da API OpenRouter                     |
| `OPENROUTER_MODEL_NAME`    | Modelo **free** com sufixo `:free`          |
| `AUTO_JSON_FALLBACK_FOR_FREE` | `true` — JSON direto em modelos free   |
| `LLM_MAX_TOKENS`           | Limite de tokens por chamada (ex: `2048`)   |
| `LANGCHAIN_TRACING_V2`     | `true` para ativar LangSmith                |
| `LANGCHAIN_API_KEY`        | Chave LangSmith                             |
| `LANGCHAIN_PROJECT`        | Nome do projeto no LangSmith                |

### Modelos 100% gratuitos (OpenRouter)

Todos abaixo têm **custo $0** (tier `:free`). Lista completa em [openrouter.ai/collections/free-models](https://openrouter.ai/collections/free-models).

| Modelo | Velocidade | Uso recomendado |
|--------|------------|-----------------|
| `qwen/qwen-2.5-7b-instruct:free` | Rápido | **Padrão da POC** |
| `google/gemma-2-9b-it:free` | Rápido | Testes rápidos |
| `meta-llama/llama-3.3-70b-instruct:free` | Médio | Melhor qualidade free |
| `nvidia/nemotron-3-super-120b-a12b:free` | Muito lento | Evitar — filas longas |
| `openrouter/free` | Variável | Roteador automático free |

```env
OPENROUTER_MODEL_NAME=qwen/qwen-2.5-7b-instruct:free
AUTO_JSON_FALLBACK_FOR_FREE=true
```

O Uranium detecta modelos `:free` e usa **fallback JSON** automaticamente (evita o erro `choices=None` do Nemotron e similares).

## Uso

```bash
# Pipeline completo (CLI)
uv run python scripts/run_pipeline.py "Criar CRUD de Cliente com nome, CPF e email"

# Saída JSON
uv run python scripts/run_pipeline.py "Criar API de produtos" -o json

# Testes unitários (sem chamadas à API)
uv run pytest tests/ -v
```

## Estrutura

```
src/
├── config.py          # LLM factory + limites de iteração
├── state.py           # WorkflowState compartilhado
├── graph.py           # Grafo LangGraph
├── schemas/           # Pydantic models
└── agents/            # Nós do grafo
scripts/
└── run_pipeline.py    # CLI
tests/                 # Testes com mocks
```

## Observabilidade (LangSmith)

Com `LANGCHAIN_TRACING_V2=true`, cada execução registra automaticamente:

- Nós executados e ordem
- Prompts e respostas estruturadas
- Tokens, latência e custo estimado

Acesse [smith.langchain.com](https://smith.langchain.com/) no projeto `uranium-poc`.

## Desenvolvimento

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

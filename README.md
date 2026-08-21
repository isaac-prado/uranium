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

| Variável                  | Descrição                                                     |
| ------------------------- | ------------------------------------------------------------- |
| `OPENROUTER_API_KEY`      | Chave da API OpenRouter                                        |
| `OPENROUTER_MODEL_NAME`   | Modelo **pago**; tier `:free` é recusado                       |
| `OPENROUTER_PROVIDER`     | Provedor único a pinar (`provider.only`)                       |
| `LLM_SEED`                | Semente fixa, para reprodutibilidade                           |
| `LLM_TEMPERATURE`         | `0` nos dois braços do estudo                                  |
| `LLM_MAX_TOKENS`          | Teto por chamada (padrão `8192`)                               |
| `STRUCTURED_OUTPUT_METHOD`| `function_calling` (mesmo mecanismo das ferramentas)           |
| `RUN_MAX_TOKENS`          | Orçamento de tokens por run (circuit breaker)                  |

### Escolha do modelo

O modelo não é fixado no código: ele é escolhido por um **teste de aptidão**
que mede conformidade de tool calling, estabilidade do provedor servido e
determinismo.

```bash
# quais provedores servem um modelo
uv run python scripts/fitness_test.py --list-providers vendor/modelo

# laudo de aptidão (5 sondagens)
uv run python scripts/fitness_test.py --model vendor/modelo --provider Fireworks -n 5
```

O cliente é montado com `provider.only`, `allow_fallbacks: false`,
`require_parameters: true` e `data_collection: deny`. Se o provedor pinado
não puder atender, o OpenRouter devolve erro em vez de servir por outro —
o pino é auto-verificável.

Não há reparo de JSON degradado: se o modelo não conformar ao schema, o erro
sobe e é contabilizado. Consertar a saída do agente por fora contaminaria a
comparação entre os braços.

## Benchmark (estudo E1)

```bash
# espelho local do repositório-semente (único passo que usa rede)
uv run python scripts/setup_mirror.py tomlkit
```

O repositório-semente é o **tomlkit** (MIT, ~4.6k LOC, 1030 testes em 1,5s,
zero dependências de runtime). Cada tarefa materializa um clone isolado num
commit-base, via `Workspace.materialize()`, com testes e configuração
protegidos contra escrita pelo agente.

## Uso

```bash
# Pipeline completo — exporta código para output/latest/ (padrão)
uv run python scripts/run_pipeline.py "Criar CRUD de Cliente com nome, CPF e email"

# Ver trecho do código no terminal
uv run python scripts/run_pipeline.py "Criar API de produtos" --show-code

# Só terminal, sem gravar arquivos
uv run python scripts/run_pipeline.py "Criar API" --no-export

# Saída JSON (inclui metadados de exportação)
uv run python scripts/run_pipeline.py "Criar API de produtos" -o json
```

### Artefatos exportados

Após cada execução com `--export` (padrão):

```
output/
├── latest/              ← abra esta pasta no IDE
│   ├── manifest.json    ← resumo (goal, validação, lista de arquivos)
│   ├── pipeline_state.json
│   ├── artifacts/       ← código gerado pelo DeveloperAgent
│   └── tests/           ← testes do TestAgent
└── runs/<timestamp>/    ← histórico de execuções
```

`output/` está no `.gitignore` interno — não polui o repositório, mas fica local para revisão e TCC.

```bash
# Testes unitários (sem chamadas à API)
uv run pytest tests/ -v
```

## Estrutura

```
src/
├── config.py          # LLM com provedor pinado + métricas de chamada
├── workspace.py       # Clone isolado do repo-semente num commit-base
├── seeds.py           # Especificação dos repositórios-semente
├── tools/             # Ferramentas do agente (fs + execução de testes)
├── state.py           # WorkflowState compartilhado
├── graph.py           # Grafo LangGraph
├── schemas/           # Pydantic models
└── agents/            # Nós do grafo
scripts/
├── setup_mirror.py    # Espelhos bare locais dos repos-semente
├── fitness_test.py    # Teste de aptidão de modelo
└── run_pipeline.py    # CLI
tests/                 # Testes (unitários + integração sobre workspace real)
```

## Observabilidade

A telemetria oficial do estudo é **JSONL local**, por evento, gravada durante
o run — não depende de serviço externo nem de rede. O LangSmith continua
disponível como apoio de depuração (`LANGSMITH_TRACING=true`), mas nenhuma
métrica reportada no TCC vem dele.

Cada chamada de LLM registra tokens (prompt/completion/reasoning), custo em
USD devolvido pelo OpenRouter (`usage.include`), provedor servido e latência.

## Desenvolvimento

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

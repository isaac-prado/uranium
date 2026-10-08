# Uranium

Pipeline multi-agente de **Engenharia de Software 3.0**: agentes especializados
orquestrados em **LangGraph** que agem sobre um repositório Python real —
leem, editam e executam a suíte de testes. É o braço `orchestration` do
estudo E1, comparado contra um agente único (braço `single-agent`) sob o
mesmo modelo, ferramentas e tarefas.

## Arquitetura

```
START → IntentRefiner → [Clarification ↔ IntentRefiner]* → Developer → Validator → [Developer]* → TestGenerator → END
```

Este é o grafo do braço `orchestration` ([src/graph.py](src/graph.py)). O braço
`single-agent` tem topologia própria, de dois nós — ver "Os dois braços",
abaixo.

| Agente            | Responsabilidade                                                     |
| ----------------- | --------------------------------------------------------------------- |
| **IntentRefiner** | Converte solicitação em intent estruturada                            |
| **Clarification** | Resolve ambiguidades da intent com respostas simuladas                |
| **Developer**     | Edita o repositório real por ferramentas (loop de tool calling); o artefato é o diff do workspace |
| **Validator**     | Roda a suíte de testes; só pode rebaixar o veredito por revisão semântica, nunca promovê-lo |
| **TestGenerator** | Gera plano de testes complementar (não conta como oráculo)            |

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Conta [OpenRouter](https://openrouter.ai/) (LLM)

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

O estudo tem dois braços, executados pelo mesmo runner — muda só o grafo:

```bash
# braço orchestration — multiagente com papéis especializados
uv run python scripts/run_arm.py --arm orchestration --task tomlkit-0001 \
    --base-commit 11e22aefccd8069a90ae75d20613b9b1068754a1 \
    --statement "Levantar erro em elemento malformado de array."

# braço single-agent — agente único, dirigido por política determinística
uv run python scripts/run_arm.py --arm single-agent --task tomlkit-0001 \
    --base-commit 11e22aefccd8069a90ae75d20613b9b1068754a1 \
    --statement-file tasks/tomlkit-0001/statement.md
```

### Coleta definitiva e análise

```bash
# todas as tarefas de tasks/ × 2 braços × 3 repetições; retomável
uv run python scripts/run_collection.py --repetitions 3 --workers 2
uv run python scripts/run_collection.py --dry-run      # só mostra o estado

# teste de sinal e Wilcoxon pareados por tarefa, exatos
uv run python scripts/analyze_collection.py --out runs/collection

# avaliar um run avulso
uv run python -m harness.evaluate --run-dir <run_dir> --task tasks/tomlkit-0001
```

A coleta grava em `runs/collection/<tarefa>/<braço>/repNN/attemptNN/` e lê
o próprio estado do disco: interromper e rodar de novo executa só o que
falta. Run perdido por infraestrutura (429, chave revogada, 5xx, timeout)
termina com `stop_reason: infra_error: ...` (Ctrl+C: `interrupted: ...`), fica
gravado como evidência e é reexecutado até `--max-attempts` por execução.
Célula que esgota as tentativas sai do denominador junto com o par dela, e é
tentada de novo na próxima execução. Chave revogada ou crédito esgotado (401,
402) param a coleta na hora; `--max-consecutive-lost` células perdidas em
sequência também.

Cada run grava em `runs/<arm>/<task>/<run_id>/`:

| Arquivo | Conteúdo |
| --- | --- |
| `manifest.json` | configuração resolvida — modelo, provedor, seed, orçamento, topologia |
| `events.jsonl` | telemetria por evento |
| `summary.json` | resultado, turnos, tokens, custo |
| `patch.diff` | o diff produzido pelo agente |
| `workspace/` | repositório modificado, entregue ao harness |

### Os dois braços

| | **single-agent** | **orchestration** |
| --- | --- | --- |
| Topologia | agente único, sem papéis | grafo multiagente com papéis |
| Operador | `DeterministicDriver` (política fixa) | autônomo |
| `agent_role` na telemetria | `null` | preenchido |
| Modelo, ferramentas, orçamento, seed | idênticos | idênticos |

A política do driver do `single-agent` é fixa e vai inteira para o manifesto:
entrega a especificação uma vez, aceita todo patch sem revisão, roda a suíte quando o
agente para de agir, e devolve o **stderr cru** em caso de falha — sem
sumarizar nem sugerir, porque isso seria engenharia do harness creditada ao
agente.

`tests/test_arm_parity.py` verifica por execução que os manifestos dos dois
braços só divergem em `arm`, `topology`, `driver_policy`, `run_id` e
`started_at`. Qualquer outra divergência derruba a suíte.

## Estrutura

```
src/
├── config.py             # LLM com provedor pinado + métricas de chamada
├── workspace.py          # Clone isolado do repo-semente num commit-base
├── seeds.py              # Especificação dos repositórios-semente
├── budget.py             # Orçamento do run (turnos, tokens, tempo) — circuit breaker
├── runtime.py            # RunContext: liga estado, telemetria, LLM e workspace por run_id
├── telemetry.py          # Telemetria JSONL, um evento por linha
├── structured_llm.py     # invoke_structured(): saída estruturada por function calling
├── prompts.py            # Prompt do agente que escreve código, comum aos dois braços
├── tools/                # Ferramentas do agente (fs + execução de testes)
├── state.py              # WorkflowState compartilhado
├── graph.py              # Grafo LangGraph do braço orchestration
├── arms/                 # Braço single-agent, runner comum aos dois braços, piloto
├── schemas/              # Pydantic models
└── agents/               # Nós do grafo do braço orchestration
harness/                  # Avaliador externo — isolado de src/, roda sem rede
scripts/
├── setup_mirror.py       # Espelho bare local + ambiente de teste de um repo-semente
├── fitness_test.py       # Teste de aptidão de modelo (tool calling, pino, determinismo)
├── run_arm.py            # CLI do estudo: executa um braço sobre uma tarefa
├── run_pilot.py          # Piloto: roda os dois braços na mesma tarefa e compara
├── run_collection.py     # Coleta definitiva: tarefas × braços × repetições, retomável
├── analyze_collection.py # Estado da coleta: pares perdidos e censura por braço
├── mine_tasks.py         # Minera candidatos a tarefa no histórico do repo-semente
├── emit_task.py          # Gera o diretório de uma tarefa a partir de um candidato minerado
├── validate_task.py      # Portão de validação de uma tarefa
├── context_accounting.py # Reconstrói a composição do prompt a partir de events.jsonl
└── analyze_results.py    # Análise pareada dos result.json (as sete métricas do estudo)
tests/                    # Testes (unitários + integração sobre workspace real)
```

## Observabilidade

A telemetria é **JSONL local, por evento** (`src/telemetry.py`), gravada com
`flush + fsync` a cada linha e validada contra
`harness/schema/event.schema.json`. Não há tracing remoto: nenhuma
dependência de rede além do próprio OpenRouter entra no caminho de coleta.

Cada chamada de LLM registra tokens (prompt/completion/reasoning), custo em
USD devolvido pelo OpenRouter (`usage.include`), provedor servido e latência.
Cada uso de ferramenta registra duração, bytes lidos/escritos e se houve
recusa por caminho protegido.

O LangSmith foi removido deliberadamente. Ele acrescentava um ponto de falha
externo ao caminho de medição — e, na prática, estava respondendo 403 sem
gravar nada. `src/config.py` desliga o tracing do LangChain de forma
incondicional no import, para que uma variável de ambiente perdida não o
reative no meio de uma coleta.

## Desenvolvimento

```bash
uv sync --extra dev --extra harness
uv run pytest tests/ -v
```

## Documentação do estudo

A metodologia do TCC, etapa por etapa (o que cada uma verifica, na ordem em
que foi feita), está em [docs/tcc/00-guia-etapas.md](docs/tcc/00-guia-etapas.md).
O inventário de fato sobre o estado do repositório — o que existe, o que é
placeholder, contradições entre código e documentação — está em
[docs/tcc/01-inventario.md](docs/tcc/01-inventario.md).

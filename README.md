# Uranium

Instrumento de um experimento controlado sobre topologias de agentes de IA
que corrigem defeitos reais em repositórios Python: um **agente único** com
operador determinístico (braço `single-agent`) contra uma **orquestração de
papéis** em LangGraph (braço `orchestration`), com o mesmo modelo, o mesmo
prompt de sistema, as mesmas ferramentas na mesma ordem, o mesmo orçamento e a
mesma semente por repetição. Só a topologia varia; um teste de paridade falha
se qualquer outra coisa divergir.

**Estado (04/11/2026).** Coleta fechada em três modelos de dois laboratórios
(Qwen3-Coder, DeepSeek V3.2, Devstral 2): 13 tarefas × 3 repetições × 2
braços × 3 modelos, 234 runs finais, 117 pares com a mesma semente, depois de
nove rodadas de engenharia e mais de 580 runs. Na taxa de resolução, desfecho
primário, não há diferença detectável (80 contra 77 runs, McNemar p = 0,70,
igual nos três modelos). O orquestrado gasta 29% menos dólares na carga
inteira, tem custo de falha limitado (pior run 2,9 M tokens contra 8,1 M),
vence a tarefa de funcionalidade nova de longo horizonte (7/9 contra 2/9) e
perde onde o plano serializa defeitos independentes (0/9 contra 4/9).
Relatório completo em [docs/tcc/27-relatorio-cientifico.md](docs/tcc/27-relatorio-cientifico.md);
análise exploratória em [28](docs/tcc/28-exploratorio-orquestrado.md).

## Arquitetura

```
START → IntentRefiner → [Clarification ↔ IntentRefiner]* → Planner → Developer → Validator → [Developer]* → TestGenerator → END
```

Grafo do braço `orchestration` ([src/graph.py](src/graph.py)), na configuração
da rodada 4 usada na replicação. O braço `single-agent` tem dois nós: o agente
e o operador ([src/arms/single_agent.py](src/arms/single_agent.py)).

| Nó | Responsabilidade |
| --- | --- |
| **IntentRefiner** | Converte o enunciado em intent estruturada (v2: blocos de reprodução, saídas esperadas, restrições e critérios copiados literalmente) |
| **Clarification** | Resolve ambiguidades da intent com respostas simuladas |
| **Planner** | Explora o repositório só com leitura (até 12 turnos) e fatia a intent em até 6 sub-tarefas |
| **Developer** | Edita o repositório por ferramentas, uma sub-tarefa por vez, até 40 turnos por ciclo; volta ao ciclo seguinte com a memória de trabalho, não com a transcrição |
| **Validator** | Roda a suíte visível, executa os blocos de reprodução, revisa a sub-tarefa e faz a revisão final; só pode rebaixar o veredito, nunca promovê-lo |
| **TestGenerator** | Gera um plano de testes em texto (não escreve na suíte, não conta como oráculo) |

Compartilhado pelos dois braços: workspace que nasce só com o commit-base (sem
histórico git, sem rede), área de testes protegida contra escrita, sete
ferramentas (`list_files`, `read_file`, `search_code`, `write_file`,
`replace_in_file`, `run_python`, `run_tests`), toda execução de código em caixa
de areia bubblewrap, orçamento de 120 turnos, 8 M tokens e 3.600 s por run.

Depois do run, fora do caminho do agente: o **oráculo** (`harness/oracle.py`)
injeta os testes escondidos que o projeto original escreveu com a correção e
faz três verificações (fail-to-pass, pass-to-pass, regressão); o **detector de
trapaça** (`harness/cheat.py`) aplica oito regras ao patch (editar testes,
silenciar exceções, código do futuro do projeto etc.), e violação crítica anula
o run. "Resolvido" exige as três verificações e o detector limpo.

## Pré-requisitos

- Python 3.12+ e [uv](https://docs.astral.sh/uv/)
- `bwrap` (bubblewrap): a suíte e qualquer run falham sem ele
- Conta [OpenRouter](https://openrouter.ai/) com chave própria do provedor registrada (BYOK)

## Configuração

```bash
cp .env.example .env
# Edite .env com suas chaves
uv sync --extra dev --extra harness
```

Variáveis principais:

| Variável | Descrição |
| --- | --- |
| `OPENROUTER_API_KEY` | Chave da API OpenRouter |
| `OPENROUTER_MODEL_NAME` | Modelo **pago**; tier `:free` é recusado |
| `OPENROUTER_PROVIDER` | Provedor único a pinar (`provider.only`) |
| `LLM_SEED` | Semente base; a repetição k dos dois braços usa a mesma semente |
| `LLM_TEMPERATURE` | `0` nos dois braços |
| `RUN_MAX_TURNS`, `RUN_MAX_TOKENS`, `RUN_MAX_WALL_SECONDS` | Tetos do run (120, 8 000 000, 3600), congelados desde 12/10/2026 |
| `PLANNER`, `SUBTASK_CHECK`, `REVIEW_EXECUTION`, `REVIEW_COMPARE`, `REVIEW_STRICT`, `REPRODUCTION_COMPILE_CHECK`, `REPRODUCTION_SOURCE`, `BLOCK_EXPECTED` | Política do orquestrado; vai inteira ao manifesto (`orchestration_policy`) |
| `URANIUM_SANDBOX` | `off` só para depuração; registrado no manifesto |

Os tetos e as políticas das nove rodadas estão listados em
[CLAUDE.md](CLAUDE.md), com as decisões do autor em
[docs/tcc/09-decisoes-do-autor.md](docs/tcc/09-decisoes-do-autor.md).

### Escolha do modelo

O modelo é escolhido por um **teste de aptidão**: o endpoint precisa aceitar
`seed`, ferramentas, temperatura e teto de saída, ter pesos abertos com
quantização publicada e não gastar tokens de raciocínio ocultos
([docs/tcc/08-escolha-modelo.md](docs/tcc/08-escolha-modelo.md)).

```bash
uv run python scripts/fitness_test.py --list-providers vendor/modelo
uv run python scripts/fitness_test.py --model vendor/modelo --provider DeepInfra -n 5
```

O cliente é montado com `provider.only`, `allow_fallbacks: false`,
`require_parameters: true` e `data_collection: deny`. Não há reparo de JSON
degradado: se o modelo não conformar ao schema, o erro sobe e é contabilizado.

## Tarefas

As 13 tarefas vêm de correções reais de cinco projetos (tomlkit, peewee,
sqlite-utils, pygments, attrs), em três faixas de tamanho calculadas sobre a
mudança de referência (3 grandes, 4 médias, 6 pequenas). Cada tarefa passou por
cinco portões com duas soluções de referência antes de entrar
(`scripts/validate_task.py`). Estão em `tasks/<id>/` com enunciado, testes
escondidos, patch de teste e referências.

```bash
# espelho local do repositório-semente e venv de teste (único passo com rede)
uv run python scripts/setup_mirror.py tomlkit
```

## Uso

```bash
# um braço numa tarefa
uv run python scripts/run_arm.py --arm orchestration --task tomlkit-0001 \
    --base-commit 11e22aefccd8069a90ae75d20613b9b1068754a1 \
    --statement-file tasks/tomlkit-0001/statement.md
uv run python scripts/run_arm.py --arm single-agent --task tomlkit-0001 \
    --base-commit 11e22aefccd8069a90ae75d20613b9b1068754a1 \
    --statement-file tasks/tomlkit-0001/statement.md

# coleta: todas as tarefas × 2 braços × 3 repetições; retomável
uv run python scripts/run_collection.py --repetitions 3 --workers 2
uv run python scripts/run_collection.py --dry-run

# avaliar um run avulso (oráculo + detector)
uv run python -m harness.evaluate --run-dir <run_dir> --task tasks/tomlkit-0001
```

Cada run grava `manifest.json` (configuração resolvida), `events.jsonl`
(telemetria por evento), `summary.json`, `result.json` (oráculo, detector,
custo, qualidade), `patch.diff` e `workspace/`. Run perdido por
infraestrutura (`stop_reason` em `infra_error:` ou `interrupted:`) é
reexecutado com a mesma semente e `attempt + 1`.

### Análise

```bash
uv run python scripts/analyze_results.py ...            # as sete métricas, testes exatos pareados
python3 scripts/agregado_tres_modelos.py                # 234 runs: McNemar por par, faixas, poder
python3 scripts/por_tarefa_tres_modelos.py              # seis células por tarefa: teto, piso, discriminam
python3 scripts/exploratorio_orquestrado.py             # custo da carga, mecanismos, pares discordantes
python3 scripts/calibracao_h4.py                        # regras de parada do revisor simuladas nos eventos
```

As saídas versionadas ficam em `docs/tcc/dados/coleta-deepseek/*.txt`; os dados
das coletas em `docs/tcc/dados/coleta*`, `coleta-deepseek` e `coleta-devstral`.

## Os dois braços

| | **single-agent** | **orchestration** |
| --- | --- | --- |
| Topologia | agente e operador determinístico | grafo com papéis |
| Parada | agente deixa de agir e a suíte visível está verde | revisor aprova com a suíte verde |
| Orçamento | igual | igual |
| Modelo, ferramentas, prompt, semente | idênticos | idênticos |

O operador do `single-agent` roda a suíte quando o agente para de agir e
devolve o **stderr cru** em caso de falha, sem sumarizar nem sugerir. As
mensagens de protocolo dos dois braços vivem só em `src/feedback.py`.
`tests/test_arm_parity.py` verifica que os manifestos só divergem nas chaves
justificadas em `src/arms/runner.py`.

## Estrutura

```
src/
├── config.py             # LLM com provedor pinado + métricas de chamada
├── workspace.py          # Workspace só com o commit-base, sem histórico nem rede
├── seeds.py              # Repositórios-semente e caminhos protegidos
├── budget.py             # Orçamento do run (turnos, tokens, tempo)
├── runtime.py            # RunContext: estado, telemetria, LLM e workspace por run
├── telemetry.py          # Telemetria JSONL, um evento por linha
├── prompts.py            # Prompt do agente que escreve código, comum aos dois braços
├── feedback.py           # Mensagens de protocolo, memória de trabalho, sub-tarefa
├── enunciado.py          # Reparo da cópia dos blocos de reprodução pelo enunciado
├── verificacao.py        # Comparação de saídas esperadas
├── tools/                # Ferramentas do agente; exec.py: caixa de areia bubblewrap
├── graph.py              # Grafo LangGraph do braço orchestration
├── arms/                 # single_agent.py, driver.py, runner.py, collection.py
├── schemas/              # Pydantic: intent, plano, validação
└── agents/               # intent_refiner, planner, developer, validator, test_generator
harness/                  # oracle.py, cheat.py, evaluate.py, quality.py — roda sem rede
scripts/                  # setup_mirror, fitness_test, run_arm, run_collection, mine_tasks,
                          # emit_task, validate_task, analyze_results e os scripts de análise
tasks/                    # as 13 tarefas validadas
tests/                    # suíte (751 testes), inclui o teste de paridade dos braços
docs/tcc/                 # documentos numerados do estudo e dados versionados
```

## Observabilidade

Telemetria **JSONL local, por evento** (`src/telemetry.py`), gravada com
`flush + fsync` a cada linha e validada contra
`harness/schema/event.schema.json`. Cada chamada de LLM registra tokens,
tokens em cache, custo em USD devolvido pelo OpenRouter (BYOK: taxa mais custo
do provedor), provedor servido e latência; cada uso de ferramenta registra
duração, bytes e recusa por caminho protegido. Não há tracing remoto; o
LangSmith foi removido e o tracing do LangChain é desligado no import.

## Desenvolvimento

```bash
uv run pytest -q          # exige bwrap; ~4 min
```

Num worktree, aponte `URANIUM_MIRROR_DIR` e `URANIUM_VENV_DIR` para o
`.uranium/` da árvore principal. Os componentes listados como intocáveis em
[CLAUDE.md](CLAUDE.md) só mudam com aprovação escrita do autor.

## Documentação do estudo

| Documento | Conteúdo |
| --- | --- |
| [00-guia-etapas](docs/tcc/00-guia-etapas.md), [01-inventario](docs/tcc/01-inventario.md), [03-metricas](docs/tcc/03-metricas.md) | desenho, inventário e as sete métricas |
| [09-decisoes-do-autor](docs/tcc/09-decisoes-do-autor.md) | decisões numeradas, com data e aprovação |
| [07-execucao](docs/tcc/07-execucao.md) | registro de execução por etapa |
| [17](docs/tcc/17-rodada-2.md) a [24](docs/tcc/24-rodada-8.md) | rodadas 2 a 8 do orquestrado |
| [25](docs/tcc/25-vazamento-historico-git.md) | vazamento do histórico git e isolamento |
| [26-replicacao](docs/tcc/26-replicacao.md) | replicação em DeepSeek V3.2 e Devstral 2 |
| [27-relatorio-cientifico](docs/tcc/27-relatorio-cientifico.md) | relatório consolidado: método, rodadas, três coletas, proposições, poder, ameaças |
| [28-exploratorio-orquestrado](docs/tcc/28-exploratorio-orquestrado.md) | onde o orquestrado se destaca, onde perde e por quê; hipóteses H1 a H8 |
| [29-pacote-redacao](docs/tcc/29-pacote-redacao.md) | pacote de fatos e números para a redação do artigo |
| [30-calibracao-h4](docs/tcc/30-calibracao-h4.md) | calibração offline das regras de parada do revisor |

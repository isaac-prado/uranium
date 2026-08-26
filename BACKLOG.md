# Backlog do E1

O que falta para a coleta definitiva. Ordem é de dependência, não de esforço.

---

## 0. Calibração do orçamento — **feita**, falta aplicar

Piloto de 23/08/2026 em `tomlkit-0001`, `qwen/qwen3-coder` via DeepInfra,
provedor pinado em todas as chamadas. Custo total da calibração: US$ 0,065.

| braço | teto | turnos | tokens | US$ | parada | oráculo |
|---|---|---|---|---|---|---|
| single-agent | 120k | 9 | 120.486 | 0,0164 | `budget: max_tokens` | não resolveu |
| orchestration | 120k | 13 | 129.163 | 0,0182 | `concluiu` | **resolveu** (f2p 1/1) |
| single-agent | 300k | 29 | 227.350 | 0,0307 | `tests_pass` | **resolveu** (f2p 1/1) |

**O teto de 120k era confundidor.** Com 120k o single-agent gastou os nove
turnos inteiros lendo arquivo e ainda não tinha editado nada quando foi cortado; com
300k ele resolveu. Um teto que corta um braço no meio do trabalho mede o teto,
não a topologia — e cortava justamente o braço que a hipótese não favorece,
que é a direção perigosa do viés.

**A aplicar:** `RUN_MAX_TOKENS = 300_000` na coleta definitiva. Parada por
orçamento passa a ser exceção (agente em ciclo), não regra. Projeção de custo:
12 tarefas × 2 braços × 3 repetições = 72 execuções × ~US$ 0,025 ≈ **US$ 2**.

**A investigar antes da coleta:** o single-agent precisou de 29 turnos e 227k
tokens contra 13 turnos e 127k do orchestration para o mesmo resultado —
1,8× mais caro. O
piloto tem n=1 e não sustenta inferência nenhuma, mas é a diferença que o
estudo existe para medir, e vale conferir se ela se mantém nas outras tarefas.

O consumo é dominado pelo reenvio do contexto: no single-agent de 300k,
220.219 tokens de prompt contra 7.131 de completion. Cresce com o quadrado do número de
turnos, então qualquer braço que precise de mais turnos paga desproporcional.

---

## 1. Renomear os braços — **feito**

`A2` e `B` eram nomes herdados de um desenho de três braços que não existe
mais. Passaram a ser:

| antes | agora | topologia |
|---|---|---|
| `A2` | `single-agent` | agente único, sem papéis, dirigido por política determinística |
| `B` | `orchestration` | grafo multiagente com papéis especializados |

O rename alcançou o valor do campo `arm` na telemetria, no manifesto e no
resumo do run; os enums dos dois JSON Schema do harness; o `choices` do
`--arm`; o módulo `src/arms/a2.py` → [src/arms/single_agent.py](src/arms/single_agent.py);
`build_a2_graph` → `build_single_agent_graph`; o caminho de saída
`runs/<arm>/...`; e a prosa toda.

Foi feito antes da coleta definitiva de propósito: enquanto não há dado
gravado, é substituição de texto; depois viraria migração.

Os runs do piloto em `runs/` ficam com o valor antigo. Não são dado de
coleta, então não precisam migrar.

---

## 2. Adotar `peewee` e `sqlite-utils` como repos-semente

Hoje só o `tomlkit` está montado. Os dois novos cobrem cenários que o tomlkit
não tem: entidades e transações em banco, referência circular, migração de
schema.

Medido até agora:

| repo | LOC | licença | commits | suíte |
|---|---|---|---|---|
| `tomlkit` | ~5k | MIT | — | verde, rápida |
| `sqlite-utils` | 9.813 | Apache-2.0 | 1.199 | **não mediu** — falta `sqlite_fts4` |
| `peewee` | 15.461 | MIT | 5.316 | **não mediu** — `runtests.py`, não pytest direto |

Bloqueio: nenhum dos dois teve a suíte rodando ponta a ponta. Antes de virar
repo-semente, cada um precisa de:

1. instalação de dependências reprodutível e offline;
2. suíte verde no commit-base, cronometrada (entra no `test_timeout_s`);
3. espelho bare local via `scripts/setup_mirror.py`;
4. `protected_globs` conferidos — o agente não pode escrever teste nem config.

---

## 3. Estratificar o backlog por dificuldade

Sem estratificação, um resultado agregado esconde onde a diferença entre os
braços aparece. Proposta: três faixas por repo, classificadas pelo patch de
referência do upstream.

| faixa | critério | exemplo já verificado |
|---|---|---|
| baixa | 1 arquivo, < 30 linhas | `495a42ec` (+24/-0) |
| média | 2–3 arquivos | `a3cb8a2b` (+49/-1), `cbf6b4e0` (+88/-25) |
| alta | 4+ arquivos ou módulo novo | `7f237d8f` (+189/-71), `deac74db` (+111/-0) |

Com 3 repos × 4 tarefas = 12 tarefas. O mínimo estatístico é 8 (ver §5).

---

## 4. Construir as tarefas restantes

Uma tarefa pronta = `task.json` + `statement.md` + `hidden/` + `reference/` +
patches de trapaça, validada por `scripts/validate_task.py`.

Só a `tomlkit-0001` está pronta. Candidatos do tomlkit **já verificados como
discriminantes** (falham antes do patch, passam depois):

| commit | diffstat | arquivos | testes ocultos |
|---|---|---|---|
| `495a42ec` | +24/-0 | 1 | — |
| `832e8557` | +48/-9 | 2 | — |
| `e6e5d380` | +14/-9 | 2 | — |
| `a766d3a2` | +12/-20 | 2 | — |
| `a3cb8a2b` | +49/-1 | 3 | — |
| `cbf6b4e0` | +88/-25 | 3 | 9 |
| `deac74db` | +111/-0 | 3 | cria módulo novo |
| `7f237d8f` | +189/-71 | 4 | 25 |

---

## 5. Limitações a declarar no TCC

Não são pendências: são fatos do desenho que precisam estar escritos.

**Refatoração não é categoria de tarefa possível.** Um refactor que preserva
comportamento passa nos mesmos testes antes e depois — não existe fail-to-pass,
e o oráculo não discrimina. Verificado empiricamente em `9ac3f982` e
`a46ac201`. Refatoração só entra como métrica secundária (delta de MI/CC do
`radon`), nunca como corretude.

**Modelos da Anthropic estão fora.** Nenhum dos 8 endpoints do
`claude-haiku-4.5` no OpenRouter aceita `seed`. Com provedor pinado, não há
reprodutibilidade. É limitação de plataforma, não escolha de mérito.

**A unidade de análise é a tarefa, não a repetição.** Repetições da mesma
tarefa não são observações independentes. Num teste de sinal pareado
unicaudal, o menor p alcançável é 0,0625 com 4 tarefas — impossível chegar a
p<0,05. Com 5 exige unanimidade. Com 8, tolera um resultado discordante. Daí o
mínimo de 8.

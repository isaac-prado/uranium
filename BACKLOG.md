# Backlog do E1

O que falta para a coleta definitiva. Ordem é de dependência, não de esforço.

---

## 0. Calibração do orçamento — **feita e aplicada**

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

**Aplicado:** o piloto deixou de ter tetos próprios e passou a herdar os
`RUN_MAX_*` da coleta (400k tokens, 40 turnos, 1800s). Piloto mais apertado
que a coleta não calibra a coleta: mede o teto.

O teto de turnos era o segundo confundidor, e passou despercebido na
primeira leitura — o padrão do piloto era 25 e o single-agent precisou de
29. Ele teria sido cortado de novo, por outro motivo.

Projeção de custo: 12 tarefas × 2 braços × 3 repetições = 72 execuções ×
~US$ 0,025 ≈ **US$ 2**.

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

## 2. Repos-semente `peewee` e `sqlite-utils` — **feito**

Os três repos estão montados, com espelho bare local e ambiente de teste
próprio, e a suíte foi verificada verde no HEAD:

| repo | LOC | licença | commits | suíte no HEAD | tempo |
|---|---|---|---|---|---|
| `tomlkit` | ~5k | MIT | 586 | 1.052 passed | 1,3s |
| `sqlite-utils` | 9.813 | Apache-2.0 | 1.199 | 1.488 passed, 16 skipped | 11,6s |
| `peewee` | 15.461 | MIT | 5.324 | 1.634 passed, 161 skipped | 23,7s |

Dois achados que viraram código:

**Cada repo roda no próprio venv.** Antes tudo caía em `sys.executable`, o
venv do projeto, com langchain e mais cinquenta pacotes visíveis para a
suíte do upstream. `SeedRepoSpec.python_bin` resolve o interpretador do
repo e falha alto se o ambiente não existir — cair no do projeto
silenciosamente invalidaria o resultado sem deixar rastro.

**O peewee precisa de alvo de coleta explícito.** Os módulos de teste dele
se chamam `models.py`, `fields.py`, `sql.py`: nenhum casa com `test_*.py`,
e um pytest pelado acha 5 testes de 1.634. O alvo é `tests/__init__.py`,
que é o conjunto que o `runtests.py` do upstream monta.

Preparar tudo:

```bash
uv run python scripts/setup_mirror.py --all --check
```

---

## 3. Estratificação por dificuldade — **feito, embutida no minerador**

A faixa sai do tamanho do patch de referência do upstream, calculada
automaticamente em `scripts/mine_tasks.py`:

| faixa | critério |
|---|---|
| baixa | 1 arquivo de fonte, menos de 30 linhas |
| média | 2 a 3 arquivos |
| alta | 4 ou mais arquivos |

O emissor de tarefas alterna as faixas ao escolher, para não sair uma leva
só de tarefa fácil.

---

## 4. Construir as tarefas restantes — **ferramenta pronta, conteúdo pendente**

O caminho deixou de ser manual:

```bash
uv run python scripts/mine_tasks.py --all --limit 30 --scan 600
uv run python scripts/emit_task.py --from mined/peewee.json --top 4
uv run python scripts/validate_task.py tasks/peewee-0001
```

`mine_tasks.py` decide por execução, não por leitura de mensagem de commit:
com o pai como base, traz só os testes da correção e exige a suíte
vermelha; traz a fonte e exige verde. O fail-to-pass é exatamente o
conjunto que fez essa transição.

O oráculo passou a poder ser o **patch de teste do upstream**
(`test_patch`), aplicado pelo avaliador sobre os testes restaurados do
commit-base. Escala, mede o critério que o mantenedor escreveu, e desfaz
adulteração de teste antes de medir. A `tomlkit-0001` continua no formato
antigo, de arquivo oculto avulso; as duas formas convivem.

**O que ainda é trabalho humano em cada tarefa:**

1. **`statement.md`.** É o insumo que os dois braços recebem e define o que
   está sendo medido. Não pode nascer da mensagem de commit, que
   frequentemente já entrega a solução. O emissor deixa o esqueleto marcado
   como `PENDENTE` e o validador não passa até ser escrito.
2. **`reference/alternative.patch`.** Uma segunda solução válida, diferente
   da do upstream. É o que prova que o oráculo não está travado numa forma
   específica de resolver. Não dá para gerar automaticamente sem virar
   variação cosmética, que seria uma garantia falsa.
3. **Patch de trapaça C5** (detectar pytest em tempo de execução). O
   emissor gera o C1 mecanicamente; o C5 depende do ponto certo no código.

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

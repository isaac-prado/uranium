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

**Provedor é parte do tratamento.** Em 28/09/2026 duas tentativas seguidas em
`sqlite-utils-0001` (`runs/pilot-sqlite-01`, `pilot-sqlite-02`) morreram na
primeira chamada por `429 — qwen/qwen3-coder is temporarily rate-limited
upstream` no DeepInfra: 0 tokens, US$ 0. O piloto passou para o **Novita**, que
é apto segundo `fitness_test.py --list-providers`, com todos os parâmetros
exigidos, inclusive `seed`. A troca é entre levas, nunca dentro de um run
(`allow_fallbacks: false`), e os dois braços usam o mesmo provedor, então a
leva continua pareada. Os números dela não se misturam com os pilotos no
DeepInfra. Falta rodar o laudo de 5 sondagens no Novita.

## 6. Erro de infraestrutura contado como erro do modelo — **feito**

No mesmo episódio, o braço orchestration registrou o 429 como
`StructuredOutputError: modelo não conformou ao schema`; o single-agent
registrou `RateLimitError`. Causa: o `except Exception` de
`src/structured_llm.py` põe falha de chamada (429, 5xx, timeout) no mesmo balde
de falha de conformidade. O viés recai só sobre o multiagente. A correção tem
duas partes: tipo próprio para falha de chamada e, para run perdido por
infraestrutura, reexecução fora do denominador em vez de contar como fracasso.

**Corrigido em 28/09/2026.** `src/config.py` ganhou `ProviderError` e
`is_provider_error` (401, 402, 403, 408, 409, 429, 5xx, rede, timeout; 400,
404 e 422 ficam fora porque são resposta à requisição que o run montou).
`invoke_structured_raw` levanta `ProviderError` na primeira falha de
provedor, sem retentar: o cliente já retentou `LLM_MAX_RETRIES` vezes, igual
ao single-agent. Antes havia uma segunda camada só no orchestration
(`STRUCTURED_OUTPUT_RETRIES + 1` = 3 × 7 = 21 tentativas contra 7), e ela
agora cobre só saída fora do schema; o valor vai no manifesto
(`structured_output`). O runner grava `stop_reason: infra_error: ...` e
`lost: true` no resumo, nos dois braços. Ctrl+C grava
`interrupted: ...`, também `lost`, e não vira mais fracasso do braço.

Coleta, depois da revisão do mesmo dia:

- 401 e 402 (chave revogada, crédito esgotado) param a coleta com
  `CollectionAborted` na primeira tentativa, em vez de levar cada célula a
  `lost`. `--max-consecutive-lost` (padrão 3) para a coleta quando o provedor
  fica fora por várias células seguidas.
- `--max-attempts` conta as tentativas da execução atual: célula `lost` volta
  a ser tentada quando a coleta é retomada.
- O `stop_reason` do orchestration mostra a exceção do cliente por baixo do
  `ProviderError` (`infra_error: RateLimitError`, não `infra_error: ProviderError`).
- A regra de qual tentativa vale está só em `harness/attempts.py`, usada pela
  coleta e pela análise.
- A análise mostra tentativas perdidas, células perdidas e runs cortados por
  orçamento **por braço**: reexecutar até sair limpo seleciona runs sem falha
  de provedor, e a seleção pesa mais no braço que perde mais. A coleta
(`scripts/run_collection.py`) reexecuta a célula perdida e a análise
(`scripts/analyze_collection.py`) tira o par do denominador.

O mesmo episódio teve mais três fatos a registrar:

- **Terceiro 429 no DeepInfra** (`runs/pilot-sqlite-03`), logo depois de o
  `fitness_test.py` passar nele com 3/3. Sondagem curta passa, run real não:
  o teste de aptidão não mede disponibilidade sob contexto grande.
- **Chave revogada no meio do piloto** (401 `User not found`, 10h39): o
  orchestration de `runs/pilot-sqlite-novita-02` morreu na primeira chamada e
  o erro saiu, de novo, como "não conformou ao schema" — antes da correção.
- **Timeout por chamada de 300s para 90s.** Nas 854 chamadas registradas
  até então: p50 1,7s, p95 14s, p99 60s, máximo 190s. No Novita, com contexto
  grande, as latências do single-agent saíram em múltiplos de ~92s (93, 183,
  369, 466): chamada estourando o timeout e sendo retentada. O run foi cortado
  por `max_wall_seconds` esperando o provedor, o que é censura por
  infraestrutura e não por comportamento do agente. Timeout e provedor
  precisam ser fixados juntos, com o p99 medido no provedor escolhido.

**Nota de procedência.** Os pilotos de 28/09 até as 10h50 rodaram na branch
`runs-17-09-2026`, que tem o `harness/evaluate.py` anterior à cópia
descartável. A falha de C1 vista na `sqlite-utils-0001` vinha daí: na
`develop` a tarefa valida nos quatro portões.

## 7. Desenho do braço orchestration — **a repensar (outro agente)**

Revisão do grafo em 28/09/2026 (`src/graph.py`, `src/agents/*.py`, comparados
com `src/arms/single_agent.py` e `src/arms/driver.py`). Objetivo: uma
orquestração simples, objetiva e **funcional**, que não pague custo por
obrigação. Este item é o insumo; a decisão é do desenho do estudo.

### 7.1 Grafo atual

```
START → intent_refiner ─┬─(is_ready ou 3 voltas)→ developer → validator ─┬─(verde, orçamento ou 2 voltas)→ test_generator → END
            ↑           └─(senão)→ clarification ─┘            ↑         └─(senão)→ developer
            └──────────────────────────────────────            └──────────────────────────────
```

Chamadas LLM por run: `intent_refiner` 1 a 4, `clarification` 0 a 3,
`developer` N turnos (o único nó que age no repositório), `validator` 0 a 2
(revisão semântica, só com a suíte verde), `test_generator` 1.

### 7.2 Erros de desenho encontrados

Cada um com o que o código faz, o efeito e a evidência.

**D1. `test_generator` é custo sem consumidor.** Roda em todo run, inclusive
depois do verde e depois de estourar a validação. Manda a intent e até 12k
caracteres de diff e recebe um `TestPlan`. Esse plano só é lido por
`src/export.py`, e o nó não escreve no workspace, embora a docstring diga que
os testes iriam para `tests/uranium/`. Não afeta `resolved`, nem o laço, nem o
developer. *Evidência:* `grep test_plan src/` → só `export.py` e o próprio nó.

**D2. `clarification` inventa requisitos.** Quando o `intent_refiner` marca
`is_ready=false`, o `clarification` pede ao LLM "respostas técnicas plausíveis
assumindo boas práticas" às próprias perguntas, e o `intent_refiner` roda de
novo com elas, até `MAX_CLARIFICATION_ITERATIONS` = 3 voltas. Não há humano
nem fonte de verdade no laço: é o modelo conversando consigo mesmo. Isso
custa até 6 chamadas e, pior, pode enxertar no enunciado requisitos que não
existem na issue.

**D3. O developer não recebe o enunciado, e sim a paráfrase do LLM.** O
single-agent recebe `goal = statement` cru (estado inicial do runner). O
developer do orchestration recebe `parse_intent(state)`, que é o JSON
reescrito pelo `intent_refiner`: `context`, `goal`, `phases`,
`acceptance_criteria`, mais o que o D2 tiver acrescentado. A informação que
entra no único nó que age passa por uma compressão com perda feita pelo LLM.
Detalhes da issue (nome exato de função, mensagem de erro, trecho de
traceback) podem sumir. O efeito sobre `resolved` é desconhecido e é
confundidor: mede a qualidade da paráfrase, não a topologia.

**D4. A reprovação semântica volta ao developer sem o motivo.** Com a suíte
verde, o `validator` pede ao LLM que julgue se a mudança resolve a tarefa. Se
`is_valid=false`, o grafo volta ao developer. Mas o `_build_prompt` do
developer só lê `test_report` e `changed_files`. Com o relatório verde, a
única coisa que ele recebe é "Arquivos já modificados: ...". `issues` e
`suggestions` ficam no estado e só `export.py` os lê. O developer repete o
trabalho às cegas. **É bug, não escolha de desenho.**
**Corrigido em 28/09/2026:** com a suíte verde, arquivos alterados e a
revisão reprovando, o prompt do developer traz `issues`, `missing_criteria` e
`suggestions` do revisor, sem texto do harness além dos títulos
(`_revisao_reprovada` em `src/agents/developer.py`). Suíte vermelha
prevalece sobre revisão antiga. Continua valendo o D5: o developer recebe o
motivo, mas numa conversa nova.

**D5. Cada volta ao developer recomeça a conversa do zero.** `developer()`
monta `mensagens = [system, human]` a cada entrada no nó. Tudo o que ele leu
e aprendeu na volta anterior se perde; ele reexplora o repositório e paga de
novo o contexto. O single-agent mantém `ctx.conversation` entre os ciclos do
driver. Como o custo é dominado pelo reenvio de contexto (seção 0: 220k de
prompt contra 7k de completion), a reexploração é cara.

**D6. O orchestration desiste com orçamento sobrando.** `route_after_validator`
encerra quando `validation_iteration_count >= MAX_VALIDATION_ITERATIONS` = 2.
O driver do single-agent não tem limite de voltas: segue até o verde ou o
orçamento. Um braço tem 2 chances de corrigir depois do pytest; o outro tem
quantas o orçamento pagar. É assimetria de tratamento que não vem da
topologia de papéis e enviesa contra o orchestration.
**Corrigido em 28/09/2026:** suíte vermelha e diff vazio voltam ao developer
até o orçamento acabar, como no driver. O único teto que sobrou é o da
reprovação semântica sobre código verde, que não tem equivalente no
single-agent: `MAX_SEMANTIC_REJECTIONS` = 2 (antes `MAX_VALIDATION_ITERATIONS`,
que contava toda volta). O contador é `semantic_rejections` no estado, e os
dois tetos do orchestration vão para o manifesto (`orchestration`).

**D7. O feedback do pytest é diferente nos dois braços.** O driver do
single-agent corta a saída em `stderr_chars` = 4000 e a embrulha em
`suite_falhou()`. O developer recebe `report.stdout_tail` inteiro, com outro
texto em volta. Tamanho e redação do feedback são variáveis que o estudo diz
controlar.
**Corrigido em 28/09/2026:** com a suíte vermelha ou o diff vazio, o
developer recebe a mensagem que `DeterministicDriver().apos_turno` produz,
com a política padrão, a mesma que o single-agent usa. Há teste de identidade
literal em `tests/test_arm_parity.py`. Limite: uma `DriverPolicy` diferente
passada ao single-agent, para ablação, não chega ao orchestration.

**D8. O sinal do validator é fraco por construção.** A suíte visível já está
verde no commit-base: o teste que discrimina é oculto. Depois de qualquer
mudança que não quebre nada, o validator dá verde. O laço
developer↔validator só dispara quando o agente quebra algo; a revisão
semântica (D4) é a única coisa que olha se a tarefa foi feita, e ela não
passa o motivo adiante. O single-agent tem o mesmo limite, mas não paga uma
chamada LLM por ele.

**D9. Tolerância a falha de provedor 3× maior** — corrigido em 28/09 (seção
6). Registrado aqui porque tem a mesma origem dos outros: camadas somadas nos
nós estruturados, sem comparação com o outro braço.

### 7.3 Custo fixo contra custo que escala

- **Custo fixo por run:** `intent_refiner` (1), `test_generator` (1) e, no
  pior caso, `clarification` com o refinamento de novo (+6), além da revisão
  semântica (+1 a 2).
- **Custo que escala:** os turnos do developer, que crescem com o quadrado
  por causa do reenvio de contexto, e dobram com o D5.

Nas tarefas pequenas, o developer resolve em poucos turnos e o custo fixo
vira uma fração grande do total. Isso explica "orchestration mais caro mesmo
em tarefa pequena" **como hipótese**. Não há número: a telemetria dos pilotos
de variância não está mais no disco, e o único custo registrado (seção 0, n=1)
teve o orchestration **mais barato**, US$ 0,0182 contra 0,0307.

### 7.4 O que medir antes de decidir

A partir do `events.jsonl` das primeiras células da coleta:

- custo e chamadas por `node`;
- quantas vezes `clarification` roda e quanto o `goal` refinado difere do
  enunciado;
- quantas vezes a revisão semântica reprova um run que o oráculo dá como
  resolvido, e o contrário;
- quantas voltas developer↔validator acontecem e quantas terminam no teto de
  2 com orçamento sobrando.

### 7.5 Cuidado com o desenho do estudo

Mudar o grafo muda o tratamento. Separar três categorias:

1. **Bugs, que cabem antes da coleta:** D4 (motivo da reprovação), D6 (teto
   de voltas que o outro braço não tem) e D7 (feedback diferente). Os três
   violam a promessa de que só a topologia difere.
2. **Escolhas de desenho que precisam ser declaradas se mantidas:** D3
   (paráfrase no lugar do enunciado) e D5 (nó sem memória).
3. **Nós sem efeito sobre o desfecho:** D1 e D2. Removê-los redefine o braço.
   Ou se faz uma ablação (`developer` + `validator` só) como braço adicional,
   ou se declara como limitação.

### 7.6 Literatura (levantamento de 28/09/2026)

Levantamento feito por subagente com busca web. [V] = fonte aberta e
conferida; [B] = só pelo resultado de busca. **Conferir os números nas fontes
antes de citar no TCC**: vieram de resumos e versões HTML, que mudam entre
versões do arXiv.

**O que a literatura diz, em resumo.** Nas tarefas estilo SWE-bench, o que se
mostra forte e barato é agente único com boa interface de ferramentas, ou
pipeline fixo. Grafo com muitos papéis não aparece entre os mais eficientes.
Com orçamento igual, agente único empata ou supera multiagente, e o ganho
atribuído a multiagente costuma ser computação extra não contabilizada. Crítica
por LLM sem feedback externo ajuda pouco ou piora; o que ajuda é feedback
executável que volta a quem executa. A própria Anthropic diz que multiagente
não serve para "most coding tasks", porque todos precisam do mesmo contexto.

**Evidência que bate com os defeitos da 7.2:**

| Defeito | Evidência |
|---|---|
| D1 test_generator sem consumidor | Teste gerado só vale quando é executado e filtra patch. Agentless: 77 → 81 → 96 resoluções com votação, + regressão, + teste de reprodução (+US$ 0,25/issue). Mas só 94 dos 213 testes que reproduziam o bug validavam o patch de referência: é filtro, não oráculo. SWT-bench: testes gerados dobram a precisão do SWE-agent como filtro. |
| D2 clarificação inventada | Ambig-SWE (ICLR 2026): perguntar ajuda quando **um humano responde**, e os modelos confundem enunciado completo com subespecificado (o gatilho `is_ready=false` dispara à toa). Nenhuma fonte sustenta o LLM respondendo às próprias perguntas. MAST: "fail to ask for clarification" pressupõe interlocutor real. |
| D3 paráfrase no lugar do enunciado | Cognition: passar o trace completo, não mensagem resumida. MAST: "disobey task specification" (11,8%) e "task derailment" (7,4%). Tran & Kiela 2026: cada handoff só pode perder informação (medido em raciocínio multi-hop, não em código). |
| D4 motivo da reprovação não repassado | MAST: "incorrect verification" (9,1%), "information withholding", "ignored other agent's input". Huang et al. (ICLR 2024): sem feedback externo o desempenho "even degrades after self-correction". Olausson et al. (ICLR 2024): o gargalo do self-repair é a qualidade do feedback. |
| D5 nó sem memória | MAST: "conversation reset", "loss of conversation history", "step repetition" (15,7%, o modo mais comum depois dos de verificação). Cognition: agente linear de uma thread só. |
| custo fixo sem ablação | Kapoor et al. 2024 ("AI Agents That Matter"): foco só em acurácia produz agentes "unnecessarily complex and expensive"; baseline simples frequentemente empata. Yin et al. 2025: o framework multiagente teve as trajetórias mais longas, por coordenação. |

**Padrões funcionais, do mais barato ao mais caro:**

- **P1. Agente único, boa interface de ferramentas, histórico contínuo.**
  SWE-agent (ablações mostram que o desenho da ferramenta muda o resultado);
  mini-SWE-agent (>74% no Verified segundo o README, [B]). É o single-agent
  daqui, e o developer já é isso, menos o D5.
- **P2. Pipeline fixo localização → reparo → validação.** Agentless: 32% no
  Lite a US$ 0,70/issue, sem agente. AutoCodeRover: 19% a US$ 0,43. Aqui: um
  nó de localização que entrega arquivos e símbolos candidatos **anexados** ao
  enunciado, sem reescrevê-lo.
- **P3. Teste de reprodução antes do fix.** Agentless e SWT-bench, acima. Aqui:
  o test_generator vai para antes do developer, escreve um teste executável,
  confere que ele falha no commit-base, e o validator roda esse teste. Se não
  reproduzir em N passos, segue sem ele.
- **P4. Evaluator-optimizer com feedback executável repassado.** Anthropic
  "Building effective agents"; AgentCoder (programador + designer de teste +
  executor: 96,3% no HumanEval com menos tokens que o anterior, em geração de
  função, não em issue de repositório).
- **P5. Roteamento ou cascata.** Gao et al. 2025: cascata agente único →
  multiagente, até −20% de custo com ganho de acurácia. Aqui: developer
  direto, e localização/reprodução só se a primeira tentativa esgotar sem
  progresso.
- **P6. Papéis com contexto curto por sub-tarefa** (MASAI, CodeR, ~28% no
  Lite). Ressalva: ficam perto ou abaixo do Agentless, que é mais simples, e
  não há ablação com orçamento igual contra agente único.

**Arquitetura mínima sugerida pelo levantamento** (para discutir, não
decidida):

```
START → [analyst opcional] → [reproducer condicional] → developer ⇄ validator → END
```

1. Sai `intent_refiner` obrigatório e `clarification`. Um `analyst` opcional
   devolve só um anexo `{arquivos_candidatos, hipótese, critérios_extraídos_literalmente}`;
   ambiguidade vira `assumptions` explícitas, sem reescrever o `goal`.
2. `reproducer` (o test_generator movido): teste que falha antes do fix.
3. `developer` igual ao single-agent, com a conversa preservada entre
   reentradas; o feedback do validator entra como mensagem nova.
4. `validator` determinístico: pytest + teste de reprodução, saída crua de
   volta. Revisão semântica só rebaixa se der motivo concreto, e o motivo é
   repassado; ou sai do braço principal e vira ablação. Parada: duas voltas
   seguidas sem diff novo nem saída de teste nova.
5. Sai o `test_generator` final.
6. Entre nós, nada parafraseado: enunciado cru, anexo do analyst, caminho e
   saída do teste de reprodução, histórico do developer, saída do pytest e
   motivo da revisão.

**Comparação justa:** mesmo orçamento total contando todas as chamadas de
todos os nós; taxa de resolução com IC, custo médio, custo por issue
resolvida; fronteira de Pareto custo × acurácia (Kapoor et al.); ablação
declarada como braços nomeados (`orch-full` = atual, `orch-min`,
`orch-min − X` por nó removido), para que a diferença contra o single-agent
seja atribuível a um componente.

**Decisão em aberto para o estudo:** se o E1 mantém o `orch-full` como está
(ineficiências incluídas, declaradas) e adiciona `orch-min` como braço de
ablação, ou se troca o braço principal. A segunda opção muda a hipótese.

**Referências:**

- [V] Xia et al., 2024. *Agentless: Demystifying LLM-based Software Engineering Agents*. https://arxiv.org/abs/2407.01489
- [V] Yang et al., 2024. *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*. https://arxiv.org/abs/2405.15793
- [B] mini-SWE-agent (README). https://github.com/SWE-agent/mini-swe-agent
- [V] Wang et al., ICLR 2025. *OpenHands: An Open Platform for AI Software Developers*. https://arxiv.org/abs/2407.16741
- [V] Wang et al., ICML 2024. *Executable Code Actions Elicit Better LLM Agents* (CodeAct). https://arxiv.org/abs/2402.01030
- [V] Zhang et al., 2024. *AutoCodeRover: Autonomous Program Improvement*. https://arxiv.org/abs/2404.05427
- [V] Arora et al., 2024. *MASAI: Modular Architecture for Software-engineering AI Agents*. https://arxiv.org/abs/2406.11638
- [V] Chen et al., 2024. *CodeR: Issue Resolving with Multi-Agent and Task Graphs*. https://arxiv.org/abs/2406.01304
- [V] Huang et al., 2023/24. *AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation*. https://arxiv.org/abs/2312.13010
- [V] Islam, Ali, Parvez, 2024. *MapCoder: Multi-Agent Code Generation for Competitive Problem Solving*. https://arxiv.org/abs/2405.11403
- [V] Mündler et al., 2024. *SWT-Bench: Testing and Validating Real-World Bug-Fixes with Code Agents*. https://arxiv.org/abs/2406.12952
- [V] Cemri et al., 2025. *Why Do Multi-Agent LLM Systems Fail?* (MAST). https://arxiv.org/abs/2503.13657
- [V] Tran, Kiela, 2026. *Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets*. https://arxiv.org/abs/2604.02460
- [V] Gao et al., 2025. *Single-agent or Multi-agent Systems? Why Not Both?* https://arxiv.org/abs/2505.18286
- [V] Kapoor et al., 2024. *AI Agents That Matter*. https://arxiv.org/abs/2407.01502
- [V] Olausson et al., ICLR 2024. *Is Self-Repair a Silver Bullet for Code Generation?* https://arxiv.org/abs/2306.09896
- [V] Huang et al., ICLR 2024. *Large Language Models Cannot Self-Correct Reasoning Yet*. https://arxiv.org/abs/2310.01798
- [V] Yin et al., 2025. *A Comprehensive Empirical Evaluation of Agent Frameworks on Code-centric Software Engineering Tasks*. https://arxiv.org/abs/2511.00872
- [B] Vijayvargiya et al., ICLR 2026. *Ambig-SWE: Interactive Agents to Overcome Underspecificity in Software Engineering*. https://arxiv.org/abs/2502.13069
- [V] Anthropic, dez/2024. *Building effective agents*. https://www.anthropic.com/engineering/building-effective-agents
- [V] Anthropic, jun/2025. *How we built our multi-agent research system*. https://www.anthropic.com/engineering/multi-agent-research-system
- [V] Yan (Cognition), jun/2025. *Don't Build Multi-Agents*. https://cognition.com/blog/dont-build-multi-agents

## 8. Pontos abertos da revisão do Bloco A — **a decidir**

Revisão de 28/09/2026 da coleta e da análise. Os bugs foram corrigidos (seção
6); ficaram estes, que não bloqueiam mas precisam de decisão antes da coleta:

- **403 do OpenRouter pode ser moderação** ("input flagged"). Aí é resposta ao
  conteúdo que o run montou, como o 400, e não infraestrutura. Hoje o 403 é
  reexecutado e, se persistir, a célula sai `lost` e tira o par do
  denominador. Improvável com Novita e Qwen, mas a regra deveria distinguir
  pelo corpo da resposta ou tratar 403 como erro do run.
- **`resposta vazia (choices=None)` conta como erro de schema.** No OpenRouter
  costuma ser um 200 com erro do provedor por baixo. Hoje, depois de esgotar
  `STRUCTURED_OUTPUT_RETRIES`, vira `StructuredOutputError` e fracasso do
  orchestration. O single-agent não tem esse caminho.
- **Erro determinístico de montagem vira perda silenciosa.** Espelho ausente
  ou `base_commit` errado falham antes do `summary.json`; a tentativa conta
  como perdida, é reexecutada e a célula sai do denominador. Hoje só aparece
  no código de saída e no `crash.txt`. Sugestão: validar tarefas e espelhos
  antes de começar (`--dry-run` pode fazer isso).
- **O single-agent roda sempre primeiro no par.** Alternar a ordem por
  repetição custa uma linha em `plan_cells` e elimina efeito de ordem
  (cache do provedor, horário).
- **Degradação lenta do provedor entra no desfecho.** Timeout de 90s × 7
  tentativas dá até 630s por chamada; o run vira `budget: max_wall_seconds` e
  conta como "não resolveu". Com a correção da tolerância (seção 6) o teto é
  igual nos dois braços, mas continua sendo censura por infraestrutura. Fixar
  timeout e provedor juntos, com o p99 medido no provedor escolhido (seção 6).
- **SIGKILL/SIGTERM não passam pelo `finally`.** A tentativa fica sem resumo
  e já conta como perdida; o risco é só o workspace ficar pela metade no
  disco, o que não afeta a análise.

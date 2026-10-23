# 24. Rodada 8: blocos de reprodução consertados pelo enunciado e saída esperada amarrada ao bloco (22/10/2026)

Aprovada por escrito em 22/10/2026 (decisão 48 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md)), depois da pergunta do autor sobre as tarefas grandes. Só fumaças nesta rodada, com o saldo restante da DeepInfra (cerca de US$ 4,7); os 39 runs dependem de crédito novo.

## 1. O que a rodada 7 mostrou sobre as tarefas grandes

Três tarefas grandes (tomlkit-0002, 0003 e 0004), 9 runs por lado ([23-rodada-7.md](23-rodada-7.md) §4; `runs/coleta-r4`, `dados/coleta-r7/`, `runs/coleta-r2-analise`):

| tarefa | single-agent | rodada 4 | rodada 7 | o que a decide |
|---|---|---|---|---|
| tomlkit-0003 | 3/3 | 3/3 | 3/3 | sempre resolvida |
| tomlkit-0002 | 1/3 | 2/3 | 1/3 | 10 linhas em `api.py`: `key()` aceita lista e devolve `DottedKey(..., sep=" = ")`; sem o `sep` a saída é `foo.bar=1` e o teste oculto exige `foo.bar = 1` |
| tomlkit-0004 | 0/3 | 0/3 | 0/3 | referência de 337 linhas em 3 arquivos (chaves pontilhadas no parser); single-agent 3/7 ocultos em todos os runs com 4 a 5 M de tokens; orquestrado 0 a 3/7; na rodada 7, 2 runs com diff vazio após 120 turnos |

- A tomlkit-0004 é teto dos dois braços com os tetos congelados: o máximo alcançável na faixa grande é 6/9, e a rodada 4 chegou a 5.
- Os dois runs perdidos da tomlkit-0002 na rodada 7 construíram a chave sem o separador (`runs/coleta-r7/tomlkit-0002/.../rep02`, `rep03`, `patch.diff`): rep03 imprimiu `'foo.bar=1\n'`, a revisão reprovou citando o espaçamento e, na seguinte, aprovou a mesma saída; rep02 foi aprovada às cegas, porque os dois blocos de reprodução copiados pelo refinador não compilavam (`["a", "b", "c"]` virou `["a\nb\nc`; `SyntaxError: unmatched ']'`).
- Na rodada 7, 23 blocos de reprodução não compilaram: 16 não são Python (TOML, linha de comando) e 7 eram cópias deturpadas de blocos válidos do enunciado (cerca de markdown dentro do código, caracteres trocados). Sem bloco executado, o revisor aprovou às cegas 3 vezes (tomlkit-0001 rep02, tomlkit-0002 rep02, tomlkit-0003 rep02), uma delas errada.
- Barreira automática não resolve: calibração offline da rodada 7 (`scripts/calibrar_comparacao.py docs/tcc/dados/coleta-r7`), uma barreira dura sobre as saídas esperadas da intent pegaria 4 das 6 aprovações erradas e derrubaria 5 runs resolvidos (saídas parafraseadas pelo refinador). O teto de 2 reprovações não é a causa: as 6 aprovações erradas foram decisões do modelo (`strict_coerced: false` em todas).

## 2. O que muda em relação à rodada 4

| item | chave | rodada 4 | rodada 8 | onde |
|---|---|---|---|---|
| 1. cópia dos blocos de reprodução | `REPRODUCTION_SOURCE` | `intent` (cópia do refinador) | `statement`: cerca perdida removida; bloco que não compila trocado pelo bloco Python mais parecido do enunciado (sobreposição de tokens ≥ 0,5); `fonte` no evento `validation` | `src/enunciado.py::reparar_blocos`; `validator._executar_reproducao` |
| 2. saída esperada por bloco | `BLOCK_EXPECTED` | `off` | `statement`: bloco Python amarrado à "saída esperada" escrita logo depois dele no enunciado ("hoje"/"atual" fora); revisor final e de sub-tarefa recebem, por bloco e por linha, encontrada / NÃO encontrada; informação, sem regra | `pares_esperados`, `esperado_do_bloco`, `comparar_bloco`; `feedback.COMPARACAO_POR_BLOCO` |
| 2a. correção após a fumaça (23/10/2026) | idem | | a comparação é por **exemplo do enunciado**, não por bloco da intent: o refinador costuma fatiar um exemplo em vários blocos (sqlite-utils-0003: 1 exemplo com 4 saídas esperadas virou 4 blocos), e comparar as 4 linhas só com o 1º bloco dava 3 "NÃO encontrada" falsas; agora os blocos de um mesmo exemplo são agregados e a linha vai ao revisor como "exemplo k do enunciado (blocos a a b)". Exemplo cuja execução não terminou bem (`exit≠0`, `RECUSADO`, `TIMEOUT`) vira "não verificável", não "NÃO encontrada" (na rodada 4 a execução da revisão final da sqlite-utils-0003 rep02 morreu em `exit=1` num run resolvido) | `anotar_comparacoes`, `exemplo_do_bloco`, `execucao_terminou_bem` |
| 2b. modo guardado | `BLOCK_EXPECTED=strict` | | o revisor não pode aprovar com linha esperada **NÃO encontrada** em exemplo executado: a aprovação é rebaixada com as próprias linhas como motivo (`strict_coerced`), nunca promovida; "não verificável" não rebaixa. Só com aprovação do autor, depois da calibração da seção 5 | `validator._linhas_nao_encontradas` |
| herdados da rodada 7 | `REPRODUCTION_COMPILE_CHECK`, `REPRODUCTION_SHELL` | off | on | decisões 42 e 44 |
| não herdado | `SUBTASK_MAX_CYCLES` | 2 | 2 (a rodada 7 usou 1: mais barato, sem tarefa nova) | decisão 44 |

Pareamento nos 13 enunciados (`tests/test_enunciado.py::test_enunciados_reais`): saída esperada encontrada em tomlkit-0002, 0003, 0004, 0005 e sqlite-utils-0003; nenhuma nos outros 8 (attrs-0001 só traz "Saída hoje"; sqlite-utils-0002 anuncia com "No exemplo acima", sem a palavra "esperada", e fica de fora por conservadorismo).

Comando: `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on PLANNER_MAX_TURNS=12 PLANNER_MAX_SUBTASKS=6 SUBTASK_CHECK=llm REVIEW_COMPARE=off PLANNER_CONTEXT_MAX_CHARS=0 SUBTASK_MAX_CYCLES=2 REPRODUCTION_COMPILE_CHECK=on REPRODUCTION_SHELL=on REPRODUCTION_SOURCE=statement BLOCK_EXPECTED=statement MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=off DEVELOPER_INPUT=intent .venv/bin/python scripts/run_collection.py --arms orchestration ...` (manifesto v17).

## 3. Fumaças (22/10/2026, 23:29 a 23:51, US$ 0,82)

`runs/fumaca-r8`, dados sem workspaces em [dados/fumaca-r8/](dados/fumaca-r8/) (custo pela soma dos `llm_call`). 8 células, 0 perdidas: **5 resolvidas, 3 cortadas por orçamento, 0 aprovações erradas.** As mesmas 7 tarefas na rodada 7 (21 runs, `dados/coleta-r7/`): 13 resolvidas, 5 aprovações erradas, 4 cortes.

| tarefa | rodada 7 (3 reps) | fumaça r8 | o que os eventos mostram |
|---|---|---|---|
| attrs-0001 | 2/3, 1 aprovação errada | **1/1**, 81 turnos, 3/3 ocultos | sem saída esperada no enunciado (só "Saída hoje"): mede o item 1 sozinho; os 2 blocos rodaram |
| sqlite-utils-0001 | 2/3, 1 aprovação às cegas (0/1 verificável) | **1/1**, 35 turnos, 5/5 | bloco rodou; sem saída esperada pareada |
| sqlite-utils-0003 | 2/3, 1 aprovação errada (9/12 + regressão no CSV) | 0/1, orçamento, **11/12 ocultos, 0 regressões** | 9 reprovações finais, 5 citando as linhas esperadas; a comparação por bloco mostrou sempre 1 de 4 linhas encontrada (faltam `{'id': 1, 'id_3': 2, 'id_2': 3}`, `Cleo`, `tanuki`); o developer não fechou a última |
| tomlkit-0001 | 3/3 | **1/1**, 30 turnos | 1 bloco não compila: é TOML, correto |
| tomlkit-0002 | 1/3, 2 aprovações erradas (`foo.bar=1`) | **1/2**: rep01 resolvida em 56 turnos; rep02 orçamento | rep01: 1ª revisão reprovou, 2ª aprovou com as 4 linhas `'foo.bar = 1\n'` **encontradas**. rep02: 2 reprovações citando "esperava `'foo.bar = 1\n'`, obteve `'foo.bar=1\n'`"; o developer, em vez de passar o separador, reescreveu `items.py` e `container.py` (70 linhas) no 3º ciclo e quebrou 49 testes; não recuperou |
| tomlkit-0003 | 3/3 | **1/1**, 30 turnos (rodada 7: 45 a 57) | 2 linhas esperadas encontradas na 1ª revisão |
| tomlkit-0005 | 0/3, 3 cortes | 0/1, orçamento | 3 reprovações, todas citando `PySequence_Check = 0` não encontrado; ninguém resolve esta tarefa |

**Mecanismo 1 (cópia consertada pelo enunciado).** Não foi exercitado: nas 8 células nenhuma cópia do refinador precisou de conserto (`fonte` ausente em todas as execuções; na rodada 7 foram 7 blocos deturpados em 39 runs, cerca de 1 a cada 5 runs). Inócuo quando não é preciso; a prova fica para os 39 runs.

**Mecanismo 2 (saída esperada por bloco).** Apareceu nas 5 tarefas com par no enunciado (tomlkit-0002, 0003, 0005, sqlite-utils-0003; attrs-0001 e sqlite-utils-0001 não têm). O revisor citou as linhas esperadas em 9 das 14 reprovações finais dessas tarefas (sqlite-utils-0003 5 de 9, tomlkit-0002 rep02 1 de 2, tomlkit-0005 3 de 3) e não aprovou nenhuma vez com linha "NÃO encontrada"; aprovou a tomlkit-0002 rep01 na revisão em que as 4 linhas passaram a "encontrada". As revisões de sub-tarefa também levaram as linhas (tomlkit-0002 rep02 4 de 4, tomlkit-0005 4 de 4, sqlite-utils-0003 2 de 9, porque só a sub-tarefa 1 apontava o bloco pareado).

**Correção da leitura (23/10/2026).** Na sqlite-utils-0003 as 3 linhas "NÃO encontrada" eram falsas: o refinador fatiou o único exemplo do enunciado em 4 blocos e a comparação, então por bloco, cobrava as 4 saídas do 1º bloco. Recalculada por exemplo ([dados/fumaca-r8/calibracao-por-exemplo-r4-a-r8.txt](dados/fumaca-r8/calibracao-por-exemplo-r4-a-r8.txt)), a última reprovação desse run tinha as 4 linhas **encontradas**: o revisor reprovou um estado com 11 de 12 ocultos citando, em parte, linhas falsas; o que de fato faltava (o caso `--csv` da linha de comando) nenhum exemplo Python cobre. As reprovações da tomlkit-0002 rep02 e da tomlkit-0005 continuam com linhas faltando de verdade.

**Leitura (insight mínimo, 8 runs).** As aprovações erradas da rodada 7 eram um problema de evidência, não de juízo: com a saída esperada do enunciado ao lado da saída real, por bloco e por linha, o revisor foi consistente nas 8 células, inclusive nas 5 tarefas onde a rodada 7 aprovou errado. O custo é que a perda muda de lugar: em vez de aprovar errado, o run vai ao orçamento (3 de 8), e resolver passa a depender de o developer fechar a diferença que o revisor nomeia. Na tomlkit-0002 isso aconteceu 1 vez em 2 (na outra o developer reescreveu demais); na sqlite-utils-0003 chegou a 11 de 12 sem a regressão do CSV que perdia a rodada 7. Se isso dá mais tarefas que a rodada 4 só os 39 runs dizem (cerca de US$ 5; saldo após a fumaça ≈ US$ 3,9). Cache gravado: 86 a 92 %.

### 3.1 Fumaça em modo `strict` (23/10/2026, 07:56 a 08:04, US$ 0,36)

Antes dos 39 runs, duas execuções com `BLOCK_EXPECTED=strict` (`runs/fumaca-r8-strict`, dados sem workspaces em [dados/fumaca-r8-strict/](dados/fumaca-r8-strict/); custo pela soma de `cost.cost_usd` dos `result.json`), para ver a comparação por exemplo do enunciado, corrigida em 23/10, rodando ao vivo. 2 células, 0 perdidas: **1 resolvida, 1 cortada por orçamento, 0 aprovações erradas, 0 rebaixamentos** (`strict_coerced` não disparou: nas 5 revisões que receberam linhas de comparação, o revisor concordou com elas).

| tarefa | fumaça `statement` (22/10) | fumaça `strict` (23/10) | o que os eventos mostram |
|---|---|---|---|
| sqlite-utils-0003 | 0/1, orçamento, 11/12 ocultos | **1/1**, 64 turnos, 12/12 ocultos, 0 regressões, US$ 0,17 | planejador fez 5 sub-tarefas cobrindo `dedupe_keys`, `query`, `rows_where`, `search` e a linha de comando (como nos planos das rodadas 4 e 7). 1ª revisão final: 4 linhas NÃO encontradas (só `utils.py` escrito), reprovou. 2ª: as 4 encontradas, reprovou pelo bloco de linha de comando sem `--csv`. 3ª: aprovou, e estava certo. A sub-tarefa 1 (`dedupe_keys`) foi adiada após 2 ciclos sem o revisor de sub-tarefa a dar por feita; a tarefa fechou pela revisão final mesmo assim |
| tomlkit-0002 | **1/1**, 56 turnos | 0/1, orçamento, 1/1 oculto mas 2 módulos de teste sem importar, US$ 0,19 | o mecanismo funcionou: na sub-tarefa 2 a saída foi `foo.bar=1`, a linha «`'foo.bar = 1\n'`» veio NÃO encontrada e o revisor reprovou citando o espaço; no ciclo seguinte veio encontrada e aprovou. A perda é do developer: na sub-tarefa 1 reescreveu `tomlkit/api.py` inteiro com `write_file` (149 linhas alteradas) e deixou `ws` e `key_value` de fora; `tests/test_items.py` e `tests/test_toml_document.py` deixaram de importar. Rodou a suíte 4 vezes no 1º ciclo (8, 8, 8 e 2 erros de coleta), anotou na nota de ciclo "preciso restaurar `ws` e `key_value`" e não restaurou; 13 turnos do planejador, 41 na sub-tarefa 1, 66 na 2, orçamento com as sub-tarefas 3 e 4 pendentes e sem revisão final |

**Detalhe de desenho que apareceu.** Em `SUBTASK_CHECK=llm` (base da rodada 4) o revisor de sub-tarefa recebe o diff e as execuções, não o resultado da suíte (`validator._build_subtask_review_prompt`), e aprovou a sub-tarefa 1 da tomlkit-0002 com 2 erros de coleta na suíte. É raro: sub-tarefa aprovada com suíte vermelha ocorreu em 1 run de 40 na rodada 4, 1 de 41 na rodada 7 e 1 de 8 na fumaça de 22/10, este resolvido ([dados/fumaca-r8-strict/subtarefa-aprovada-com-suite-vermelha.txt](dados/fumaca-r8-strict/subtarefa-aprovada-com-suite-vermelha.txt), `scripts/subtarefa_suite_vermelha.py`). Não é causa sistemática; fica registrado, sem mudança nesta rodada.

**Leitura.** Mesma semente das fumaças de 22/10 e resultado invertido nas duas tarefas: a diferença entre as fumaças é variação do modelo, não a configuração (`strict` não rebaixou nada). O mecanismo da decisão 48 fez o que devia nas duas; o que decide a tarefa continua sendo o developer fechar a diferença que o revisor nomeia sem reescrever demais.

## 4. Execução dos 39 runs (lançada em 23/10/2026, 08:06)

Crédito de US$ 5 adicionado pelo autor em 23/10/2026 e etapa 1 aprovada ("prossiga com a etapa 1 de teste, já adicionei os US$5"): fumaça em `strict` (§3.1) e, confirmada, os 39 runs. Lançados às 08:06 em `runs/coleta-r8` (13 tarefas × 3 repetições, só o orquestrado, `BLOCK_EXPECTED=strict`, manifesto v17; o primeiro manifesto gravado traz `block_expected: strict`, `reproduction_source: statement`, `subtask_max_cycles: 2`). Comando: o de §2 com `BLOCK_EXPECTED=strict` e `--repetitions 3 --out runs/coleta-r8 --retry-delay 300 --max-attempts 5`. Critério (decisão 45): a rodada 8 vira a configuração decisiva da replicação se chegar a 10 ou mais tarefas de 13 sem perder na faixa grande em relação à rodada 4 (5/9); senão a rodada 4 fica. Resultado nesta seção quando fechar.

## 5. Calibração da barreira por exemplo (23/10/2026)

`scripts/calibrar_por_exemplo.py` sobre a última revisão final de cada run gravado, com o pareamento por exemplo e a regra "execução que não terminou bem é não verificável" ([dados/fumaca-r8/calibracao-por-exemplo-r4-a-r8.txt](dados/fumaca-r8/calibracao-por-exemplo-r4-a-r8.txt)). Pergunta: se o revisor fosse impedido de aprovar com linha NÃO encontrada (`BLOCK_EXPECTED=strict`), quantos runs resolvidos cairiam e quantas aprovações erradas seriam pegas?

| coleta | runs | derrubaria resolvidos | pegaria aprovações erradas | aprovações erradas que escapam (sem exemplo que as cubra) |
|---|---|---|---|---|
| rodada 4 | 39 | 0 | 0 | 2 |
| rodada 5 | 39 | 0 | 0 | 5 |
| rodada 6 | 39 | 0 | 0 | 4 |
| rodada 7 | 39 | 0 | 2 (sqlite-utils-0003 rep02, tomlkit-0002 rep03) | 4 |
| fumaça r8 | 8 | 0 | 0 | 0 |
| **total** | **164** | **0** | **2** | **15** |

Leitura: a barreira é segura (nenhum run resolvido cairia em 164) e pequena (pega 2 das 17 aprovações erradas das cinco coletas). As outras 15 são aprovações de código que nenhum exemplo do enunciado exercita (CSV e `rows_where`/`search` da sqlite-utils-0003, `transform` da sqlite-utils-0001/0002, `Field`/`Attribute` da attrs-0001): o revisor só pode errar sobre o que não roda, e isso é o limite da revisão por execução, não um defeito do revisor. Decisão para o autor: rodar os 39 runs da rodada 8 com `statement` (só informa) ou `strict` (impede a contradição).

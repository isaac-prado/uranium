# 23. Rodada 7: teto de um ciclo por sub-tarefa, blocos que não compilam fora da evidência e blocos de linha de comando executados (22/10/2026)

Objetivo aprovado por escrito em 22/10/2026 (decisão 44 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md)): uma rodada que supere a rodada 4 e sirva de configuração decisiva do orquestrado para a replicação final com dois modelos (decisão 45). Base: rodada 4 ([20-rodada-4.md](20-rodada-4.md)), a melhor até aqui (24/39 runs, 9/13 tarefas). Só o orquestrado roda, 13 tarefas × 3 repetições, mesmas sementes; single-agent de comparação: o pareado da rodada 2. Manifesto v16. Dados: `dados/coleta-r7/` (a versionar no fechamento); fumaça em `dados/fumaca-r7/`.

## 1. O que muda em relação à rodada 4

| item | chave | rodada 4 | rodada 7 | evidência (rodadas 4 a 6, eventos `plan`, `memory`, `validation`) | onde |
|---|---|---|---|---|---|
| 1. ciclos por sub-tarefa | `SUBTASK_MAX_CYCLES` | 2 | 1 (adiada após um ciclo de 40 turnos; volta ao fim com o orçamento restante) | 66 das 69 sub-tarefas concluídas fecharam no 1º ciclo; 3 no 2º; 0 das 74 adiadas foram concluídas depois. peewee-0002: 53 a 82 turnos na sub-tarefa 1 nos 9 runs, 0 de 9 resolvidos, single-agent 2 de 3 | `src/agents/validator.py::_avancar_plano` |
| 2. bloco que não compila | `REPRODUCTION_COMPILE_CHECK` | off | on: não roda, sai da cadeia acumulada, não entra nos prompts de revisão, fica no evento | fumaça 1 da rodada 6: rótulo citado como motivo em 8 de 8 reprovações; fumaça 2 com o filtro: 3 de 3 | `_blocos_que_nao_compilam`, `_evidencias` |
| 3. bloco em linha de comando | `REPRODUCTION_SHELL` | off (texto não-Python morria em `SyntaxError`) | on: `python -m ...`, `$ sqlite-utils ...` rodam como processo no workspace; saída na revisão e na comparação | sqlite-utils-0003: 5 de 9 runs com 12/12 ocultos e uma regressão só (CSV da CLI, critério 7), blocos da CLI nunca executados | `_comando_shell`, `_executar_comandos` |

Demais chaves iguais às da rodada 4: `INTENT_REFINER=v2`, `REVIEW_EXECUTION=cumulative`, `CYCLE_NOTE=on`, `PLANNER=on`, `PLANNER_MAX_TURNS=12`, `PLANNER_MAX_SUBTASKS=6`, `SUBTASK_CHECK=llm`, `REVIEW_COMPARE=off`, `REVIEW_STRICT=off`, `PLANNER_CONTEXT_MAX_CHARS=0`, `MAX_SEMANTIC_REJECTIONS=2`, `DEVELOPER_INPUT=intent`. Código que mudou desde o manifesto v12 sem depender de chave: intent em markdown numerada (v13); planejador executa os blocos na base e recebe o cabeçalho de saídas já produzidas, plano com `expected` (v14), ambos sem efeito com `SUBTASK_CHECK=llm` e `REVIEW_COMPARE=off`.

Comando: `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on PLANNER_MAX_TURNS=12 PLANNER_MAX_SUBTASKS=6 SUBTASK_CHECK=llm REVIEW_COMPARE=off PLANNER_CONTEXT_MAX_CHARS=0 SUBTASK_MAX_CYCLES=1 REPRODUCTION_COMPILE_CHECK=on REPRODUCTION_SHELL=on MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=off DEVELOPER_INPUT=intent scripts/run_collection.py --arms orchestration --repetitions 3 --out runs/coleta-r7 --workers 1 --retry-delay 300 --max-attempts 5`.

## 2. O que a rodada mede e o critério

- Se liberar a sub-tarefa travada após um ciclo devolve os turnos que a peewee-0002 e os 31 runs cortados com sub-tarefa pendente perderam, sem tirar das tarefas que a rodada 4 resolvia.
- Se executar os blocos de CLI fecha a sqlite-utils-0003 (média), onde o estado certo chegou a existir em 5 de 9 runs.
- Critério de decisiva: 10 ou mais tarefas de 13 (rodada 4: 9) sem perder na faixa grande (5/9). Custo esperado próximo ao da rodada 4 (US$ 5,67).
- Primeira coleta com `payload.tokens_cached` em cada `llm_call` (decisão 46, 22/10/2026): a fração do prompt lida do cache da DeepInfra passa a ser medida, não inferida do custo (rodada 4: 82,5 % inferida; [08-escolha-modelo.md](08-escolha-modelo.md) §10.2). `scripts/cache_fraction.py` imprime as duas lado a lado para conferir a inferência das rodadas anteriores.

## 3. Fumaça (22/10/2026, 19:42 a 19:57, US$ 0,44)

peewee-0002, sqlite-utils-0003 e tomlkit-0003 (controle), 1 repetição, `runs/fumaca-r7`. Esperado nos eventos: sub-tarefa adiada após um ciclo e o developer passando à seguinte (peewee-0002); blocos de CLI com `shell: true` e a saída da CLI na revisão (sqlite-utils-0003); tomlkit-0003 resolvendo em ~20 turnos.

**Resultado** ([dados/fumaca-r7/](dados/fumaca-r7/), eventos sem os workspaces; custo pela soma dos `llm_call`): 3 células, 0 perdidas, 1 de 3 resolvida. Os três mecanismos apareceram nos eventos, que era o critério da fumaça; o desfecho das duas não resolvidas é da mesma classe das perdas das rodadas 4 a 6, e é o que os 39 runs vão medir.

| tarefa | desfecho | turnos | o que os eventos mostram | cache | custo |
|---|---|---|---|---|---|
| tomlkit-0003 (controle) | **resolvida**, `concluiu` | 44 (rodada 6, fumaça 2: 20) | revisão final única e aprovada; o bloco 1 da reprodução não compila, ficou fora da cadeia e a revisão não o citou (`nao_compila: true`, `executado: false`) | 94,3 % | 0,121 |
| sqlite-utils-0003 (blocos de CLI) | não resolvida, `concluiu` aos 61 turnos: ocultos 10/12 (faltam `test_fts::test_search_duplicate_columns_are_deduped` e `test_rows::test_rows_where_duplicate_select_columns_are_deduped`) e regressão em `test_cli::test_query_csv_duplicate_columns_are_preserved` | 61 | o bloco 5 (`$ python -m sqlite_utils memory 'select 1 as id, 2 as id, …'`) rodou como processo nas duas revisões finais (`shell: true`): na 1ª mostrou o bug (`[{"id": 2, "value": "y"}]`) e a revisão reprovou com critérios 1 a 5 e 7 faltando; na 2ª mostrou a correção (`[{"id": 1, "id_2": 2, "value": "x", "value_2": "y"}]`) e a revisão aprovou. Plano de 5 sub-tarefas com 1 feita e 3 pendentes: o developer corrigiu além da sub-tarefa corrente e a revisão final aprovou com o plano aberto. Nenhum bloco da intent exercita `rows_where`/`search` com colunas duplicadas nem o CSV, então a revisão não tinha como ver as duas faltas e a regressão: a mesma perda das rodadas 5 e 6 nesta tarefa | 88,6 % | 0,151 |
| peewee-0002 (teto de 1 ciclo) | não resolvida, orçamento (120 turnos): ocultos 3/6 (passam os das sub-tarefas 1 a 3; faltam `make_index_name_long`, `column_map_not_shared_with_class`, `on_conflict unbound_error`) | 120 | plano de 6 sub-tarefas: 1, 2 e 3 **feitas** aos 181 s, 341 s e 457 s (um ciclo cada); 4 **adiada** após um ciclo aos 544 s, 5 **adiada** aos 599 s, 6 em andamento no corte. Nas rodadas 4 a 6 o developer gastava 53 a 82 turnos na sub-tarefa 1 e nenhum dos 9 runs passou dela; agora três sub-tarefas fecharam e o orçamento acabou nas três mais difíceis | 92,3 % | 0,169 |

Leitura: o teto de um ciclo liberou a peewee-0002 (3 de 6 ocultos, contra 0 de 6 habitual), mas não a fecha com 120 turnos; a execução dos blocos de CLI entrega ao revisor exatamente a saída que a tarefa descreve, e a perda restante está no que a intent não exercita (CSV, `rows_where`, `search`), que nenhuma execução de reprodução alcança. Primeira coleta com `tokens_cached` gravado: 88,6 a 94,3 % do prompt em cache (decisão 46), na faixa inferida para as rodadas 5 e 6.

## 4. Execução (22/10/2026, 19:58 a 22:26) e resultado

**Resultado: 23 de 39 runs e 9 de 13 tarefas. Igual à rodada 4 em tarefas (9) e um run abaixo (24). Não atinge o critério de decisiva da seção 2: 10 ou mais tarefas sem perder na faixa grande, e a faixa grande caiu de 5/9 para 4/9.** Custou menos (US$ 4,37 contra 5,67; 32,3 M de tokens contra 37,9 M; 10 cortes por orçamento contra 16), mas a revisão final aprovou errado 6 vezes (rodada 4: 3). 39 células, 1 tentativa perdida (429 na peewee-0003 rep03, refeita como attempt02) e 2 runs encerrados por erro do provedor que o harness não classificou como perda (abaixo). Fontes: [dados/coleta-r7/](dados/coleta-r7/) (eventos sem os workspaces, `collection.json`, `analise-sete-metricas.{md,json}`, `apendice-metricas.md` e `resumo-rodadas-4-6-7.txt`, saída de `scripts/resumo_rodada.py`); single-agent pareado de `runs/coleta-r2-analise`.

### 4.1 Rodadas lado a lado (orquestrado; single-agent da coleta principal)

| | single-agent | rodada 4 | rodada 6 | **rodada 7** |
|---|---|---|---|---|
| runs resolvidos | 23/39 | 24/39 | 19/39 | **23/39** |
| tarefas resolvidas (maioria das repetições) | 8/13 | 9/13 | 6/13 | **9/13** |
| faixa grande / média / pequena (runs) | 4/9 · 10/12 · 9/18 | 5/9 · 7/12 · 12/18 | 4/9 · 4/12 · 11/18 | **4/9 · 6/12 · 13/18** |
| cortes por orçamento | 10 | 16 | 16 | **10** |
| `concluiu` sem resolver (aprovação errada) | — | 3 | 5 | **6** |
| resolvidas no corte | — | 4 | 1 | 1 |
| custo (US$) · tokens | 8,52 · 73,1 M | 5,67 · 37,9 M | 5,97 · 46,3 M | **4,37 · 32,3 M** |
| mediana de tokens por run | 0,31 M | 0,88 M | 1,30 M | **0,69 M** |
| fração do prompt em cache | 95,4 % (inferida) | 82,5 % (inferida) | 92,4 % (inferida) | **90,7 % (gravada)** |

Por tarefa (runs resolvidos de 3; faixa entre parênteses):

| tarefa | single-agent | rodada 4 | rodada 7 | o que mudou na 7 |
|---|---|---|---|---|
| attrs-0001 (média) | 3 | 2 | 2 | rep01 `concluiu` com 2/3 ocultos (`test_handler_non_attrs_generic_class`) |
| peewee-0001 (média) | 3 | 3 | **2** | rep03 cortada com 0/4 ocultos e 6 sub-tarefas adiadas nos 3 runs |
| peewee-0002 (média) | 2 | 0 | 0 | rep01 cortada com **5/6 ocultos**, o melhor do orquestrado nesta tarefa em 12 runs; rep03 morta por erro do provedor no turno 27 |
| peewee-0003 (pequena) | 3 | 3 | 3 | |
| pygments-0001 (pequena) | 2 | 3 | 3 | rep01 resolvida no turno 78, quando morreu por erro do provedor |
| sqlite-utils-0001 (pequena) | 1 | 1 | **2** | ganhou a rep03 (rodada 4: corte); rep01 `concluiu` com 0/5 |
| sqlite-utils-0002 (pequena) | 0 | 2 | 2 | rep03 `concluiu` com 5/11 |
| sqlite-utils-0003 (média) | 2 | 2 | 2 | blocos de CLI executados nos 3 runs (18 execuções); rep02 `concluiu` com 9/12 e a regressão do CSV; rep03 12/12 no corte |
| tomlkit-0001 (pequena) | 3 | 3 | 3 | |
| tomlkit-0002 (grande) | 1 | 2 | **1** | rep02 e rep03 `concluiu` aos 102 e 81 turnos com `test_add_dotted_key` falhando (rodada 4: rep01 cortada) |
| tomlkit-0003 (grande) | 3 | 3 | 3 | |
| tomlkit-0004 (grande) | 0 | 0 | 0 | cortada 3×, 0/7 ocultos; nenhum braço resolve |
| tomlkit-0005 (pequena) | 0 | 0 | 0 | cortada 3×, regressões na suíte; nenhum braço resolve |

### 4.2 As sete métricas (`analise-sete-metricas.md`, orquestrado − single-agent)

Taxa de resolução 9/13 × 8/13 (sinal exato, p = 1,0); custo em tokens, mediana por tarefa entre as 7 resolvidas por ambos, 350.684 × 314.294 (Wilcoxon, p = 0,81; rodada 4: 769.526, p = 0,30); tempo 154,0 × 154,9 s (p = 0,69); Δ complexidade 0,013 × 0,014 (p = 0,56); consistência 4/10 × 5/10; conclusão sem corte **29/39 × 29/39** (rodada 4: 23/39); violações 1 crítica, 0 bloqueadas e 28 negações × 0, 0, 5. Em dólares, mediana por run 0,0469 × 0,0372; chamadas ao modelo 42 × 29.

### 4.3 Os mecanismos, nos eventos (`resumo-rodadas-4-6-7.txt`)

- **Teto de um ciclo por sub-tarefa.** 162 sub-tarefas planejadas em 41 tentativas; 26 feitas, 46 adiadas em algum momento, 7 abandonadas; só 2 adiadas foram concluídas depois (attrs-0001, tomlkit-0005), repetindo as rodadas 4 a 6 (0 de 74). O que o teto comprou foi orçamento: cortes de 16 para 10, mediana de tokens por run de 0,88 M para 0,69 M, conclusão sem corte igual à do single-agent. O que não comprou foi tarefa: a peewee-0002 chegou a 5/6 ocultos e ficou sem turnos; a peewee-0001 rep03 adiou tudo e não fechou nada.
- **Blocos de linha de comando.** 18 execuções em 3 runs, todos da sqlite-utils-0003, com a saída da CLI na revisão. A tarefa ficou em 2/3 como na rodada 4: o run que a revisão aprovou errado (rep02) tinha 9/12 ocultos e a regressão do CSV, que nenhum bloco da intent exercita.
- **Bloco que não compila fora da evidência.** 17 blocos em 4 runs (tomlkit-0002 8, tomlkit-0001 5, tomlkit-0003 3, sqlite-utils-0002 1); nenhuma reprovação citou o rótulo. tomlkit-0001 e tomlkit-0003 fecharam 3/3.
- **Cache.** Primeira coleta com o campo gravado: 90,7 % do prompt lido do cache, 63 chamadas a preço cheio (rodada 4: 82,5 % inferido, 481 a preço cheio). Menos ciclos e menos replanejamentos (2) mantêm o prefixo.

### 4.4 Onde a rodada 7 perdeu

Seis aprovações erradas (rodada 4: 3), todas com a suíte visível verde e a revisão final sem comparação de saídas (`REVIEW_COMPARE=off`, como na rodada 4): attrs-0001 rep01, sqlite-utils-0001 rep01, sqlite-utils-0002 rep03, sqlite-utils-0003 rep02 e tomlkit-0002 rep02 e rep03. As duas da tomlkit-0002 custaram a faixa grande (2/3 → 1/3) e são o motivo de a rodada não ser decisiva: nos dois runs o developer passou de 80 turnos, a revisão reprovou várias vezes e depois aprovou um estado em que `test_add_dotted_key` continua falhando. Os cortes restantes são as tarefas que nenhum braço resolve (tomlkit-0004, tomlkit-0005) e a peewee-0002.

**Dois runs mortos por erro do provedor contados como terminados.** pygments-0001 rep01 (turno 78, patch já resolvia) e peewee-0002 rep03 (turno 27, 0/6) morreram com `ValueError({'message': 'Upstream error from DeepInfra: ... Response payload is not completed', 'code': 502, 'metadata': {'error_type': 'provider_unavailable'}})`: o OpenRouter devolveu o erro no corpo de uma resposta 200, o cliente do LangChain o levanta como `ValueError` e `src/config.py::is_provider_error` só olhava `APIStatusError`, então o `stop_reason` saiu `error: ValueError` e `lost: false` (a coleta não os refez). Pela definição de run perdido (decisão 14: 5xx do provedor é perda) os dois são perdas. Correção feita em 22/10/2026 (`openrouter_error_body`; teste em `tests/test_structured_llm.py`), válida para a replicação, onde o mesmo 502 silencioso viraria run terminado. O veredito da rodada não depende deles: pygments-0001 fica resolvida com 2 ou 3 de 3, e peewee-0002 fica em 0 de 3 com qualquer desfecho. **Pendente do autor:** reclassificar os dois `summary.json` como perdidos e refazê-los como attempt02 (mesma semente, cerca de US$ 0,30), ou mantê-los e declará-los no texto.

**Um sinal crítico do detector de trapaça e um run envenenado pela guarda.** peewee-0002 rep02 terminou com `exec_test.py` na raiz do workspace (regra C1, padrão protegido `**/*_test.py`; run não resolvido, 2/6 ocultos, não bloqueado). O arquivo não veio de `write_file` (o ledger registra `peewee.py` e `teste_temp.py`): foi criado por código que o developer executou em `run_python`. Na execução seguinte a guarda de `src/tools/exec.py` viu o arquivo protegido, respondeu `RECUSADO` e "reverteu" com `git checkout -- exec_test.py`, que não remove arquivo novo (não rastreado); o arquivo ficou, e **toda execução posterior foi recusada**: 16 chamadas de `run_python` negadas do turno 42 ao 120, e 28 das execuções de reprodução do validador devolvidas como `RECUSADO`, que a revisão citou ("os scripts de reprodução tentaram modificar arquivos protegidos e foram recusados"). Nas rodadas 4 a 6 nenhuma execução do validador foi recusada; na 7, só neste run. Rodada 6 teve o único outro sinal C1 (tomlkit-0004 rep03, `tests/examples/example.toml`). A guarda de caminho é intocável sem aprovação; **proposta para o autor, antes da replicação:** ao recusar, remover o arquivo protegido que a execução criou (não rastreado) em vez de só `git checkout`, e comparar o estado antes e depois da execução, para que um arquivo deixado por uma execução anterior não recuse as seguintes.

### 4.5 Leitura e o que decidir

A rodada 7 empata com a 4 em tarefas (9/13) e é melhor em custo, cortes e conclusão sem corte; é pior em aprovações erradas (6 × 3) e na faixa grande (4/9 × 5/9). Pelo critério da seção 2 ela **não** supera a 4, e a regra da decisão 45 ("rodada 7 se superar a 4; senão, a 4") aponta a **rodada 4** como configuração decisiva do orquestrado na replicação. O autor decide se mantém a regra ou troca pela rodada 7 pelo custo; o que os dados dizem é que a diferença entre as duas está dentro do ruído de 3 repetições (tomlkit-0002 2/3 × 1/3 e peewee-0001 3/3 × 2/3 de um lado, sqlite-utils-0001 1/3 × 2/3 do outro) e que nenhuma das duas resolve o que a intent não exercita.

## 5. Depois da rodada 7: replicação final (decisão 45)

Configuração decisiva do orquestrado (rodada 7 se superar a 4; senão, a 4: pelo resultado da seção 4, a regra leva à rodada 4, pendente da confirmação do autor) e o single-agent, 13 × 3 cada, com `deepseek/deepseek-v3.2` não-pensante (DeepInfra, fp4) e `mistralai/devstral-2512` (Mistral). Por modelo: sondagem de aptidão, fumaça de 3 tarefas nos dois braços, 78 runs. Projeção (perfil da rodada 4 e do single-agent pareado; [08-escolha-modelo.md](08-escolha-modelo.md) §10): DeepSeek US$ 15 a 29; Devstral US$ 8 a 46; sondagens e fumaças ~US$ 2.

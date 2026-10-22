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

## 4. Execução (em andamento)

Lançada em 22/10/2026 às 19:58, desacoplada do editor (`setsid nohup bash fila-r7.sh`), 39 células em `runs/coleta-r7`, um run por vez, vigia a cada 5 minutos; saldo estimado na DeepInfra antes do lançamento: US$ 9,1 (9,5 menos a fumaça). Fechamento: raiz pareada `runs/coleta-r7-analise` (orquestrado r7 + single-agent da coleta principal), sete métricas e apêndice em `dados/coleta-r7/`, resultado aqui e no registro da decisão 44.

## 5. Depois da rodada 7: replicação final (decisão 45)

Configuração decisiva do orquestrado (rodada 7 se superar a 4; senão, a 4) e o single-agent, 13 × 3 cada, com `deepseek/deepseek-v3.2` não-pensante (DeepInfra, fp4) e `mistralai/devstral-2512` (Mistral). Por modelo: sondagem de aptidão, fumaça de 3 tarefas nos dois braços, 78 runs. Projeção (perfil da rodada 4 e do single-agent pareado; [08-escolha-modelo.md](08-escolha-modelo.md) §10): DeepSeek US$ 15 a 29; Devstral US$ 8 a 46; sondagens e fumaças ~US$ 2.

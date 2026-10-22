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

## 3. Fumaça (a preencher)

peewee-0002, sqlite-utils-0003 e tomlkit-0003 (controle), 1 repetição, `runs/fumaca-r7`. Esperado nos eventos: sub-tarefa adiada após um ciclo e o developer passando à seguinte (peewee-0002); blocos de CLI com `shell: true` e a saída da CLI na revisão (sqlite-utils-0003); tomlkit-0003 resolvendo em ~20 turnos.

## 4. Execução (a preencher)

## 5. Depois da rodada 7: replicação final (decisão 45)

Configuração decisiva do orquestrado (rodada 7 se superar a 4; senão, a 4) e o single-agent, 13 × 3 cada, com `deepseek/deepseek-v3.2` não-pensante (DeepInfra, fp4) e `mistralai/devstral-2512` (Mistral). Por modelo: sondagem de aptidão, fumaça de 3 tarefas nos dois braços, 78 runs. Projeção (perfil da rodada 4 e do single-agent pareado; [08-escolha-modelo.md](08-escolha-modelo.md) §10): DeepSeek US$ 15 a 29; Devstral US$ 8 a 46; sondagens e fumaças ~US$ 2.

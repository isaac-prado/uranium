# 26. Replicação com dois modelos (decisão 45): aptidão, fumaças e coletas

## 1. Desenho

Duas replicações do estudo principal, cada uma com os dois braços, 13 tarefas × 3 repetições (78 runs), mesmas sementes e tetos (decisão 12), orquestrado na configuração da rodada 4 (regra da decisão 45, fechada em 27/10/2026 com o resultado da rodada 8: [24-rodada-8.md](24-rodada-8.md) §4.1). Modelos: `deepseek/deepseek-v3.2` não-pensante na DeepInfra (chave BYOK do autor) e `mistralai/devstral-2512` na Mistral. Manifesto v18: os dois braços e os dois modelos rodam com o workspace só no commit-base e a execução do agente em caixa de areia (decisão 49, [25-vazamento-historico-git.md](25-vazamento-historico-git.md)), o que a coleta principal e as rodadas 2 a 8 não tinham.

Comando (orquestrado da rodada 4, chaves explícitas): `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on PLANNER_MAX_TURNS=12 PLANNER_MAX_SUBTASKS=6 SUBTASK_CHECK=llm REVIEW_COMPARE=off PLANNER_CONTEXT_MAX_CHARS=0 SUBTASK_MAX_CYCLES=2 REPRODUCTION_COMPILE_CHECK=off REPRODUCTION_SHELL=off REPRODUCTION_SOURCE=intent BLOCK_EXPECTED=off MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=off DEVELOPER_INPUT=intent .venv/bin/python scripts/run_collection.py --model <modelo> --provider <provedor> --repetitions 3 --out runs/coleta-<modelo> --workers 1 --retry-delay 300 --max-attempts 5`.

## 2. Sondagem de aptidão (27/10/2026)

`scripts/fitness_test.py --model <modelo> --provider <provedor> -n 5`, laudo em [dados/sondagens/aptidao-replicacao-2026-10-27.txt](dados/sondagens/aptidao-replicacao-2026-10-27.txt):

| modelo · provedor | tool calling | provedor servido | determinismo (assinaturas distintas em 5) | tokens de raciocínio | BYOK | veredito |
|---|---|---|---|---|---|---|
| deepseek/deepseek-v3.2 · DeepInfra | 5/5, argumentos exatos 5/5 | DeepInfra 5/5 | 3 (divergente: declarar a variabilidade) | 0 | sim | apto |
| mistralai/devstral-2512 · Mistral | 5/5, argumentos exatos 5/5 | Mistral 5/5 | 1 | 0 | não (chave Mistral a registrar no OpenRouter) | apto |

O DeepSeek V3.2 na DeepInfra responde sem raciocínio por padrão (`reasoning_tokens` 0 na sondagem e na chamada direta); nada muda no pino de provedor.

## 3. Fumaça do DeepSeek (27/10/2026, 21:59 a 23:17, US$ 1,43)

`runs/fumaca-deepseek`, dados sem workspaces em [dados/fumaca-deepseek/](dados/fumaca-deepseek/). 3 tarefas × 2 braços × 1 repetição, 0 perdidas. Primeira coleta sob a decisão 49: 125 execuções de código do agente (`run_python` e `run_tests`) dentro da caixa de areia, 0 recusadas, 0 erros de ferramenta, 0 sinais do detector; 521 de 521 chamadas BYOK na DeepInfra; 0 tokens de raciocínio.

| tarefa | single-agent | orquestrado |
|---|---|---|
| tomlkit-0003 (grande) | resolvida, 102 turnos, US$ 0,38 | resolvida, 41 turnos, US$ 0,09 |
| sqlite-utils-0003 (média) | resolvida 12/12, 71 turnos, US$ 0,20 | resolvida 12/12, 54 turnos, US$ 0,14 |
| peewee-0002 (média) | orçamento, 5/6 ocultos e 45 regressões, US$ 0,40 | orçamento, 4/6 ocultos e 2 regressões, US$ 0,23 |

4 de 6, as mesmas 4 que o Qwen3-Coder resolve nessas tarefas; peewee-0002 continua sem solução em qualquer modelo ou braço. Cache gravado: 98 a 99 % no single-agent, 88 a 90 % no orquestrado. Latência mediana por chamada entre 4 e 10 s (Qwen: 1 a 3 s): os 78 runs devem levar de 10 a 14 horas de parede. Custo projetado dos 78 runs pela fumaça (US$ 0,09 a 0,40 por run): entre US$ 20 e 30 na DeepInfra, acima dos US$ 16 projetados em [08-escolha-modelo.md](08-escolha-modelo.md) §10.2.

## 4. Pendente

- Crédito na DeepInfra (cerca de US$ 30; saldo estimado após a fumaça ≈ US$ 2) para os 78 runs do DeepSeek (`runs/coleta-deepseek`).
- Chave da Mistral registrada como BYOK no OpenRouter e crédito na Mistral (cerca de US$ 15) para a fumaça e os 78 runs do Devstral (`runs/fumaca-devstral`, `runs/coleta-devstral`); sem BYOK o Devstral passa pelo crédito do OpenRouter (US$ 5), que cobre só a fumaça.
- Fechamento de cada replicação com as sete métricas (`scripts/analyze_results.py`) e a comparação com o estudo principal.

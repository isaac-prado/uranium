# Coleta definitiva: resultados das 13 tarefas (12 e 13/10/2026)

Dados: `dados/coleta/<tarefa>/<braço>/rep0k/attemptNN/` (78 runs admitidos, 79 tentativas), `dados/coleta/collection.json`, logs `collection-grandes.log`, `collection-etapa2.log`, `collection-etapa2b.log`. Análise de registro (sete métricas, `scripts/analyze_results.py`): `dados/coleta/analise-sete-metricas.md` e `.json`. Análise operacional (`scripts/analyze_collection.py`): `dados/coleta/analise-operacional.md`. Contabilidade de contexto: `dados/coleta/contabilidade-contexto.md` (discrepância mediana 0,0%). Configuração congelada (decisão 12, manifesto v7): 120 turnos, 8 M tokens, 3.600 s; orquestrado com memória de trabalho e ciclos de 40 turnos; `qwen/qwen3-coder` no DeepInfra com chave própria.

## 1. Execução

| | |
|---|---|
| Células | 13 tarefas × 2 braços × 3 repetições = 78 |
| Perdidas | 0 células; 1 tentativa perdida (reinício da máquina em 12/10 às 23:53 durante `sqlite-utils-0003/single-agent/rep01/attempt01`, sem `summary.json`; refeita como `attempt02` com a mesma semente, regra de `harness/attempts.py`) |
| Chave própria | `byok_calls == llm_calls` nos 78 runs |
| Custo | US$ 17,26 (soma de `cost.cost_usd` dos 78 admitidos; single-agent US$ 12,05, orchestration US$ 5,21) mais US$ 0,08 da tentativa perdida |
| Tokens | single-agent 100,6 M; orchestration 40,6 M |
| Duração | etapa 1 (grandes) 12/10 21:09–22:18; etapa 2 12/10 22:19–23:53 (interrompida) e 13/10 08:17–15:31 |
| Cortes por tokens | 5, todos no single-agent: `pygments-0001` rep. 1 e 3 (resolvidas), `sqlite-utils-0002` rep. 1 (resolvida), 2 e 3 (não) |
| Cortes por parede | 0 |
| Cortes por turnos | single-agent 8, orchestration 16 |
| Admissão | 78 de 78; nenhum par quebrado; nenhuma violação crítica ou bloqueante do detector; avisos (C6, exceção silenciada): single-agent 8, orchestration 5 |

## 2. As sete métricas (`analise-sete-metricas.md`, unidade = tarefa, mediana das repetições)

| # | Métrica | single-agent | orchestration | teste | p |
|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | **8/13** | **6/13** | sinal exato bilateral, n = 9 | 0,180 |
| 2 | Custo (tokens, mediana; tarefas resolvidas por ambos, n = 5) | 121.675 | 278.656 | Wilcoxon bilateral | 0,813 |
| 3 | Tempo até a solução (s, mediana; n = 5) | 113,4 | 127,0 | Wilcoxon bilateral | 0,188 |
| 4 | Consistência (tarefas resolvidas nas 3 repetições / tarefas resolvidas ao menos uma vez) | 6/11 | 3/8 | descritivo | — |
| 5 | Δ complexidade (mediana, n = 13) | 0,025 | 0,024 | Wilcoxon bilateral | 0,969 |
| 6 | Conclusão sem corte (runs) | 26/39 | 23/39 | descritivo | — |
| 7 | Violações (críticas; bloqueantes; negações de ferramenta) | 0; 0; 11 | 0; 0; 39 | descritivo | — |

Hipótese primária H1 ("orchestration resolve mais que single-agent"), teste unicaudal do sinal sobre as 9 tarefas com diferença (`analise-operacional.md`): +2 −7, p = 0,98; Wilcoxon p = 0,95. **H1 não é sustentada; a direção observada é a contrária.** Por run: single-agent 25/39 resolvidos, orchestration 17/39.

Secundárias na análise operacional (todas as 13 tarefas, média das repetições, Wilcoxon bilateral): custo em dólares por tarefa SA 0,220 × OR 0,138 (p = 0,022); tokens SA 1,998 M × OR 0,945 M (p = 0,002); turnos p = 0,38; parede p = 0,24. As duas análises divergem no custo porque censuram diferente: a de registro compara só tarefas resolvidas por ambos (n = 5, orquestrado mais caro na mediana), a operacional compara todas (orquestrado mais barato porque gasta menos quando falha). As duas vão para o texto com a regra de censura ao lado.

## 3. Por tarefa (runs resolvidos de 3; `analise-operacional.md`)

| tarefa | faixa | single-agent | orchestration | observação |
|---|---|---|---|---|
| tomlkit-0003 | grande | 3 | 3 | ambos sempre; orquestrado mais barato em 2 de 3 |
| tomlkit-0002 | grande | 1 | 1 | ambos só na rep. 2; revisor reprovou 4× o patch correto do orquestrado |
| tomlkit-0004 | grande | 0 | 0 | melhor parcial: single-agent rep. 3, 5/7 ocultos |
| attrs-0001 | média | 3 | 2 | orquestrado rep. 2: 2/3 ocultos e 1 regressão |
| peewee-0001 | média | 3 | 2 | orquestrado rep. 1: 3/4 ocultos |
| peewee-0002 | média | 2 | 0 | orquestrado 2–3/6 ocultos nas três, cortado por turnos |
| sqlite-utils-0003 | média | 2 | 0 | orquestrado 9–11/12 ocultos, 3 a 36 regressões |
| peewee-0003 | pequena | 3 | 3 | ambos sempre, 9 a 18 turnos |
| tomlkit-0001 | pequena | 3 | 2 | |
| pygments-0001 | pequena | 3 | 0 | single-agent cortado por tokens em 2 das 3 com a correção pronta (8,1 M); orquestrado 0/2 ocultos nas três |
| sqlite-utils-0001 | pequena | 1 | 0 | orquestrado passa 5/5 ocultos em 2 reps mas deixa 1 regressão (não conta como resolvido) |
| sqlite-utils-0002 | pequena | 1 | 3 | single-agent cortado por tokens nas três (8,0–8,2 M), 1 resolvida |
| tomlkit-0005 | pequena | 0 | 1 | |

Por faixa (runs resolvidos): grande SA 4/9, OR 4/9; média SA 10/12, OR 4/12; pequena SA 11/18, OR 9/18. A diferença a favor do single-agent concentra-se na faixa média.

## 4. O que a telemetria do orquestrado mostra (39 runs, eventos `intent`, `validation`, `memory`)

- **Ciclos.** 14 runs com 1 ciclo, 25 com 2 ou mais (memória de trabalho efetivamente usada); distribuição 1:14, 2:6, 3:11, 4:4, 6:2, 11:1, 33:1. Os dois últimos são runs em que o developer encerrava sem mudar nada e voltava com o aviso de diff vazio.
- **Revisão semântica.** 50 revisões com a suíte verde: 22 aprovadas, 28 reprovadas. **Cinco runs resolvidos pelo oráculo tiveram ao menos uma reprovação do revisor** (`peewee-0001` r2, `tomlkit-0001` r3, `tomlkit-0002` r2 com quatro, `tomlkit-0003` r3 com duas, `tomlkit-0005` r1): falsos negativos de um revisor que lê o diff sem executar. Um run fechou pelo teto semântico.
- **Negações de ferramenta.** 39 no orquestrado contra 11 no single-agent; 33 das 39 são `write_file`/`replace_in_file` na área protegida de testes: o developer orquestrado tenta escrever testes com mais frequência.
- **Custo.** O orquestrado gastou 40% dos tokens do single-agent no total (40,6 M contra 100,6 M). O single-agent paga pelo histórico persistente: 5 cortes por tokens, todos dele, em repositórios cujo `run_tests` devolve saída longa (pygments, sqlite-utils); o orquestrado zera o contexto a cada 40 turnos.

## 5. Leitura para o texto

1. **Resultado principal.** Com `qwen/qwen3-coder`, o protótipo orquestrado não resolve mais tarefas que o agente único; resolve menos, com diferença não significativa no teste do sinal (p = 0,18 bilateral) e concentrada na faixa média. H1 não se sustenta.
2. **Custo.** O orquestrado é mais barato no agregado e quando falha; nas tarefas que ambos resolvem, a mediana por tarefa não favorece nenhum braço (p = 0,81). A troca "contexto curto e barato contra contexto longo e caro" (decisões 8 e 25) aparece nos dados: o single-agent é o único cortado por tokens.
3. **Onde o orquestrado perde.** (a) O revisor semântico reprova patches corretos e consome turnos; (b) o developer, diante de suíte vermelha num ponto de checagem, desfaz ou reescreve em vez de corrigir (patches de 750 a 2.130 linhas com centenas de regressões nas grandes); (c) em `sqlite-utils-0001` e `attrs-0001` o orquestrado passa os ocultos e perde por uma regressão.
4. **Onde o orquestrado ganha.** `sqlite-utils-0002` (3 contra 1) e `tomlkit-0005` (1 contra 0): tarefas em que o single-agent estoura tokens ou cicla sem convergir.
5. **Ameaças.** n = 13 tarefas de 5 repositórios, 3 repetições, um único modelo; a ordem fixa dentro do par (single-agent primeiro); o revisor semântico não executa código (limitação do protótipo, declarada); a faixa grande tem uma tarefa no chão nos dois braços.

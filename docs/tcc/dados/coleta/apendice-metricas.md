# Apêndice de métricas da coleta (78 runs admitidos, `docs/tcc/dados/coleta`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.524 | 4 | 9 | 5/9 | 0 | 3265263 | 0.35 | 102 | 271 | 60 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 4/9 | 0.444 | 5 | 94 | 3/9 | 0 | 1774426 | 0.207 | 121 | 207 | 13 | 0 | -0.588 | 6 | 4 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 4/12 | 0.75 | 8 | 10 | 8/12 | 0 | 872534 | 0.106 | 75 | 326 | 57 | 0.007 | -0.059 | 10 | 1 |
| pequena | single-agent | 18 | 11/18 | 0.704 | 7 | 4 | 10/18 | 5 | 1005354 | 0.122 | 72 | 326 | 32 | 0.011 | 0 | 7 | 8 |
| pequena | orchestration | 18 | 9/18 | 0.656 | 8 | 1 | 12/18 | 0 | 559889 | 0.08 | 64 | 213 | 24 | 0.024 | 0 | 23 | 0 |
| todas | single-agent | 39 | 25/39 | 0.749 | 13 | 6 | 26/39 | 5 | 1598793 | 0.174 | 80 | 271 | 39 | 0.025 | 0 | 11 | 8 |
| todas | orchestration | 39 | 17/39 | 0.636 | 21 | 2 | 23/39 | 0 | 860128 | 0.103 | 78 | 221 | 29 | 0.011 | 0 | 39 | 5 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 0 | 0 | 3 | — |
| media | 4 | 0 | 4 | 0 | 0.125 |
| pequena | 6 | 2 | 3 | 1 | 1 |
| todas | 13 | 2 | 7 | 4 | 0.1797 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 5 | 0.625 |
| fração de ocultos passados | ambos_resolvem_mediana | 5 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 7 | 0 | 0 | 1 |
| tokens | todas | 13 | -146263 | 21 | 0.0942 |
| tokens | ambos_resolvem_mediana | 5 | 10426 | 6 | 0.8125 |
| tokens | ambos_resolvem_ao_menos_uma | 7 | -65186 | 9 | 0.4688 |
| US$ | todas | 13 | -0.019 | 21 | 0.0942 |
| US$ | ambos_resolvem_mediana | 5 | 0.004 | 6 | 0.8125 |
| US$ | ambos_resolvem_ao_menos_uma | 7 | -0.007 | 9 | 0.4688 |
| chamadas | todas | 13 | 5 | 29.5 | 0.2817 |
| chamadas | ambos_resolvem_mediana | 5 | 6 | 4 | 0.4375 |
| chamadas | ambos_resolvem_ao_menos_uma | 7 | 6 | 5 | 0.1562 |
| parede (s) | todas | 13 | -0.148 | 44 | 0.946 |
| parede (s) | ambos_resolvem_mediana | 5 | 49.221 | 2 | 0.1875 |
| parede (s) | ambos_resolvem_ao_menos_uma | 7 | 15.567 | 11 | 0.6875 |
| turnos | todas | 13 | 0 | 25.5 | 0.5322 |
| turnos | ambos_resolvem_mediana | 5 | 3 | 5 | 0.625 |
| turnos | ambos_resolvem_ao_menos_uma | 7 | 3 | 5 | 0.3125 |
| linhas do patch | todas | 13 | -4 | 24 | 0.4648 |
| linhas do patch | ambos_resolvem_mediana | 5 | 0 | 3 | 1 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 7 | -4 | 4 | 0.4375 |
| ΔCC | todas | 13 | 0 | 17.5 | 0.9688 |
| ΔCC | ambos_resolvem_mediana | 5 | 0 | 0 | 1 |
| ΔCC | ambos_resolvem_ao_menos_uma | 7 | 0 | 1.5 | 0.75 |
| regressões | todas | 13 | 0 | 8 | 0.375 |
| regressões | ambos_resolvem_mediana | 5 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 7 | 0 | 1 | 1 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 14, 2: 6, 3: 11, 4: 4, 6: 2, 11: 1, 33: 1}; runs com 2+ ciclos (memória de trabalho usada): 25/39.
- Revisões semânticas (suíte verde): 50; aprovadas 22, reprovadas 28.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 5 — [('peewee-0001', 2, 1), ('tomlkit-0001', 3, 2), ('tomlkit-0002', 2, 4), ('tomlkit-0003', 3, 2), ('tomlkit-0005', 1, 1)].
- Runs resolvidos com todas as revisões aprovadas: 9; runs não resolvidos com ao menos uma reprovação: 8.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | não | 0/1 | 1 | 120 | 125 | 1918293 | 0.222 | 295 | 2 | 13 | 0.043 | -0.588 | 2 | 0 | budget: max_turns | 40·25·40·15 | RRRR |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | sim | 1/1 | 0 | 120 | 125 | 1535970 | 0.178 | 200 | 2 | 12 | 0.043 | -0.676 | 1 | 0 | budget: max_turns | 37·40·40·3 | RRRR |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | não | 0/1 | 428 | 120 | 121 | 2373775 | 0.272 | 301 | 3 | 608 | -0.017 | 5.868 | 1 | 0 | budget: max_turns | 40·40·40 | — |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 21 | 24 | 180589 | 0.025 | 72 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 21 | A |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 31 | 34 | 290700 | 0.037 | 77 | 2 | 4 | 0 | 0 | 0 | 0 | concluiu | 31 | A |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 61 | 65 | 544278 | 0.068 | 129 | 2 | 4 | 0 | 0 | 0 | 0 | concluiu | 27·34 | RR |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 94 | 120 | 121 | 1774426 | 0.207 | 207 | 1 | 987 | -0.822 | -0.814 | 0 | 0 | budget: max_turns | 40·40·40 | — |
| tomlkit-0004 | grande | 1 | single-agent | não | 0/7 | 9 | 120 | 120 | 5211394 | 0.559 | 381 | 2 | 59 | 0.158 | -1.407 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 0/7 | 121 | 120 | 121 | 2506897 | 0.288 | 250 | 4 | 1696 | -0.813 | -6.245 | 1 | 4 | budget: max_turns | 40·40·40 | — |
| tomlkit-0004 | grande | 2 | single-agent | não | 0/7 | 9 | 120 | 120 | 3913926 | 0.421 | 277 | 2 | 181 | 1.102 | -5.715 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 0/7 | 9 | 120 | 121 | 1924723 | 0.227 | 339 | 1 | 200 | 0.625 | -5.642 | 1 | 0 | budget: max_turns | 40·40·40 | — |
| tomlkit-0004 | grande | 3 | single-agent | não | 5/7 | 2 | 102 | 102 | 3814927 | 0.413 | 235 | 1 | 60 | 0.355 | -1.625 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 21 | 24 | 117411 | 0.018 | 77 | 2 | 12 | 0.078 | -0.232 | 2 | 0 | concluiu | 21 | A |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | não | 2/3 | 1 | 22 | 25 | 123745 | 0.019 | 127 | 2 | 25 | 0.156 | -0.507 | 0 | 0 | concluiu | 22 | A |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | sim | 3/3 | 0 | 55 | 58 | 476538 | 0.061 | 221 | 3 | 22 | 0.056 | -0.118 | 2 | 0 | concluiu | 38·17 | A |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | não | 3/4 | 1 | 87 | 92 | 734495 | 0.091 | 595 | 1 | 53 | 0 | 0 | 0 | 0 | concluiu | 28·40·19 | RRA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 111 | 115 | 1583075 | 0.206 | 880 | 1 | 286 | 0.003 | 0 | 2 | 0 | concluiu | 40·31·40 | RA |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 25 | 28 | 251781 | 0.038 | 276 | 1 | 51 | 0.003 | 0 | 0 | 0 | concluiu | 25 | A |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 2/6 | 18 | 120 | 123 | 1143904 | 0.139 | 597 | 3 | 74 | 0.01 | 0.036 | 0 | 0 | budget: max_turns | 40·19·40·21 | RR |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 2/6 | 152 | 120 | 122 | 3439738 | 0.621 | 3357 | 4 | 3209 | -0.558 | 17.199 | 1 | 0 | budget: max_turns | 40·40·40 | R |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 3/6 | 17 | 120 | 123 | 1087824 | 0.125 | 376 | 2 | 16 | 0.002 | 0 | 0 | 0 | budget: max_turns | 40·40·40 | RR |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | não | 11/12 | 36 | 120 | 121 | 2511222 | 0.306 | 480 | 3 | 479 | 0.047 | -1.489 | 2 | 1 | budget: max_turns | 40·40·40 | — |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | não | 9/12 | 4 | 54 | 58 | 884941 | 0.108 | 140 | 3 | 65 | 0.005 | -0.258 | 0 | 0 | concluiu | 37·17 | RA |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | não | 9/12 | 3 | 40 | 43 | 860128 | 0.103 | 158 | 3 | 61 | 0.031 | -0.277 | 1 | 0 | concluiu | 40 | A |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 9 | 12 | 34893 | 0.007 | 143 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 9 | A |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 10 | 13 | 36407 | 0.008 | 205 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 10 | A |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 18 | 21 | 117097 | 0.017 | 194 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | concluiu | 18 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | não | 0/2 | 2 | 68 | 71 | 941898 | 0.115 | 221 | 1 | 40 | 0 | 0 | 0 | 0 | concluiu | 40·28 | A |
| pygments-0001 | pequena | 1 | single-agent | sim | 2/2 | 0 | 115 | 115 | 8111726 | 0.87 | 1511 | 1 | 36 | 0 | 0 | 1 | 0 | budget: max_tokens | — | — |
| pygments-0001 | pequena | 2 | orchestration | não | 0/2 | 2 | 120 | 121 | 1387656 | 0.214 | 866 | 1 | 38 | 0 | 0 | 7 | 0 | budget: max_turns | 22·7·6·8·9·9·16·1·8·9·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·1·3 | — |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 120 | 120 | 6608004 | 0.877 | 1198 | 1 | 26 | 0 | 0 | 2 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 3 | orchestration | não | 0/2 | 2 | 55 | 58 | 505694 | 0.084 | 1099 | 1 | 30 | 0 | 0 | 1 | 0 | concluiu | 40·15 | A |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 120 | 120 | 8104295 | 1.09 | 2077 | 1 | 55 | 0 | 0 | 1 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 5/5 | 1 | 23 | 26 | 191321 | 0.029 | 94 | 1 | 37 | 0.052 | 0 | 1 | 0 | concluiu | 23 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | não | 4/5 | 1 | 36 | 39 | 411514 | 0.055 | 130 | 1 | 29 | 0.071 | 0 | 1 | 0 | concluiu | 36 | A |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 5/5 | 1 | 26 | 29 | 361446 | 0.049 | 151 | 1 | 20 | 0.045 | 0 | 1 | 0 | concluiu | 26 | A |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 120 | 121 | 1566456 | 0.193 | 401 | 1 | 29 | 0.025 | 0 | 3 | 0 | budget: max_turns | 40·25·17·15·20·3 | — |
| sqlite-utils-0002 | pequena | 1 | single-agent | sim | 11/11 | 0 | 100 | 100 | 8156392 | 0.863 | 803 | 1 | 28 | 0.031 | 0 | 1 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | sim | 11/11 | 0 | 120 | 121 | 1926824 | 0.237 | 456 | 1 | 34 | 0.012 | 0 | 3 | 0 | budget: max_turns | 40·40·14·10·3·1·1·1·1·1·8 | — |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 6 | 100 | 100 | 8136340 | 1.184 | 2430 | 1 | 69 | 0.093 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | sim | 11/11 | 0 | 120 | 121 | 1754943 | 0.224 | 476 | 1 | 43 | 0.025 | 0 | 3 | 0 | budget: max_turns | 40·31·17·16·15·1 | — |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 9/11 | 6 | 104 | 104 | 8004114 | 1.145 | 1230 | 1 | 38 | 0.043 | 0 | 1 | 0 | budget: max_tokens | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 24 | 27 | 206286 | 0.027 | 111 | 1 | 3 | 0 | 0 | 0 | 0 | concluiu | 24 | A |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | não | 0/1 | 0 | 39 | 42 | 278656 | 0.034 | 119 | 1 | 7 | 0.024 | 0 | 0 | 0 | concluiu | 39 | A |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 77 | 82 | 627208 | 0.08 | 138 | 1 | 14 | 0.024 | 0 | 0 | 0 | concluiu | 40·16·21 | RRA |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | sim | 1/1 | 0 | 74 | 78 | 614084 | 0.08 | 319 | 1 | 10 | 0.004 | 0 | 2 | 0 | concluiu | 39·35 | RA |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 0/1 | 1 | 120 | 125 | 1466274 | 0.182 | 391 | 1 | 32 | -0.009 | 0 | 1 | 0 | budget: max_turns | 40·40·39·1 | RRRR |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | não | 0/1 | 1 | 120 | 123 | 1918750 | 0.219 | 324 | 0 | 0 | — | — | 0 | 0 | budget: max_turns | 40·40·40 | RR |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


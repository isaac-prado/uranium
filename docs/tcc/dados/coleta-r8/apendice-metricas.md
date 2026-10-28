# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-r8-analise`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.587 | 4 | 22 | 4/9 | 0 | 3265263 | 0.35 | 120 | 295 | 124 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 6/9 | 0.667 | 2 | 77 | 5/9 | 0 | 606970 | 0.082 | 70 | 95 | 11 | 0.032 | -0.318 | 2 | 4 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 5/12 | 0.653 | 6 | 2 | 8/12 | 0 | 880206 | 0.115 | 72 | 342 | 44 | 0.025 | -0.077 | 2 | 0 |
| pequena | single-agent | 18 | 9/18 | 0.598 | 9 | 4 | 14/18 | 1 | 507754 | 0.064 | 38 | 170 | 36 | 0 | 0 | 1 | 8 |
| pequena | orchestration | 18 | 9/18 | 0.662 | 9 | 4 | 12/18 | 0 | 652101 | 0.089 | 58 | 193 | 22 | 0.002 | 0 | 1 | 0 |
| todas | single-agent | 39 | 23/39 | 0.715 | 15 | 6 | 29/39 | 1 | 979282 | 0.117 | 50 | 243 | 40 | 0.014 | 0 | 5 | 8 |
| todas | orchestration | 39 | 20/39 | 0.66 | 17 | 4 | 25/39 | 0 | 774655 | 0.108 | 65 | 197 | 22 | 0.016 | 0 | 5 | 4 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 1 | 0 | 2 | 1 |
| media | 4 | 1 | 3 | 0 | 0.625 |
| pequena | 6 | 1 | 1 | 4 | 1 |
| todas | 13 | 3 | 4 | 6 | 1 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 4 | 0.875 |
| fração de ocultos passados | ambos_resolvem_mediana | 6 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 7 | 0 | 0 | 1 |
| tokens | todas | 13 | -74065 | 28 | 0.2439 |
| tokens | ambos_resolvem_mediana | 6 | 13510 | 9 | 0.8438 |
| tokens | ambos_resolvem_ao_menos_uma | 7 | -14858 | 12 | 0.8125 |
| US$ | todas | 13 | 0 | 38 | 0.6355 |
| US$ | ambos_resolvem_mediana | 6 | 0.008 | 2 | 0.0938 |
| US$ | ambos_resolvem_ao_menos_uma | 7 | 0.008 | 9 | 0.4688 |
| chamadas | todas | 13 | 10 | 20 | 0.0784 |
| chamadas | ambos_resolvem_mediana | 6 | 14.5 | 2 | 0.0938 |
| chamadas | ambos_resolvem_ao_menos_uma | 7 | 10 | 8 | 0.375 |
| parede (s) | todas | 13 | -8.651 | 40 | 0.7354 |
| parede (s) | ambos_resolvem_mediana | 6 | 25.632 | 9 | 0.8438 |
| parede (s) | ambos_resolvem_ao_menos_uma | 7 | 11.818 | 12 | 0.8125 |
| turnos | todas | 13 | 7 | 23 | 0.2251 |
| turnos | ambos_resolvem_mediana | 6 | 9.5 | 4 | 0.2188 |
| turnos | ambos_resolvem_ao_menos_uma | 7 | 7 | 11 | 0.6875 |
| linhas do patch | todas | 13 | -9 | 12 | 0.0322 |
| linhas do patch | ambos_resolvem_mediana | 6 | -7.5 | 0 | 0.0625 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 7 | -9 | 0 | 0.0312 |
| ΔCC | todas | 13 | 0 | 16 | 0.8438 |
| ΔCC | ambos_resolvem_mediana | 6 | 0 | 0 | 0.5 |
| ΔCC | ambos_resolvem_ao_menos_uma | 7 | 0 | 2 | 0.75 |
| regressões | todas | 13 | 0 | 0 | 0.5 |
| regressões | ambos_resolvem_mediana | 6 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 7 | 0 | — | — |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 12, 2: 9, 3: 9, 4: 6, 5: 1, 6: 1, 10: 1}; runs com 2+ ciclos (memória de trabalho usada): 27/39.
- Revisões semânticas (suíte verde): 153; aprovadas 48, reprovadas 105.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 11 — [('peewee-0001', 1, 1), ('peewee-0001', 3, 3), ('peewee-0003', 1, 15), ('pygments-0001', 1, 2), ('pygments-0001', 3, 3), ('sqlite-utils-0003', 1, 6), ('sqlite-utils-0003', 2, 2), ('sqlite-utils-0003', 3, 2), ('tomlkit-0002', 1, 1), ('tomlkit-0002', 2, 6), ('tomlkit-0002', 3, 1)].
- Runs resolvidos com todas as revisões aprovadas: 9; runs não resolvidos com ao menos uma reprovação: 16.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | sim | 1/1 | 0 | 59 | 64 | 451225 | 0.06 | 95 | 2 | 10 | 0.043 | -0.498 | 0 | 0 | concluiu | 20·26 | RAA |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | sim | 1/1 | 0 | 120 | 129 | 1288139 | 0.157 | 197 | 2 | 15 | 0.043 | -0.318 | 0 | 0 | budget: max_turns | 24·41·27·15 | RARRRRRA |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | sim | 1/1 | 0 | 65 | 70 | 606970 | 0.082 | 87 | 2 | 11 | 0.043 | -0.409 | 0 | 0 | concluiu | 15·41 | RAA |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 40 | 43 | 463507 | 0.063 | 83 | 1 | 12 | 0.016 | 0 | 2 | 0 | concluiu | 27 | A |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 31 | 34 | 400935 | 0.06 | 73 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 18 | A |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 34 | 37 | 423553 | 0.062 | 62 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 21 | A |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 0 | 120 | 124 | 2682089 | 0.352 | 327 | 11 | 6327 | 0.23 | -10.033 | 0 | 3 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0004 | grande | 1 | single-agent | não | 3/7 | 60 | 120 | 120 | 4007174 | 0.453 | 348 | 2 | 176 | 0.814 | -3.691 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 0/7 | 7 | 120 | 126 | 1565800 | 0.198 | 210 | 1 | 2 | 0.032 | -0.176 | 0 | 0 | budget: max_turns | 41·41·25 | RRRRR |
| tomlkit-0004 | grande | 2 | single-agent | não | 3/7 | 7 | 120 | 120 | 4864896 | 0.522 | 555 | 2 | 40 | 0.288 | -0.238 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 0/7 | 147 | 120 | 124 | 1985759 | 0.247 | 167 | 5 | 2446 | -0.631 | -6.254 | 0 | 1 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0004 | grande | 3 | single-agent | não | 3/7 | 4 | 120 | 120 | 4921834 | 0.53 | 367 | 1 | 216 | 1.24 | -5.642 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | não | 2/3 | 1 | 77 | 81 | 821560 | 0.109 | 299 | 3 | 102 | 0.1 | -0.372 | 0 | 0 | concluiu | 41·23 | RA |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | não | 2/3 | 1 | 27 | 32 | 147219 | 0.026 | 126 | 2 | 7 | 0.078 | -0.232 | 0 | 0 | concluiu | 12·7 | RAA |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | não | 2/3 | 1 | 34 | 39 | 209963 | 0.032 | 94 | 2 | 6 | 0.078 | -0.155 | 0 | 0 | concluiu | 13·8 | RAA |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 27 | 32 | 163884 | 0.027 | 309 | 1 | 23 | 0.002 | 0 | 0 | 0 | concluiu | 6·8 | RAA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | não | 0/4 | 0 | 120 | 126 | 2795279 | 0.361 | 828 | 1 | 9938 | -1.267 | 46.289 | 1 | 0 | budget: max_turns | 7·41·33·26 | RARRR |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 41 | 48 | 299436 | 0.045 | 375 | 1 | 42 | 0.003 | 0 | 0 | 0 | concluiu | 6·8·14 | RARRA |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 3/6 | 3 | 120 | 127 | 1181229 | 0.155 | 818 | 1 | 20 | 0.005 | 0 | 1 | 0 | budget: max_turns | 12·41·33·21 | RARARA |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 0/6 | 6 | 120 | 127 | 1034731 | 0.129 | 478 | 1 | 22 | 0.003 | 0 | 0 | 0 | budget: max_turns | 41·40·26 | RRRRRR |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 2/6 | 4 | 120 | 133 | 1033318 | 0.134 | 683 | 1 | 47 | 0.014 | 0 | 0 | 0 | budget: max_turns | 14·25·23·19·10·16 | RRRRRRRARARR |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | sim | 12/12 | 0 | 94 | 105 | 1757669 | 0.246 | 463 | 3 | 89 | 0.065 | -0.703 | 0 | 0 | concluiu | 13·18·13·18·21 | RARARRRRA |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | sim | 12/12 | 0 | 58 | 63 | 938851 | 0.121 | 238 | 3 | 51 | 0.035 | -0.682 | 0 | 0 | concluiu | 7·38 | RRA |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | sim | 12/12 | 0 | 52 | 57 | 774655 | 0.106 | 134 | 3 | 80 | 0.038 | -0.363 | 0 | 0 | concluiu | 6·33 | RRA |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 120 | 140 | 876789 | 0.127 | 2088 | 1 | 13 | 0.154 | 12.266 | 0 | 0 | budget: max_turns | 10·11·6·7·15·13·12·16·14·0 | RARARARRRARRRRRRRRR |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 21 | 24 | 121066 | 0.021 | 190 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 8 | A |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 23 | 26 | 143471 | 0.024 | 105 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 10 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | sim | 2/2 | 0 | 60 | 65 | 931846 | 0.132 | 288 | 1 | 31 | 0 | 0 | 0 | 0 | concluiu | 41·6 | RRA |
| pygments-0001 | pequena | 1 | single-agent | não | 0/2 | 2 | 120 | 120 | 7109886 | 0.819 | 859 | 1 | 53 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 2 | orchestration | não | 0/2 | 2 | 120 | 127 | 2750932 | 0.367 | 649 | 1 | 77 | 0 | 0 | 0 | 0 | budget: max_turns | 41·41·25 | RRRRRR |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 17 | 17 | 229142 | 0.037 | 127 | 1 | 47 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | sim | 2/2 | 0 | 104 | 110 | 1718143 | 0.23 | 272 | 1 | 44 | 0 | 0 | 0 | 0 | concluiu | 9·41·41 | RRRA |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 50 | 50 | 1288314 | 0.179 | 606 | 1 | 61 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 4/5 | 1 | 24 | 27 | 181548 | 0.03 | 122 | 1 | 26 | 0.058 | 0 | 0 | 0 | concluiu | 11 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | não | 1/5 | 4 | 27 | 30 | 245105 | 0.039 | 91 | 1 | 30 | 0.052 | 0 | 0 | 0 | concluiu | 19 | A |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 0/5 | 5 | 82 | 88 | 766319 | 0.108 | 217 | 1 | 50 | 0.028 | 0 | 0 | 0 | concluiu | 15·15·15·24 | RRRA |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 46 | 49 | 537883 | 0.071 | 131 | 1 | 19 | 0.025 | 0 | 1 | 0 | concluiu | 33 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 28 | 28 | 452395 | 0.057 | 119 | 1 | 30 | 0.031 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | não | 5/11 | 6 | 34 | 37 | 415850 | 0.058 | 103 | 1 | 30 | 0.037 | 0 | 0 | 0 | concluiu | 21 | A |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 10 | 117 | 117 | 8077370 | 1.113 | 1328 | 1 | 38 | -0.008 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | não | 5/11 | 85 | 120 | 124 | 2808887 | 0.369 | 371 | 2 | 502 | -0.07 | -2.922 | 0 | 0 | budget: max_turns | 41·41·25 | RAA |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 45 | 45 | 821788 | 0.096 | 161 | 1 | 34 | 0.011 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 34 | 37 | 212988 | 0.031 | 62 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 21 | A |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 29 | 32 | 162675 | 0.025 | 65 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 18 | A |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 47 | 50 | 330240 | 0.043 | 53 | 1 | 3 | 0 | 0 | 0 | 0 | concluiu | 34 | A |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | não | 0/1 | 1 | 120 | 129 | 1146393 | 0.153 | 229 | 1 | 4 | 0 | 0 | 0 | 0 | budget: max_turns | 24·41·41·1 | RRRRRRRR |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 1/1 | 89 | 120 | 125 | 1265118 | 0.17 | 256 | 1 | 52 | -0.044 | 0 | 0 | 0 | budget: max_turns | 38·16·41·12 | RRRA |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | não | 0/1 | 1 | 120 | 126 | 1398553 | 0.177 | 195 | 2 | 8 | 0.004 | 0 | 0 | 0 | budget: max_turns | 30·39·38 | RRRRR |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


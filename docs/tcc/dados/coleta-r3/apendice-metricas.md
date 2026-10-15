# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-r3-analise`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.587 | 4 | 22 | 4/9 | 0 | 3265263 | 0.35 | 120 | 295 | 124 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 5/9 | 0.556 | 4 | 7 | 3/9 | 0 | 1506359 | 0.19 | 122 | 379 | 71 | 0.114 | -0.498 | 0 | 1 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 5/12 | 0.722 | 7 | 3 | 8/12 | 0 | 1146432 | 0.146 | 69 | 376 | 33 | 0.011 | -0.199 | 0 | 1 |
| pequena | single-agent | 18 | 9/18 | 0.598 | 9 | 4 | 14/18 | 1 | 507754 | 0.064 | 38 | 170 | 36 | 0 | 0 | 1 | 8 |
| pequena | orchestration | 18 | 9/18 | 0.623 | 9 | 1 | 11/18 | 0 | 731508 | 0.104 | 62 | 280 | 24 | 0.013 | 0 | 1 | 0 |
| todas | single-agent | 39 | 23/39 | 0.715 | 15 | 6 | 29/39 | 1 | 979282 | 0.117 | 50 | 243 | 40 | 0.014 | 0 | 5 | 8 |
| todas | orchestration | 39 | 19/39 | 0.638 | 20 | 3 | 22/39 | 0 | 1062830 | 0.146 | 83 | 324 | 30 | 0.015 | 0 | 1 | 2 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 1 | 0 | 2 | 1 |
| media | 4 | 0 | 3 | 1 | 0.25 |
| pequena | 6 | 1 | 1 | 4 | 1 |
| todas | 13 | 2 | 4 | 7 | 0.6875 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 10 | 1 |
| fração de ocultos passados | ambos_resolvem_mediana | 4 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 9 | 0 | 3 | 0.625 |
| tokens | todas | 13 | 109562 | 42 | 0.8394 |
| tokens | ambos_resolvem_mediana | 4 | 139725.5 | 3 | 0.625 |
| tokens | ambos_resolvem_ao_menos_uma | 9 | 109562 | 21 | 0.9102 |
| US$ | todas | 13 | 0.017 | 43 | 0.8926 |
| US$ | ambos_resolvem_mediana | 4 | 0.02 | 3 | 0.625 |
| US$ | ambos_resolvem_ao_menos_uma | 9 | 0.017 | 21 | 0.9102 |
| chamadas | todas | 13 | 14 | 13 | 0.0203 |
| chamadas | ambos_resolvem_mediana | 4 | 15 | 3 | 0.625 |
| chamadas | ambos_resolvem_ao_menos_uma | 9 | 14 | 10 | 0.1562 |
| parede (s) | todas | 13 | 98.372 | 11 | 0.0134 |
| parede (s) | ambos_resolvem_mediana | 4 | 207.49 | 1 | 0.25 |
| parede (s) | ambos_resolvem_ao_menos_uma | 9 | 98.372 | 5 | 0.0391 |
| turnos | todas | 13 | 11 | 7.5 | 0.0391 |
| turnos | ambos_resolvem_mediana | 4 | 12 | 3 | 0.625 |
| turnos | ambos_resolvem_ao_menos_uma | 9 | 11 | 6 | 0.2031 |
| linhas do patch | todas | 13 | -9 | 20.5 | 0.0837 |
| linhas do patch | ambos_resolvem_mediana | 4 | -2 | 3 | 0.625 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 9 | -2 | 19 | 0.7148 |
| ΔCC | todas | 13 | 0 | 18 | 0.6523 |
| ΔCC | ambos_resolvem_mediana | 4 | 0.001 | 0 | 0.5 |
| ΔCC | ambos_resolvem_ao_menos_uma | 9 | 0 | 3 | 0.3125 |
| regressões | todas | 13 | 0 | 4 | 0.5 |
| regressões | ambos_resolvem_mediana | 4 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 9 | 0 | 4 | 1 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 12, 2: 5, 3: 15, 4: 3, 6: 1, 8: 1, 11: 2}; runs com 2+ ciclos (memória de trabalho usada): 27/39.
- Revisões semânticas (suíte verde): 98; aprovadas 22, reprovadas 76.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 10 — [('peewee-0001', 1, 1), ('peewee-0003', 1, 11), ('peewee-0003', 2, 11), ('peewee-0003', 3, 2), ('sqlite-utils-0002', 1, 7), ('sqlite-utils-0003', 3, 2), ('tomlkit-0001', 1, 1), ('tomlkit-0002', 1, 4), ('tomlkit-0002', 3, 3), ('tomlkit-0003', 2, 6)].
- Runs resolvidos com todas as revisões aprovadas: 9; runs não resolvidos com ao menos uma reprovação: 12.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | sim | 1/1 | 0 | 120 | 125 | 1193992 | 0.16 | 655 | 3 | 85 | 0.114 | -0.333 | 0 | 0 | budget: max_turns | 41·33·28·18 | RRRR |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | não | 0/1 | 1 | 120 | 122 | 1580102 | 0.192 | 375 | 2 | 30 | 0.15 | -0.498 | 0 | 1 | budget: max_turns | 41·41·38 | R |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | sim | 1/1 | 0 | 113 | 119 | 1506359 | 0.19 | 318 | 2 | 79 | 0.135 | -0.918 | 0 | 0 | concluiu | 41·34·16·22 | RRRA |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 16 | 19 | 123215 | 0.038 | 430 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 16 | A |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 120 | 127 | 1497414 | 0.188 | 492 | 1 | 2 | 0 | 0 | 0 | 0 | budget: max_turns | 31·13·18·41·15·2 | RRRRRR |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 19 | 22 | 315347 | 0.04 | 70 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 19 | A |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 7 | 120 | 123 | 1715242 | 0.225 | 379 | 2 | 100 | 0.094 | -1.805 | 0 | 0 | budget: max_turns | 41·41·38 | RR |
| tomlkit-0004 | grande | 1 | single-agent | não | 3/7 | 60 | 120 | 120 | 4007174 | 0.453 | 348 | 2 | 176 | 0.814 | -3.691 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 0/7 | 7 | 120 | 122 | 1583669 | 0.193 | 383 | 3 | 71 | 0.208 | -1.322 | 0 | 0 | budget: max_turns | 41·41·38 | R |
| tomlkit-0004 | grande | 2 | single-agent | não | 3/7 | 7 | 120 | 120 | 4864896 | 0.522 | 555 | 2 | 40 | 0.288 | -0.238 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 0/7 | 12 | 120 | 121 | 2339161 | 0.293 | 277 | 1 | 98 | 0.535 | -4.919 | 0 | 0 | budget: max_turns | 41·41·38 | — |
| tomlkit-0004 | grande | 3 | single-agent | não | 3/7 | 4 | 120 | 120 | 4921834 | 0.53 | 367 | 1 | 216 | 1.24 | -5.642 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 18 | 21 | 110270 | 0.019 | 133 | 2 | 23 | 0.226 | -0.659 | 0 | 0 | concluiu | 18 | A |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | não | 2/3 | 1 | 59 | 62 | 538492 | 0.076 | 200 | 3 | 16 | 0 | -0.016 | 0 | 0 | concluiu | 41·18 | A |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | não | 0/3 | 3 | 56 | 62 | 435779 | 0.063 | 294 | 2 | 10 | 0.078 | -0.145 | 0 | 0 | concluiu | 20·11·14·11 | RRRA |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 79 | 83 | 1040280 | 0.136 | 588 | 2 | 58 | 0.005 | -0.253 | 0 | 0 | concluiu | 41·38 | RA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 40 | 43 | 484183 | 0.061 | 234 | 3 | 86 | 0.01 | -0.367 | 0 | 0 | concluiu | 40 | A |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 29 | 32 | 334583 | 0.042 | 202 | 1 | 30 | 0.001 | 0 | 0 | 0 | concluiu | 29 | A |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 1/6 | 5 | 120 | 124 | 1252584 | 0.156 | 523 | 1 | 34 | 0.005 | 0 | 0 | 0 | budget: max_turns | 41·41·38 | RRR |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 3/6 | 3 | 120 | 124 | 1339971 | 0.323 | 2781 | 1 | 29 | 0.008 | 0 | 0 | 0 | budget: max_turns | 41·41·38 | RRR |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 2/6 | 4 | 120 | 124 | 1298420 | 0.158 | 496 | 1 | 32 | 0.012 | 0 | 0 | 1 | budget: max_turns | 41·41·38 | RRR |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | não | 12/12 | 6 | 120 | 121 | 2504709 | 0.327 | 434 | 4 | 265 | 0.041 | -0.856 | 0 | 0 | budget: max_turns | 41·41·38 | — |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | não | 12/12 | 1 | 41 | 44 | 1313994 | 0.179 | 444 | 3 | 74 | 0.02 | -0.365 | 0 | 0 | concluiu | 41 | A |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | sim | 12/12 | 0 | 71 | 76 | 1304805 | 0.175 | 318 | 3 | 87 | 0.049 | -0.392 | 0 | 0 | concluiu | 41·21·9 | RRA |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 120 | 132 | 1208963 | 0.177 | 2088 | 1 | 11 | 0.308 | 7.437 | 0 | 0 | budget: max_turns | 15·14·5·7·6·32·7·9·11·8·6 | RRRRRRRRRRR |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 120 | 132 | 952803 | 0.146 | 2016 | 1 | 16 | 0.462 | 4.517 | 0 | 0 | budget: max_turns | 9·20·17·12·9·19·12·7·8·7·0 | RRRRRRRRRRR |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 53 | 58 | 402160 | 0.071 | 867 | 1 | 12 | 0.176 | -0.27 | 0 | 0 | concluiu | 17·28·8 | RRA |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | não | 1/2 | 1 | 120 | 124 | 3090071 | 0.409 | 1045 | 1 | 95 | 0 | 0 | 0 | 0 | budget: max_turns | 41·41·38 | RRR |
| pygments-0001 | pequena | 1 | single-agent | não | 0/2 | 2 | 120 | 120 | 7109886 | 0.819 | 859 | 1 | 53 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 2 | orchestration | não | 0/2 | 2 | 38 | 42 | 588948 | 0.092 | 517 | 1 | 48 | 0 | 0 | 0 | 0 | concluiu | 19·19 | RA |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 17 | 17 | 229142 | 0.037 | 127 | 1 | 47 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | sim | 2/2 | 0 | 41 | 44 | 802269 | 0.115 | 212 | 1 | 65 | 0 | 0 | 0 | 0 | concluiu | 41 | A |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 50 | 50 | 1288314 | 0.179 | 606 | 1 | 61 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 4/5 | 1 | 64 | 67 | 660747 | 0.085 | 255 | 1 | 55 | 0.021 | 0 | 1 | 0 | concluiu | 41·23 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | sim | 5/5 | 0 | 27 | 30 | 263304 | 0.037 | 217 | 1 | 48 | 0.015 | 0 | 0 | 0 | concluiu | 27 | A |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 0/5 | 5 | 35 | 38 | 499589 | 0.067 | 163 | 1 | 77 | 0.047 | 0 | 0 | 0 | concluiu | 35 | A |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 108 | 118 | 1364165 | 0.212 | 1233 | 1 | 22 | 0.012 | 0 | 0 | 0 | concluiu | 20·4·13·11·7·9·17·27 | RRRRRRRA |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 28 | 28 | 452395 | 0.057 | 119 | 1 | 30 | 0.031 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | não | 5/11 | 44 | 120 | 121 | 2889956 | 0.351 | 559 | 2 | 538 | -0.125 | 2.951 | 0 | 0 | budget: max_turns | 41·41·38 | — |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 10 | 117 | 117 | 8077370 | 1.113 | 1328 | 1 | 38 | -0.008 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | não | 5/11 | 6 | 20 | 23 | 214569 | 0.032 | 92 | 1 | 20 | 0.025 | 0 | 0 | 0 | concluiu | 20 | A |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 45 | 45 | 821788 | 0.096 | 161 | 1 | 34 | 0.011 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 33 | 37 | 231237 | 0.031 | 133 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 23·10 | RA |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 30 | 33 | 310857 | 0.04 | 121 | 1 | 10 | 0.073 | 0 | 0 | 0 | concluiu | 30 | A |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 30 | 33 | 228518 | 0.029 | 80 | 1 | 5 | 0 | 0 | 0 | 0 | concluiu | 30 | A |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | não | 0/1 | 1 | 120 | 124 | 1062830 | 0.139 | 305 | 2 | 25 | 0.051 | -0.759 | 0 | 0 | budget: max_turns | 41·41·38 | RRR |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 0/1 | 1 | 120 | 124 | 1331498 | 0.163 | 324 | 2 | 26 | 0 | 0 | 0 | 0 | budget: max_turns | 41·41·38 | RRR |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | não | 0/1 | 1 | 120 | 123 | 1185112 | 0.149 | 223 | 1 | 12 | 0 | 0 | 0 | 0 | budget: max_turns | 41·41·38 | RR |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


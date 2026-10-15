# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-r2-analise`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.587 | 4 | 22 | 4/9 | 0 | 3265263 | 0.35 | 120 | 295 | 124 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 4/9 | 0.603 | 5 | 9 | 4/9 | 0 | 1261619 | 0.148 | 121 | 383 | 76 | 0.079 | -0.588 | 1 | 0 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 6/12 | 0.889 | 6 | 1 | 9/12 | 0 | 494172 | 0.065 | 40 | 286 | 44 | 0.02 | -0.155 | 0 | 0 |
| pequena | single-agent | 18 | 9/18 | 0.598 | 9 | 4 | 14/18 | 1 | 507754 | 0.064 | 38 | 170 | 36 | 0 | 0 | 1 | 8 |
| pequena | orchestration | 18 | 13/18 | 0.806 | 5 | 2 | 15/18 | 0 | 432352 | 0.059 | 40 | 210 | 27 | 0.004 | 0 | 2 | 0 |
| todas | single-agent | 39 | 23/39 | 0.715 | 15 | 6 | 29/39 | 1 | 979282 | 0.117 | 50 | 243 | 40 | 0.014 | 0 | 5 | 8 |
| todas | orchestration | 39 | 23/39 | 0.784 | 16 | 2 | 28/39 | 0 | 463756 | 0.068 | 47 | 280 | 34 | 0.01 | 0 | 3 | 0 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 0 | 0 | 3 | — |
| media | 4 | 0 | 3 | 1 | 0.25 |
| pequena | 6 | 2 | 1 | 3 | 1 |
| todas | 13 | 2 | 4 | 7 | 0.6875 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 8 | 0.375 |
| fração de ocultos passados | ambos_resolvem_mediana | 5 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 9 | 0 | 3 | 1 |
| tokens | todas | 13 | -110164 | 18 | 0.0574 |
| tokens | ambos_resolvem_mediana | 5 | -28178 | 5 | 0.625 |
| tokens | ambos_resolvem_ao_menos_uma | 9 | -71234 | 14 | 0.3594 |
| US$ | todas | 13 | -0.005 | 30 | 0.3054 |
| US$ | ambos_resolvem_mediana | 5 | 0.001 | 4 | 0.4375 |
| US$ | ambos_resolvem_ao_menos_uma | 9 | -0.001 | 20 | 0.8203 |
| chamadas | todas | 13 | 4 | 31 | 0.3389 |
| chamadas | ambos_resolvem_mediana | 5 | 4 | 5.5 | 0.6875 |
| chamadas | ambos_resolvem_ao_menos_uma | 9 | 4 | 13.5 | 0.3125 |
| parede (s) | todas | 13 | 51.892 | 26 | 0.1909 |
| parede (s) | ambos_resolvem_mediana | 5 | 113.067 | 1 | 0.125 |
| parede (s) | ambos_resolvem_ao_menos_uma | 9 | 51.892 | 13 | 0.3008 |
| turnos | todas | 13 | 0 | 20.5 | 0.8438 |
| turnos | ambos_resolvem_mediana | 5 | 0 | 5 | 1 |
| turnos | ambos_resolvem_ao_menos_uma | 9 | 0 | 12 | 0.8125 |
| linhas do patch | todas | 13 | -7 | 11.5 | 0.0283 |
| linhas do patch | ambos_resolvem_mediana | 5 | -2 | 2 | 0.375 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 9 | -7 | 2.5 | 0.0312 |
| ΔCC | todas | 13 | 0 | 15 | 0.7422 |
| ΔCC | ambos_resolvem_mediana | 5 | 0 | 0 | 1 |
| ΔCC | ambos_resolvem_ao_menos_uma | 9 | 0 | 3 | 0.625 |
| regressões | todas | 13 | 0 | 10 | 0.3047 |
| regressões | ambos_resolvem_mediana | 5 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 9 | 0 | 0 | 0.125 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 14, 2: 11, 3: 12, 4: 2}; runs com 2+ ciclos (memória de trabalho usada): 25/39.
- Revisões semânticas (suíte verde): 59; aprovadas 22, reprovadas 37.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 11 — [('peewee-0003', 1, 2), ('peewee-0003', 2, 1), ('sqlite-utils-0001', 2, 1), ('sqlite-utils-0003', 1, 2), ('tomlkit-0001', 1, 2), ('tomlkit-0001', 2, 2), ('tomlkit-0001', 3, 1), ('tomlkit-0002', 1, 2), ('tomlkit-0003', 2, 2), ('tomlkit-0005', 1, 1), ('tomlkit-0005', 3, 1)].
- Runs resolvidos com todas as revisões aprovadas: 12; runs não resolvidos com ao menos uma reprovação: 9.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | sim | 1/1 | 0 | 80 | 84 | 978161 | 0.12 | 199 | 3 | 48 | 0.079 | -0.333 | 0 | 0 | concluiu | 41·33·6 | RR |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | não | 0/1 | 1 | 120 | 124 | 1372896 | 0.241 | 2211 | 2 | 76 | 0.082 | -0.588 | 0 | 0 | budget: max_turns | 41·41·38 | RRR |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | não | 0/1 | 25 | 120 | 121 | 1261619 | 0.148 | 234 | 1 | 187 | -0.137 | -16.959 | 0 | 0 | budget: max_turns | 41·41·38 | — |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 17 | 20 | 256670 | 0.063 | 359 | 2 | 4 | 0 | 0 | 0 | 0 | concluiu | 17 | A |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 52 | 56 | 500309 | 0.065 | 394 | 1 | 2 | 0 | 0 | 1 | 0 | concluiu | 18·34 | RR |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 16 | 19 | 144650 | 0.021 | 67 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 16 | A |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 120 | 120 | 121 | 1795032 | 0.218 | 383 | 2 | 196 | 0.427 | -4.402 | 0 | 0 | budget: max_turns | 41·41·38 | — |
| tomlkit-0004 | grande | 1 | single-agent | não | 3/7 | 60 | 120 | 120 | 4007174 | 0.453 | 348 | 2 | 176 | 0.814 | -3.691 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 5/7 | 2 | 120 | 122 | 2300846 | 0.329 | 1067 | 2 | 113 | 0.423 | -2.633 | 0 | 0 | budget: max_turns | 41·41·38 | R |
| tomlkit-0004 | grande | 2 | single-agent | não | 3/7 | 7 | 120 | 120 | 4864896 | 0.522 | 555 | 2 | 40 | 0.288 | -0.238 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 5/7 | 9 | 120 | 122 | 2386401 | 0.299 | 681 | 1 | 224 | 0.582 | -5.339 | 0 | 0 | budget: max_turns | 41·41·38 | R |
| tomlkit-0004 | grande | 3 | single-agent | não | 3/7 | 4 | 120 | 120 | 4921834 | 0.53 | 367 | 1 | 216 | 1.24 | -5.642 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 27 | 30 | 180327 | 0.03 | 280 | 2 | 18 | 0.162 | -0.396 | 0 | 0 | concluiu | 27 | A |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | sim | 3/3 | 0 | 15 | 18 | 115281 | 0.019 | 80 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | concluiu | 15 | A |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | não | 2/3 | 1 | 24 | 28 | 137070 | 0.026 | 123 | 2 | 14 | 0.078 | -0.155 | 0 | 0 | concluiu | 16·8 | RR |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 22 | 25 | 208819 | 0.036 | 292 | 1 | 51 | 0.002 | 0 | 0 | 0 | concluiu | 22 | A |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 22 | 25 | 219388 | 0.031 | 196 | 2 | 57 | 0.012 | -0.319 | 0 | 0 | concluiu | 22 | A |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 28 | 31 | 263525 | 0.036 | 245 | 1 | 36 | 0.002 | 0 | 0 | 0 | concluiu | 28 | A |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 5/6 | 1 | 101 | 106 | 951694 | 0.146 | 921 | 3 | 51 | 0.002 | -0.041 | 0 | 0 | concluiu | 41·41·19 | RRA |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 4/6 | 26 | 120 | 123 | 1277112 | 0.152 | 363 | 3 | 17 | 0.001 | -0.012 | 0 | 0 | budget: max_turns | 41·41·38 | RR |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 4/6 | 27 | 120 | 123 | 1697776 | 0.209 | 503 | 1 | 28 | 0.007 | 0 | 0 | 0 | budget: max_turns | 41·41·38 | RR |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | sim | 12/12 | 0 | 44 | 48 | 724819 | 0.094 | 270 | 3 | 71 | 0.028 | -0.449 | 0 | 0 | concluiu | 34·10 | RR |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | não | 11/12 | 1 | 120 | 122 | 2245107 | 0.406 | 2170 | 2 | 125 | 0.102 | -0.845 | 0 | 0 | budget: max_turns | 41·41·38 | A |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | não | 11/12 | 1 | 109 | 112 | 2301883 | 0.311 | 922 | 2 | 200 | 0.093 | -1.532 | 0 | 0 | concluiu | 41·41·27 | A |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 16 | 20 | 73415 | 0.017 | 322 | 1 | 2 | 0.154 | -0.988 | 0 | 0 | concluiu | 9·7 | RR |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 23 | 27 | 139886 | 0.028 | 455 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 13·10 | RA |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 12 | 15 | 72633 | 0.013 | 157 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 12 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | não | 0/2 | 2 | 120 | 124 | 2499790 | 0.359 | 1138 | 1 | 46 | 0 | 0 | 0 | 0 | budget: max_turns | 41·41·38 | RRR |
| pygments-0001 | pequena | 1 | single-agent | não | 0/2 | 2 | 120 | 120 | 7109886 | 0.819 | 859 | 1 | 53 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 2 | orchestration | sim | 2/2 | 0 | 23 | 26 | 433163 | 0.068 | 223 | 1 | 56 | 0 | 0 | 0 | 0 | concluiu | 23 | A |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 17 | 17 | 229142 | 0.037 | 127 | 1 | 47 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | não | 1/2 | 1 | 41 | 44 | 964087 | 0.137 | 241 | 1 | 37 | 0 | 0 | 0 | 0 | concluiu | 41 | A |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 50 | 50 | 1288314 | 0.179 | 606 | 1 | 61 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 0/5 | 5 | 25 | 28 | 227507 | 0.031 | 117 | 1 | 47 | 0.028 | 0 | 0 | 0 | concluiu | 25 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | sim | 5/5 | 0 | 38 | 42 | 436475 | 0.057 | 182 | 1 | 32 | 0.058 | 0 | 0 | 0 | concluiu | 27·11 | RA |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 5/5 | 5 | 120 | 121 | 2345352 | 0.298 | 620 | 2 | 421 | 0.01 | -1.206 | 1 | 0 | budget: max_turns | 41·28·41·10 | — |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 15 | 18 | 142479 | 0.023 | 154 | 1 | 25 | 0.031 | 0 | 0 | 0 | concluiu | 15 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 28 | 28 | 452395 | 0.057 | 119 | 1 | 30 | 0.031 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | sim | 11/11 | 0 | 25 | 28 | 291012 | 0.039 | 127 | 1 | 29 | -0.002 | 0 | 0 | 0 | concluiu | 25 | A |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 10 | 117 | 117 | 8077370 | 1.113 | 1328 | 1 | 38 | -0.008 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | sim | 11/11 | 0 | 29 | 32 | 463756 | 0.06 | 136 | 1 | 34 | 0.037 | 0 | 0 | 0 | concluiu | 29 | A |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 45 | 45 | 821788 | 0.096 | 161 | 1 | 34 | 0.011 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 43 | 47 | 356189 | 0.045 | 124 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 27·16 | RR |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 33 | 37 | 431541 | 0.085 | 1418 | 1 | 3 | 0 | 0 | 0 | 0 | concluiu | 17·16 | RR |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 57 | 61 | 364982 | 0.048 | 136 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 16·41 | RA |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | sim | 1/1 | 0 | 75 | 79 | 698482 | 0.088 | 197 | 1 | 3 | 0.004 | 0 | 0 | 0 | concluiu | 41·34 | RA |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 0/1 | 1 | 120 | 125 | 1267656 | 0.172 | 317 | 2 | 45 | -0.006 | 0 | 1 | 0 | budget: max_turns | 38·41·41·0 | RRRR |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | sim | 1/1 | 0 | 74 | 78 | 921262 | 0.15 | 683 | 1 | 3 | 0.004 | 0 | 0 | 0 | concluiu | 41·33 | RA |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


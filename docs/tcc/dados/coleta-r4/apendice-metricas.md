# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-r4-analise`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.587 | 4 | 22 | 4/9 | 0 | 3265263 | 0.35 | 120 | 295 | 124 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 5/9 | 0.556 | 3 | 122 | 3/9 | 0 | 1257119 | 0.201 | 110 | 284 | 47 | 0.015 | 0 | 0 | 0 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 7/12 | 0.722 | 4 | 4 | 8/12 | 0 | 1146942 | 0.151 | 78 | 439 | 32 | 0.005 | 0 | 1 | 0 |
| pequena | single-agent | 18 | 9/18 | 0.598 | 9 | 4 | 14/18 | 1 | 507754 | 0.064 | 38 | 170 | 36 | 0 | 0 | 1 | 8 |
| pequena | orchestration | 18 | 12/18 | 0.692 | 6 | 3 | 12/18 | 0 | 752681 | 0.111 | 63 | 250 | 26 | 0.015 | 0 | 9 | 3 |
| todas | single-agent | 39 | 23/39 | 0.715 | 15 | 6 | 29/39 | 1 | 979282 | 0.117 | 50 | 243 | 40 | 0.014 | 0 | 5 | 8 |
| todas | orchestration | 39 | 24/39 | 0.67 | 13 | 5 | 23/39 | 0 | 883706 | 0.133 | 78 | 290 | 28 | 0.013 | 0 | 10 | 3 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 1 | 0 | 2 | 1 |
| media | 4 | 0 | 2 | 2 | 0.5 |
| pequena | 6 | 2 | 0 | 4 | 0.5 |
| todas | 13 | 3 | 2 | 8 | 1 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 7 | 1 |
| fração de ocultos passados | ambos_resolvem_mediana | 7 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 9 | 0 | 1 | 1 |
| tokens | todas | 13 | 43031 | 44 | 0.946 |
| tokens | ambos_resolvem_mediana | 7 | 100944 | 7 | 0.2969 |
| tokens | ambos_resolvem_ao_menos_uma | 9 | 100944 | 17 | 0.5703 |
| US$ | todas | 13 | 0.017 | 38 | 0.6355 |
| US$ | ambos_resolvem_mediana | 7 | 0.025 | 4 | 0.1094 |
| US$ | ambos_resolvem_ao_menos_uma | 9 | 0.025 | 14 | 0.3594 |
| chamadas | todas | 13 | 18 | 9 | 0.0078 |
| chamadas | ambos_resolvem_mediana | 7 | 20 | 0 | 0.0156 |
| chamadas | ambos_resolvem_ao_menos_uma | 9 | 20 | 6 | 0.0547 |
| parede (s) | todas | 13 | 170.743 | 20 | 0.0803 |
| parede (s) | ambos_resolvem_mediana | 7 | 170.743 | 8 | 0.375 |
| parede (s) | ambos_resolvem_ao_menos_uma | 9 | 100.064 | 14 | 0.3594 |
| turnos | todas | 13 | 9 | 10 | 0.0195 |
| turnos | ambos_resolvem_mediana | 7 | 13 | 0 | 0.0156 |
| turnos | ambos_resolvem_ao_menos_uma | 9 | 13 | 7 | 0.0742 |
| linhas do patch | todas | 13 | -8 | 12 | 0.0635 |
| linhas do patch | ambos_resolvem_mediana | 7 | -8 | 1 | 0.125 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 9 | -8 | 1 | 0.0312 |
| ΔCC | todas | 13 | 0 | 13 | 0.9375 |
| ΔCC | ambos_resolvem_mediana | 7 | 0 | 0 | 0.5 |
| ΔCC | ambos_resolvem_ao_menos_uma | 9 | 0 | 2 | 0.75 |
| regressões | todas | 13 | 0 | 3 | 0.625 |
| regressões | ambos_resolvem_mediana | 7 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 9 | 0 | 0 | 1 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 7, 2: 12, 3: 9, 4: 6, 5: 1, 6: 3, 7: 1}; runs com 2+ ciclos (memória de trabalho usada): 32/39.
- Revisões semânticas (suíte verde): 171; aprovadas 37, reprovadas 134.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 18 — [('attrs-0001', 1, 3), ('attrs-0001', 2, 1), ('peewee-0001', 1, 1), ('peewee-0001', 2, 1), ('peewee-0001', 3, 1), ('pygments-0001', 1, 6), ('pygments-0001', 2, 2), ('pygments-0001', 3, 2), ('sqlite-utils-0002', 2, 1), ('sqlite-utils-0003', 2, 9), ('sqlite-utils-0003', 3, 2), ('tomlkit-0001', 1, 13), ('tomlkit-0001', 3, 10), ('tomlkit-0002', 2, 1), ('tomlkit-0002', 3, 1), ('tomlkit-0003', 1, 8), ('tomlkit-0003', 2, 8), ('tomlkit-0003', 3, 5)].
- Runs resolvidos com todas as revisões aprovadas: 6; runs não resolvidos com ao menos uma reprovação: 14.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | não | 0/1 | 57 | 120 | 124 | 1806028 | 0.319 | 2753 | 4 | 236 | 0.015 | -5.975 | 0 | 0 | budget: max_turns | 33·41·33 | ARR |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | sim | 1/1 | 0 | 74 | 78 | 752819 | 0.097 | 133 | 1 | 12 | 0.131 | -1.836 | 0 | 0 | concluiu | 41·23 | RA |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | sim | 1/1 | 0 | 50 | 55 | 414394 | 0.056 | 85 | 2 | 12 | 0.043 | -0.498 | 0 | 0 | concluiu | 13·24 | RAA |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 81 | 90 | 723160 | 0.201 | 3729 | 2 | 4 | 0 | 0 | 0 | 0 | budget: max_wall_seconds | 21·11·17·19 | RRRRRRRR |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 120 | 129 | 1257119 | 0.162 | 258 | 2 | 4 | 0 | 0 | 0 | 0 | budget: max_turns | 21·41·41·4 | RRRRRRRR |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 102 | 110 | 1197082 | 0.159 | 284 | 2 | 47 | 0.078 | 0.038 | 0 | 0 | concluiu | 9·18·41·24 | RRRRRA |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 0 | 81 | 84 | 1437367 | 0.403 | 4069 | 1 | 1001 | 0.01 | 12.92 | 0 | 0 | budget: max_wall_seconds | 41·27 | RR |
| tomlkit-0004 | grande | 1 | single-agent | não | 3/7 | 60 | 120 | 120 | 4007174 | 0.453 | 348 | 2 | 176 | 0.814 | -3.691 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 0/7 | 123 | 120 | 124 | 2571678 | 0.315 | 231 | 1 | 1323 | 0.282 | 8.758 | 0 | 0 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0004 | grande | 2 | single-agent | não | 3/7 | 7 | 120 | 120 | 4864896 | 0.522 | 555 | 2 | 40 | 0.288 | -0.238 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 0/7 | 122 | 120 | 124 | 2348749 | 0.29 | 290 | 2 | 1124 | -1.766 | 14.298 | 0 | 0 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0004 | grande | 3 | single-agent | não | 3/7 | 4 | 120 | 120 | 4921834 | 0.53 | 367 | 1 | 216 | 1.24 | -5.642 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 39 | 46 | 214263 | 0.04 | 213 | 2 | 13 | 0.078 | -0.281 | 0 | 0 | concluiu | 11·7·11 | RRRAA |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | sim | 3/3 | 0 | 34 | 39 | 206518 | 0.04 | 912 | 2 | 12 | 0.078 | -0.204 | 0 | 0 | concluiu | 10·11 | RAA |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | não | 0/3 | 0 | 120 | 124 | 1905965 | 0.244 | 468 | 2 | 3400 | -1.305 | 35.846 | 0 | 0 | budget: max_turns | 41·41·25 | RRR |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 38 | 43 | 266119 | 0.043 | 271 | 1 | 28 | 0.001 | 0 | 0 | 0 | concluiu | 7·18 | RAA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 35 | 40 | 265226 | 0.045 | 224 | 1 | 36 | 0.001 | 0 | 0 | 0 | concluiu | 6·16 | RAA |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 36 | 41 | 249746 | 0.039 | 272 | 1 | 45 | 0.001 | 0 | 0 | 0 | concluiu | 7·16 | RAA |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 1/6 | 5 | 120 | 129 | 1497208 | 0.205 | 1849 | 1 | 15 | 0.003 | 0 | 0 | 0 | budget: max_turns | 41·41·17·8 | RRRRRARR |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 0/6 | 602 | 120 | 128 | 1284448 | 0.169 | 413 | 1 | 13 | 0.003 | 0 | 1 | 0 | budget: max_turns | 14·41·41·11 | RRRRRRR |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 3/6 | 3 | 120 | 131 | 1022496 | 0.133 | 559 | 1 | 28 | 0.006 | 0 | 0 | 0 | budget: max_turns | 21·41·22·13·10 | RARRRARARR |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | não | 12/12 | 1 | 73 | 80 | 1271388 | 0.184 | 409 | 3 | 68 | 0.02 | -0.355 | 0 | 0 | concluiu | 6·40·14 | RRRRA |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | sim | 12/12 | 0 | 114 | 127 | 1648938 | 0.219 | 465 | 3 | 63 | 0.02 | -0.411 | 0 | 0 | concluiu | 6·19·31·28·10·7 | RARRRRRRRRA |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | sim | 12/12 | 0 | 70 | 75 | 1327799 | 0.183 | 487 | 3 | 71 | 0.036 | -0.548 | 0 | 0 | concluiu | 16·41 | RRA |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 20 | 23 | 103574 | 0.02 | 88 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | concluiu | 7 | A |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 25 | 28 | 198330 | 0.038 | 175 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 12 | A |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 20 | 23 | 118844 | 0.02 | 109 | 1 | 2 | 0.154 | -0.988 | 0 | 0 | concluiu | 7 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | sim | 2/2 | 0 | 62 | 71 | 699240 | 0.108 | 365 | 1 | 39 | 0 | 0 | 0 | 0 | concluiu | 11·15·8·15 | RRRRRRA |
| pygments-0001 | pequena | 1 | single-agent | não | 0/2 | 2 | 120 | 120 | 7109886 | 0.819 | 859 | 1 | 53 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 2 | orchestration | sim | 2/2 | 0 | 56 | 61 | 1075889 | 0.149 | 682 | 1 | 41 | 0 | 0 | 0 | 0 | concluiu | 34·19 | RRA |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 17 | 17 | 229142 | 0.037 | 127 | 1 | 47 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | sim | 2/2 | 0 | 51 | 56 | 883706 | 0.123 | 261 | 1 | 28 | 0 | 0 | 0 | 0 | concluiu | 9·29 | RRA |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 50 | 50 | 1288314 | 0.179 | 606 | 1 | 61 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 0/5 | 882 | 120 | 124 | 1756764 | 0.245 | 1118 | 2 | 1660 | 0.175 | 0.204 | 0 | 3 | budget: max_turns | 41·41·25 | RRR |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | sim | 5/5 | 0 | 50 | 53 | 632408 | 0.085 | 230 | 1 | 42 | 0.015 | 0 | 0 | 0 | concluiu | 37 | A |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 0/5 | 5 | 80 | 85 | 709873 | 0.099 | 225 | 1 | 27 | 0.065 | 0 | 1 | 0 | concluiu | 22·22·23 | RRA |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 44 | 47 | 587183 | 0.078 | 188 | 1 | 29 | 0.025 | 0 | 2 | 0 | concluiu | 31 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 28 | 28 | 452395 | 0.057 | 119 | 1 | 30 | 0.031 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | sim | 11/11 | 0 | 61 | 65 | 892019 | 0.114 | 368 | 1 | 29 | 0.025 | 0 | 0 | 0 | concluiu | 12·36 | RA |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 10 | 117 | 117 | 8077370 | 1.113 | 1328 | 1 | 38 | -0.008 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | não | 5/11 | 6 | 54 | 57 | 864819 | 0.15 | 530 | 1 | 24 | -0.008 | 0 | 2 | 0 | concluiu | 41 | A |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 45 | 45 | 821788 | 0.096 | 161 | 1 | 34 | 0.011 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 120 | 135 | 935129 | 0.132 | 355 | 1 | 7 | 0.024 | 0 | 0 | 0 | budget: max_turns | 26·18·4·16·16·10·4 | RRRRRARRRRRRRR |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 32 | 35 | 254059 | 0.037 | 51 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 19 | A |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 120 | 132 | 769526 | 0.104 | 233 | 1 | 4 | 0 | 0 | 0 | 0 | budget: max_turns | 28·14·13·14·14·11 | RRRRRRRRRRA |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | não | 0/1 | 1 | 65 | 70 | 735836 | 0.226 | 3852 | 1 | 69 | -0.051 | -16.665 | 0 | 0 | budget: max_wall_seconds | 41·15 | RRRR |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 0/1 | 1 | 120 | 130 | 1805068 | 0.241 | 691 | 1 | 8 | 0 | 0 | 3 | 0 | budget: max_turns | 16·37·5·2·41·7 | RRRRRRRRR |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | não | 0/1 | 1 | 120 | 124 | 1190387 | 0.157 | 239 | 0 | 0 | — | — | 1 | 0 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


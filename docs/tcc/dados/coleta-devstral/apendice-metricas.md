# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-devstral`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.746 | 5 | 18 | 2/9 | 0 | 3940573 | 0.342 | 120 | 365 | 34 | 0.016 | -0.362 | 0 | 0 |
| grande | orchestration | 9 | 5/9 | 0.714 | 4 | 10 | 4/9 | 0 | 1883175 | 0.198 | 124 | 310 | 67 | 0.069 | -0.409 | 0 | 0 |
| media | single-agent | 12 | 11/12 | 0.972 | 1 | 2 | 10/12 | 0 | 1176403 | 0.081 | 60 | 181 | 56 | 0.033 | -0.33 | 0 | 0 |
| media | orchestration | 12 | 9/12 | 0.861 | 3 | 4 | 11/12 | 0 | 612022 | 0.086 | 57 | 247 | 30 | 0.012 | -0.131 | 0 | 0 |
| pequena | single-agent | 18 | 13/18 | 0.756 | 4 | 4 | 15/18 | 0 | 977953 | 0.075 | 54 | 158 | 15 | 0.029 | 0 | 0 | 0 |
| pequena | orchestration | 18 | 16/18 | 0.889 | 2 | 1 | 17/18 | 0 | 510420 | 0.079 | 48 | 175 | 21 | 0.007 | 0 | 0 | 0 |
| todas | single-agent | 39 | 28/39 | 0.82 | 10 | 6 | 27/39 | 0 | 1252515 | 0.087 | 64 | 219 | 31 | 0.028 | 0 | 0 | 0 |
| todas | orchestration | 39 | 30/39 | 0.84 | 9 | 5 | 32/39 | 0 | 699039 | 0.089 | 56 | 271 | 28 | 0.015 | 0 | 0 | 0 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 1 | 0 | 2 | 1 |
| media | 4 | 0 | 1 | 3 | 1 |
| pequena | 6 | 2 | 1 | 3 | 1 |
| todas | 13 | 3 | 2 | 8 | 1 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 4.5 | 1 |
| fração de ocultos passados | ambos_resolvem_mediana | 7 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 10 | 0 | 1.5 | 1 |
| tokens | todas | 13 | -576217 | 7 | 0.0046 |
| tokens | ambos_resolvem_mediana | 7 | -136590 | 1 | 0.0312 |
| tokens | ambos_resolvem_ao_menos_uma | 10 | -302445.5 | 7 | 0.0371 |
| US$ | todas | 13 | -0.016 | 27 | 0.2163 |
| US$ | ambos_resolvem_mediana | 7 | 0.008 | 13 | 0.9375 |
| US$ | ambos_resolvem_ao_menos_uma | 10 | -0.004 | 22 | 0.625 |
| chamadas | todas | 13 | -7 | 31 | 0.3311 |
| chamadas | ambos_resolvem_mediana | 7 | -7 | 10 | 0.5781 |
| chamadas | ambos_resolvem_ao_menos_uma | 10 | -1.5 | 22 | 0.625 |
| parede (s) | todas | 13 | 3.884 | 32 | 0.3757 |
| parede (s) | ambos_resolvem_mediana | 7 | 3.405 | 11 | 0.6875 |
| parede (s) | ambos_resolvem_ao_menos_uma | 10 | 14.711 | 15 | 0.2324 |
| turnos | todas | 13 | -10 | 15.5 | 0.127 |
| turnos | ambos_resolvem_mediana | 7 | -10 | 7.5 | 0.3281 |
| turnos | ambos_resolvem_ao_menos_uma | 10 | -5 | 14.5 | 0.375 |
| linhas do patch | todas | 13 | 0 | 29 | 0.7441 |
| linhas do patch | ambos_resolvem_mediana | 7 | -4 | 4 | 0.5 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 10 | -2 | 15 | 0.7266 |
| ΔCC | todas | 13 | -0.006 | 27 | 1 |
| ΔCC | ambos_resolvem_mediana | 7 | 0 | 6 | 0.8125 |
| ΔCC | ambos_resolvem_ao_menos_uma | 10 | -0.003 | 13 | 0.9375 |
| regressões | todas | 13 | 0 | 6.5 | 0.875 |
| regressões | ambos_resolvem_mediana | 7 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 10 | 0 | 1 | 1 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 21, 2: 9, 3: 6, 5: 2, 9: 1}; runs com 2+ ciclos (memória de trabalho usada): 18/39.
- Revisões semânticas (suíte verde): 103; aprovadas 36, reprovadas 67.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 10 — [('attrs-0001', 1, 1), ('pygments-0001', 2, 2), ('pygments-0001', 3, 2), ('sqlite-utils-0003', 1, 2), ('sqlite-utils-0003', 2, 2), ('sqlite-utils-0003', 3, 4), ('tomlkit-0001', 1, 17), ('tomlkit-0002', 3, 10), ('tomlkit-0003', 2, 1), ('tomlkit-0005', 3, 1)].
- Runs resolvidos com todas as revisões aprovadas: 20; runs não resolvidos com ao menos uma reprovação: 8.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | sim | 1/1 | 0 | 54 | 56 | 925276 | 0.094 | 271 | 3 | 88 | 0.069 | -0.451 | 0 | 0 | concluiu | 41 | A |
| tomlkit-0002 | grande | 1 | single-agent | não | 1/1 | 31 | 120 | 120 | 3332904 | 0.342 | 365 | 3 | 116 | 0.11 | -0.451 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | não | 1/1 | 21 | 120 | 125 | 1992250 | 0.199 | 303 | 2 | 143 | 0.499 | -0.409 | 0 | 0 | budget: max_turns | 41·41·25 | RRAR |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 106 | 106 | 2785556 | 0.166 | 236 | 2 | 95 | 0.145 | -0.498 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | sim | 1/1 | 0 | 120 | 131 | 1883175 | 0.198 | 310 | 3 | 93 | 0.1 | -0.392 | 0 | 0 | budget: max_turns | 41·41·12·3·10 | RRRRRRRRRR |
| tomlkit-0002 | grande | 3 | single-agent | não | 1/1 | 91 | 120 | 120 | 3940573 | 0.238 | 299 | 4 | 138 | 0.108 | -0.362 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 54 | 56 | 554880 | 0.062 | 255 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 41 | A |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 120 | 120 | 4720079 | 0.379 | 450 | 1 | 10 | 0.016 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 95 | 98 | 1264196 | 0.14 | 384 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 41·41 | RA |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 72 | 72 | 1879725 | 0.148 | 236 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 44 | 47 | 465548 | 0.057 | 94 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 31 | A |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 120 | 120 | 3068812 | 0.201 | 271 | 2 | 6 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 7 | 120 | 126 | 1978311 | 0.217 | 358 | 2 | 37 | -0.058 | -0.416 | 0 | 0 | budget: max_turns | 41·41·25 | RRRRR |
| tomlkit-0004 | grande | 1 | single-agent | não | 0/7 | 7 | 120 | 120 | 5957698 | 0.366 | 422 | 1 | 11 | 0 | 0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 3/7 | 10 | 120 | 124 | 2931019 | 0.284 | 439 | 1 | 134 | 0.612 | -5.642 | 0 | 0 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0004 | grande | 2 | single-agent | não | 0/7 | 7 | 120 | 120 | 6819305 | 0.392 | 597 | 1 | 34 | -0.028 | -1.443 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 0/7 | 11 | 120 | 124 | 2193223 | 0.198 | 314 | 1 | 67 | 0.097 | -1.678 | 0 | 0 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0004 | grande | 3 | single-agent | não | 5/7 | 18 | 120 | 120 | 7095453 | 0.49 | 457 | 2 | 181 | 0.473 | -2.945 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 55 | 60 | 525005 | 0.106 | 223 | 2 | 42 | 0.167 | -0.447 | 0 | 0 | concluiu | 17·25 | RAA |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 23 | 23 | 151944 | 0.02 | 62 | 2 | 16 | 0.084 | -0.34 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | sim | 3/3 | 0 | 34 | 37 | 304041 | 0.049 | 112 | 2 | 12 | 0.078 | -0.261 | 0 | 0 | concluiu | 21 | A |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 47 | 47 | 589472 | 0.048 | 143 | 2 | 27 | 0.156 | -0.435 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | sim | 3/3 | 0 | 54 | 56 | 859572 | 0.089 | 271 | 2 | 52 | 0.459 | -1.331 | 0 | 0 | concluiu | 41 | A |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 41 | 41 | 508196 | 0.046 | 127 | 2 | 50 | -0.309 | -0.349 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 33 | 36 | 282920 | 0.037 | 164 | 1 | 28 | 0.001 | 0 | 0 | 0 | concluiu | 20 | A |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 70 | 70 | 1333880 | 0.087 | 356 | 3 | 78 | 0.016 | -0.329 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 42 | 45 | 426493 | 0.048 | 166 | 1 | 28 | 0 | 0 | 0 | 0 | concluiu | 29 | A |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 74 | 74 | 1597041 | 0.103 | 357 | 3 | 78 | 0.016 | -0.349 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 39 | 42 | 401883 | 0.054 | 185 | 1 | 30 | 0.001 | 0 | 0 | 0 | concluiu | 26 | A |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 64 | 64 | 1041111 | 0.068 | 311 | 3 | 67 | 0.009 | -0.243 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 1/6 | 5 | 49 | 51 | 493520 | 0.06 | 363 | 1 | 8 | 0.003 | 0 | 0 | 0 | concluiu | 36 | — |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 120 | 120 | 2994080 | 0.157 | 219 | 5 | 40 | 0.038 | -0.307 | 0 | 0 | budget: max_turns | — | — |
| peewee-0002 | media | 2 | orchestration | não | 5/6 | 1 | 120 | 126 | 1735109 | 0.174 | 482 | 2 | 29 | 0.004 | 0 | 0 | 0 | budget: max_turns | 41·41·25 | RAARA |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 95 | 95 | 1764241 | 0.101 | 239 | 5 | 31 | 0.039 | -0.307 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 2/6 | 4 | 69 | 73 | 699039 | 0.082 | 420 | 1 | 14 | 0.003 | 0 | 0 | 0 | concluiu | 41·15 | RA |
| peewee-0002 | media | 3 | single-agent | não | 4/6 | 2 | 120 | 120 | 3043069 | 0.158 | 261 | 5 | 36 | 0.039 | -0.313 | 0 | 0 | budget: max_turns | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | sim | 12/12 | 0 | 54 | 58 | 945861 | 0.112 | 353 | 3 | 71 | 0.02 | -0.344 | 0 | 0 | concluiu | 9·32 | RRA |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 47 | 47 | 1002483 | 0.075 | 134 | 3 | 62 | 0.02 | -0.331 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | sim | 12/12 | 0 | 57 | 61 | 936631 | 0.105 | 339 | 3 | 68 | 0.02 | -0.318 | 0 | 0 | concluiu | 9·35 | RRA |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 39 | 39 | 790107 | 0.061 | 113 | 3 | 77 | 0.028 | -0.329 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | sim | 12/12 | 0 | 58 | 65 | 848610 | 0.116 | 205 | 3 | 61 | 0.02 | -0.397 | 0 | 0 | concluiu | 7·3·37 | RRRRA |
| sqlite-utils-0003 | media | 3 | single-agent | sim | 12/12 | 0 | 55 | 55 | 1311695 | 0.088 | 143 | 3 | 72 | 0.039 | -0.497 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 23 | 26 | 140639 | 0.03 | 180 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | concluiu | 12 | A |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 25 | 25 | 180564 | 0.02 | 155 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 35 | 38 | 301890 | 0.043 | 259 | 1 | 5 | 0.154 | 1.855 | 0 | 0 | concluiu | 24 | A |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 11 | 11 | 52296 | 0.009 | 138 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 22 | 25 | 126525 | 0.026 | 154 | 1 | 7 | 0.308 | 0.962 | 0 | 0 | concluiu | 13 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 22 | 22 | 161743 | 0.019 | 289 | 2 | 14 | 0.254 | 0.672 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | sim | 2/2 | 0 | 30 | 32 | 456004 | 0.089 | 450 | 1 | 35 | 0 | 0 | 0 | 0 | concluiu | 23 | A |
| pygments-0001 | pequena | 1 | single-agent | sim | 2/2 | 0 | 55 | 55 | 1776912 | 0.171 | 313 | 1 | 40 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 2 | orchestration | sim | 2/2 | 0 | 61 | 65 | 1154778 | 0.172 | 515 | 1 | 36 | 0 | 0 | 0 | 0 | concluiu | 41·10 | RRA |
| pygments-0001 | pequena | 2 | single-agent | não | 0/2 | 0 | 120 | 120 | 5161035 | 0.302 | 343 | 1 | 20 | — | — | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 3 | orchestration | sim | 2/2 | 0 | 72 | 77 | 1618553 | 0.216 | 466 | 1 | 41 | 0 | 0 | 0 | 0 | concluiu | 41·20 | RRA |
| pygments-0001 | pequena | 3 | single-agent | não | 0/2 | 2 | 120 | 120 | 5386330 | 0.308 | 362 | 0 | 0 | — | — | 0 | 0 | budget: max_turns | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | sim | 5/5 | 0 | 47 | 50 | 543043 | 0.071 | 140 | 1 | 37 | 0.021 | 0 | 0 | 0 | concluiu | 34 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 63 | 63 | 1119260 | 0.08 | 170 | 1 | 35 | 0.04 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | sim | 5/5 | 0 | 50 | 53 | 883471 | 0.092 | 154 | 1 | 38 | 0.015 | 0 | 0 | 0 | concluiu | 37 | A |
| sqlite-utils-0001 | pequena | 2 | single-agent | não | 1/5 | 4 | 71 | 71 | 1252515 | 0.088 | 199 | 1 | 49 | 0.021 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | sim | 5/5 | 0 | 40 | 43 | 429562 | 0.056 | 104 | 1 | 27 | 0.015 | 0 | 0 | 0 | concluiu | 27 | A |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 4 | 60 | 60 | 1054454 | 0.079 | 162 | 1 | 33 | 0.04 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 37 | 40 | 477796 | 0.064 | 170 | 1 | 20 | 0.018 | 0 | 0 | 0 | concluiu | 24 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | sim | 11/11 | 0 | 53 | 53 | 1019228 | 0.082 | 177 | 1 | 25 | 0.037 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | sim | 11/11 | 0 | 54 | 57 | 841954 | 0.087 | 154 | 1 | 22 | 0.031 | 0 | 0 | 0 | concluiu | 41 | A |
| sqlite-utils-0002 | pequena | 2 | single-agent | sim | 11/11 | 0 | 120 | 120 | 3696139 | 0.268 | 537 | 1 | 26 | 0.012 | 0 | 0 | 0 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | sim | 11/11 | 0 | 43 | 46 | 550927 | 0.065 | 123 | 1 | 27 | 0.056 | 0 | 0 | 0 | concluiu | 30 | A |
| sqlite-utils-0002 | pequena | 3 | single-agent | sim | 11/11 | 0 | 47 | 47 | 864526 | 0.064 | 146 | 1 | 32 | 0.05 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 57 | 76 | 454810 | 0.127 | 444 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 7·3·3·4·4·4·4·4·4 | RRRRRRRRRRRRRRRRR |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 12 | 12 | 56289 | 0.009 | 35 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 14 | 17 | 119959 | 0.031 | 59 | 1 | 15 | -0.025 | 0 | 0 | 0 | concluiu | 7 | A |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 30 | 30 | 265218 | 0.025 | 55 | 1 | 8 | 0.048 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 14 | 17 | 123460 | 0.033 | 55 | 1 | 15 | -0.025 | 0 | 0 | 0 | concluiu | 7 | A |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 30 | 30 | 260050 | 0.025 | 58 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | não | 0/1 | 1 | 120 | 129 | 1562077 | 0.258 | 384 | 1 | 63 | -0.069 | 0 | 0 | 0 | budget: max_turns | 41·37·5·5·19 | RRRRRRRA |
| tomlkit-0005 | pequena | 1 | single-agent | sim | 1/1 | 0 | 34 | 34 | 271756 | 0.023 | 57 | 1 | 3 | 0.004 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 0/1 | 1 | 95 | 99 | 1451827 | 0.164 | 349 | 1 | 18 | -0.022 | 0 | 0 | 0 | concluiu | 41·41 | RA |
| tomlkit-0005 | pequena | 2 | single-agent | sim | 1/1 | 0 | 58 | 58 | 936678 | 0.07 | 129 | 1 | 3 | 0.004 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | sim | 1/1 | 0 | 87 | 90 | 1277008 | 0.134 | 339 | 1 | 16 | 0 | 0 | 0 | 0 | concluiu | 41·33 | RA |
| tomlkit-0005 | pequena | 3 | single-agent | sim | 1/1 | 0 | 71 | 71 | 1190423 | 0.081 | 130 | 1 | 9 | 0.012 | 0 | 0 | 0 | tests_pass | — | — |


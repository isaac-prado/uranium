# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-r7-analise`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.587 | 4 | 22 | 4/9 | 0 | 3265263 | 0.35 | 120 | 295 | 124 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 4/9 | 0.444 | 5 | 7 | 6/9 | 0 | 1029701 | 0.134 | 109 | 154 | 7 | 0.021 | -0.247 | 5 | 0 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 6/12 | 0.715 | 5 | 4 | 8/12 | 0 | 717138 | 0.112 | 76 | 242 | 28 | 0.005 | -0.099 | 16 | 0 |
| pequena | single-agent | 18 | 9/18 | 0.598 | 9 | 4 | 14/18 | 1 | 507754 | 0.064 | 38 | 170 | 36 | 0 | 0 | 1 | 8 |
| pequena | orchestration | 18 | 13/18 | 0.803 | 5 | 46 | 15/18 | 0 | 595848 | 0.077 | 50 | 169 | 23 | 0 | 0 | 7 | 4 |
| todas | single-agent | 39 | 23/39 | 0.715 | 15 | 6 | 29/39 | 1 | 979282 | 0.117 | 50 | 243 | 40 | 0.014 | 0 | 5 | 8 |
| todas | orchestration | 39 | 23/39 | 0.693 | 15 | 6 | 29/39 | 0 | 693997 | 0.099 | 74 | 180 | 21 | 0.009 | 0 | 28 | 4 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 0 | 0 | 3 | — |
| media | 4 | 0 | 3 | 1 | 0.25 |
| pequena | 6 | 3 | 0 | 3 | 0.25 |
| todas | 13 | 3 | 3 | 7 | 1 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 4 | 0.875 |
| fração de ocultos passados | ambos_resolvem_mediana | 7 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 9 | 0 | 0 | 1 |
| tokens | todas | 13 | -50112 | 30 | 0.3054 |
| tokens | ambos_resolvem_mediana | 7 | -26308 | 12 | 0.8125 |
| tokens | ambos_resolvem_ao_menos_uma | 9 | -26308 | 20 | 0.8203 |
| US$ | todas | 13 | 0.005 | 42 | 0.8394 |
| US$ | ambos_resolvem_mediana | 7 | 0.006 | 6 | 0.2188 |
| US$ | ambos_resolvem_ao_menos_uma | 9 | 0.006 | 15 | 0.4258 |
| chamadas | todas | 13 | 16 | 5 | 0.0024 |
| chamadas | ambos_resolvem_mediana | 7 | 16 | 0 | 0.0156 |
| chamadas | ambos_resolvem_ao_menos_uma | 9 | 16 | 3 | 0.0195 |
| parede (s) | todas | 13 | -24.618 | 31 | 0.3396 |
| parede (s) | ambos_resolvem_mediana | 7 | -22.273 | 11 | 0.6875 |
| parede (s) | ambos_resolvem_ao_menos_uma | 9 | -22.273 | 17 | 0.5703 |
| turnos | todas | 13 | 9 | 9 | 0.0151 |
| turnos | ambos_resolvem_mediana | 7 | 13 | 0 | 0.0156 |
| turnos | ambos_resolvem_ao_menos_uma | 9 | 13 | 6 | 0.0508 |
| linhas do patch | todas | 13 | -12 | 12 | 0.0342 |
| linhas do patch | ambos_resolvem_mediana | 7 | -6 | 3 | 0.1562 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 9 | -6 | 3 | 0.0391 |
| ΔCC | todas | 13 | -0.002 | 26 | 0.5615 |
| ΔCC | ambos_resolvem_mediana | 7 | 0 | 7 | 1 |
| ΔCC | ambos_resolvem_ao_menos_uma | 9 | 0 | 13 | 0.9219 |
| regressões | todas | 13 | 0 | 6.5 | 0.875 |
| regressões | ambos_resolvem_mediana | 7 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 9 | 0 | 1 | 1 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 12, 2: 9, 3: 7, 4: 5, 5: 2, 6: 1, 7: 2, 9: 1}; runs com 2+ ciclos (memória de trabalho usada): 27/39.
- Revisões semânticas (suíte verde): 163; aprovadas 52, reprovadas 111.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 14 — [('attrs-0001', 2, 6), ('peewee-0001', 1, 2), ('peewee-0001', 2, 1), ('pygments-0001', 1, 3), ('pygments-0001', 2, 5), ('pygments-0001', 3, 6), ('sqlite-utils-0001', 2, 1), ('sqlite-utils-0001', 3, 1), ('sqlite-utils-0003', 1, 2), ('sqlite-utils-0003', 3, 15), ('tomlkit-0002', 1, 4), ('tomlkit-0003', 1, 1), ('tomlkit-0003', 2, 2), ('tomlkit-0003', 3, 2)].
- Runs resolvidos com todas as revisões aprovadas: 9; runs não resolvidos com ao menos uma reprovação: 13.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | sim | 1/1 | 0 | 111 | 119 | 1029701 | 0.134 | 184 | 3 | 50 | 0.079 | -0.67 | 0 | 0 | concluiu | 17·41·16·24 | RARRRA |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | não | 0/1 | 1 | 102 | 109 | 1171645 | 0.148 | 179 | 1 | 7 | 0.087 | -1.176 | 0 | 0 | concluiu | 13·41·41 | RARRA |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | não | 0/1 | 1 | 81 | 86 | 693997 | 0.086 | 97 | 1 | 8 | 0.087 | -0.998 | 0 | 0 | concluiu | 27·41 | RAA |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 45 | 49 | 373949 | 0.052 | 91 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 21·11 | RA |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 57 | 62 | 578538 | 0.074 | 105 | 2 | 7 | 0.017 | -0.194 | 0 | 0 | concluiu | 14·34 | RRA |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 45 | 50 | 463586 | 0.065 | 66 | 1 | 21 | 0.021 | 0 | 0 | 0 | concluiu | 25·7 | RRA |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 7 | 120 | 127 | 1620653 | 0.201 | 154 | 0 | 0 | — | — | 1 | 0 | budget: max_turns | 41·41·25 | RRRRRR |
| tomlkit-0004 | grande | 1 | single-agent | não | 3/7 | 60 | 120 | 120 | 4007174 | 0.453 | 348 | 2 | 176 | 0.814 | -3.691 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 0/7 | 7 | 120 | 125 | 1980490 | 0.255 | 217 | 0 | 0 | — | — | 4 | 0 | budget: max_turns | 41·41·25 | RRRR |
| tomlkit-0004 | grande | 2 | single-agent | não | 3/7 | 7 | 120 | 120 | 4864896 | 0.522 | 555 | 2 | 40 | 0.288 | -0.238 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 0/7 | 7 | 120 | 129 | 1760696 | 0.23 | 176 | 1 | 2 | 0 | -0.247 | 0 | 0 | budget: max_turns | 14·41·41·11 | RRRRRRRR |
| tomlkit-0004 | grande | 3 | single-agent | não | 3/7 | 4 | 120 | 120 | 4921834 | 0.53 | 367 | 1 | 216 | 1.24 | -5.642 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | não | 2/3 | 1 | 29 | 34 | 159898 | 0.027 | 79 | 2 | 12 | 0.15 | -0.517 | 0 | 0 | concluiu | 9·13 | RAA |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | sim | 3/3 | 0 | 77 | 89 | 614936 | 0.099 | 254 | 2 | 43 | 0.15 | -0.479 | 0 | 0 | concluiu | 14·19·9·5·3·4 | RRARARARAR |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | sim | 3/3 | 0 | 39 | 42 | 350684 | 0.047 | 83 | 2 | 10 | 0 | -0.099 | 0 | 0 | concluiu | 26 | A |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 27 | 32 | 198272 | 0.033 | 199 | 1 | 27 | 0.002 | 0 | 0 | 0 | concluiu | 7·7 | RRA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 36 | 41 | 287986 | 0.043 | 219 | 1 | 29 | 0.001 | 0 | 0 | 0 | concluiu | 10·13 | RAA |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | não | 0/4 | 0 | 120 | 127 | 2008235 | 0.261 | 292 | 1 | 9885 | -0.832 | 33.529 | 0 | 0 | budget: max_turns | 6·28·29·41·7 | RRRRRR |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 5/6 | 1 | 120 | 131 | 1027916 | 0.129 | 587 | 2 | 24 | 0.002 | 0 | 0 | 0 | budget: max_turns | 21·22·10·38·16 | RARARARARA |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 2/6 | 4 | 120 | 129 | 1198607 | 0.153 | 573 | 1 | 18 | 0.005 | 0 | 16 | 0 | budget: max_turns | 41·41·21·4 | RARARRRR |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 0/6 | 6 | 27 | 27 | 165444 | 0.025 | 290 | 0 | 0 | — | — | 0 | 0 | error: ValueError | 13 | — |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | sim | 12/12 | 0 | 65 | 72 | 819339 | 0.125 | 223 | 3 | 76 | 0.051 | -0.533 | 0 | 0 | concluiu | 12·26·14 | RARAA |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | não | 9/12 | 4 | 73 | 80 | 871244 | 0.13 | 230 | 3 | 66 | 0.013 | -0.327 | 0 | 0 | concluiu | 13·15·32 | RRRRA |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | sim | 12/12 | 0 | 120 | 139 | 2068454 | 0.283 | 327 | 3 | 69 | 0.013 | -0.334 | 0 | 0 | budget: max_turns | 6·18·9·6·18·9·15·16·10 | RRRARARARRRRRRRRRR |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 22 | 25 | 123811 | 0.021 | 154 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 9 | A |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 17 | 20 | 82677 | 0.016 | 95 | 1 | 3 | 0.154 | 1.806 | 0 | 0 | concluiu | 6 | A |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 23 | 26 | 138198 | 0.024 | 171 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 10 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | sim | 2/2 | 0 | 78 | 82 | 1115732 | 0.152 | 472 | 1 | 26 | 0 | 0 | 0 | 0 | error: ValueError | 13·41·10 | RRRA |
| pygments-0001 | pequena | 1 | single-agent | não | 0/2 | 2 | 120 | 120 | 7109886 | 0.819 | 859 | 1 | 53 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 2 | orchestration | sim | 2/2 | 0 | 109 | 118 | 1744438 | 0.239 | 317 | 1 | 34 | 0 | 0 | 0 | 0 | concluiu | 18·41·30·7 | RRRRRAA |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 17 | 17 | 229142 | 0.037 | 127 | 1 | 47 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | sim | 2/2 | 0 | 81 | 90 | 1238202 | 0.169 | 308 | 1 | 38 | 0 | 0 | 0 | 0 | concluiu | 7·13·41·7 | RRRRRRA |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 50 | 50 | 1288314 | 0.179 | 606 | 1 | 61 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 0/5 | 5 | 29 | 32 | 270366 | 0.044 | 91 | 1 | 24 | 0.052 | 0 | 1 | 0 | concluiu | 20 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | sim | 5/5 | 0 | 70 | 74 | 759277 | 0.104 | 180 | 1 | 45 | 0.015 | 0 | 3 | 0 | concluiu | 16·41 | RA |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | sim | 5/5 | 0 | 83 | 87 | 1027484 | 0.134 | 188 | 1 | 54 | -0.047 | 0 | 0 | 1 | concluiu | 41·29 | RA |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 44 | 47 | 543046 | 0.071 | 198 | 1 | 34 | 0.031 | 0 | 0 | 3 | concluiu | 31 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 28 | 28 | 452395 | 0.057 | 119 | 1 | 30 | 0.031 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | sim | 11/11 | 0 | 50 | 53 | 648651 | 0.083 | 135 | 1 | 14 | 0.037 | 0 | 0 | 0 | concluiu | 37 | A |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 10 | 117 | 117 | 8077370 | 1.113 | 1328 | 1 | 38 | -0.008 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | não | 5/11 | 6 | 36 | 39 | 385941 | 0.052 | 51 | 1 | 22 | 0.025 | 0 | 1 | 0 | concluiu | 23 | A |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 45 | 45 | 821788 | 0.096 | 161 | 1 | 34 | 0.011 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 30 | 33 | 366012 | 0.053 | 54 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 17 | A |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 32 | 35 | 201015 | 0.029 | 45 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 19 | A |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 22 | 25 | 168596 | 0.029 | 48 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 14 | A |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | não | 0/1 | 134 | 120 | 130 | 1405507 | 0.199 | 288 | 2 | 361 | -0.255 | 9.678 | 0 | 0 | budget: max_turns | 14·12·41·12·11·17·0 | RRRRRRRRR |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 1/1 | 46 | 120 | 128 | 1240304 | 0.17 | 270 | 1 | 203 | -0.086 | 0 | 1 | 0 | budget: max_turns | 39·32·9·19·1·5·0 | RRAARAR |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | não | 0/1 | 56 | 120 | 124 | 1390350 | 0.181 | 167 | 2 | 14 | -0.004 | 0 | 1 | 0 | budget: max_turns | 41·41·25 | RRR |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-r6-analise`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.587 | 4 | 22 | 4/9 | 0 | 3265263 | 0.35 | 120 | 295 | 124 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 4/9 | 0.667 | 5 | 31 | 3/9 | 0 | 1664077 | 0.207 | 121 | 254 | 48 | 0.131 | -0.496 | 2 | 0 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 4/12 | 0.799 | 8 | 2 | 6/12 | 0 | 1473804 | 0.183 | 122 | 520 | 38 | 0.035 | -0.129 | 0 | 1 |
| pequena | single-agent | 18 | 9/18 | 0.598 | 9 | 4 | 14/18 | 1 | 507754 | 0.064 | 38 | 170 | 36 | 0 | 0 | 1 | 8 |
| pequena | orchestration | 18 | 11/18 | 0.692 | 6 | 5 | 14/18 | 0 | 708445 | 0.095 | 46 | 200 | 26 | 0.012 | 0 | 0 | 0 |
| todas | single-agent | 39 | 23/39 | 0.715 | 15 | 6 | 29/39 | 1 | 979282 | 0.117 | 50 | 243 | 40 | 0.014 | 0 | 5 | 8 |
| todas | orchestration | 39 | 19/39 | 0.719 | 19 | 5 | 23/39 | 0 | 1296059 | 0.168 | 101 | 318 | 37 | 0.026 | 0 | 2 | 1 |

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
| fração de ocultos passados | todas | 13 | 0 | 3 | 0.625 |
| fração de ocultos passados | ambos_resolvem_mediana | 5 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 7 | 0 | 1 | 1 |
| tokens | todas | 13 | 79539 | 38 | 0.6355 |
| tokens | ambos_resolvem_mediana | 5 | 79539 | 0 | 0.0625 |
| tokens | ambos_resolvem_ao_menos_uma | 7 | 79539 | 7 | 0.2969 |
| US$ | todas | 13 | 0.013 | 35 | 0.4973 |
| US$ | ambos_resolvem_mediana | 5 | 0.013 | 0 | 0.0625 |
| US$ | ambos_resolvem_ao_menos_uma | 7 | 0.013 | 7 | 0.2969 |
| chamadas | todas | 13 | 15 | 3 | 0.0012 |
| chamadas | ambos_resolvem_mediana | 5 | 15 | 0 | 0.0625 |
| chamadas | ambos_resolvem_ao_menos_uma | 7 | 15 | 0 | 0.0156 |
| parede (s) | todas | 13 | 29.969 | 33 | 0.4143 |
| parede (s) | ambos_resolvem_mediana | 5 | 29.969 | 6 | 0.8125 |
| parede (s) | ambos_resolvem_ao_menos_uma | 7 | 29.969 | 8 | 0.375 |
| turnos | todas | 13 | 9 | 5 | 0.0088 |
| turnos | ambos_resolvem_mediana | 5 | 9 | 0 | 0.0625 |
| turnos | ambos_resolvem_ao_menos_uma | 7 | 9 | 0 | 0.0312 |
| linhas do patch | todas | 13 | -4 | 29 | 0.458 |
| linhas do patch | ambos_resolvem_mediana | 5 | -2 | 0 | 0.125 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 7 | -2 | 4 | 0.1875 |
| ΔCC | todas | 13 | 0 | 19 | 0.4316 |
| ΔCC | ambos_resolvem_mediana | 5 | 0 | 1 | 1 |
| ΔCC | ambos_resolvem_ao_menos_uma | 7 | 0 | 1 | 0.25 |
| regressões | todas | 13 | 0 | 5 | 0.1406 |
| regressões | ambos_resolvem_mediana | 5 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 7 | 0 | 0 | 0.5 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 12, 2: 5, 3: 11, 4: 5, 5: 3, 6: 2, 12: 1}; runs com 2+ ciclos (memória de trabalho usada): 27/39.
- Revisões semânticas (suíte verde): 175; aprovadas 39, reprovadas 136.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 9 — [('attrs-0001', 1, 1), ('peewee-0001', 1, 2), ('peewee-0003', 1, 4), ('peewee-0003', 2, 3), ('pygments-0001', 1, 2), ('pygments-0001', 2, 2), ('sqlite-utils-0002', 3, 2), ('tomlkit-0003', 2, 10), ('tomlkit-0003', 3, 4)].
- Runs resolvidos com todas as revisões aprovadas: 10; runs não resolvidos com ao menos uma reprovação: 18.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | não | 1/1 | 29 | 120 | 124 | 1664077 | 0.207 | 318 | 3 | 48 | 0.079 | -0.333 | 0 | 0 | budget: max_turns | 41·41·29 | RARAR |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | não | 0/1 | 31 | 120 | 121 | 1955004 | 0.244 | 411 | 3 | 87 | 0.15 | -0.496 | 0 | 0 | budget: max_turns | 41·41·29 | RRR |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | sim | 1/1 | 0 | 37 | 40 | 467161 | 0.062 | 61 | 1 | 11 | 0.131 | -1.663 | 0 | 0 | concluiu | 28 | A |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 23 | 26 | 327493 | 0.051 | 62 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 14 | A |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 120 | 131 | 1474692 | 0.19 | 421 | 1 | 2 | 0.011 | 0 | 0 | 0 | budget: max_turns | 14·13·41·20·23 | RRRRRRRRRR |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 58 | 65 | 866787 | 0.117 | 143 | 1 | 27 | 0.026 | 0 | 0 | 0 | concluiu | 18·14·17 | RRRRA |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 3/7 | 8 | 120 | 121 | 1846912 | 0.224 | 254 | 3 | 90 | 0.417 | -1.928 | 0 | 0 | budget: max_turns | 41·41·29 | RRR |
| tomlkit-0004 | grande | 1 | single-agent | não | 3/7 | 60 | 120 | 120 | 4007174 | 0.453 | 348 | 2 | 176 | 0.814 | -3.691 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 1/7 | 73 | 120 | 122 | 2432276 | 0.296 | 364 | 2 | 271 | 0.779 | -4.411 | 0 | 0 | budget: max_turns | 41·41·29 | RRRR |
| tomlkit-0004 | grande | 2 | single-agent | não | 3/7 | 7 | 120 | 120 | 4864896 | 0.522 | 555 | 2 | 40 | 0.288 | -0.238 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 3/7 | 60 | 120 | 121 | 2223369 | 0.27 | 229 | 3 | 219 | 0.19 | -4.416 | 2 | 0 | budget: max_turns | 41·41·29 | RRR |
| tomlkit-0004 | grande | 3 | single-agent | não | 3/7 | 4 | 120 | 120 | 4921834 | 0.53 | 367 | 1 | 216 | 1.24 | -5.642 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 51 | 56 | 602308 | 0.1 | 954 | 2 | 27 | 0.09 | -0.221 | 0 | 0 | concluiu | 32·10 | RAA |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | não | 2/3 | 1 | 120 | 127 | 1296059 | 0.166 | 415 | 2 | 27 | 0.18 | -0.308 | 0 | 0 | budget: max_turns | 21·11·19·33·14·4 | RARRRRRRRRRR |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | não | 2/3 | 1 | 90 | 101 | 820154 | 0.12 | 441 | 2 | 37 | 0.022 | -1.221 | 0 | 1 | concluiu | 30·14·8·11·12 | RARARARAR |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 115 | 121 | 1651425 | 0.209 | 502 | 3 | 235 | 0.095 | -0.407 | 0 | 0 | concluiu | 30·41·26 | RARAA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 25 | 28 | 248735 | 0.037 | 186 | 1 | 39 | 0.002 | 0 | 0 | 0 | concluiu | 16 | A |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 35 | 38 | 398257 | 0.057 | 254 | 1 | 38 | 0.001 | 0 | 0 | 0 | concluiu | 26 | A |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 3/6 | 3 | 120 | 125 | 1839519 | 0.225 | 539 | 1 | 29 | 0.006 | 0 | 0 | 0 | budget: max_turns | 41·41·20·9 | RRRRRRRR |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 5/6 | 15 | 120 | 123 | 1459272 | 0.182 | 540 | 3 | 37 | -0.017 | -0.036 | 0 | 0 | budget: max_turns | 41·12·41·17 | RRRRRR |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 1/6 | 5 | 120 | 127 | 1488337 | 0.184 | 624 | 1 | 48 | 0.009 | 0 | 0 | 0 | budget: max_turns | 18·41·41·11 | RRRRRRRR |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | não | 9/12 | 60 | 120 | 121 | 2523739 | 0.323 | 533 | 3 | 424 | 0.317 | 0.409 | 0 | 0 | budget: max_turns | 23·16·41·31 | RRRR |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | não | 12/12 | 1 | 120 | 122 | 2512941 | 0.318 | 606 | 3 | 290 | 0.188 | -2.005 | 0 | 0 | budget: max_turns | 14·17·41·14·22·3 | RRRRARR |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | não | 12/12 | 1 | 118 | 124 | 2844840 | 0.362 | 507 | 3 | 335 | 0.048 | -0.539 | 0 | 0 | concluiu | 26·41·28·14 | RRRRAA |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 95 | 104 | 1197379 | 0.168 | 885 | 1 | 21 | -0.185 | 5.071 | 0 | 0 | concluiu | 6·41·7·17·8 | RARARARAA |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 25 | 31 | 157459 | 0.028 | 577 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | concluiu | 6·5·5 | RARRA |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 16 | 19 | 85902 | 0.015 | 165 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | concluiu | 7 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | sim | 2/2 | 0 | 75 | 79 | 1367853 | 0.181 | 292 | 1 | 51 | 0 | 0 | 0 | 0 | concluiu | 41·25 | RRA |
| pygments-0001 | pequena | 1 | single-agent | não | 0/2 | 2 | 120 | 120 | 7109886 | 0.819 | 859 | 1 | 53 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 2 | orchestration | sim | 2/2 | 0 | 83 | 87 | 1805781 | 0.235 | 351 | 1 | 65 | 0 | 0 | 0 | 0 | concluiu | 41·33 | RRA |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 17 | 17 | 229142 | 0.037 | 127 | 1 | 47 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | sim | 2/2 | 0 | 48 | 51 | 1005871 | 0.134 | 209 | 1 | 37 | 0 | 0 | 0 | 0 | concluiu | 39 | A |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 50 | 50 | 1288314 | 0.179 | 606 | 1 | 61 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 1/5 | 5 | 18 | 21 | 148340 | 0.026 | 76 | 1 | 26 | 0.039 | 0 | 0 | 0 | concluiu | 12 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | não | 0/5 | 5 | 120 | 137 | 1587052 | 0.211 | 513 | 1 | 38 | 0.028 | 0 | 0 | 0 | budget: max_turns | 22·11·11·6·6·8·10·7·3·4·11·3 | RRRRRRRRRRRRRRRRRRRRRRRR |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 4/5 | 1 | 74 | 77 | 1287164 | 0.16 | 191 | 1 | 153 | 0.099 | 0 | 0 | 0 | concluiu | 41·24 | RA |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | não | 5/11 | 6 | 34 | 37 | 374524 | 0.052 | 92 | 1 | 26 | 0.037 | 0 | 0 | 0 | concluiu | 25 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 28 | 28 | 452395 | 0.057 | 119 | 1 | 30 | 0.031 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | sim | 11/11 | 0 | 23 | 26 | 302037 | 0.045 | 83 | 1 | 30 | 0.025 | 0 | 0 | 0 | concluiu | 14 | A |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 10 | 117 | 117 | 8077370 | 1.113 | 1328 | 1 | 38 | -0.008 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | sim | 11/11 | 0 | 38 | 42 | 411019 | 0.057 | 118 | 1 | 21 | 0.056 | 0 | 0 | 0 | concluiu | 18·11 | RRA |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 45 | 45 | 821788 | 0.096 | 161 | 1 | 34 | 0.011 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 21 | 24 | 142954 | 0.024 | 98 | 1 | 9 | -0.025 | 0 | 0 | 0 | concluiu | 14 | A |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 26 | 29 | 190445 | 0.028 | 59 | 1 | 17 | 0.024 | 0 | 0 | 0 | concluiu | 17 | A |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 26 | 29 | 257173 | 0.036 | 69 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 19 | A |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | não | 0/1 | 1 | 120 | 124 | 1456160 | 0.182 | 319 | 2 | 14 | -0.004 | 0 | 0 | 0 | budget: max_turns | 41·41·29 | RRRRRR |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 0/1 | 192 | 120 | 121 | 1922923 | 0.242 | 430 | 2 | 78 | -0.035 | 0 | 0 | 0 | budget: max_turns | 41·41·29 | RRR |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | não | 0/1 | 0 | 120 | 122 | 1678333 | 0.206 | 257 | 2 | 55 | -0.016 | 0.328 | 0 | 0 | budget: max_turns | 41·41·29 | RRRR |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


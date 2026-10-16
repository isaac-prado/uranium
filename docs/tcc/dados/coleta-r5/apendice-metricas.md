# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-r5-analise`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 4/9 | 0.587 | 4 | 22 | 4/9 | 0 | 3265263 | 0.35 | 120 | 295 | 124 | 0.025 | -0.186 | 1 | 0 |
| grande | orchestration | 9 | 5/9 | 0.571 | 4 | 11 | 5/9 | 0 | 676866 | 0.104 | 65 | 131 | 12 | 0.097 | -1.353 | 0 | 1 |
| media | single-agent | 12 | 10/12 | 0.986 | 2 | 141 | 11/12 | 0 | 936442 | 0.11 | 52 | 240 | 50 | 0.034 | -0.155 | 3 | 0 |
| media | orchestration | 12 | 4/12 | 0.743 | 8 | 3 | 8/12 | 0 | 582698 | 0.086 | 43 | 259 | 29 | 0.026 | -0.096 | 0 | 0 |
| pequena | single-agent | 18 | 9/18 | 0.598 | 9 | 4 | 14/18 | 1 | 507754 | 0.064 | 38 | 170 | 36 | 0 | 0 | 1 | 8 |
| pequena | orchestration | 18 | 9/18 | 0.671 | 8 | 5 | 13/18 | 0 | 722572 | 0.103 | 73 | 263 | 26 | 0.017 | 0 | 4 | 0 |
| todas | single-agent | 39 | 23/39 | 0.715 | 15 | 6 | 29/39 | 1 | 979282 | 0.117 | 50 | 243 | 40 | 0.014 | 0 | 5 | 8 |
| todas | orchestration | 39 | 18/39 | 0.67 | 20 | 5 | 26/39 | 0 | 613921 | 0.093 | 65 | 236 | 27 | 0.031 | 0 | 4 | 1 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 1 | 0 | 2 | 1 |
| media | 4 | 0 | 3 | 1 | 0.25 |
| pequena | 6 | 2 | 2 | 2 | 1 |
| todas | 13 | 3 | 5 | 5 | 0.7266 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 11 | 0.6875 |
| fração de ocultos passados | ambos_resolvem_mediana | 5 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 7 | 0 | 1 | 1 |
| tokens | todas | 13 | -115619 | 32 | 0.3757 |
| tokens | ambos_resolvem_mediana | 5 | 123052 | 5 | 0.625 |
| tokens | ambos_resolvem_ao_menos_uma | 7 | 123052 | 13 | 0.9375 |
| US$ | todas | 13 | -0.006 | 36 | 0.5417 |
| US$ | ambos_resolvem_mediana | 5 | 0.008 | 3 | 0.3125 |
| US$ | ambos_resolvem_ao_menos_uma | 7 | 0.008 | 10 | 0.5781 |
| chamadas | todas | 13 | 1 | 32 | 0.3672 |
| chamadas | ambos_resolvem_mediana | 5 | 32 | 2 | 0.1875 |
| chamadas | ambos_resolvem_ao_menos_uma | 7 | 10 | 9 | 0.4688 |
| parede (s) | todas | 13 | 5.023 | 42 | 0.8394 |
| parede (s) | ambos_resolvem_mediana | 5 | 27.159 | 4 | 0.4375 |
| parede (s) | ambos_resolvem_ao_menos_uma | 7 | 5.023 | 12 | 0.8125 |
| turnos | todas | 13 | 0 | 33 | 0.6636 |
| turnos | ambos_resolvem_mediana | 5 | 26 | 3 | 0.3125 |
| turnos | ambos_resolvem_ao_menos_uma | 7 | 7 | 11 | 0.6875 |
| linhas do patch | todas | 13 | -15 | 0 | 0.0005 |
| linhas do patch | ambos_resolvem_mediana | 5 | -12 | 0 | 0.125 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 7 | -12 | 0 | 0.0312 |
| ΔCC | todas | 13 | 0 | 17 | 0.5703 |
| ΔCC | ambos_resolvem_mediana | 5 | 0 | 0 | 1 |
| ΔCC | ambos_resolvem_ao_menos_uma | 7 | 0 | 1 | 0.5 |
| regressões | todas | 13 | 0 | 2.5 | 0.1562 |
| regressões | ambos_resolvem_mediana | 5 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 7 | 0 | 0 | 1 |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 11, 2: 7, 3: 8, 4: 6, 5: 4, 6: 1, 7: 1, 8: 1}; runs com 2+ ciclos (memória de trabalho usada): 28/39.
- Revisões semânticas (suíte verde): 174; aprovadas 57, reprovadas 117.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 12 — [('attrs-0001', 1, 3), ('peewee-0001', 1, 1), ('peewee-0001', 2, 1), ('peewee-0001', 3, 1), ('peewee-0003', 1, 4), ('peewee-0003', 3, 12), ('pygments-0001', 1, 3), ('pygments-0001', 2, 2), ('tomlkit-0001', 1, 5), ('tomlkit-0001', 3, 4), ('tomlkit-0003', 3, 6), ('tomlkit-0005', 3, 2)].
- Runs resolvidos com todas as revisões aprovadas: 6; runs não resolvidos com ao menos uma reprovação: 16.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | sim | 1/1 | 0 | 50 | 53 | 643036 | 0.083 | 86 | 1 | 12 | 0.131 | -1.836 | 0 | 0 | concluiu | 41 | A |
| tomlkit-0002 | grande | 1 | single-agent | não | 0/1 | 37 | 120 | 120 | 3265263 | 0.35 | 295 | 3 | 124 | 0.025 | -0.186 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | sim | 1/1 | 0 | 50 | 53 | 529023 | 0.069 | 71 | 1 | 10 | 0.087 | -1.353 | 0 | 0 | concluiu | 41 | A |
| tomlkit-0002 | grande | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 2349817 | 0.264 | 271 | 3 | 174 | 2.717 | -10.081 | 0 | 0 | tests_pass | — | — |
| tomlkit-0002 | grande | 3 | orchestration | não | 0/1 | 1 | 120 | 124 | 1565694 | 0.191 | 207 | 2 | 42 | 0.097 | -0.831 | 0 | 0 | budget: max_turns | 35·41·33·2 | RRRRRRR |
| tomlkit-0002 | grande | 3 | single-agent | não | 0/1 | 0 | 120 | 120 | 4450887 | 0.481 | 306 | 2 | 1570 | -0.945 | 49.502 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 22 | 25 | 221948 | 0.034 | 52 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 13 | A |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 42 | 42 | 599857 | 0.068 | 113 | 2 | 7 | -0.002 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 31 | 34 | 457404 | 0.064 | 60 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 22 | A |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 80 | 80 | 1928407 | 0.218 | 230 | 1 | 4 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 57 | 65 | 676866 | 0.104 | 131 | 2 | 7 | -0.002 | 0 | 0 | 0 | concluiu | 26·2·2·3·3·3 | RARARARARAR |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 20 | 20 | 141896 | 0.018 | 34 | 1 | 2 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 0/7 | 9 | 120 | 121 | 2442376 | 0.294 | 260 | 1 | 52 | 0.128 | -1.675 | 0 | 0 | budget: max_turns | 41·41·30 | RRR |
| tomlkit-0004 | grande | 1 | single-agent | não | 3/7 | 60 | 120 | 120 | 4007174 | 0.453 | 348 | 2 | 176 | 0.814 | -3.691 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 1/7 | 13 | 120 | 121 | 2533648 | 0.317 | 241 | 2 | 126 | 0.649 | -4.657 | 0 | 0 | budget: max_turns | 41·41·17·1·11 | RRRRR |
| tomlkit-0004 | grande | 2 | single-agent | não | 3/7 | 7 | 120 | 120 | 4864896 | 0.522 | 555 | 2 | 40 | 0.288 | -0.238 | 1 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 0/7 | 88 | 120 | 121 | 2272756 | 0.269 | 197 | 1 | 96 | 0.409 | -3.5 | 0 | 1 | budget: max_turns | 41·41·29 | RRR |
| tomlkit-0004 | grande | 3 | single-agent | não | 3/7 | 4 | 120 | 120 | 4921834 | 0.53 | 367 | 1 | 216 | 1.24 | -5.642 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 53 | 59 | 475072 | 0.071 | 140 | 2 | 18 | 0.084 | -0.155 | 0 | 0 | concluiu | 7·7·7·14 | RARARAA |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 18 | 18 | 100267 | 0.014 | 65 | 2 | 12 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | não | 2/3 | 1 | 25 | 28 | 137575 | 0.023 | 83 | 2 | 6 | 0.084 | -0.155 | 0 | 0 | concluiu | 16 | A |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 19 | 19 | 113319 | 0.015 | 78 | 2 | 11 | 0.078 | -0.155 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | não | 2/3 | 1 | 26 | 29 | 250548 | 0.037 | 70 | 2 | 6 | 0.078 | -0.155 | 0 | 0 | concluiu | 17 | A |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 25 | 25 | 163612 | 0.021 | 88 | 2 | 11 | 0.09 | -0.155 | 1 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 24 | 28 | 190042 | 0.031 | 236 | 1 | 27 | 0.001 | 0 | 0 | 0 | concluiu | 9·6 | RAA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 25 | 25 | 229401 | 0.028 | 287 | 1 | 60 | 0.001 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 42 | 46 | 551745 | 0.078 | 377 | 3 | 90 | 0.021 | -0.232 | 0 | 0 | concluiu | 9·24 | RAA |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 93 | 93 | 2458889 | 0.343 | 2752 | 3 | 77 | 0.009 | -0.226 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 26 | 30 | 198675 | 0.032 | 276 | 1 | 31 | 0.002 | 0 | 0 | 0 | concluiu | 5·12 | RAA |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 29 | 29 | 314294 | 0.037 | 234 | 1 | 38 | 0.003 | 0 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 1/6 | 5 | 120 | 124 | 1790234 | 0.213 | 295 | 1 | 14 | 0.002 | 0 | 0 | 0 | budget: max_turns | 41·41·29 | RRRRRR |
| peewee-0002 | media | 1 | single-agent | sim | 6/6 | 0 | 87 | 87 | 1598793 | 0.174 | 246 | 3 | 30 | 0.002 | 0.023 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 2 | orchestration | não | 4/6 | 16 | 120 | 123 | 1476705 | 0.18 | 459 | 3 | 27 | -0.018 | -0.036 | 0 | 0 | budget: max_turns | 41·28·41·1 | RRRRRR |
| peewee-0002 | media | 2 | single-agent | sim | 6/6 | 0 | 111 | 111 | 2108779 | 0.228 | 530 | 5 | 60 | 0.014 | -0.348 | 1 | 0 | tests_pass | — | — |
| peewee-0002 | media | 3 | orchestration | não | 1/6 | 5 | 120 | 124 | 1429114 | 0.173 | 438 | 1 | 47 | 0.012 | 0 | 0 | 0 | budget: max_turns | 31·41·39 | RRRRRR |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 112 | 112 | 2422402 | 0.259 | 309 | 5 | 41 | 0.036 | -0.204 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | não | 9/12 | 25 | 120 | 121 | 4506372 | 0.621 | 955 | 2 | 238 | 0.221 | 1.968 | 0 | 0 | budget: max_turns | 41·37·33 | RRR |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 60 | 60 | 1012916 | 0.121 | 155 | 3 | 238 | 0.031 | -1.134 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | não | 11/12 | 1 | 36 | 40 | 613921 | 0.099 | 241 | 2 | 56 | 0.031 | -0.624 | 0 | 0 | concluiu | 11·16 | RAA |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 45 | 45 | 859969 | 0.099 | 141 | 3 | 72 | 0.038 | -0.385 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | não | 11/12 | 1 | 36 | 40 | 613651 | 0.093 | 164 | 2 | 72 | 0.053 | -0.807 | 0 | 0 | concluiu | 6·23 | RAA |
| sqlite-utils-0003 | media | 3 | single-agent | não | 12/12 | 281 | 120 | 120 | 4121040 | 0.464 | 496 | 4 | 996 | 0.449 | 0.727 | 0 | 0 | budget: max_turns | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 42 | 48 | 234558 | 0.038 | 596 | 1 | 5 | 0.154 | 1.855 | 0 | 0 | concluiu | 8·5·5·7 | RARARAR |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 18 | 18 | 120971 | 0.016 | 111 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 20 | 23 | 134897 | 0.023 | 170 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | concluiu | 11 | A |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 16 | 16 | 101593 | 0.019 | 274 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 67 | 77 | 527751 | 0.087 | 1291 | 1 | 6 | 0.154 | 3.885 | 0 | 0 | concluiu | 8·6·10·4·8·5·6·6 | RRRRRARRRRRARAR |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 9 | 9 | 38423 | 0.006 | 179 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | sim | 2/2 | 0 | 88 | 92 | 1411366 | 0.188 | 633 | 1 | 37 | 0 | 0 | 0 | 0 | concluiu | 15·41·23 | RRRA |
| pygments-0001 | pequena | 1 | single-agent | não | 0/2 | 2 | 120 | 120 | 7109886 | 0.819 | 859 | 1 | 53 | 0 | 0 | 0 | 0 | budget: max_turns | — | — |
| pygments-0001 | pequena | 2 | orchestration | sim | 2/2 | 0 | 64 | 68 | 1207595 | 0.158 | 272 | 1 | 50 | 0 | 0 | 0 | 0 | concluiu | 41·14 | RRA |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 17 | 17 | 229142 | 0.037 | 127 | 1 | 47 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | não | 0/2 | 2 | 120 | 125 | 3042836 | 0.451 | 1125 | 1 | 38 | 0 | 0 | 0 | 0 | budget: max_turns | 20·28·41·22 | RARARRRR |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 50 | 50 | 1288314 | 0.179 | 606 | 1 | 61 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 4/5 | 1 | 31 | 34 | 421814 | 0.06 | 255 | 1 | 27 | 0.058 | 0 | 0 | 0 | concluiu | 22 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 28 | 28 | 241494 | 0.031 | 114 | 1 | 39 | 0.065 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | não | 0/5 | 5 | 82 | 91 | 859493 | 0.145 | 859 | 1 | 30 | 0.058 | 0 | 0 | 0 | concluiu | 30·6·6·7·7·7·6 | RARARARARARAR |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 35 | 35 | 507709 | 0.068 | 130 | 1 | 50 | 0.021 | 0 | 1 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 0/5 | 5 | 28 | 31 | 279333 | 0.043 | 99 | 1 | 26 | 0.058 | 0 | 0 | 0 | concluiu | 19 | A |
| sqlite-utils-0001 | pequena | 3 | single-agent | não | 1/5 | 268 | 120 | 120 | 5639360 | 0.616 | 848 | 2 | 895 | 0.659 | -1.799 | 0 | 8 | budget: max_turns | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | sim | 11/11 | 0 | 34 | 37 | 532178 | 0.07 | 79 | 1 | 23 | 0.037 | 0 | 1 | 0 | concluiu | 25 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 28 | 28 | 452395 | 0.057 | 119 | 1 | 30 | 0.031 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | não | 9/11 | 6 | 120 | 121 | 2106741 | 0.257 | 320 | 1 | 33 | 0.068 | 0 | 3 | 0 | budget: max_turns | 41·28·24·15·3 | RRRRR |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 10 | 117 | 117 | 8077370 | 1.113 | 1328 | 1 | 38 | -0.008 | 0 | 0 | 0 | budget: max_tokens | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | não | 5/11 | 6 | 32 | 35 | 537960 | 0.072 | 108 | 1 | 25 | 0.031 | 0 | 0 | 0 | concluiu | 23 | A |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 45 | 45 | 821788 | 0.096 | 161 | 1 | 34 | 0.011 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 62 | 69 | 585650 | 0.09 | 153 | 1 | 3 | 0 | 0 | 0 | 0 | concluiu | 15·5·5·7·12 | RARARARAR |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 41 | 41 | 507799 | 0.059 | 128 | 1 | 17 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | não | 1/1 | 74 | 120 | 124 | 1755675 | 0.234 | 296 | 2 | 248 | -0.015 | 3.349 | 0 | 0 | budget: max_turns | 19·10·15·41·17 | RARARARR |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 14 | 14 | 60692 | 0.008 | 23 | 1 | 5 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 44 | 50 | 324965 | 0.055 | 111 | 1 | 2 | 0 | 0 | 0 | 0 | concluiu | 7·8·5·8 | RARARAR |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 17 | 17 | 121675 | 0.015 | 22 | 1 | 15 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | não | 0/1 | 0 | 120 | 121 | 1803318 | 0.236 | 356 | 2 | 2258 | -0.361 | 3.406 | 0 | 0 | budget: max_turns | 41·41·29 | RRR |
| tomlkit-0005 | pequena | 1 | single-agent | não | 0/1 | 1 | 120 | 120 | 2992841 | 0.346 | 519 | 1 | 60 | -0.065 | 0 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | não | 0/1 | 1 | 120 | 124 | 1781375 | 0.215 | 187 | 2 | 16 | -0.008 | -0.317 | 0 | 0 | budget: max_turns | 41·41·29 | RRRRRR |
| tomlkit-0005 | pequena | 2 | single-agent | não | 0/1 | 1 | 75 | 75 | 979282 | 0.117 | 377 | 1 | 25 | -0.003 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | sim | 1/1 | 0 | 86 | 90 | 941013 | 0.116 | 160 | 2 | 7 | 0.002 | 0 | 0 | 0 | concluiu | 41·36 | RRA |
| tomlkit-0005 | pequena | 3 | single-agent | não | 0/1 | 1 | 68 | 68 | 1031426 | 0.126 | 243 | 1 | 79 | -0.067 | 0 | 0 | 0 | tests_pass | — | — |


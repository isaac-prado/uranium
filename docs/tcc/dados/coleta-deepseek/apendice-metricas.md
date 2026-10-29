# Apêndice de métricas da coleta (78 runs admitidos, `runs/coleta-deepseek`)

Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.

## A. Agregados por faixa e braço (sobre runs)

| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grande | single-agent | 9 | 3/9 | 0.857 | 6 | 16 | 3/9 | 0 | 3757974 | 0.502 | 120 | 1030 | 97 | 0.104 | -0.399 | 0 | 0 |
| grande | orchestration | 9 | 6/9 | 0.905 | 3 | 2 | 6/9 | 0 | 1288589 | 0.188 | 99 | 628 | 16 | 0.065 | -0.618 | 0 | 0 |
| media | single-agent | 12 | 9/12 | 0.931 | 3 | 1 | 10/12 | 0 | 1027377 | 0.14 | 58 | 505 | 68 | 0.04 | -0.361 | 0 | 0 |
| media | orchestration | 12 | 8/12 | 0.882 | 4 | 3 | 8/12 | 0 | 1030416 | 0.15 | 68 | 677 | 54 | 0.065 | -0.496 | 0 | 0 |
| pequena | single-agent | 18 | 14/18 | 0.865 | 4 | 6 | 18/18 | 0 | 542768 | 0.077 | 37 | 365 | 22 | 0.018 | 0 | 0 | 0 |
| pequena | orchestration | 18 | 12/18 | 0.791 | 6 | 4 | 14/18 | 0 | 735506 | 0.111 | 57 | 670 | 20 | 0.012 | 0 | 0 | 1 |
| todas | single-agent | 39 | 26/39 | 0.883 | 13 | 6 | 31/39 | 0 | 990152 | 0.136 | 57 | 499 | 39 | 0.034 | 0 | 0 | 0 |
| todas | orchestration | 39 | 26/39 | 0.845 | 13 | 4 | 28/39 | 0 | 832830 | 0.124 | 57 | 669 | 36 | 0.031 | 0 | 0 | 1 |

## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)

| faixa | tarefas | +OR | −SA | empates | p (bilateral) |
|---|---:|---:|---:|---:|---:|
| grande | 3 | 1 | 0 | 2 | 1 |
| media | 4 | 0 | 1 | 3 | 1 |
| pequena | 6 | 0 | 1 | 5 | 1 |
| todas | 13 | 1 | 2 | 10 | 1 |

## C. Pareamentos por tarefa e sensibilidade da censura

| métrica | tarefas usadas | n | mediana da diferença | W+ | p |
|---|---|---:|---:|---:|---:|
| fração de ocultos passados | todas | 13 | 0 | 0 | 0.25 |
| fração de ocultos passados | ambos_resolvem_mediana | 8 | 0 | — | — |
| fração de ocultos passados | ambos_resolvem_ao_menos_uma | 8 | 0 | — | — |
| tokens | todas | 13 | -73719 | 31 | 0.3396 |
| tokens | ambos_resolvem_mediana | 8 | 130862 | 13 | 0.5469 |
| tokens | ambos_resolvem_ao_menos_uma | 8 | 130862 | 13 | 0.5469 |
| US$ | todas | 13 | -0.002 | 34 | 0.4548 |
| US$ | ambos_resolvem_mediana | 8 | 0.027 | 11 | 0.3828 |
| US$ | ambos_resolvem_ao_menos_uma | 8 | 0.027 | 11 | 0.3828 |
| chamadas | todas | 13 | 6 | 21 | 0.1694 |
| chamadas | ambos_resolvem_mediana | 8 | 14 | 6 | 0.2188 |
| chamadas | ambos_resolvem_ao_menos_uma | 8 | 14 | 6 | 0.2188 |
| parede (s) | todas | 13 | 215.098 | 20 | 0.0803 |
| parede (s) | ambos_resolvem_mediana | 8 | 216.64 | 4 | 0.0547 |
| parede (s) | ambos_resolvem_ao_menos_uma | 8 | 216.64 | 4 | 0.0547 |
| turnos | todas | 13 | 2 | 19.5 | 0.4492 |
| turnos | ambos_resolvem_mediana | 8 | 11 | 7 | 0.2656 |
| turnos | ambos_resolvem_ao_menos_uma | 8 | 11 | 7 | 0.2656 |
| linhas do patch | todas | 13 | -6 | 8.5 | 0.0527 |
| linhas do patch | ambos_resolvem_mediana | 8 | 0 | 6.5 | 0.875 |
| linhas do patch | ambos_resolvem_ao_menos_uma | 8 | 0 | 6.5 | 0.875 |
| ΔCC | todas | 13 | 0 | 14 | 0.6406 |
| ΔCC | ambos_resolvem_mediana | 8 | 0 | 2 | 0.75 |
| ΔCC | ambos_resolvem_ao_menos_uma | 8 | 0 | 2 | 0.75 |
| regressões | todas | 13 | 0 | 3 | 0.625 |
| regressões | ambos_resolvem_mediana | 8 | 0 | — | — |
| regressões | ambos_resolvem_ao_menos_uma | 8 | 0 | — | — |

## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)

- Ciclos do developer por run: {1: 20, 2: 7, 3: 8, 4: 2, 5: 2}; runs com 2+ ciclos (memória de trabalho usada): 19/39.
- Revisões semânticas (suíte verde): 112; aprovadas 45, reprovadas 67.
- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): 13 — [('attrs-0001', 1, 6), ('peewee-0001', 1, 2), ('pygments-0001', 1, 2), ('pygments-0001', 2, 2), ('sqlite-utils-0003', 2, 2), ('tomlkit-0001', 1, 9), ('tomlkit-0001', 2, 10), ('tomlkit-0001', 3, 8), ('tomlkit-0002', 1, 1), ('tomlkit-0002', 3, 1), ('tomlkit-0003', 1, 2), ('tomlkit-0005', 1, 5), ('tomlkit-0005', 3, 1)].
- Runs resolvidos com todas as revisões aprovadas: 13; runs não resolvidos com ao menos uma reprovação: 6.

## E. Componentes por run

| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| tomlkit-0002 | grande | 1 | orchestration | sim | 1/1 | 0 | 72 | 77 | 737023 | 0.109 | 381 | 2 | 16 | 0.043 | -0.598 | 0 | 0 | concluiu | 18·41 | RAA |
| tomlkit-0002 | grande | 1 | single-agent | não | 1/1 | 24 | 120 | 120 | 3912545 | 0.524 | 704 | 3 | 79 | 0.104 | -0.341 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 2 | orchestration | sim | 1/1 | 0 | 53 | 56 | 676317 | 0.097 | 472 | 2 | 16 | 0.065 | -0.837 | 0 | 0 | concluiu | 40 | A |
| tomlkit-0002 | grande | 2 | single-agent | não | 1/1 | 7 | 120 | 120 | 3838510 | 0.514 | 1097 | 2 | 97 | 0.253 | -0.676 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0002 | grande | 3 | orchestration | sim | 1/1 | 0 | 95 | 99 | 1432715 | 0.207 | 700 | 3 | 95 | 0.098 | -0.618 | 0 | 0 | concluiu | 41·41 | RA |
| tomlkit-0002 | grande | 3 | single-agent | não | 1/1 | 5 | 120 | 120 | 3458536 | 0.465 | 1080 | 3 | 125 | 0.139 | -0.399 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0003 | grande | 1 | orchestration | sim | 1/1 | 0 | 95 | 100 | 1288589 | 0.188 | 589 | 2 | 10 | -0.008 | 0 | 0 | 0 | concluiu | 41·41 | RRA |
| tomlkit-0003 | grande | 1 | single-agent | sim | 1/1 | 0 | 100 | 100 | 2655169 | 0.355 | 530 | 2 | 27 | -0.054 | -0.175 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 2 | orchestration | sim | 1/1 | 0 | 54 | 57 | 794029 | 0.118 | 606 | 2 | 4 | 0 | 0 | 0 | 0 | concluiu | 41 | A |
| tomlkit-0003 | grande | 2 | single-agent | sim | 1/1 | 0 | 87 | 87 | 2287472 | 0.306 | 800 | 1 | 8 | -0.008 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0003 | grande | 3 | orchestration | sim | 1/1 | 0 | 54 | 57 | 988964 | 0.145 | 628 | 2 | 5 | 0 | -0.015 | 0 | 0 | concluiu | 41 | A |
| tomlkit-0003 | grande | 3 | single-agent | sim | 1/1 | 0 | 120 | 120 | 3684206 | 0.492 | 1030 | 1 | 14 | 0.021 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0004 | grande | 1 | orchestration | não | 5/7 | 2 | 120 | 125 | 1845685 | 0.268 | 850 | 1 | 110 | 0.316 | -2.336 | 0 | 0 | budget: max_turns | 41·41·25 | RARA |
| tomlkit-0004 | grande | 1 | single-agent | não | 6/7 | 30 | 120 | 120 | 3933894 | 0.525 | 658 | 3 | 147 | 0.564 | -2.624 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 2 | orchestration | não | 5/7 | 58 | 120 | 124 | 1802514 | 0.26 | 1031 | 2 | 131 | 0.384 | -2.166 | 0 | 0 | budget: max_turns | 41·41·25 | RAA |
| tomlkit-0004 | grande | 2 | single-agent | não | 6/7 | 27 | 120 | 120 | 3757974 | 0.502 | 1120 | 4 | 175 | 0.082 | -1.53 | 0 | 0 | budget: max_turns | — | — |
| tomlkit-0004 | grande | 3 | orchestration | não | 5/7 | 2 | 120 | 125 | 2087641 | 0.304 | 1400 | 3 | 217 | 0.454 | -2.816 | 0 | 0 | budget: max_turns | 41·41·25 | RRRR |
| tomlkit-0004 | grande | 3 | single-agent | não | 0/7 | 9 | 120 | 120 | 4159422 | 0.557 | 1117 | 3 | 232 | 0.122 | -1.465 | 0 | 0 | budget: max_turns | — | — |
| attrs-0001 | media | 1 | orchestration | sim | 3/3 | 0 | 120 | 129 | 1245015 | 0.183 | 1091 | 2 | 34 | 0.156 | -0.546 | 0 | 0 | budget: max_turns | 20·24·24·26 | RARARRRR |
| attrs-0001 | media | 1 | single-agent | sim | 3/3 | 0 | 39 | 39 | 379000 | 0.053 | 234 | 2 | 35 | 0.084 | -0.328 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 2 | orchestration | sim | 3/3 | 0 | 54 | 57 | 742870 | 0.109 | 505 | 2 | 53 | 0.281 | -0.756 | 0 | 0 | concluiu | 41 | A |
| attrs-0001 | media | 2 | single-agent | sim | 3/3 | 0 | 49 | 49 | 599594 | 0.083 | 279 | 2 | 31 | 0.114 | -0.354 | 0 | 0 | tests_pass | — | — |
| attrs-0001 | media | 3 | orchestration | sim | 3/3 | 0 | 39 | 42 | 374968 | 0.058 | 501 | 2 | 35 | 0.186 | -0.506 | 0 | 0 | concluiu | 26 | A |
| attrs-0001 | media | 3 | single-agent | sim | 3/3 | 0 | 59 | 59 | 814044 | 0.112 | 505 | 2 | 75 | 0.192 | -0.516 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 1 | orchestration | sim | 4/4 | 0 | 73 | 78 | 832830 | 0.124 | 571 | 2 | 70 | 0.015 | -0.363 | 0 | 0 | concluiu | 19·41 | RRA |
| peewee-0001 | media | 1 | single-agent | sim | 4/4 | 0 | 57 | 57 | 859480 | 0.118 | 512 | 3 | 129 | 0.031 | -0.44 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 2 | orchestration | sim | 4/4 | 0 | 54 | 57 | 634134 | 0.095 | 443 | 3 | 55 | 0.005 | -0.159 | 0 | 0 | concluiu | 41 | A |
| peewee-0001 | media | 2 | single-agent | sim | 4/4 | 0 | 71 | 71 | 1211444 | 0.164 | 627 | 4 | 120 | 0.041 | -0.843 | 0 | 0 | tests_pass | — | — |
| peewee-0001 | media | 3 | orchestration | sim | 4/4 | 0 | 54 | 57 | 594684 | 0.091 | 640 | 1 | 58 | 0.003 | 0 | 0 | 0 | concluiu | 41 | A |
| peewee-0001 | media | 3 | single-agent | sim | 4/4 | 0 | 53 | 53 | 753258 | 0.107 | 701 | 3 | 99 | 0.02 | -0.405 | 0 | 0 | tests_pass | — | — |
| peewee-0002 | media | 1 | orchestration | não | 4/6 | 16 | 120 | 126 | 1409335 | 0.201 | 750 | 2 | 44 | 0.068 | -0.489 | 0 | 0 | budget: max_turns | 41·41·25 | RARAA |
| peewee-0002 | media | 1 | single-agent | não | 5/6 | 1 | 120 | 120 | 2875366 | 0.382 | 410 | 4 | 58 | 0.045 | -0.337 | 0 | 0 | budget: max_turns | — | — |
| peewee-0002 | media | 2 | orchestration | não | 3/6 | 3 | 120 | 127 | 1493779 | 0.216 | 1150 | 3 | 43 | 0.065 | -0.503 | 0 | 0 | budget: max_turns | 41·41·25 | RARARR |
| peewee-0002 | media | 2 | single-agent | não | 3/6 | 3 | 120 | 120 | 2834655 | 0.382 | 701 | 3 | 32 | 0.064 | -0.503 | 0 | 0 | budget: max_turns | — | — |
| peewee-0002 | media | 3 | orchestration | não | 3/6 | 3 | 120 | 127 | 1344320 | 0.198 | 921 | 3 | 33 | 0.064 | -0.503 | 0 | 0 | budget: max_turns | 41·41·25 | RARARA |
| peewee-0002 | media | 3 | single-agent | não | 5/6 | 1 | 116 | 116 | 2369507 | 0.32 | 842 | 5 | 51 | 0.039 | -0.263 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 1 | orchestration | sim | 12/12 | 0 | 50 | 53 | 886555 | 0.128 | 519 | 3 | 78 | 0.028 | -0.383 | 0 | 0 | concluiu | 37 | A |
| sqlite-utils-0003 | media | 1 | single-agent | sim | 12/12 | 0 | 53 | 53 | 998925 | 0.137 | 357 | 3 | 69 | 0.028 | -0.368 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 2 | orchestration | sim | 12/12 | 0 | 91 | 98 | 1206328 | 0.177 | 968 | 3 | 74 | 0.028 | -0.377 | 0 | 0 | concluiu | 12·36·30 | RARAA |
| sqlite-utils-0003 | media | 2 | single-agent | sim | 12/12 | 0 | 54 | 54 | 1055829 | 0.144 | 499 | 3 | 79 | 0.02 | -0.294 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0003 | media | 3 | orchestration | não | 11/12 | 1 | 54 | 57 | 1174277 | 0.172 | 714 | 2 | 88 | 0.097 | -1.226 | 0 | 0 | concluiu | 41 | A |
| sqlite-utils-0003 | media | 3 | single-agent | sim | 12/12 | 0 | 69 | 69 | 1295534 | 0.176 | 504 | 3 | 67 | 0.029 | -0.331 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 1 | orchestration | sim | 1/1 | 0 | 47 | 50 | 519292 | 0.076 | 434 | 1 | 7 | 0.308 | 4.866 | 0 | 0 | concluiu | 34 | A |
| peewee-0003 | pequena | 1 | single-agent | sim | 1/1 | 0 | 30 | 30 | 235157 | 0.033 | 296 | 1 | 5 | 0.154 | 1.806 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 2 | orchestration | sim | 1/1 | 0 | 54 | 57 | 587517 | 0.088 | 673 | 1 | 8 | 0.154 | 5.359 | 0 | 0 | concluiu | 41 | A |
| peewee-0003 | pequena | 2 | single-agent | sim | 1/1 | 0 | 31 | 31 | 233513 | 0.033 | 305 | 1 | 5 | 0.308 | 1.087 | 0 | 0 | tests_pass | — | — |
| peewee-0003 | pequena | 3 | orchestration | sim | 1/1 | 0 | 47 | 50 | 528802 | 0.079 | 523 | 1 | 7 | 0.154 | 3.668 | 0 | 0 | concluiu | 34 | A |
| peewee-0003 | pequena | 3 | single-agent | sim | 1/1 | 0 | 28 | 28 | 207437 | 0.031 | 406 | 1 | 8 | 0.154 | 5.408 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 1 | orchestration | sim | 2/2 | 0 | 49 | 54 | 841350 | 0.128 | 694 | 1 | 39 | 0 | 0 | 0 | 0 | concluiu | 16·20 | RRA |
| pygments-0001 | pequena | 1 | single-agent | sim | 2/2 | 0 | 29 | 29 | 505361 | 0.071 | 238 | 1 | 48 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 2 | orchestration | sim | 2/2 | 0 | 54 | 58 | 939782 | 0.139 | 1624 | 1 | 41 | 0 | 0 | 0 | 0 | concluiu | 24·17 | RRA |
| pygments-0001 | pequena | 2 | single-agent | sim | 2/2 | 0 | 39 | 39 | 691397 | 0.098 | 565 | 1 | 35 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| pygments-0001 | pequena | 3 | orchestration | sim | 2/2 | 0 | 43 | 46 | 730388 | 0.11 | 770 | 1 | 40 | 0 | 0 | 0 | 0 | concluiu | 30 | A |
| pygments-0001 | pequena | 3 | single-agent | sim | 2/2 | 0 | 26 | 26 | 441073 | 0.063 | 356 | 1 | 39 | 0 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 1 | orchestration | não | 1/5 | 4 | 41 | 44 | 442401 | 0.067 | 384 | 1 | 38 | 0.052 | 0 | 0 | 0 | concluiu | 28 | A |
| sqlite-utils-0001 | pequena | 1 | single-agent | não | 1/5 | 4 | 35 | 35 | 441128 | 0.062 | 248 | 1 | 55 | 0.034 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 2 | orchestration | não | 1/5 | 4 | 49 | 52 | 644331 | 0.096 | 834 | 1 | 34 | 0.065 | 0 | 0 | 0 | concluiu | 36 | A |
| sqlite-utils-0001 | pequena | 2 | single-agent | sim | 5/5 | 0 | 46 | 46 | 666319 | 0.094 | 421 | 1 | 44 | 0.021 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0001 | pequena | 3 | orchestration | não | 1/5 | 4 | 54 | 57 | 792195 | 0.119 | 669 | 1 | 70 | 0.066 | 0 | 0 | 1 | concluiu | 41 | A |
| sqlite-utils-0001 | pequena | 3 | single-agent | sim | 5/5 | 0 | 69 | 69 | 1329939 | 0.181 | 572 | 1 | 38 | 0.015 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 1 | orchestration | não | 8/11 | 3 | 54 | 57 | 752619 | 0.112 | 377 | 1 | 13 | 0.025 | 0 | 0 | 0 | concluiu | 41 | A |
| sqlite-utils-0002 | pequena | 1 | single-agent | não | 5/11 | 6 | 50 | 50 | 990152 | 0.136 | 308 | 1 | 37 | 0.043 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 2 | orchestration | não | 5/11 | 6 | 48 | 51 | 654676 | 0.096 | 554 | 1 | 39 | 0.031 | 0 | 0 | 0 | concluiu | 35 | A |
| sqlite-utils-0002 | pequena | 2 | single-agent | não | 5/11 | 6 | 57 | 57 | 1120776 | 0.156 | 469 | 1 | 47 | 0.099 | 0 | 0 | 0 | tests_pass | — | — |
| sqlite-utils-0002 | pequena | 3 | orchestration | não | 5/11 | 6 | 52 | 55 | 728804 | 0.107 | 550 | 1 | 26 | 0.006 | 0 | 0 | 0 | concluiu | 39 | A |
| sqlite-utils-0002 | pequena | 3 | single-agent | não | 5/11 | 6 | 47 | 47 | 681956 | 0.094 | 392 | 1 | 38 | 0.056 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 1 | orchestration | sim | 1/1 | 0 | 120 | 130 | 1127888 | 0.165 | 719 | 1 | 9 | -0.025 | 0 | 0 | 0 | budget: max_turns | 22·16·41·24·0 | RRRRRRRRR |
| tomlkit-0001 | pequena | 1 | single-agent | sim | 1/1 | 0 | 31 | 31 | 277744 | 0.039 | 177 | 1 | 9 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 2 | orchestration | sim | 1/1 | 0 | 120 | 131 | 975569 | 0.148 | 1231 | 1 | 9 | -0.025 | 0 | 0 | 0 | budget: max_turns | 27·23·15·17·12 | RRRRRRRRRR |
| tomlkit-0001 | pequena | 2 | single-agent | sim | 1/1 | 0 | 30 | 30 | 232189 | 0.034 | 215 | 1 | 9 | -0.025 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0001 | pequena | 3 | orchestration | sim | 1/1 | 0 | 120 | 129 | 1238606 | 0.18 | 1056 | 1 | 9 | -0.025 | 0 | 0 | 0 | budget: max_turns | 28·21·38·20 | RRRRRRRR |
| tomlkit-0001 | pequena | 3 | single-agent | sim | 1/1 | 0 | 49 | 49 | 580174 | 0.082 | 373 | 1 | 9 | 0.024 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 1 | orchestration | sim | 1/1 | 0 | 120 | 126 | 1281676 | 0.188 | 672 | 1 | 36 | -0.002 | 0 | 0 | 0 | budget: max_turns | 41·41·25 | RRRRR |
| tomlkit-0005 | pequena | 1 | single-agent | sim | 1/1 | 0 | 34 | 34 | 328643 | 0.046 | 225 | 1 | 9 | 0.012 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 2 | orchestration | sim | 1/1 | 0 | 54 | 57 | 660605 | 0.099 | 472 | 1 | 9 | 0.012 | 0 | 0 | 0 | concluiu | 41 | A |
| tomlkit-0005 | pequena | 2 | single-agent | sim | 1/1 | 0 | 89 | 89 | 1730042 | 0.236 | 636 | 1 | 9 | 0.012 | 0 | 0 | 0 | tests_pass | — | — |
| tomlkit-0005 | pequena | 3 | orchestration | sim | 1/1 | 0 | 77 | 81 | 740623 | 0.111 | 575 | 1 | 9 | 0.012 | 0 | 0 | 0 | concluiu | 41·23 | RA |
| tomlkit-0005 | pequena | 3 | single-agent | sim | 1/1 | 0 | 57 | 57 | 814342 | 0.113 | 426 | 1 | 9 | 0.012 | 0 | 0 | 0 | tests_pass | — | — |


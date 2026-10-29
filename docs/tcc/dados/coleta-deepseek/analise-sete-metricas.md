## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 9/13 | 9/13 | sinal exato bilateral | 1 | 3 | 1.0000 |
| 2 | Custo (tokens, mediana) | 706968 | 792110 | Wilcoxon exato bilateral | 13 | 8 | 0.5469 |
| 3 | Tempo (s, mediana) | 391.168 | 590.685 | Wilcoxon exato bilateral | 4 | 8 | 0.0547 |
| 5 | Δ complexidade (mediana) | 0.031 | 0.028 | Wilcoxon exato bilateral | 14 | 8 | 0.6406 |
| 4 | Consistência | 8/9 | 8/9 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 31/39 | 28/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 0 | 0; 0; 0 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.097984 × 0.119573; chamadas ao modelo (mediana) 51.500 × 57.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 1 | 599594 × 742870 | 143276 | 278.564 × 505.380 | 226.816 | 0.072 |
| `peewee-0001` | media | 1 × 1 | 859480 × 634134 | -225346 | 627.420 × 570.926 | -56.494 | -0.026 |
| `peewee-0002` | media | 0 × 0 | 2834655 × 1409335 | -1425320 | 701.417 × 920.565 | 219.148 | 0.020 |
| `peewee-0003` | pequena | 1 × 1 | 233513 × 528802 | 295289 | 304.858 × 523.040 | 218.182 | 0 |
| `pygments-0001` | pequena | 1 × 1 | 505361 × 841350 | 335989 | 356.101 × 770.004 | 413.903 | 0 |
| `sqlite-utils-0001` | pequena | 0.67 × 0 | 666319 × 644331 | -21988 | 420.901 × 668.897 | 247.996 | 0.044 |
| `sqlite-utils-0002` | pequena | 0 × 0 | 990152 × 728804 | -261348 | 392.076 × 550.319 | 158.243 | -0.031 |
| `sqlite-utils-0003` | media | 1 × 0.67 | 1055829 × 1174277 | 118448 | 498.651 × 713.749 | 215.098 | 0 |
| `tomlkit-0001` | pequena | 1 × 1 | 277744 × 1127888 | 850144 | 214.756 × 1056.012 | 841.256 | 0 |
| `tomlkit-0002` | grande | 0 × 1 | 3838510 × 737023 | -3101487 | 1080.447 × 472.328 | -608.119 | -0.074 |
| `tomlkit-0003` | grande | 1 × 1 | 2655169 × 988964 | -1666205 | 800.180 × 606.096 | -194.084 | 0.008 |
| `tomlkit-0004` | grande | 0 × 0 | 3933894 × 1845685 | -2088209 | 1117.246 × 1031.050 | -86.196 | 0.262 |
| `tomlkit-0005` | pequena | 1 × 1 | 814342 × 740623 | -73719 | 426.235 × 575.273 | 149.038 | 0 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 8 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por single-agent e orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent e orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 8 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por single-agent e orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent e orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


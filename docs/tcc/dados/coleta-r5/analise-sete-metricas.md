## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 6/13 | sinal exato bilateral | 3 | 8 | 0.7266 |
| 2 | Custo (tokens, mediana) | 314294 | 457404 | Wilcoxon exato bilateral | 5 | 5 | 0.6250 |
| 3 | Tempo (s, mediana) | 178.646 | 275.970 | Wilcoxon exato bilateral | 4 | 5 | 0.4375 |
| 5 | Δ complexidade (mediana) | 0.014 | 0.037 | Wilcoxon exato bilateral | 17 | 9 | 0.5703 |
| 4 | Consistência | 5/10 | 3/9 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 29/39 | 26/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 5 | 0; 0; 4 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.037177 × 0.063568; chamadas ao modelo (mediana) 29 × 48.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0.33 | 113319 × 250548 | 137229 | 77.745 × 82.768 | 5.023 | 0.006 |
| `peewee-0001` | media | 1 × 1 | 314294 × 198675 | -115619 | 286.941 × 275.970 | -10.971 | -0.001 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1476705 | -632074 | 308.632 × 438.082 | 129.450 | -0.012 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 234558 | 132965 | 178.646 × 596.051 | 417.405 | 0 |
| `pygments-0001` | pequena | 0.67 × 0.67 | 1288314 × 1411366 | 123052 | 605.645 × 632.804 | 27.159 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0 | 507709 × 421814 | -85895 | 130.210 × 254.546 | 124.336 | -0.007 |
| `sqlite-utils-0002` | pequena | 0 × 0.33 | 821788 × 537960 | -283828 | 160.809 × 107.665 | -53.144 | 0.026 |
| `sqlite-utils-0003` | media | 0.67 × 0 | 1012916 × 613921 | -398995 | 154.903 × 241.111 | 86.208 | 0.015 |
| `tomlkit-0001` | pequena | 1 × 0.67 | 121675 × 585650 | 463975 | 22.970 × 152.553 | 129.583 | 0 |
| `tomlkit-0002` | grande | 0.33 × 0.67 | 3265263 × 643036 | -2622227 | 295.301 × 85.889 | -209.412 | 0.072 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 457404 | -142453 | 113.449 × 59.886 | -53.563 | 0 |
| `tomlkit-0004` | grande | 0 × 0 | 4864896 × 2442376 | -2422520 | 366.977 × 240.639 | -126.338 | -0.405 |
| `tomlkit-0005` | pequena | 0 × 0.33 | 1031426 × 1781375 | 749949 | 377.161 × 187.222 | -189.939 | 0.057 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


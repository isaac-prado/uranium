## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 5/13 | sinal exato bilateral | 2 | 6 | 0.6875 |
| 2 | Custo (tokens, mediana) | 217984.500 | 399765 | Wilcoxon exato bilateral | 3 | 4 | 0.6250 |
| 3 | Tempo (s, mediana) | 146.047 | 331.964 | Wilcoxon exato bilateral | 1 | 4 | 0.2500 |
| 5 | Δ complexidade (mediana) | 0.014 | 0.012 | Wilcoxon exato bilateral | 18 | 9 | 0.6523 |
| 4 | Consistência | 5/10 | 4/10 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 29/39 | 22/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 5 | 0; 0; 1 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.026421 × 0.050662; chamadas ao modelo (mediana) 23 × 38.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0.33 | 113319 × 435779 | 322460 | 77.745 × 199.853 | 122.108 | 0 |
| `peewee-0001` | media | 1 × 1 | 314294 × 484183 | 169889 | 286.941 × 233.869 | -53.072 | 0.002 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1298420 | -810359 | 308.632 × 523.455 | 214.823 | -0.006 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 952803 | 851210 | 178.646 × 2015.603 | 1836.957 | 0.154 |
| `pygments-0001` | pequena | 0.67 × 0.33 | 1288314 × 802269 | -486045 | 605.645 × 517.293 | -88.352 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0.33 | 507709 × 499589 | -8120 | 130.210 × 216.657 | 86.447 | -0.044 |
| `sqlite-utils-0002` | pequena | 0 × 0.33 | 821788 × 1364165 | 542377 | 160.809 × 559.174 | 398.365 | 0.001 |
| `sqlite-utils-0003` | media | 0.67 × 0.33 | 1012916 × 1313994 | 301078 | 154.903 × 434.199 | 279.296 | 0.003 |
| `tomlkit-0001` | pequena | 1 × 1 | 121675 × 231237 | 109562 | 22.970 × 121.342 | 98.372 | 0 |
| `tomlkit-0002` | grande | 0.33 × 0.67 | 3265263 × 1506359 | -1758904 | 295.301 × 374.730 | 79.429 | 0.110 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 315347 | -284510 | 113.449 × 430.058 | 316.609 | 0 |
| `tomlkit-0004` | grande | 0 × 0 | 4864896 × 1715242 | -3149654 | 366.977 × 379.353 | 12.376 | -0.606 |
| `tomlkit-0005` | pequena | 0 × 0 | 1031426 × 1185112 | 153686 | 377.161 × 304.524 | -72.637 | 0.065 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 4 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 4 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por orchestration
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


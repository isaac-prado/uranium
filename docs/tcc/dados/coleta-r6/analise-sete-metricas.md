## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 6/13 | sinal exato bilateral | 2 | 6 | 0.6875 |
| 2 | Custo (tokens, mediana) | 314294 | 398257 | Wilcoxon exato bilateral | 0 | 5 | 0.0625 |
| 3 | Tempo (s, mediana) | 178.646 | 253.973 | Wilcoxon exato bilateral | 6 | 5 | 0.8125 |
| 5 | Δ complexidade (mediana) | 0.014 | 0.037 | Wilcoxon exato bilateral | 19 | 10 | 0.4316 |
| 4 | Consistência | 5/10 | 5/8 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 29/39 | 23/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 5 | 1; 0; 2 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.037177 × 0.056614; chamadas ao modelo (mediana) 29 × 38.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0.33 | 113319 × 820154 | 706835 | 77.745 × 440.625 | 362.880 | 0.012 |
| `peewee-0001` | media | 1 × 1 | 314294 × 398257 | 83963 | 286.941 × 253.973 | -32.968 | -0.001 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1488337 | -620442 | 308.632 × 539.531 | 230.899 | -0.008 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 157459 | 55866 | 178.646 × 577.295 | 398.649 | 0 |
| `pygments-0001` | pequena | 0.67 × 1 | 1288314 × 1367853 | 79539 | 605.645 × 292.227 | -313.418 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0 | 507709 × 1287164 | 779455 | 130.210 × 190.871 | 60.661 | -0.026 |
| `sqlite-utils-0002` | pequena | 0 × 0.67 | 821788 × 374524 | -447264 | 160.809 × 91.937 | -68.872 | 0.026 |
| `sqlite-utils-0003` | media | 0.67 × 0 | 1012916 × 2523739 | 1510823 | 154.903 × 533.052 | 378.149 | 0.150 |
| `tomlkit-0001` | pequena | 1 × 1 | 121675 × 190445 | 68770 | 22.970 × 68.930 | 45.960 | 0 |
| `tomlkit-0002` | grande | 0.33 × 0.33 | 3265263 × 1664077 | -1601186 | 295.301 × 318.084 | 22.783 | 0.106 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 866787 | 266930 | 113.449 × 143.418 | 29.969 | 0.011 |
| `tomlkit-0004` | grande | 0 × 0 | 4864896 × 2223369 | -2641527 | 366.977 × 253.944 | -113.033 | -0.397 |
| `tomlkit-0005` | pequena | 0 × 0 | 1031426 × 1678333 | 646907 | 377.161 × 319.245 | -57.916 | 0.049 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


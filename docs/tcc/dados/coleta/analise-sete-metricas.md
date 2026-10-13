## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 6/13 | sinal exato bilateral | 2 | 9 | 0.1797 |
| 2 | Custo (tokens, mediana) | 121675 | 278656 | Wilcoxon exato bilateral | 6 | 5 | 0.8125 |
| 3 | Tempo (s, mediana) | 113.449 | 126.966 | Wilcoxon exato bilateral | 2 | 5 | 0.1875 |
| 5 | Δ complexidade (mediana) | 0.025 | 0.024 | Wilcoxon exato bilateral | 17.500 | 8 | 0.9688 |
| 4 | Consistência | 6/11 | 3/8 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 26/39 | 23/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 11 | 0; 0; 39 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.015665 × 0.034437; chamadas ao modelo (mediana) 19 × 34.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0.67 | 113319 × 123745 | 10426 | 77.745 × 126.966 | 49.221 | 0 |
| `peewee-0001` | media | 1 × 0.67 | 314294 × 734495 | 420201 | 286.941 × 594.562 | 307.621 | 0 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1143904 | -964875 | 308.632 × 597.074 | 288.442 | -0.012 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 36407 | -65186 | 178.646 × 194.213 | 15.567 | 0 |
| `pygments-0001` | pequena | 1 × 0 | 8104295 × 941898 | -7162397 | 1510.780 × 865.807 | -644.973 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0 | 507709 × 361446 | -146263 | 130.210 × 129.561 | -0.649 | -0.013 |
| `sqlite-utils-0002` | pequena | 0.33 × 1 | 8136340 × 1754943 | -6381397 | 1230.099 × 456.337 | -773.762 | -0.018 |
| `sqlite-utils-0003` | media | 0.67 × 0 | 1012916 × 884941 | -127975 | 154.903 × 158.138 | 3.235 | -0.007 |
| `tomlkit-0001` | pequena | 1 × 0.67 | 121675 × 278656 | 156981 | 22.970 × 119.296 | 96.326 | 0.024 |
| `tomlkit-0002` | grande | 0.33 × 0.33 | 3265263 × 1918293 | -1346970 | 295.301 × 295.153 | -0.148 | 0.018 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 290700 | -309157 | 113.449 × 76.973 | -36.476 | 0 |
| `tomlkit-0004` | grande | 0 × 0 | 3913926 × 1924723 | -1989203 | 276.895 × 250.237 | -26.658 | -1.168 |
| `tomlkit-0005` | pequena | 0 × 0.33 | 1031426 × 1466274 | 434848 | 377.161 × 324.413 | -52.748 | 0.062 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por orchestration
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


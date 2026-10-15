## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 9/13 | sinal exato bilateral | 3 | 5 | 1.0000 |
| 2 | Custo (tokens, mediana) | 314294 | 769526 | Wilcoxon exato bilateral | 7 | 7 | 0.2969 |
| 3 | Tempo (s, mediana) | 154.903 | 284.192 | Wilcoxon exato bilateral | 8 | 7 | 0.3750 |
| 5 | Δ complexidade (mediana) | 0.014 | 0.010 | Wilcoxon exato bilateral | 13 | 7 | 0.9375 |
| 4 | Consistência | 5/10 | 5/10 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 29/39 | 23/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 5 | 0; 0; 10 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.037177 × 0.103753; chamadas ao modelo (mediana) 29 × 61.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0.67 | 113319 × 214263 | 100944 | 77.745 × 467.788 | 390.043 | 0 |
| `peewee-0001` | media | 1 × 1 | 314294 × 265226 | -49068 | 286.941 × 270.693 | -16.248 | -0.002 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1284448 | -824331 | 308.632 × 558.660 | 250.028 | -0.011 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 118844 | 17251 | 178.646 × 108.765 | -69.881 | 0 |
| `pygments-0001` | pequena | 0.67 × 1 | 1288314 × 883706 | -404608 | 605.645 × 365 | -240.645 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0.33 | 507709 × 709873 | 202164 | 130.210 × 230.274 | 100.064 | 0 |
| `sqlite-utils-0002` | pequena | 0 × 0.67 | 821788 × 864819 | 43031 | 160.809 × 368.105 | 207.296 | 0.014 |
| `sqlite-utils-0003` | media | 0.67 × 0.67 | 1012916 × 1327799 | 314883 | 154.903 × 465.339 | 310.436 | -0.018 |
| `tomlkit-0001` | pequena | 1 × 1 | 121675 × 769526 | 647851 | 22.970 × 232.995 | 210.025 | 0 |
| `tomlkit-0002` | grande | 0.33 × 0.67 | 3265263 × 752819 | -2512444 | 295.301 × 133.144 | -162.157 | 0.018 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 1197082 | 597225 | 113.449 × 284.192 | 170.743 | 0 |
| `tomlkit-0004` | grande | 0 × 0 | 4864896 × 2348749 | -2516147 | 366.977 × 290.078 | -76.899 | -0.804 |
| `tomlkit-0005` | pequena | 0 × 0 | 1031426 × 1190387 | 158961 | 377.161 × 690.895 | 313.734 | 0.040 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 7 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 7 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 7/13 | sinal exato bilateral | 3 | 7 | 1.0000 |
| 2 | Custo (tokens, mediana) | 457075.500 | 361494.500 | Wilcoxon exato bilateral | 9 | 6 | 0.8438 |
| 3 | Tempo (s, mediana) | 166.774 | 214.203 | Wilcoxon exato bilateral | 9 | 6 | 0.8438 |
| 5 | Δ complexidade (mediana) | 0.014 | 0.025 | Wilcoxon exato bilateral | 16 | 8 | 0.8438 |
| 4 | Consistência | 5/10 | 5/8 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 29/39 | 25/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 5 | 0; 0; 5 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.052783 × 0.053649; chamadas ao modelo (mediana) 35.500 × 42.500.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0 | 113319 × 209963 | 96644 | 77.745 × 125.836 | 48.091 | 0 |
| `peewee-0001` | media | 1 × 0.67 | 314294 × 299436 | -14858 | 286.941 × 375.266 | 88.325 | -0.001 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1034731 | -1074048 | 308.632 × 683.204 | 374.572 | -0.009 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 143471 | 41878 | 178.646 × 190.464 | 11.818 | 0 |
| `pygments-0001` | pequena | 0.67 × 0.67 | 1288314 × 1718143 | 429829 | 605.645 × 287.638 | -318.007 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0 | 507709 × 245105 | -262604 | 130.210 × 121.559 | -8.651 | -0.013 |
| `sqlite-utils-0002` | pequena | 0 × 0.33 | 821788 × 537883 | -283905 | 160.809 × 131.016 | -29.793 | 0.014 |
| `sqlite-utils-0003` | media | 0.67 × 1 | 1012916 × 938851 | -74065 | 154.903 × 237.942 | 83.039 | 0 |
| `tomlkit-0001` | pequena | 1 × 1 | 121675 × 212988 | 91313 | 22.970 × 62.415 | 39.445 | -0.025 |
| `tomlkit-0002` | grande | 0.33 × 1 | 3265263 × 606970 | -2658293 | 295.301 × 94.669 | -200.632 | 0.018 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 423553 | -176304 | 113.449 × 72.606 | -40.843 | 0 |
| `tomlkit-0004` | grande | 0 × 0 | 4864896 × 1985759 | -2879137 | 366.977 × 210.442 | -156.535 | -0.782 |
| `tomlkit-0005` | pequena | 0 × 0 | 1031426 × 1265118 | 233692 | 377.161 × 228.542 | -148.619 | 0.065 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 6 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent e orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 6 tarefa(s) no teste.
- `attrs-0001` (faixa media): não resolvida por orchestration
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent e orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


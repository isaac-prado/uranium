## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 9/13 | 10/13 | sinal exato bilateral | 3 | 5 | 1.0000 |
| 2 | Custo (tokens, mediana) | 1002483 | 525005 | Wilcoxon exato bilateral | 1 | 7 | 0.0312 |
| 3 | Tempo (s, mediana) | 154.522 | 180.059 | Wilcoxon exato bilateral | 11 | 7 | 0.6875 |
| 5 | Δ complexidade (mediana) | 0.028 | 0.015 | Wilcoxon exato bilateral | 27 | 10 | 1.0000 |
| 4 | Consistência | 8/11 | 9/11 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 27/39 | 32/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 0 | 0; 0; 0 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.074552 × 0.062445; chamadas ao modelo (mediana) 47 × 46.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 1 | 508196 × 525005 | 16809 | 127.496 × 223.359 | 95.863 | 0.083 |
| `peewee-0001` | media | 1 × 1 | 1333880 × 401883 | -931997 | 356.308 × 165.901 | -190.407 | -0.015 |
| `peewee-0002` | media | 0.67 × 0 | 2994080 × 699039 | -2295041 | 238.661 × 420.049 | 181.388 | -0.036 |
| `peewee-0003` | pequena | 1 × 1 | 161743 × 140639 | -21104 | 154.522 × 180.059 | 25.537 | 0.054 |
| `pygments-0001` | pequena | 0.33 × 1 | 5161035 × 1154778 | -4006257 | 342.907 × 465.695 | 122.788 | 0 |
| `sqlite-utils-0001` | pequena | 0 × 1 | 1119260 × 543043 | -576217 | 170.285 × 140 | -30.285 | -0.025 |
| `sqlite-utils-0002` | pequena | 1 × 1 | 1019228 × 550927 | -468301 | 176.873 × 153.539 | -23.334 | -0.006 |
| `sqlite-utils-0003` | media | 1 × 1 | 1002483 × 936631 | -65852 | 133.676 × 339.497 | 205.821 | -0.008 |
| `tomlkit-0001` | pequena | 1 × 1 | 260050 × 123460 | -136590 | 55.303 × 58.708 | 3.405 | 0 |
| `tomlkit-0002` | grande | 0.33 × 0.67 | 3332904 × 1883175 | -1449729 | 298.651 × 302.535 | 3.884 | -0.010 |
| `tomlkit-0003` | grande | 1 × 1 | 3068812 × 554880 | -2513932 | 271.478 × 254.645 | -16.833 | 0 |
| `tomlkit-0004` | grande | 0 × 0 | 6819305 × 2193223 | -4626082 | 457.122 × 357.694 | -99.428 | 0.097 |
| `tomlkit-0005` | pequena | 1 × 0.33 | 936678 × 1451827 | 515149 | 129.089 × 349.209 | 220.120 | -0.026 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 7 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 7 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent
- `tomlkit-0002` (faixa grande): não resolvida por single-agent
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 9/13 | sinal exato bilateral | 3 | 6 | 1.0000 |
| 2 | Custo (tokens, mediana) | 314294 | 350684 | Wilcoxon exato bilateral | 12 | 7 | 0.8125 |
| 3 | Tempo (s, mediana) | 154.903 | 154.028 | Wilcoxon exato bilateral | 11 | 7 | 0.6875 |
| 5 | Δ complexidade (mediana) | 0.014 | 0.013 | Wilcoxon exato bilateral | 26 | 11 | 0.5615 |
| 4 | Consistência | 5/10 | 4/10 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 29/39 | 29/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 5 | 1; 0; 28 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.037177 × 0.046877; chamadas ao modelo (mediana) 29 × 42.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0.67 | 113319 × 350684 | 237365 | 77.745 × 83.466 | 5.721 | 0.072 |
| `peewee-0001` | media | 1 × 0.67 | 314294 × 287986 | -26308 | 286.941 × 219.406 | -67.535 | -0.002 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1027916 | -1080863 | 308.632 × 573.173 | 264.541 | -0.011 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 123811 | 22218 | 178.646 × 154.028 | -24.618 | 0 |
| `pygments-0001` | pequena | 0.67 × 1 | 1288314 × 1238202 | -50112 | 605.645 × 316.960 | -288.685 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0.67 | 507709 × 759277 | 251568 | 130.210 × 179.851 | 49.641 | -0.050 |
| `sqlite-utils-0002` | pequena | 0 × 0.67 | 821788 × 543046 | -278742 | 160.809 × 135.328 | -25.481 | 0.020 |
| `sqlite-utils-0003` | media | 0.67 × 0.67 | 1012916 × 871244 | -141672 | 154.903 × 230.029 | 75.126 | -0.025 |
| `tomlkit-0001` | pequena | 1 × 1 | 121675 × 201015 | 79340 | 22.970 × 48.141 | 25.171 | -0.025 |
| `tomlkit-0002` | grande | 0.33 × 0.33 | 3265263 × 1029701 | -2235562 | 295.301 × 178.914 | -116.387 | 0.062 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 463586 | -136271 | 113.449 × 91.176 | -22.273 | 0.017 |
| `tomlkit-0004` | grande | 0 × 0 | 4864896 × 1760696 | -3104200 | 366.977 × 175.986 | -190.991 | -0.814 |
| `tomlkit-0005` | pequena | 0 × 0 | 1031426 × 1390350 | 358924 | 377.161 × 270.064 | -107.097 | -0.021 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 7 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `tomlkit-0002` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 7 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `tomlkit-0002` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent e orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


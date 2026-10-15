## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 8/13 | 7/13 | sinal exato bilateral | 2 | 6 | 0.6875 |
| 2 | Custo (tokens, mediana) | 121675 | 219388 | Wilcoxon exato bilateral | 5 | 5 | 0.6250 |
| 3 | Tempo (s, mediana) | 113.449 | 245.157 | Wilcoxon exato bilateral | 1 | 5 | 0.1250 |
| 5 | Δ complexidade (mediana) | 0.014 | 0.028 | Wilcoxon exato bilateral | 15 | 8 | 0.7422 |
| 4 | Consistência | 5/10 | 5/11 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 29/39 | 28/39 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 5 | 0; 0; 3 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.015665 × 0.036146; chamadas ao modelo (mediana) 19 × 25.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `attrs-0001` | media | 1 × 0.67 | 113319 × 137070 | 23751 | 77.745 × 122.690 | 44.945 | 0 |
| `peewee-0001` | media | 1 × 1 | 314294 × 219388 | -94906 | 286.941 × 245.157 | -41.784 | -0.001 |
| `peewee-0002` | media | 0.67 × 0 | 2108779 × 1277112 | -831667 | 308.632 × 502.910 | 194.278 | -0.012 |
| `peewee-0003` | pequena | 1 × 1 | 101593 × 73415 | -28178 | 178.646 × 321.665 | 143.019 | 0 |
| `pygments-0001` | pequena | 0.67 × 0.33 | 1288314 × 964087 | -324227 | 605.645 × 241.143 | -364.502 | 0 |
| `sqlite-utils-0001` | pequena | 0.33 × 0.33 | 507709 × 436475 | -71234 | 130.210 × 182.102 | 51.892 | -0.037 |
| `sqlite-utils-0002` | pequena | 0 × 1 | 821788 × 291012 | -530776 | 160.809 × 135.617 | -25.192 | 0.020 |
| `sqlite-utils-0003` | media | 0.67 × 0.33 | 1012916 × 2245107 | 1232191 | 154.903 × 921.758 | 766.855 | 0.055 |
| `tomlkit-0001` | pequena | 1 × 1 | 121675 × 364982 | 243307 | 22.970 × 136.037 | 113.067 | 0 |
| `tomlkit-0002` | grande | 0.33 × 0.33 | 3265263 × 1261619 | -2003644 | 295.301 × 234.262 | -61.039 | 0.054 |
| `tomlkit-0003` | grande | 1 × 1 | 599857 × 256670 | -343187 | 113.449 × 358.778 | 245.329 | 0 |
| `tomlkit-0004` | grande | 0 × 0 | 4864896 × 2300846 | -2564050 | 366.977 × 680.756 | 313.779 | -0.387 |
| `tomlkit-0005` | pequena | 0 × 0.67 | 1031426 × 921262 | -110164 | 377.161 × 316.887 | -60.274 | 0.069 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 5 tarefa(s) no teste.
- `peewee-0002` (faixa media): não resolvida por orchestration
- `pygments-0001` (faixa pequena): não resolvida por orchestration
- `sqlite-utils-0001` (faixa pequena): não resolvida por single-agent e orchestration
- `sqlite-utils-0002` (faixa pequena): não resolvida por single-agent
- `sqlite-utils-0003` (faixa media): não resolvida por orchestration
- `tomlkit-0002` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0004` (faixa grande): não resolvida por single-agent e orchestration
- `tomlkit-0005` (faixa pequena): não resolvida por single-agent

**5. Variação da complexidade** — censura `ambos_com_valor`; 13 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

78 de 78 execução(ões) admitida(s).

Nenhum par quebrado.


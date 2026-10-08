## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 2/2 | 2/2 | sinal exato bilateral | — | 0 | — |
| 2 | Custo (tokens, mediana) | 321306.500 | 321844.500 | Wilcoxon exato bilateral | 1 | 2 | 1.0000 |
| 3 | Tempo (s, mediana) | 49.058 | 111.557 | Wilcoxon exato bilateral | 0 | 2 | 0.5000 |
| 5 | Δ complexidade (mediana) | 0.043 | -0.015 | Wilcoxon exato bilateral | 0 | 2 | 0.5000 |
| 4 | Consistência | 2/2 | 2/2 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 1/2 | 1/2 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 0 | 0; 0; 0 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) 0.037491 × 0.040005; chamadas ao modelo (mediana) 25.500 × 39.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `tomlkit-0001` | pequena | 1 × 1 | 128235 × 248593 | 120358 | 26.460 × 105.567 | 79.107 | -0.074 |
| `tomlkit-0002` | grande | 1 × 1 | 514378 × 395096 | -119282 | 71.655 × 117.547 | 45.892 | -0.044 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 2 tarefa(s) no teste.
- nenhuma tarefa excluída.

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 2 tarefa(s) no teste.
- nenhuma tarefa excluída.

**5. Variação da complexidade** — censura `ambos_com_valor`; 2 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

4 de 4 execução(ões) admitida(s).

Nenhum par quebrado.


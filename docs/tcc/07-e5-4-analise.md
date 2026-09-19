## E5 item 4 — Script de análise: as sete métricas com teste de sinal e Wilcoxon

Exigência: script que lê os `result.json`, agrega por tarefa, aplica a censura declarada e emite as sete métricas com teste de sinal e Wilcoxon, reportando a faixa ao lado de cada par; sem `scipy`, com testes exatos para n ≤ 12. Base: [03-metricas.md](03-metricas.md) seções 2 e 3.

### Diff resumido

Dois arquivos novos; nada existente foi alterado. `harness/` e `src/` intocados.

| arquivo | o que faz |
|---|---|
| `scripts/analyze_results.py` | CLI `analyze_results.py <raízes> [--markdown] [--json saida.json] [--tasks-dir tasks/]`. Descobre todo `result.json` recursivamente (mesmo padrão de `find_runs` em [scripts/context_accounting.py](../../scripts/context_accounting.py)), aplica os três portões de admissão da seção 3, resolve a faixa de cada tarefa, agrega por `(task_id, arm)` pela mediana das repetições, emite as sete métricas em Markdown e em JSON. Os dois testes estatísticos são funções puras no próprio arquivo: `teste_sinal` (binomial exato bilateral) e `wilcoxon` (signed-rank exato bilateral por enumeração das 2^n atribuições de sinal), com `postos_medios` para os empates. |
| `tests/test_analyze_results.py` | 54 testes: os estatísticos contra valores fechados calculados à mão, os três portões de admissão, a resolução da faixa, a agregação por mediana, e um estudo sintético completo de ponta a ponta. |

Fontes de número no script, todas de arquivo: `resolved`, `resolved_blocked_by_cheat`, `oracle.*.network_isolated`, `cheat.critical_count`, `quality.cc_mean_delta`, `cost.tokens_total`, `cost.cost_usd`, `cost.llm_calls`, `cost.tool_calls`, `cost.wall_seconds`, `process.stop_reason`, `process.tool_denials`, `provenance.provider_requested`, `provenance.providers_served`, `faixa`, e o `events.jsonl` ao lado.

### Testes que provam

**Os estatísticos, contra valores fechados** (não contra outra biblioteca — é justamente o que não existe aqui):

| caso | esperado | de onde vem |
|---|---|---|
| sinal, 8 de 8 na mesma direção | p = 2·(1/2)^8 = 0,0078125 | binomial exato |
| sinal, 6 de 8 | p = 2·(C(8,0)+C(8,1)+C(8,2))/2^8 = 2·37/256 = 0,2890625 | binomial exato |
| sinal, 8 positivas e 4 empates | p = 0,0078125, `n = 8`, `n_empates = 4` | empates fora da conta |
| Wilcoxon, n = 6 todas positivas | p = 2/64 = 0,03125 | só duas das 64 atribuições são tão extremas |
| Wilcoxon, as mesmas 6 mais uma diferença nula | idêntico ao de n = 6, com `n_empates = 1` | zero descartado |
| Wilcoxon com empate de postos, d = [1, 1, −2, 3] | postos 1,5; 1,5; 3; 4 → W+ = 7, W = 3, p = 10/16 = 0,625 | enumeração manual das 16 somas, conferida também por uma força bruta independente escrita no teste |
| n = 0, só empates, n = 1 | devolvem `p = None` ou `p = 1`, sem exceção | — |
| n = 12 | p = 2/4096, e roda instantâneo | 2^12 atribuições |

**Os portões de admissão**: provedor divergente do pino, avaliação sem rede isolada, `events.jsonl` com dois `run_end`, `events.jsonl` com linha fora do esquema de evento, `events.jsonl` com linha não-JSON — cada um reprova com o motivo por escrito; run sem `events.jsonl` ao lado não é reprovado pelo portão 3; run reprovado sai da agregação.

**A faixa**: lida do `result.json` quando existe, do `tasks/<id>/task.json` quando o `result.json` traz `null` (que é o que o avaliador grava para tarefa sem faixa), e `?` quando não existe em lugar nenhum — nunca inventada.

**Ponta a ponta**: estudo sintético em `tmp_path` com 14 execuções — duas tarefas completas (2 braços × 3 repetições) e uma terceira com o par quebrado por provedor divergente. Confere as sete métricas número a número, a lista de censura com o motivo de cada tarefa excluída, o par quebrado e a faixa ao lado de cada par. As fixtures são validadas contra `harness/schema/result.schema.json` e `harness/schema/event.schema.json` reais, e a versão do esquema vem de `harness.RESULT_SCHEMA_VERSION`: se o formato mudar, o teste quebra em vez de testar um formato que não existe mais.

Não foi gerado um `result.json` pelo harness dentro deste arquivo de teste: `evaluate_run` exige espelho do repositório-semente, venv própria e a suíte do upstream inteira (minutos por chamada), e o que se quer provar aqui — que o leitor lê o formato real — já está provado pela validação contra o esquema mais a execução sobre os quatro `result.json` de 11/09 registrada abaixo.

### Última linha do pytest

```
54 passed in 0.15s
```
(`.venv/bin/python -m pytest tests/test_analyze_results.py -q`)

Suíte inteira (`.venv/bin/python -m pytest -q`):

```
2 failed, 440 passed in 96.72s (0:01:36)
```

As duas falhas são `tests/test_seed_repos.py::TestSuiteVerdeNoPontoDePartida::test_roda_inteira_e_passa[peewee]` e `tests/test_seed_repos.py::test_peewee_sem_alvo_declarado_coletaria_quase_nada`: a suíte do peewee coleta zero teste no espelho desta máquina (`exit_code=5`). É estado do espelho/venv do peewee, não tem relação com este item — nenhum dos dois arquivos novos é importado por `test_seed_repos.py`.

### Decisões de método

**A comparação é sempre `orchestration` − `single-agent`.** Um sinal só tem significado se a direção estiver fixada; fica declarada no cabeçalho de toda tabela emitida.

**"Resolvida por ambos" = agregado por tarefa resolvido nos dois braços, não repetição a repetição.** A unidade de análise é a tarefa ([03-metricas.md](03-metricas.md), seção 2), e o valor de uma tarefa num braço é a mediana das repetições; censurar por repetição misturaria as duas unidades. Consequência assumida: uma tarefa resolvida em 2 de 3 repetições nos dois braços entra no teste de custo com a mediana das três, inclusive a que falhou — que é o que "mediana das repetições" significa, e é a definição que não privilegia nenhum dos braços.

**Resolvida num braço = maioria estrita das repetições admitidas.** Com 3 repetições isso é exatamente a mediana de 0/1. A regra vale para qualquer número de repetições: se um par de repetições der 0,5 (o que só acontece quando um run cai num portão e sobram duas), o desempate é para baixo. A fração das repetições resolvidas é reportada ao lado em toda tabela, então a informação que a maioria descarta não se perde.

**Empates.** No teste de sinal, diferença zero é ausência de informação sobre a direção: sai da conta e é reportada em `n_empates` — com 12 tarefas e muitas concordâncias, o `n` efetivo é o número que decide o poder do teste, e escondê-lo seria esconder por que o p é alto. No Wilcoxon, a diferença zero é descartada pela regra clássica; o empate entre MÓDULOS de diferenças diferentes de zero recebe posto médio, e a enumeração é feita sobre os postos que de fato ocorreram (com as médias), de modo que a distribuição nula usada é a do conjunto observado de postos — é assim que o empate fica tratado corretamente sem correção assintótica.

**Agregação.** Mediana, não média, porque o desenho declara mediana e porque três repetições com um corte de orçamento no meio têm média dominada pelo teto. Campo ausente numa repetição (por exemplo `quality.cc_mean_delta` nulo quando o radon não mediu) não apaga a tarefa: a mediana é tirada das repetições que têm valor, e só vira `None` se nenhuma tiver.

**Censura por métrica, e declarada na saída.** As métricas 2 e 3 usam `resolvidas_por_ambos`, pelo motivo da seção 2 do 03-metricas (execução cortada por limite custa o teto, não o custo de resolver). A métrica 5 é exploratória e usa `ambos_com_valor`: censurar a complexidade por resolução mediria só o subconjunto fácil. Toda tarefa excluída sai listada com o motivo, com a faixa ao lado.

**Portão 1 estrito.** `providers_served` vazio, ou `provider_requested` ausente, reprovam: o pino não é verificável, e portão de admissão que passa na dúvida não é portão.

**Portão 3 só quando há trilha.** Se não existe `events.jsonl` ao lado do `result.json`, o portão não se aplica (não reprova). Sem `jsonschema` instalado o script cai para a validação mínima — uma linha, um objeto JSON, um único `run_end` — e não reprova por não ter conseguido validar o esquema. No `.venv` deste repositório o `jsonschema` está presente e a validação é a completa.

**Par quebrado é reportado, não remendado.** A repetição k de um braço e a k do outro rodam com a mesma semente e formam um par. Quando um dos dois cai num portão, o par deixa de existir: o script lista tarefa, repetição e o estado de cada lado, e o braço sobrevivente continua na agregação com uma repetição a menos. É o insumo do mecanismo de reexecução (item 2 do E5).

**Enumeração, não aproximação.** `wilcoxon` recusa n > 20 com `ValueError` em vez de cair para a aproximação normal. O desenho tem 12 tarefas; se algum dia chegar n maior, a escolha do método passa a ser uma decisão de método, e tem de ser tomada por escrito, não por um `if` silencioso.

### Portão G7 do cronograma

[04-cronograma.md](04-cronograma.md) pede, no G7, que o script rode sobre os 4 `result.json` existentes e emita as sete métricas, o teste de sinal e o Wilcoxon, "mesmo sem significado". Os quatro arquivos de 11/09/2026 (2 tarefas × 2 braços × 1 repetição) foram localizados e o script rodou sobre eles. **As quatro execuções passaram nos três portões de admissão**: provedor servido igual ao pinado (`DeepInfra`) nas quatro, rede isolada nas três suítes do oráculo nas quatro, e `events.jsonl` válido com um único `run_end` nas quatro. Nenhum par quebrado.

Saída literal do comando:

```
## As sete métricas (single-agent × orchestration)

Diferença e sinal do teste sempre `orchestration` − `single-agent`. Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.

| # | Métrica | single-agent | orchestration | Teste | estatística | n | p |
|---|---|---|---|---|---|---|---|
| 1 | Taxa de resolução (tarefas) | 0/2 | 0/2 | sinal exato bilateral | — | 0 | — |
| 2 | Custo (tokens, mediana) | — | — | Wilcoxon exato bilateral | — | 0 | — |
| 3 | Tempo (s, mediana) | — | — | Wilcoxon exato bilateral | — | 0 | — |
| 5 | Δ complexidade (mediana) | 0.036 | 0.071 | Wilcoxon exato bilateral | 1 | 2 | 1.0000 |
| 4 | Consistência | 0/0 | 0/0 | descritivo | — | — | — |
| 6 | Conclusão sem corte | 1/2 | 2/2 | descritivo | — | — | — |
| 7 | Violações (crít.; bloq.; negações) | 0; 0; 0 | 0; 0; 2 | descritivo | — | — | — |

Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares (mediana) — × —; chamadas ao modelo (mediana) — × —.

## Por tarefa

| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |
|---|---|---|---|---|---|---|---|
| `sqlite-utils-0001` | media | 0 × 0 | 267626 × 467821 | 200195 | 75.954 × 158.224 | 82.270 | -0.002 |
| `tomlkit-0001` | ? | 0 × 0 | 363923 × 338901 | -25022 | 162.816 × 163.750 | 0.934 | 0.073 |

## Censura declarada

**2. Custo computacional** — censura `resolvidas_por_ambos`; 0 tarefa(s) no teste.
- `sqlite-utils-0001` (faixa media): não resolvida por single-agent e orchestration
- `tomlkit-0001` (faixa ?): não resolvida por single-agent e orchestration

**3. Tempo até a solução** — censura `resolvidas_por_ambos`; 0 tarefa(s) no teste.
- `sqlite-utils-0001` (faixa media): não resolvida por single-agent e orchestration
- `tomlkit-0001` (faixa ?): não resolvida por single-agent e orchestration

**5. Variação da complexidade** — censura `ambos_com_valor`; 2 tarefa(s) no teste.
- nenhuma tarefa excluída.

## Portões de admissão

4 de 4 execução(ões) admitida(s).

Nenhum par quebrado.
```

Como ler isso, e o que NÃO ler: nenhuma das duas tarefas foi resolvida por nenhum dos dois braços (dados com o defeito de prompt de 11/09), então a censura declarada esvazia as métricas 2 e 3 — que é exatamente o comportamento pedido, e é a demonstração de que a censura funciona. Os traços nas colunas de custo e tempo não são dado faltante: são a censura agindo. O único teste com n > 0 é o Wilcoxon exploratório da complexidade, com n = 2 e p = 1, sem significado nenhum. A faixa `?` do `tomlkit-0001` é fiel: `tasks/tomlkit-0001/task.json` não declara faixa, e o script não inventa uma. A métrica 7 mostra 2 negações de ferramenta no braço orquestrado, contra 0 no agente único; a métrica 6 mostra uma execução do agente único encerrada por `budget: max_turns (40 >= 40)`.

Os quatro arquivos não estão versionados neste repositório (não há `runs/` na árvore). O G7 está cumprido quanto ao script; para deixá-lo reprodutível pelo leitor do TCC, os quatro `result.json` (com `manifest.json`, `summary.json` e `events.jsonl` ao lado) precisam ser trazidos para um caminho versionado ou publicado, e o comando reexecutado a partir dele:

```
uv run python scripts/analyze_results.py <raiz dos runs> --markdown
```

### Limitações

1. **O que o script emite hoje não tem poder estatístico nenhum**, e isso não é defeito dele: são 2 tarefas × 1 repetição. O Wilcoxon exato precisa de ao menos 6 pares para poder chegar a 5% ([03-metricas.md](03-metricas.md), seção 2), e o teste de sinal, com 12 tarefas e muitas concordâncias, não alcança 5% em nenhum cenário. O script reporta `n` ao lado de todo p exatamente para que isso fique visível.
2. **A faixa depende de dado que só existe pela metade.** `tomlkit-0001` não declara faixa; os `result.json` de 11/09 são anteriores à propagação da faixa até o resultado. Até a remineração do E3 fechar as 12 tarefas com faixa declarada, a coluna de faixa vai ter `?`.
3. **A censura das métricas 2 e 3 depende da seleção de tarefas.** Se menos de 6 tarefas forem resolvidas pelos dois braços, o Wilcoxon fica impossível de atingir 5% por construção; o script emite a lista de excluídas, mas não pode consertar a seleção.
4. **Consistência com 3 repetições é grossa** — assume os valores 0, 1/3, 2/3 e 1, e nada entre eles.
5. **`process.stop_reason` nulo conta como "sem corte"** na métrica 6, pela definição literal ("não iniciado em `budget:`"). O script reporta `sem_stop_reason` por braço no JSON para que esse caso não se esconda dentro do numerador.
6. **A métrica 7 soma contagens, sem teste.** É modo de falha, não desfecho; um teste pareado sobre contagem quase toda zero não diria nada.

### Dados versionados para o portão G7

Os quatro runs de 11/09/2026 (`result.json`, `manifest.json`, `summary.json`, `events.jsonl`, sem o workspace) foram copiados para `docs/tcc/dados/runs-11-09/<run_id>/` para que a saída acima seja reproduzível por qualquer leitor:

    uv run python scripts/analyze_results.py docs/tcc/dados/runs-11-09 --markdown

### Decisões que ficam com o autor

1. "Resolvida por ambos" está definida pelo agregado por tarefa (maioria das repetições em cada braço). A leitura mais dura, resolvida em todas as repetições nos dois braços, é uma linha no script e muda quais tarefas entram no Wilcoxon primário. Decidir antes da coleta definitiva.
2. `stop_reason` nulo conta como "sem corte" na métrica 6, pela definição literal. O JSON reporta `sem_stop_reason` para conferência.

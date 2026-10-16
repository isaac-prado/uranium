# 21. Rodada 5: veredito determinístico, trechos do planejador e planejador enxuto (15/10/2026)

Rodada aprovada por escrito em 15/10/2026 (decisões 35 a 38 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md)): rodada 4 mais quatro mudanças no braço orquestrado, só ele roda, 13 tarefas × 3 repetições, mesmas sementes; o single-agent de comparação continua sendo o pareado da rodada 2. Manifesto v13. Dados: `dados/coleta-r5/` (calibração offline já gravada; runs a versionar no fechamento).

## 1. O que muda em relação à rodada 4

| item (aprovação do autor) | chave | rodada 4 | rodada 5 | onde |
|---|---|---|---|---|
| 1. veredito da sub-tarefa sem opinião | `SUBTASK_CHECK` | `llm` (revisão de sub-tarefa pelo modelo; reprovou 84 %) | `deterministic`: saídas esperadas que o planejador apontou (`Subtask.expected`) comparadas por texto com a saída real dos blocos da sub-tarefa; nada verificável → vale a palavra do developer | `src/verificacao.py`, `src/agents/validator.py::_verificar_subtarefa` |
| 2. o que o planejador leu vai ao developer | `PLANNER_CONTEXT_MAX_CHARS` | 0 | 16 000 caracteres por sub-tarefa, dos arquivos que ela lista | `src/agents/planner.py::_guardar_leituras`, `src/agents/developer.py::_trechos_da_subtarefa` |
| 3. comparação automática na revisão final | `REVIEW_COMPARE` | `off` | `advisory`: uma linha por saída esperada (encontrada / NÃO encontrada / não verificável) e a regra "não verificável não reprova" no prompt do revisor; `strict` guardado (§2) | `src/agents/validator.py::_comparar_esperadas`, `REGRA_COMPARACAO` |
| 4. planejador mais barato | `PLANNER_MAX_TURNS`, `PLANNER_MAX_SUBTASKS` | 12, 6 | 8, 3; primeira sub-tarefa com o núcleo; fatia só se verificável sozinha; sem sub-tarefa de regressão | `src/agents/planner.py::SYSTEM_PROMPT` |

Mudanças de apoio, registradas no manifesto pela versão: a intent v2 em markdown numera blocos (`Bloco n:`) e saídas esperadas (`n.`), porque é por esses índices que o plano aponta; blocos copiados numa linha só com `\n` escrito são desescapados antes de qualquer uso (`StructuredIntentV2._desescapar_quebras`; na rodada 4 os cinco blocos da sqlite-utils-0003 rep02 morreram em `SyntaxError`). As demais chaves são as da rodada 4 (`INTENT_REFINER=v2`, `REVIEW_EXECUTION=cumulative`, `CYCLE_NOTE=on`, `PLANNER=on`, teto de reprovações 2, `REVIEW_STRICT=off`).

## 2. Calibração offline da comparação (`dados/coleta-r5/calibracao-offline.txt`)

Antes de gastar, a comparação de texto de `src/verificacao.py` foi aplicada aos runs já gravados das rodadas 2, 3 e 4 (`scripts/calibrar_comparacao.py`): na última revisão final de cada run, todas as saídas esperadas da intent contra a saída real dos blocos, cruzada com o oráculo.

| rodada | todas encontradas: resolvido / não | alguma NÃO encontrada: resolvido / não | nada verificável: resolvido / não | sem execução na revisão final | aprovações erradas do revisor que a barreira pegaria / deixaria passar |
|---|---|---|---|---|---|
| 2 | 10 / 2 | **9** / 11 | 4 / 0 | 3 | 3 / 2 |
| 3 | 9 / 3 | **7** / 13 | 3 / 1 | 3 | 4 / 3 |
| 4 | 15 / 2 | **4** / 7 | 5 / 0 | 6 | 1 / 2 |

Leitura: como barreira dura na revisão final ("saída verificável ausente reprova"), a comparação derrubaria 4 dos 24 runs resolvidos da rodada 4 (9 dos 23 na rodada 2, 7 dos 19 na rodada 3), e pegaria 1 das 3 aprovações erradas do revisor. As saídas esperadas copiadas do enunciado não são sempre literais: descrevem o comportamento atual (attrs-0001, "falhou: TypeError"), trazem o valor dentro de prosa (pygments-0001 rep02), usam outro formato (`Field(...)` por `Attribute(...)`) ou vêm de blocos que não compilam. Por isso a rodada 5 usa a comparação onde o erro custa pouco (veredito da sub-tarefa, que a revisão final e o oráculo ainda filtram) e como subsídio ao revisor, não como barreira. O modo `strict` fica implementado e testado para uma rodada futura, se os eventos `validation.comparisons` da rodada 5, agora sobre o conjunto que o plano aponta, mostrarem que o apontamento do planejador limpa esses casos.

Para a decisão 37: na rodada 4 o planejador leu 36,7 mil caracteres por tentativa em 9,1 chamadas de `read_file`, e o developer releu 12,0 mil em 7,4 chamadas só no primeiro ciclo (`dados/coleta-r5/leituras-planejador-r4.txt`).

## 3. O que a rodada mede

- Se a esteira de sub-tarefas passa a andar: sub-tarefas feitas por base do veredito (`validation.basis`: `comparacao` × `palavra_do_developer`), adiadas e replanejamentos, contra 13 feitas de 186 na rodada 4.
- Se a faixa média reage ao contexto entregue (peewee-0002 0/12 em todas as rodadas; attrs-0001; sqlite-utils-0003) e o que isso custa em tokens por run (rodada 4: 884 mil, 2× a rodada 2).
- Se a comparação no prompt reduz os dois erros do revisor (rodada 4: 66 reprovações em 90 revisões; 3 aprovações com oráculo vermelho), lendo `validation.comparisons` ao lado de `is_valid`.
- As sete métricas de sempre contra o single-agent pareado da rodada 2.

## 4. Fumaça (15/10/2026 22:3x a 23:37, `dados/fumaca-r5/`)

Três tarefas grandes, 1 repetição, configuração da rodada 5, US$ 0,40 no total (`result.json` de cada run):

| tarefa | resultado | turnos (planejador + pedido do plano + developer) | custo | tokens | plano | o que aconteceu |
|---|---|---|---|---|---|---|
| tomlkit-0003 | **resolvida** (1/1) | 21 (8 + 1 + 12) | US$ 0,042 | 164 mil | 2 sub-tarefas, ambas em `items.py`; trechos de `items.py` (3,9 mil) e `container.py` (4,2 mil) | developer editou `items.py` e encerrou no primeiro ciclo; revisão final aprovou com as saídas esperadas 1 e 2 encontradas. Fumaça da rodada 4: 41 turnos, US$ 0,06 |
| tomlkit-0002 | **resolvida** (1/1) | 44 (8 + 1 + 35) | US$ 0,069 | 339 mil | 2 sub-tarefas (`api.py`; `container.py` + `items.py`); trechos de 0,4 mil, 11,4 mil e 8,8 mil | developer escreveu `api.py` e `items.py` no primeiro ciclo; revisão final aprovou com as saídas 1 a 3 encontradas. Fumaça da rodada 4: 102 turnos, US$ 0,14 |
| tomlkit-0004 | não resolvida (0/7) | 120 (orçamento) | US$ 0,285 | 2,28 M | 2 sub-tarefas (`parser.py`; `items.py` + `container.py`); trechos de 25,8 mil (cortado a 16 mil), 14,0 mil e 9,3 mil | ciclo 1 (41 turnos, teto): suíte vermelha, sub-tarefa 1 não feita (`basis=suite_vermelha`); ciclo 2 (41): suíte verde, revisor reprova com a comparação mostrando a saída esperada 1 NÃO encontrada, sub-tarefa 1 não feita por comparação e adiada; ciclo 3 (29, orçamento): sub-tarefa 2, suíte verde, revisor reprova, `basis=palavra_do_developer` negativo porque o ciclo acabou pelo orçamento. Igual às 0/19 anteriores |

Leitura: as duas resolvidas fecharam em menos da metade dos turnos da fumaça da rodada 4, no primeiro ciclo, com os trechos do planejador na mão; os três estados do veredito determinístico (`suite_vermelha`, `comparacao`, `palavra_do_developer`) e o avanço do plano (adiada → próxima) apareceram na tomlkit-0004 sem erro do harness; a comparação chegou ao revisor e o parecer dele foi coerente com ela. Critério combinado com o autor atendido (0003 continua resolvendo, 0002 não piorou): rodada 5 lançada às 23:4x em `runs/coleta-r5`.

### 4.1 Falsa partida (15/10 23:4x a 16/10 00:2x, `runs/coleta-r5-descartados/`, manifesto v13)

Dos 4 primeiros runs, 3 cortados por orçamento (attrs-0001 2/3 ocultos, peewee-0001 0/4, peewee-0002 5/6) e 1 resolvido (peewee-0003). A leitura dos eventos mostrou um defeito de desenho, não variação: o refinador copia como "saídas esperadas" também as saídas atuais com que o enunciado descreve o bug (attrs-0001: `has(Caixa[str]): False`, `fields(Caixa[str]) falhou: TypeError`; peewee-0002: `commit -> OperationalError no such savepoint`), o planejador as apontou em `expected`, e a comparação passou a exigir o comportamento do bug. Na attrs-0001 o developer corrigiu no ciclo 1, recebeu "saída esperada 2: NÃO encontrada", o revisor reprovou "porque `has(Caixa[str])` retorna True", e ele desfez a correção (ciclos 2, 5 e 8), num vaivém até o orçamento; na peewee-0002 a sub-tarefa 1 nunca podia ficar feita e foi adiada com a correção certa. A rodada foi parada no 5º run (US$ 0,9 gastos), corrigida pela decisão 39 (o planejador executa os blocos no código original e o que já aparece ali sai da comparação; manifesto v14) e relançada do zero com as mesmas sementes. A peewee-0001 caiu por outro motivo, já conhecido: o developer tentou reescrever `peewee.py` inteiro com `write_file` e deixou a suíte com 28 erros até o fim.

## 5. Resultados (a preencher)

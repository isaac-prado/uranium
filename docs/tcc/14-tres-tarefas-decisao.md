# Três tarefas com "suíte verde" inalcançável: detalhe para a decisão do autor (14/10/2026)

Checagem: patch de referência aplicado no commit-base **sem** o patch de teste; suíte visível (`pass_to_pass = tests/`) rodada; resultado em `dados/coleta/checagem-suite-visivel-referencia.txt`. Nas outras dez tarefas a suíte fica verde com as duas referências. Nestas três fica vermelha com as duas, porque o patch de teste do upstream **modifica** testes que já existiam e continuam visíveis ao agente na versão antiga, ou um arquivo dourado protegido. O critério de parada dos dois braços é "suíte verde e houve mudança"; aqui ele é contraditório com a correção certa, e o feedback "a suíte falhou" (idêntico nos dois braços) empurra o agente a desfazer o que estava certo.

## 1. `pygments-0001` (pequena, bugfix): "Go lexer improvements"

- **Commit:** <https://github.com/pygments/pygments/commit/9c436b34ccafdf9376527f66c6e587ffe0d1b84c>, PR #3199. 1 arquivo-fonte (`pygments/lexers/go.py`), 26 linhas.
- **Ocultos (2):** comparação inteira de tokens das fixtures `tests/examplefiles/go/3199.go` (nova) e `generics.go` (existente).
- **Conflito:** o patch de teste **reescreve** `tests/examplefiles/go/generics.go.output` (arquivo dourado, 2 hunks). Com a correção certa, o teste visível `tests/examplefiles/go/generics.go::` compara o lexer corrigido com o dourado antigo e falha (1 falha em 5.295). O dourado está na área protegida: o agente não pode atualizá-lo.
- **O que aconteceu na coleta:** single-agent manteve a correção e foi cortado nas três repetições (84, 1 e 67 execuções da suíte; cortes por tokens, turnos e tokens), oráculo 2/2 nas três, resolvida 3 de 3. Orquestrado: r1 e r3 chegaram ao verde **desfazendo** a correção, revisor aprovou, 0/2; r2 ciclou 33 vezes sobre a mesma falha, cortado, 0/2. Resultado 3 a 0 para o single-agent, decidido por quem desiste do verde.
- **Custo da tarefa na coleta:** US$ 2,84 (single-agent) + 0,41 (orquestrado).

## 2. `sqlite-utils-0002` (pequena, bugfix): "transform: coerce empty strings to NULL"

- **Commit:** <https://github.com/simonw/sqlite-utils/commit/e4935e064407bc995f77795c025c33cef52d742e>, PR #805, issue #488. 1 arquivo-fonte (`sqlite_utils/db.py`), 21 linhas.
- **Ocultos (11):** `test_transform_empty_string_to_null_for_numeric_types[...]` (5 parametrizações, novos) e 6 parametrizações de `test_transform_sql_table_with_primary_key` / `_no_primary_key` (modificados).
- **Conflito:** os 6 testes modificados existem na base visível com o SQL antigo (`SELECT "rowid", "id", "name", "age"`); a correção certa gera `NULLIF("age", '')`, e a versão visível falha (6 falhas em 1.483). Mesmos 6 que o oráculo exige na versão nova.
- **O que aconteceu:** single-agent cortado por tokens nas três repetições (8,0 a 8,2 M; a suíte do sqlite-utils devolve saída longa e o histórico persistente infla), resolvida 1 de 3. Orquestrado resolvido 3 de 3, todos cortados por turnos com a correção no lugar. 3 a 1 para o orquestrado, de novo decidido pelo corte, não pela convergência.
- **Custo:** US$ 3,19 (single-agent) + 0,65 (orquestrado).

## 3. `tomlkit-0004` (grande, feature): "Add support for dotted keys"

- **Commit:** <https://github.com/python-poetry/tomlkit/commit/eedcdb2538326b468a59f03ff8392bd4ec348125> (2018, sem PR), issue #2. 3 arquivos-fonte, 101 linhas.
- **Ocultos (7):** parametrizados `[0.5.0]` em `test_api.py`, dois em `test_items.py`, um em `test_toml_document.py`.
- **Conflito:** `tests/test_items.py::test_items_can_be_appended_to_and_removed_from_a_table` existe na base visível esperando `"\n" == table.as_string()`; o patch de teste o altera para `"" == table.as_string()` (a quebra de linha do cabeçalho deixa de ser conteúdo da tabela, item 7 do enunciado). A correção certa faz a versão visível falhar (1 falha em 163).
- **O que aconteceu:** 0 de 6 na coleta e 0 de 16 contando as fumaças. Melhor parcial 5/7 (single-agent r3). A tarefa também é a mais difícil por conteúdo (sete ocultos sobre um mesmo arquivo de exemplo), então o conflito não explica sozinha o chão.
- **Custo:** US$ 1,39 (single-agent) + 0,72 (orquestrado), mais US$ 7,4 nas oito fumaças.

## 4. Opções

| opção | o que é | custo | efeito no estudo |
|---|---|---|---|
| (a) Declarar e manter | As três ficam; o texto declara o conflito e reporta a sensibilidade sem elas (10 tarefas: direção igual, 6 a 1 pelo single-agent, p = 0,125) | US$ 0 | Honesto, mas duas das três decidem-se por corte, não por convergência; a faixa pequena carrega as duas |
| (b) Excluir da análise principal | Análise de registro sobre 10 tarefas; as três vão para apêndice | US$ 0 | n cai para 10 (3 grandes → 2, pequenas 6 → 4); a métrica 2 fica com 4 tarefas resolvidas por ambos |
| (c) Reconstruir e recoletar | Tirar do alvo visível (`suite_targets`/`pass_to_pass` com `--deselect`) os testes que o patch de teste modifica, mantendo-os no oráculo; novo portão em `validate_task.py`; recoletar 3 × 2 × 3 = 18 runs | ≈ US$ 5 a 7 (a pygments e a sqlite-utils são caras no single-agent) | Mantém n = 13; muda o instrumento depois da coleta, declarado como correção de defeito de construção; as 18 células antigas ficam versionadas como rodada 1 |
| (d) Substituir por tarefas novas | Minerar/escrever 3 tarefas que passem no quinto portão (há 15 médias e 48 pequenas no `mined-v4`, mas nenhuma grande além das três) | mineração + validação + 18 runs ≈ US$ 5 a 7 | Mantém n; a faixa grande perde a única feature grande e fica com duas |

Sobre "features genéricas, como 'crie algo'": o desenho exige oráculo oculto verificado por execução (suíte verde na base, oculto vermelho na base e verde com a referência). Uma tarefa inventada precisa de teste oculto escrito pelo autor e de duas soluções de referência, e perde o lastro do commit real que sustenta a validade externa. É viável como último recurso, mas é mais trabalho e menos defensável que (c).

**Recomendação:** (c) quando houver crédito, com o quinto portão implementado antes; até lá, (a) no texto. A rodada 2 seria: ablação do refinador (em curso), portão novo, recoleta das três.

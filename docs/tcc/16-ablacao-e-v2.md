# 16. Ablação do refinador e refinador v2: repetição 1 (14/10/2026)

Três variantes do braço orquestrado, uma repetição cada, mesma semente da
repetição 1 da coleta principal (`seed_for_repetition(1)`), mesmos tetos
(decisão 12) e mesmo modelo (decisão 26). O single-agent de comparação é a
repetição 1 da coleta principal (`dados/coleta/*/single-agent/rep01`). Nada
aqui tem três repetições: é sinal para decidir o desenho da rodada 2, não
resultado para o capítulo de Resultados.

| variante | o que o developer recebe | dados | execução |
|---|---|---|---|
| OR-v1 | só a intent do refinador v1 (coleta principal) | `dados/coleta/*/orchestration/rep01` | 12-13/10 |
| OR-abl | enunciado cru + intent v1 (`DEVELOPER_INPUT=enunciado+intent`, decisões 7/16) | `dados/ablacao-refinador/` | 14/10 07:48 a 09:48 |
| OR-v2 | só a intent do refinador v2 (`INTENT_REFINER=v2`, decisão 28) | `dados/refinador-v2/` | 14/10 12:21 a 14:23 |
| SA | enunciado cru, histórico persistente | `dados/coleta/*/single-agent/rep01` | 12-13/10 |

Comandos: `scripts/run_collection.py --arms orchestration --repetitions 1 --out runs/<variante> --workers 1 --retry-delay 300 --max-attempts 5`, com a variável de ambiente da variante. Manifestos: v8 (ablação) e v9 (v2). 13 concluídas e 0 perdidas em cada uma (`collection-rep1.log`).

## 1. Resolvidas por tarefa (oráculo, `result.json: resolved`)

| tarefa | faixa | SA | OR-v1 | OR-abl | OR-v2 |
|---|---|---|---|---|---|
| attrs-0001 | média | ✓ | ✓ | ✓ | ✓ |
| peewee-0001 | média | ✓ | ✗ | ✓ | ✗ |
| peewee-0002 | média | ✓ | ✗ | ✗ | ✗ |
| peewee-0003 | pequena | ✓ | ✓ | ✓ | ✓ |
| pygments-0001 | pequena | ✓ | ✗ | ✓ | ✗ |
| sqlite-utils-0001 | pequena | ✗ | ✗ | ✗ | ✗ |
| sqlite-utils-0002 | pequena | ✓ | ✓ | ✓ | ✓ |
| sqlite-utils-0003 | média | ✓ | ✗ | ✓ | ✓ |
| tomlkit-0001 | pequena | ✓ | ✓ | ✓ | ✓ |
| tomlkit-0002 | grande | ✗ | ✗ | ✗ | ✓ |
| tomlkit-0003 | grande | ✓ | ✓ | ✓ | ✓ |
| tomlkit-0004 | grande | ✗ | ✗ | ✗ | ✗ |
| tomlkit-0005 | pequena | ✗ | ✓ | ✗ | ✗ |
| **total** | | **9/13** | **6/13** | **8/13** | **7/13** |
| média (4) | | 4 | 1 | 3 | 2 |
| pequena (6) | | 4 | 4 | 4 | 3 |
| grande (3) | | 1 | 1 | 1 | 2 |
| cortes em 120 turnos | | 3 | 5 | 5 | 6 |
| turnos somados | | 894 | 927 | 984 | 970 |
| tokens somados | | 32,1 M | 11,9 M | 12,9 M | 14,8 M |
| custo (`cost.cost_usd`) | | US$ 3,50 | US$ 1,46 | US$ 1,77 | US$ 2,08 |

Fonte: `result.json` e `summary.json` de cada run (tabela por run gerada em 14/10 a partir de `runs/coleta`, `runs/ablacao-refinador`, `runs/refinador-v2`). Os dois cortes do SA por tokens (pygments-0001 e sqlite-utils-0002, 8,1 M) resolveram mesmo assim.

**Leitura.** Com o enunciado nas mãos (OR-abl), o orquestrado vai de 6 para 8 e fica a uma tarefa do single-agent, sem mudar mais nada. As três que viram (peewee-0001, pygments-0001, sqlite-utils-0003) são as que [15-refinador-analise.md](15-refinador-analise.md) apontou: intent que referia conteúdo que não carregava. A ablação perde tomlkit-0005, que o OR-v1 tinha resolvido em 74 turnos; uma repetição não separa isso de variância.

O v2 fica em 7: recupera sqlite-utils-0003 e resolve tomlkit-0002, a única tarefa grande que nenhuma outra variante (nem o SA) resolveu na repetição 1; perde peewee-0001 e pygments-0001. A seção 3 mostra que essas duas perdas não estão na intent.

## 2. Tamanho da intent

Caracteres do enunciado (`tasks/<id>/statement.md`), da intent v1 (JSON, evento `intent` do run OR-v1) e da intent v2 (markdown que o developer recebe, `StructuredIntentV2.to_markdown()` sobre o evento `intent` do run OR-v2).

| tarefa | enunciado | v1 | v2 | v2/enunciado | blocos de reprodução | saídas esperadas | pontos em aberto |
|---|---|---|---|---|---|---|---|
| attrs-0001 | 3400 | 1614 | 4305 | 1,27 | 1 | 4 | 2 |
| peewee-0001 | 4448 | 1680 | 5222 | 1,17 | 1 | 4 | 2 |
| peewee-0002 | 9574 | 1604 | 11142 | 1,16 | 6 | 10 | 2 |
| peewee-0003 | 2113 | 1578 | 4046 | 1,91 | 1 | 2 | 1 |
| pygments-0001 | 7615 | 1556 | 12572 | 1,65 | 1 | 18 | 2 |
| sqlite-utils-0001 | 2713 | 1398 | 3593 | 1,32 | 1 | 1 | 2 |
| sqlite-utils-0002 | 3797 | 1301 | 4463 | 1,18 | 1 | 2 | 2 |
| sqlite-utils-0003 | 5399 | 2433 | 5950 | 1,10 | 5 | 6 | 2 |
| tomlkit-0001 | 1251 | 913 | 2418 | 1,93 | 6 | 0 | 0 |
| tomlkit-0002 | 3244 | 1539 | 3683 | 1,14 | 2 | 3 | 2 |
| tomlkit-0003 | 2562 | 1775 | 3541 | 1,38 | 1 | 2 | 0 |
| tomlkit-0004 | 6558 | 1959 | 6030 | 0,92 | 3 | 3 | 2 |
| tomlkit-0005 | 2532 | 1345 | 2868 | 1,13 | 1 | 1 | 0 |
| **total** | 55206 | 20695 | 69833 | 1,26 | | | |

O v1 entregava 37 % do enunciado; o v2 entrega 126 %. Os 17 casos do pygments e os 6 blocos do peewee-0002 estão literais na v2. `is_ready` continuou `true` em 13/13 (o nó `clarification` segue sem rodar, decisão 9).

## 3. As duas perdas do v2, traço a traço

### 3.1 pygments-0001: a intent estava certa, a suíte não podia ficar verde

`dados/refinador-v2/pygments-0001/orchestration/rep01/attempt01/events.jsonl`, eventos `memory`:

- Ciclo 1 (27 turnos): lê `pygments/lexers/go.py`, escreve, roda a suíte: `passed=5294 failed=1`. Nota: "Todos os 17 casos de teste da tarefa estão passando". O único vermelho é `tests/examplefiles/go/generics.go::`, o golden que a decisão 27 mandou tirar da suíte visível.
- Ciclos 2 a 9 (18, 12, 10, 9, 9, 9, 10, 9 turnos): nenhuma escrita (`arquivos_escritos: []`), a mesma suíte com o mesmo `failed=1`, a mesma nota "Resumo Final" repetida. O ciclo 3 diz com todas as letras: "existe um teste existente (`tests/examplefiles/go/generics.go`) que espera uma classificação diferente para o caractere `~`".
- Corte em 120 turnos. Oráculo (`result.json: oracle`): `f2p_passed 1/2`, passou `3199.go::` e falhou `generics.go::`.

Por que o golden ainda rodava, se o `task.json` tinha `visible_deselect`? Bug do harness, seção 4. O run do v2 saiu depois do commit `2f4e8ff`, com o manifesto v10 e `visible_deselect: ['tests/examplefiles/go/generics.go']` gravado, e mesmo assim o teste rodou.

Nota sobre o oráculo: `fail_to_pass` do pygments-0001 é `['tests/examplefiles/go/3199.go::', 'tests/examplefiles/go/generics.go::']`, o golden inteiro do upstream. O enunciado especifica 17 casos; o oráculo exige que toda a tokenização de `generics.go` coincida com a do upstream. A solução do v2 passou os 17 casos e o `3199.go` e divergiu em algo mais no `generics.go`. SA, OR-abl e a rodada 2 rep02 resolveram, então é alcançável, mas o enunciado é mais frouxo que o oráculo. Registrado para o texto (ameaças à validade: construção).

### 3.2 peewee-0001: o developer reescreveu o arquivo inteiro e o perdeu

`dados/refinador-v2/peewee-0001/orchestration/rep01/attempt01/`:

- A intent v2 traz o exemplo de reprodução literal, as 4 saídas esperadas e 6 critérios (evento `intent`).
- Turno 9: `replace_in_file` em `peewee.py` falha ("trecho não encontrado"). Ainda no ciclo 1 (33 turnos) a suíte passa a `errors=28` em todos os arquivos de teste e fica assim até o fim.
- `patch.diff`: 385 inserções e 7 859 remoções; `git diff --stat` no workspace: `1 file changed, 400 insertions(+), 9489 deletions(-)`; `peewee.py` foi de 9 694 para 550 linhas. As ferramentas registradas no run são `list_files`, `read_file`, `replace_in_file`, `run_python`, `run_tests`, `search_code`, e só um `replace_in_file` (falho) antes do erro: a reescrita saiu por `run_python`, que roda qualquer código no workspace, inclusive `open('peewee.py', 'w')`.
- Ciclos 3 e 4: a nota diz "O arquivo `peewee.py` foi truncado acidentalmente... Vou restaurar o conteúdo original" e o modelo tenta chamar uma ferramenta `write_file` que não existe, em texto. Ciclo 5 (39 turnos): "my simplified version of peewee.py is missing many attributes that the tests expect". Corte em 120.

O single-agent da mesma semente (`dados/coleta/peewee-0001/single-agent/rep01`) usou 4 `replace_in_file`, 6 `run_python`, 4 `run_tests` e fechou em 25 turnos. É o modo de falha 2 de [12-coleta-resultados.md](12-coleta-resultados.md) (desfaz/reescreve) no extremo; `run_python` contorna a exigência de correspondência exata do `replace_in_file`. Ferramenta compartilhada e congelada: fica como decisão 31 pendente, não foi mexida. Na rodada 2 (nota de ciclo e revisor que executa), peewee-0001 resolveu nas duas repetições já gravadas (`runs/coleta-r2/collection-orchestration.log`).

## 4. Bug: o `--deselect` da decisão 27 não valia em `runs/`

**Sintoma.** No workspace do run OR-v2 do pygments, `pytest -q --deselect tests/examplefiles/go/generics.go tests/examplefiles/go` dá `1 failed, 1 passed`; `--collect-only` mostra os node ids como `runs/refinador-v2/pygments-0001/orchestration/rep01/attempt01/workspace/tests/examplefiles/go/generics.go::`, e o cabeçalho diz `rootdir: /home/isaac/uranium, configfile: pyproject.toml`.

**Causa.** O pytest procura o arquivo de configuração subindo a partir dos argumentos; os workspaces ficam em `runs/` dentro do uranium, cujo `pyproject.toml` tem `[tool.pytest.ini_options]`. O rootdir vira a raiz do uranium, os node ids ganham o prefixo relativo a ela e o `--deselect`, que compara prefixo de node id (`_pytest/main.py: colitem.nodeid.startswith(deselect_prefixes)`), não casa nada. Vale para os três `visible_deselect` (pygments, sqlite-utils-0002, tomlkit-0004). O quinto portão de `scripts/validate_task.py` passou porque materializa em `tempfile.mkdtemp()`, fora do uranium, onde o rootdir é o próprio workspace. `tests/test_rodada2.py::test_run_pytest_deseleciona_na_suite_visivel` também usava `tmp_path`.

**Correção** (commit `4f4f80e`): `src/tools/exec.run_pytest` passa `--rootdir .` (cwd já é o workspace); chave `shared_limits.pytest_rootdir = "workspace"` no manifesto, de modo que run sem a chave é run com o bug. Teste novo `test_deselect_vale_com_pyproject_acima_do_workspace` materializa o workspace sob um diretório com `pyproject.toml` acima e exige que a suíte perca exatamente o teste. Verificação no workspace real do run OR-v2 do pygments: `tests/examplefiles/go` com `passed=1 failed=0`, suíte inteira `passed=5294 failed=0`.

**Efeito sobre os dados.** Coleta principal, ablação e v2: nenhum, porque nenhuma delas tinha deselect (o bug só se manifesta com `visible_deselect`). O oráculo (`harness/pytest_runner`) não deselecionа nada e não foi tocado. Para as 10 tarefas sem deselect, a única diferença depois da correção é a forma do node id que o agente vê na saída do pytest (`tests/test_x.py::t` em vez de `runs/.../workspace/tests/test_x.py::t`).

**Rodada 2.** Até a interrupção (14/10 16:45) estavam gravadas 19 células do orquestrado. As das três tarefas reconstruídas (pygments-0001 rep01 e rep02, sqlite-utils-0002 rep01, tomlkit-0004 rep01, mais sqlite-utils-0002 rep02 em andamento) rodaram com a suíte ainda contraditória e foram movidas para `runs/coleta-r2-descartados/` (README lá). As 15 das outras tarefas foram mantidas. Fila retomada às 17:00 com a correção, mesma semente para as células refeitas.

## 5. `StructuredOutputError` na tomlkit-0003 rep01 da rodada 2

`runs/coleta-r2-descartados/tomlkit-0003/orchestration/rep01/attempt01/events.jsonl`: o refinador v2 devolveu `reproduction` como lista de listas (`[[], ['tool.poetry.foo]...', ...]]`) nas três tentativas, o run morreu com `error: StructuredOutputError`, 0 turnos, custo 0. Pela decisão 14 é bug do harness, não perda: `StructuredIntentV2` ganhou um `field_validator(mode="before")` que achata um nível de lista e descarta itens vazios (`tests/test_intent_v2.py`), e a célula foi refeita com a mesma semente. Nos 13 runs do OR-v2 isso não tinha ocorrido.

## 6. O que fica para o texto

- Ablação (decisões 7/16): com o enunciado, 8/13 contra 6/13 na mesma semente; o refinador v1 custa duas ou três tarefas por resumir. Entra em Resultados como ablação, com uma repetição e sem estatística.
- v2 (decisão 28): recupera o conteúdo (126 % do enunciado, blocos literais) e não é a causa das duas perdas restantes. Vale pela rodada 2 completa.
- Dois modos de falha do orquestrado que o refinador não resolve: suíte contraditória (corrigida pela decisão 27, agora efetiva) e developer que destrói o arquivo via `run_python` (decisão 31 pendente).
- Oráculo do pygments mais estrito que o enunciado (ameaça de construção).
- Erros do harness desta rodada: rootdir e `StructuredOutputError`, com correção, teste e células refeitas.

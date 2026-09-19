# Breaking change e o oráculo: o que ele julga, o que não julga, e o que custaria mudar

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 19 de setembro de 2026
Relatório da exigência E3, item 3 de [EXIGENCIAS.md](tasks/EXIGENCIAS.md). **Somente leitura e relato: nada foi implementado.** O oráculo, o detector de trapaça e a guarda de caminho continuam intocados. Todo número e toda afirmação de comportamento trazem o arquivo e a linha ao lado. As linhas foram conferidas em 19/09/2026, na branch `exigencias-e2-e5`.

**Aviso sobre linhas móveis.** O `scripts/mine_tasks.py` estava sendo reescrito pelo item 1 da E3 durante a redação: 283 linhas no commit `d47abda`, 552 na árvore de trabalho. A função `avaliar`, que é a peça que importa aqui, é **idêntica nas duas versões** (conferido por `diff`). As citações a esse arquivo trazem a linha da árvore de trabalho e, entre parênteses, a do commit. Os demais arquivos citados estão estáveis no commit.

## 0. Resposta em uma frase

A leitura do autor está **parcialmente correta, e o motivo verdadeiro é outro e pior**: nas tarefas com `test_patch`, o avaliador substitui os arquivos de teste tocados pelo commit de correção pela versão do upstream antes de medir, então o oráculo **consegue** julgar a maior parte das mudanças de comportamento; quem não consegue julgar é o **laço do agente**, porque os dois braços só param quando a suíte **antiga** fica verde, e uma mudança de comportamento correta a deixa vermelha. A exclusão à la SWE-bench resolve um subcaso do problema do oráculo e **não resolve nada** do problema do laço.

---

## 1. Como o oráculo julga hoje

### 1.1 Onde nascem `fail_to_pass` e `pass_to_pass`

O `fail_to_pass` é **executado, nunca lido do texto do commit**. O minerador roda a suíte três vezes por candidato ([scripts/mine_tasks.py:343-390](../../scripts/mine_tasks.py#L343) (v1: 161-207)):

| Passo | O que faz | Exigência | Linha |
|---|---|---|---|
| 0 | roda a suíte no commit-pai | tem de estar **verde** | [mine_tasks.py:357-360](../../scripts/mine_tasks.py#L357) |
| 1 | `git checkout <fix> -- <arquivos de teste>`, fonte velha | tem de ficar **vermelha** | [mine_tasks.py:362-370](../../scripts/mine_tasks.py#L362) |
| 2 | `git checkout <fix> -- <arquivos de fonte>` | tem de ficar **verde** | [mine_tasks.py:372-381](../../scripts/mine_tasks.py#L372) |

`fail_to_pass = sorted(antes.failing_node_ids)`, ou seja, exatamente os node ids que falharam no passo 1 ([mine_tasks.py:383](../../scripts/mine_tasks.py#L383) (v1: 201)). A separação entre "arquivo de fonte" e "arquivo de teste" sai dos globs protegidos do repo-semente ([mine_tasks.py:243-252](../../scripts/mine_tasks.py#L243) (v1: 100-108); [src/seeds.py:38-54](../../src/seeds.py#L38)), e a lista de arquivos vem de `git log --name-only` ([mine_tasks.py:287-300](../../scripts/mine_tasks.py#L287) (v1: 113-130)).

O `pass_to_pass` **não é minerado**. O emissor o copia dos `suite_targets` do repo-semente ([scripts/emit_task.py:112](../../scripts/emit_task.py#L112)), e o `TaskSpec` cai em `["tests/"]` quando o campo falta ([harness/taskspec.py:104](../../harness/taskspec.py#L104)). Nenhum passo do minerador calcula quais testes passavam antes e continuam passando depois.

### 1.2 O que `pass_to_pass` contém de fato

**Não é lista de node ids. É "a suíte inteira", na forma de alvos de diretório passados ao pytest.** As duas tarefas existentes declaram `"pass_to_pass": ["tests/"]` ([tasks/tomlkit-0001/task.json:13](../../tasks/tomlkit-0001/task.json#L13); [tasks/sqlite-utils-0001/task.json:11-13](../../tasks/sqlite-utils-0001/task.json#L11)). Os alvos padrão por repo são `tests/` no tomlkit e no sqlite-utils e `tests/__init__.py` no peewee ([src/seeds.py:119,135,146](../../src/seeds.py#L119)). O tamanho da coisa: a suíte do tomlkit tem mais de mil testes ([tests/test_test_patch.py:143](../../tests/test_test_patch.py#L143) exige `p2p.passed > 1000`), e a do peewee, 1.634 ([harness/taskspec.py:40-44](../../harness/taskspec.py#L40); [src/tools/exec.py:98-101](../../src/tools/exec.py#L98); [tests/test_seed_repos.py:35](../../tests/test_seed_repos.py#L35)).

A consequência imediata é o risco **R4** já registrado: como `apply_test_patch` insere os testes novos dentro de `tests/`, eles entram na contagem de `p2p` e de `regression` ([docs/tcc/01-inventario.md:276-278](01-inventario.md); [harness/oracle.py:139-144](../../harness/oracle.py#L139)).

### 1.3 O que o agente vê e o que o avaliador traz

O agente recebe o workspace materializado no **commit-base**, com a suíte antiga e completa, e roda pytest pelos `suite_targets` do repo ([src/tools/exec.py:98-124](../../src/tools/exec.py#L98)). Ele nunca vê o patch de teste.

O avaliador, depois que o agente termina, faz três coisas em ordem, sobre uma cópia descartável do workspace ([harness/evaluate.py:46-113](../../harness/evaluate.py#L46)):

1. `git checkout <base> -- <arquivo>` para **cada arquivo capturado pela regex `^\+\+\+ b/(.+)$` do diff** ([harness/oracle.py:62,83,87-90](../../harness/oracle.py#L62));
2. `git apply` do `test_patch.diff` inteiro ([harness/oracle.py:94-96](../../harness/oracle.py#L94));
3. roda `f2p`, depois `p2p`, depois `regression` ([harness/oracle.py:136-144](../../harness/oracle.py#L136)).

**Sim, o avaliador traz os testes novos.** E traz mais do que os novos: como o patch é `git diff <base> <fix> -- <arquivos de teste>` ([scripts/emit_task.py:92-94](../../scripts/emit_task.py#L92)), restaurar o arquivo à base e aplicar o diff deixa cada arquivo de teste tocado pelo commit **idêntico à versão do commit de correção**. Um teste antigo cuja asserção o upstream mudou chega à medição **já com a asserção nova**. Um teste que o upstream apagou de dentro de um arquivo que sobreviveu chega **apagado**.

Vale notar que a docstring do módulo descreve a terceira verificação como "a suíte original completa, como estava no commit-base" ([harness/oracle.py:11](../../harness/oracle.py#L11)). Nas tarefas com `test_patch` isso não é verdade: a regressão roda sobre a suíte **já emendada**, porque `apply_test_patch` acontece antes, dentro do mesmo workspace ([harness/oracle.py:130,142-144](../../harness/oracle.py#L130)). É discrepância de documentação, não de comportamento.

### 1.4 As três verificações e a conjunção que decide

```
resolved = f2p_total > 0 and f2p_passed == f2p_total and p2p.green and regression.green
```
([harness/oracle.py:42-50](../../harness/oracle.py#L42)), e `green` é `exit_code == 0` ([harness/pytest_runner.py:44-46](../../harness/pytest_runner.py#L44)). O `result.json` ainda exige `cheat.clean` por cima ([harness/evaluate.py:115](../../harness/evaluate.py#L115)).

Três consequências para o caso de mudança de comportamento:

- `p2p` e `regression` são julgados por **código de saída da suíte inteira**, não por comparação de conjunto de node ids. Um único teste antigo vermelho reprova, seja ele legítimo ou não.
- `regression` roda `suite_targets or pass_to_pass` ([harness/oracle.py:142](../../harness/oracle.py#L142)), que hoje é o mesmo `tests/`. **Excluir testes só de `pass_to_pass` não mudaria o veredito**, porque `regression.green` continuaria exigindo a suíte inteira verde. Este ponto é decisivo para a seção 3.
- O único filtro estrutural existente é `--ignore=tests/_uranium_hidden` ([harness/oracle.py:139](../../harness/oracle.py#L139)), que só protege a forma de arquivo oculto avulso.

### 1.5 O que impede o **agente** de resolver, e não só o oráculo

Os dois braços só encerram com sucesso quando a suíte **visível** fica verde:

- braço `single-agent`: o operador roda a suíte e só devolve `ENCERRAR_VERDE` se `report.green` ([src/arms/driver.py:103-104](../../src/arms/driver.py#L103); [src/arms/single_agent.py:99-113](../../src/arms/single_agent.py#L99));
- braço `orchestration`: `is_valid = report.green and houve_mudanca and (...)` ([src/agents/validator.py:74](../../src/agents/validator.py#L74)).

A suíte visível é a **antiga**, do commit-base. Numa mudança de comportamento, a implementação correta a deixa vermelha. O agente vê o vermelho, recebe o stdout cru como feedback e tem dois caminhos: reverter a mudança correta até o vermelho sumir, ou insistir e morrer em `budget: max_turns`. **Ele não pode consertar os testes**, porque `tests/**` está na guarda de caminho ([src/seeds.py:38-54](../../src/seeds.py#L38); [harness/taskspec.py:15-19](../../harness/taskspec.py#L15)) e mexer ali é trapaça crítica C1 ([harness/cheat.py:148-159](../../harness/cheat.py#L148)).

Detalhe importante: parar por orçamento **não impede** o veredito positivo. O avaliador não olha `stop_reason` ([harness/evaluate.py:80-141](../../harness/evaluate.py#L80)). Um agente que implementasse certo, ignorasse o vermelho antigo e fosse cortado por turnos ainda poderia sair `resolved: true`. O problema é que o laço empurra na direção contrária: o incentivo visível é reverter.

### 1.6 Veredito sobre a leitura do autor

| Afirmação do autor | Situação | Evidência |
|---|---|---|
| "uma mudança de comportamento faz os testes antigos falharem legitimamente" | **Verdadeira em geral, falsa para os testes que o próprio commit corrigiu.** Estes chegam à medição já atualizados | [harness/oracle.py:69-97](../../harness/oracle.py#L69); [scripts/emit_task.py:92-94](../../scripts/emit_task.py#L92) |
| "o agente não pode tocar em `tests/`" | **Verdadeira e sem exceção** | [src/seeds.py:38-54](../../src/seeds.py#L38); [harness/cheat.py:148-159](../../harness/cheat.py#L148) |
| "o oráculo não consegue julgá-la" | **Parcialmente refutada.** Julga, desde que o commit de correção atualize na mesma leva todo teste afetado, que é justamente o que o passo 2 do minerador já verifica | [scripts/mine_tasks.py:372-381](../../scripts/mine_tasks.py#L372) |
| (não estava na leitura) o laço do agente não consegue julgá-la | **Confirmado, e é o obstáculo maior** | [src/arms/driver.py:103-104](../../src/arms/driver.py#L103); [src/agents/validator.py:74](../../src/agents/validator.py#L74) |

Evidência empírica do que o minerador já rejeita, nos 90 candidatos executados de `mined-v1/` (30 por repo): 54 aceitos, 13 "teste passa sem a correção", 16 "vermelho sem node id: erro de coleta", 1 timeout e **6 "não fica verde com a correção"**, todos no sqlite-utils. Desses 6, cinco trazem "1 das mesmas", isto é, o próprio teste discriminante continua falhando, sinal de corte errado; **um traz "0 das mesmas"** ([mined-v1/sqlite-utils.json:394](../../mined-v1/sqlite-utils.json#L394), commit `7a522146`, "drop-index command and table.drop_index(index_name)", tocando `tests/test_cli.py` e `tests/test_create.py`). Esse é exatamente o formato de dano colateral: depois da correção, quem falha é **outro** teste, não o discriminante. Um caso em 90 candidatos com o critério atual, que favorece patch pequeno; a E3 vai minerar commits maiores, onde a proporção deve subir. Não verificado: quanto ela sobe, porque a remineração ampla ainda não rodou.

### 1.7 O que a remineração do item 1 já faz a respeito

Durante a redação deste relatório, o item 1 da E3 reescreveu o minerador, e a versão nova já encosta no problema desta seção. Registro o que encontrei na árvore de trabalho, sem depender disso:

- `contar_testes_novos_e_modificados` conta, no diff dos testes, quantas funções `def test_` são **novas** e quantas são **modificadas** ([scripts/mine_tasks.py:79-136](../../scripts/mine_tasks.py#L79)), e a própria docstring aponta o item 3 como consumidor do número ([mine_tasks.py:99-102](../../scripts/mine_tasks.py#L99));
- a faixa **grande** só é atribuída quando há teste novo e `testes_novos > testes_modificados`, com assunto que não começa por `fix`/`bug` ([mine_tasks.py:182-183](../../scripts/mine_tasks.py#L182));
- cada candidato guarda `altera_testes_existentes` ([mine_tasks.py:215,336](../../scripts/mine_tasks.py#L215)).

Ou seja: a faixa grande **já nasce enviesada contra a mudança de comportamento**, o que é a alternativa conservadora B da seção 4 aplicada a uma faixa só, e por maioria em vez de exclusividade, porque `testes_modificados > 0` continua permitido desde que menor que `testes_novos`. Isso reduz o problema, não o elimina, e torna barato medi-lo: basta contar, por faixa, quantos candidatos têm `altera_testes_existentes = true`. Esse número ainda **não existe**: quando este relatório foi escrito, `mined-v2/` continha apenas `.workspaces/`, sem nenhum arquivo de resultado, e o minerador v2 ainda não estava commitado.

---

## 2. Quatro cenários concretos

Em todos, suponha um agente que implementou a mudança **corretamente**, e uma tarefa na forma `test_patch` (a forma que o emissor gera hoje, [scripts/emit_task.py:113-114](../../scripts/emit_task.py#L113)).

**(a) Commit que só adiciona testes novos.** É o caso das duas tarefas existentes. O patch cria ou estende arquivos de teste sem mexer em asserção antiga; o `sqlite-utils-0001` tem um único arquivo alvo e dois hunks, um de import e um de 122 linhas acrescentadas ([tasks/sqlite-utils-0001/test_patch.diff:1-13](../../tasks/sqlite-utils-0001/test_patch.diff)). O avaliador restaura o arquivo, aplica o diff, roda `f2p` (passa), `p2p` e `regression` sobre `tests/` (verdes). **Resolvido: sim.** O único defeito é o R4, que faz os node ids de `f2p` aparecerem dentro da contagem de `p2p` quando o agente **não** resolve ([01-inventario.md:278](01-inventario.md)).

**(b) Commit que modifica asserções de testes existentes porque o comportamento mudou.** O arquivo de teste é restaurado para a base e depois recebe o diff inteiro, ficando na versão do commit de correção ([harness/oracle.py:87-96](../../harness/oracle.py#L87)). As asserções que o avaliador executa são as **novas**. O `f2p` passa; `p2p` e `regression` ficam verdes **se e somente se** nenhum teste fora dos arquivos tocados pelo commit tiver quebrado, condição que o passo 2 do minerador já testou antes de aceitar o candidato ([scripts/mine_tasks.py:372-381](../../scripts/mine_tasks.py#L372)). **Resolvido: sim, pelo oráculo.** O problema aqui é o laço: durante a execução, o agente enxerga as asserções **antigas**, vê vermelho e é empurrado a reverter ([src/arms/driver.py:103-104](../../src/arms/driver.py#L103)). Na prática, o desfecho mais provável é `f2p` falhando porque o agente desfez a mudança, ou `budget: max_turns`. Não verificado por execução: nenhuma tarefa deste tipo existe hoje para medir a frequência.

**(c) Commit que remove testes.** Dois subcasos, e eles se comportam de forma diferente. Se o commit apaga funções de teste **dentro** de um arquivo que sobrevive, o arquivo é restaurado e emendado normalmente, e os testes removidos simplesmente não são coletados: **resolvido: sim**. Se o commit apaga o **arquivo inteiro**, o git emite `+++ /dev/null` (verificado em repositório de sondagem), a regex `^\+\+\+ b/(.+)$` não captura nada, o arquivo não é restaurado e o `git apply` o remove corretamente ([harness/oracle.py:62,83,94](../../harness/oracle.py#L62); aplicação de patch de remoção verificada com sucesso em sondagem). Ainda assim há dois pontos de quebra mecânica:
- se o patch de teste for **só** remoções e renomeações, `alvos` fica vazio e o avaliador levanta `ValueError: patch de teste não altera arquivo nenhum` ([harness/oracle.py:83-85](../../harness/oracle.py#L83)), verificado com a regex real contra um diff de sondagem contendo apenas remoção e renomeação: resultado `[]`;
- antes disso, o **minerador já quebra**: `git checkout <fix> -- <arquivo apagado no fix>` devolve `error: pathspec ... did not match any file(s) known to git` com código 1 (verificado), e `_git` converte isso em `RuntimeError` ([scripts/mine_tasks.py:236-239](../../scripts/mine_tasks.py#L236) (v1: 93-97)) dentro de `avaliar`, sem `except` ([scripts/mine_tasks.py:363](../../scripts/mine_tasks.py#L363) (v1: 181)), o que aborta a mineração inteira, e não apenas aquele candidato.

**(d) Commit que renomeia teste.** Renomeação de **arquivo** com similaridade 100% produz um diff sem `---`/`+++` (verificado): `alvos` fica vazio, e valem as mesmas quebras do item (c). Pior: `git log --name-only` lista apenas o **nome novo** (verificado), de modo que o passo 1 do minerador faz checkout do arquivo novo e **deixa o antigo no lugar** ([scripts/mine_tasks.py:363](../../scripts/mine_tasks.py#L363) (v1: 181)), duplicando a coleta. Renomeação de **função** dentro do arquivo é caso (b) disfarçado: o node id antigo some e o novo aparece, o arquivo inteiro é substituído, e **resolvido: sim** pelo oráculo, com o mesmo problema de laço. Nota de escopo: a captura de renomeação depende de `diff.renames`, que é padrão no git moderno; não verificado qual configuração vigora na máquina de coleta.

**Resumo dos quatro.** O oráculo julga bem (a), (b) e as variantes internas de (c) e (d). Ele quebra com exceção, em vez de reprovar, nas remoções e renomeações de arquivo inteiro. E em nenhum caso o laço do agente sabe parar quando a mudança de comportamento é a resposta certa.

---

## 3. O que custaria a exclusão à la SWE-bench

### 3.1 O mecanismo do SWE-bench

**Fonte: literatura do SWE-bench, não arquivo deste repositório.** Não há nenhuma referência a SWE-bench no código, nos dados ou nos documentos daqui, fora a própria exigência ([docs/tcc/tasks/EXIGENCIAS.md:69](tasks/EXIGENCIAS.md)). Portanto o parágrafo abaixo é **não verificado por leitura** e precisa ser conferido contra o repositório `princeton-nlp/SWE-bench` antes de virar texto do TCC.

Na construção de cada instância, o SWE-bench aplica o `test_patch` ao commit-base e roda a suíte duas vezes: uma sem o patch de referência ("gold"), outra com ele. Cada teste recebe um status nas duas execuções. `FAIL_TO_PASS` são os que falham antes e passam depois; `PASS_TO_PASS` são os que passam **nas duas**. Tudo o mais, inclusive o que falha nas duas e o que passava antes e falha depois, fica **fora das duas listas** e não é julgado. Ou seja: o SWE-bench não exclui "os testes que o patch de referência altera" por inspeção do diff; ele exclui por **execução**, tudo que a referência não deixa verde. E as duas listas são de **node ids explícitos**, comparadas contra o log de uma execução restrita aos arquivos de teste tocados, não um código de saída de suíte inteira.

### 3.2 A boa notícia: as duas execuções necessárias já acontecem

O passo 1 e o passo 2 do minerador são **exatamente** as duas execuções que o SWE-bench usa ([scripts/mine_tasks.py:362-381](../../scripts/mine_tasks.py#L362)). Hoje o resultado do passo 2 é jogado fora depois de conferir se ficou verde. Calcular `PASS_TO_PASS` **não custa nenhuma execução de suíte a mais**. O que falta é parsing: nem `harness/pytest_runner.py` nem `src/tools/exec.py` extraem node ids que **passaram**; ambos só capturam `FAILED` e `ERROR`, com `-rf` ([harness/pytest_runner.py:22-28,127-137](../../harness/pytest_runner.py#L22); [src/tools/exec.py:36,116-124](../../src/tools/exec.py#L36)). Trocar `-rf` por `-rA` faz o pytest listar `PASSED <node id>` por teste, com id reutilizável inclusive nos parametrizados com espaço (verificado em sondagem com o pytest do projeto). O junit-xml não serve, e a docstring já explica por quê ([src/tools/exec.py:56-62](../../src/tools/exec.py#L56)).

### 3.3 Mudanças necessárias, arquivo por arquivo

| Arquivo (tamanho hoje) | O que muda | Linhas aprox. | Toca o oráculo? |
|---|---|---|---|
| [harness/pytest_runner.py](../../harness/pytest_runner.py) (159) | `-rf` vira `-rA` em `run_pytest`; `parse_output` passa a devolver `passing_node_ids`; `PytestResult` ganha o campo e o `as_dict` também | 15 a 20 | não, é infraestrutura |
| [harness/oracle.py](../../harness/oracle.py) (157) | `evaluate_oracle` julga `p2p` por **inclusão de conjunto** (todo node id de `pass_to_pass` apareceu como `PASSED`), não por `exit_code`; `resolved` deixa de exigir `regression.green` ou a regressão vira informativa; contagem de excluídos no `as_dict` | 25 a 35 | **sim** |
| [harness/taskspec.py](../../harness/taskspec.py) (112) | `pass_to_pass` muda de "alvos de diretório" para "lista de node ids"; validação que recusa a forma antiga, ou campo novo com convivência das duas | 10 a 15 | fronteira |
| [scripts/mine_tasks.py](../../scripts/mine_tasks.py) (283) | `Candidato` ganha `pass_to_pass`; `avaliar` intersecta os `passing_node_ids` do passo 1 com os do passo 2; relatar quantos testes ficaram de fora, que é o tamanho do dano colateral | 15 a 20 | não |
| [scripts/emit_task.py](../../scripts/emit_task.py) (184) | grava a lista no `task.json` em vez de copiar `suite_targets` ([emit_task.py:112](../../scripts/emit_task.py#L112)) | 3 a 5 | não |
| [scripts/validate_task.py](../../scripts/validate_task.py) (170) | passo 1 usa a lista de node ids; portão novo, obrigatório: **toda exclusão tem de ser explicada por um teste que a referência quebra**, e nenhuma exclusão pode cobrir um teste que a referência deixa verde | 20 a 30 | não |
| [harness/schema/result.schema.json](../../harness/schema/result.schema.json) (147) | campo de contagem de excluídos; `RESULT_SCHEMA_VERSION` sobe de 2 para 3 ([harness/__init__.py:17-22](../../harness/__init__.py#L17)) | 10 a 15 | não |
| [tests/test_test_patch.py](../../tests/test_test_patch.py) (149), [tests/test_harness.py](../../tests/test_harness.py) (514) | tarefa sintética cuja referência quebra um teste antigo, e que precisa sair `resolved: true`; teste de que a exclusão **não** encobre quebra fora da lista; teste do parsing de `PASSED` | 60 a 90 | não |
| `tasks/*/task.json` (hoje 33 e 20 linhas) | regeneração das 12 tarefas com lista explícita | de 33 para **1.000 a 1.700 linhas por tarefa** (tomlkit tem mais de mil testes, peewee 1.634) | não |

**Total estimado: 100 a 140 linhas de código de produção, 60 a 90 de teste, mais a regeneração dos `task.json`.** Não é um trabalho grande. O risco não está no tamanho.

### 3.4 O que NÃO muda

Detector de trapaça, guarda de caminho, pino de provedor, prompts, ferramentas do agente, telemetria, agregação de custo, medição de qualidade, `harness/evaluate.py` (fora do campo novo no dicionário de saída) e os dois braços. O agente continua vendo a suíte antiga e continua sem poder tocar em `tests/`.

### 3.5 Sim, isso toca o oráculo, e de duas formas

A primeira é óbvia: `OracleResult.resolved` e `evaluate_oracle` mudam ([harness/oracle.py:42-50,128-157](../../harness/oracle.py#L42)). Proibição explícita do documento de exigências ([EXIGENCIAS.md:7](tasks/EXIGENCIAS.md#L7)), e este relatório existe justamente para embasar ou dispensar a aprovação.

A segunda é a que quase passa despercebida e precisa estar na decisão: **excluir testes de `pass_to_pass` sem mexer na verificação de regressão não muda veredito nenhum**. `regression` roda `suite_targets or pass_to_pass` ([harness/oracle.py:142](../../harness/oracle.py#L142)) e `resolved` exige `regression.green` ([harness/oracle.py:44-50](../../harness/oracle.py#L44)). O teste antigo legitimamente quebrado continuaria reprovando por ali. Para a exclusão ter qualquer efeito é preciso **também** enfraquecer ou remover a terceira verificação, que é a mais conservadora das três. Quem aprovar o item 3 está aprovando isso.

Efeito colateral positivo, que vale registrar: `p2p` julgado por lista explícita de node ids **fecha o R4 de graça** ([01-inventario.md:276-278](01-inventario.md)), porque os node ids de `fail_to_pass` deixam de ser contados dentro de `p2p`.

---

## 4. Ressalvas de validade

**O que "resolvido" passa a significar.** Hoje significa "os testes novos passam e a suíte inteira, na versão emendada pelo upstream, está verde". Com a exclusão passa a significar "os testes novos passam e os testes que a implementação de referência mantém verdes continuam verdes". A diferença é o buraco: o agente ganha licença para quebrar **qualquer** comportamento antigo que a referência também quebrou, **e mais**, porque a lista de exclusão é definida pelo que a referência quebra, não pelo que o agente quebra. Se a referência quebra o teste X e o agente quebra o teste X de um jeito diferente e pior, ninguém percebe. E se o agente quebra o teste Y, fora da lista, aí sim é pego. O tamanho do buraco é medível e deve ser reportado: **número de node ids excluídos por tarefa**, ao lado do total da suíte.

**Interação com o detector de trapaça: nenhuma, e é bom que seja assim.** A exclusão acontece no lado do avaliador, sobre uma lista escrita em tempo de mineração. O agente continua sem poder escrever em `tests/**` ([src/seeds.py:38-54](../../src/seeds.py#L38)), a regra C1 continua crítica ([harness/cheat.py:148-159](../../harness/cheat.py#L148)), C3 continua pegando `skip`/`xfail` inserido ([harness/cheat.py:181-194](../../harness/cheat.py#L181)) e a precedência "trapaça crítica força `resolved = false`" continua valendo ([harness/evaluate.py:115](../../harness/evaluate.py#L115)). O agente não tem como influenciar a lista de exclusão: ela é derivada da referência do upstream, antes de o agente existir. **Ressalva real:** com testes fora do julgamento, um agente que quebre um comportamento antigo **dentro** da lista deixa de ser pego por qualquer mecanismo, porque o detector de trapaça não mede corretude e nunca mediu.

**Como declarar no texto do TCC.** Um parágrafo na seção de ameaças à validade, em três frases. Primeira: nas tarefas com mudança de comportamento, o critério de regressão é restrito ao conjunto de testes que a implementação de referência do projeto mantém verdes, porque o agente não tem permissão para atualizar a suíte e a mudança de comportamento invalida legitimamente parte dela. Segunda: o conjunto excluído é derivado por execução, não por julgamento, e o número de testes excluídos é reportado por tarefa. Terceira: a consequência é que regressões restritas ao conjunto excluído não são detectadas, o que torna a taxa de resolução um **limite superior** nessas tarefas, e a comparação entre os dois braços permanece válida por serem ambos medidos com a mesma régua.

**Alternativa conservadora A: excluir do estudo a tarefa cuja mudança de comportamento deixa dano colateral.** Não é toda mudança de comportamento, e a distinção importa: o critério já existe, já roda e rejeita exatamente aquelas em que a suíte não volta ao verde com o commit de correção inteiro aplicado, que são as que o oráculo não sabe julgar. É o passo 2 do minerador ([scripts/mine_tasks.py:372-381](../../scripts/mine_tasks.py#L372)). Custo de implementação: zero. Prós: o oráculo não é tocado, a proibição da E3 é respeitada, `resolved` conserva o significado forte, e a ameaça à validade some em vez de precisar de declaração. Contras: a faixa "grande" pede funcionalidade nova com teste escrito pelo projeto ([EXIGENCIAS.md:63](tasks/EXIGENCIAS.md#L63)), e funcionalidade nova costuma vir acompanhada de ajuste de teste antigo; corre-se o risco de não achar quatro tarefas grandes elegíveis. Quanto isso restringe: **não verificado**, depende da remineração ampla do item 1 da E3.

**Alternativa conservadora B: aceitar só commits que apenas acrescentam testes.** Verificável mecanicamente no `test_patch`: nenhuma linha removida fora de contexto, nenhum arquivo removido ou renomeado. Custo: cerca de 30 linhas entre `mine_tasks.py` e um portão em `validate_task.py`, sem tocar o oráculo. Prós: elimina de uma vez os casos (b), (c) e (d) da seção 2, inclusive as duas quebras mecânicas do avaliador. Contras: é mais restritivo que a alternativa A, porque descarta também o commit que apenas reindenta ou renomeia um teste antigo sem mudar comportamento nenhum.

**Alternativa conservadora C: aceitar a tarefa com mudança de comportamento sem mexer no oráculo, e declarar.** É o que a seção 1.6 mostra ser possível: se o commit corrige na mesma leva todo teste afetado, o oráculo já julga certo. Custo: zero no avaliador, mais as correções mecânicas do caso (c) e (d), que são defeito e não política. Contras: o laço do agente continua cego, e o resultado esperado é `budget: max_turns` ou reversão da correção nos **dois** braços. Isso não enviesa a comparação numa direção, mas achata os dois braços perto de zero na faixa grande, que é exatamente o que a E4 quer evitar ([EXIGENCIAS.md:78](tasks/EXIGENCIAS.md#L78)).

---

## 5. Recomendação

Recomendo **não implementar a exclusão à la SWE-bench agora**. Ela custa pouco em linhas, fecha o R4 de brinde e é tecnicamente correta, mas resolve o problema errado: nas tarefas que a E3 vai minerar, o obstáculo dominante não é o oráculo reprovar injustamente, e sim o agente não ter como saber que terminou, porque os dois braços só param com a suíte antiga verde e nenhuma exclusão no avaliador muda o que o agente enxerga. Recomendo, nesta ordem: (1) corrigir os defeitos mecânicos dos casos (c) e (d), que são bugs e não política, e que hoje derrubam a mineração inteira com `RuntimeError`; (2) adotar a alternativa A durante a remineração, isto é, manter o passo 2 como portão e relatar dois números que hoje ninguém tem: quantos candidatos da faixa grande o passo 2 rejeita por dano colateral (com o critério antigo era 1 em 90) e quantos candidatos de cada faixa trazem `altera_testes_existentes = true` no pré-filtro v2 (seção 1.7); (3) reabrir esta decisão **com esse número na mão**, porque se a faixa grande não fechar quatro tarefas sem dano colateral, o custo de 100 a 140 linhas passa a valer a pena, e aí a discussão deixa de ser hipotética. Enquanto isso, a exclusão continua descrita e dimensionada aqui, pronta para ser implementada em uma sessão.

### Decisões que só o autor pode tomar

1. **Autorizar ou não a alteração do oráculo** ([harness/oracle.py:42-50,128-157](../../harness/oracle.py#L42)), lembrando que ela implica enfraquecer ou remover a terceira verificação, a de regressão sobre a suíte inteira (seção 3.5).
2. **Escolher o significado de "resolvido"** para a faixa grande: forte, a suíte inteira verde, ou restrito, o conjunto que a referência mantém verde.
3. **Escolher a política de amostragem**: alternativa A (excluir por execução, custo zero), B (só commits aditivos), C (aceitar e declarar) ou a exclusão à la SWE-bench.
4. **Decidir se o laço do agente pode mudar**, e este é o ponto mais delicado: qualquer mexida no critério de parada do operador ou do validador ([src/arms/driver.py:103-104](../../src/arms/driver.py#L103); [src/agents/validator.py:74](../../src/agents/validator.py#L74)) é mexer na paridade entre braços, que a E2 acabou de fechar, e mostrar a suíte nova ao agente vazaria o oráculo. Minha leitura é que não há saída boa aqui, e que a resposta é evitar a tarefa, não adaptar o laço.
5. **Decidir se o R4 é corrigido junto ou separado.** A lista explícita de node ids resolve os dois de uma vez; se a exclusão for recusada, o R4 continua aberto e precisa de correção própria ou de declaração no texto.
6. **Autorizar a subida de `RESULT_SCHEMA_VERSION` de 2 para 3** ([harness/__init__.py:17-22](../../harness/__init__.py#L17)), caso a exclusão entre, porque o `result.json` muda de forma outra vez.

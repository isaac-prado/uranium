# As tarefas do estudo: commit, problema e as duas soluções

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 8 de outubro de 2026

Treze diretórios em `tasks/`, todos com `statement.md`, `test_patch.diff` (oráculo oculto), `reference/upstream.patch`, `reference/alternative.patch` e um patch de trapaça, e todos **VALIDADOS** nos quatro portões de `scripts/validate_task.py` em 08/10/2026 (saída em [dados/validacao-08-10/validate_task_final.txt](dados/validacao-08-10/validate_task_final.txt)). O desenho pede 12; a seção 5 diz qual sobra e por quê.

**Procedência, a declarar no método.** Os enunciados e as segundas soluções das onze tarefas novas foram redigidos por um assistente de IA (Claude, modelo Opus, um agente por tarefa, em 08/10/2026) a partir do teste oculto e da issue ou PR original, nunca da mensagem de commit, e revisados pelo autor. Cada trecho reproduzível foi executado no commit-base (mostra o problema) e com cada uma das duas soluções (mostra o esperado). As duas tarefas de 19/09 (`tomlkit-0001`, `sqlite-utils-0001`) foram escritas pelo autor. Nenhum enunciado cita arquivo, função ou classe interna, nem a forma da correção; nomes de API pública que o teste oculto exercita aparecem quando sem eles a tarefa seria insolúvel, e cada caso está nas ressalvas.

Faixas pela regra de [09-decisoes-do-autor.md](09-decisoes-do-autor.md), decisão 22: pequena = 1 a 2 arquivos-fonte e 10 a 50 linhas; média = 3 a 7 arquivos e 40 a 400 linhas; grande = 3 ou mais arquivos, 80 ou mais linhas, teste novo majoritário e mensagem que não é de correção.

## 1. Faixa grande (3)

### tomlkit-0002 — adicionar item com chave pontilhada pela API

- **Commit:** <https://github.com/python-poetry/tomlkit/commit/0561e5de20fdbdf6dfc50f3c4261c88604f15901> · PR [#162](https://github.com/python-poetry/tomlkit/pull/162) · issue [#160](https://github.com/python-poetry/tomlkit/issues/160). 4 arquivos-fonte, 163 linhas. Teste oculto: `tests/test_api.py::test_add_dotted_key`.
- **Problema.** A biblioteca lê e preserva chaves pontilhadas (`foo.bar = 1`) ao analisar um arquivo, mas quem monta um documento pela API não consegue gerá-las. O pedido é que `tomlkit.key()` aceite uma lista de strings e que `add()` de documento e de tabela grave `foo.bar = 1`, inclusive `a.b.c = 1` sob `[foo]`.
- **Upstream.** Move a rotina de chave pontilhada do parser para dentro do container, que passa a desdobrar a chave em `append`; o parser usa esse mesmo caminho. Desdobra de cima para baixo alterando os objetos de chave; muda padrões do `DottedKey` e cria `Key.is_multi()`.
- **Alternativa.** Parser intocado. Uma função pura em `items.py` reescreve `a.b.c = v` como `a = {b = {c = v}}` de dentro para fora, sobre cópias, e roda na entrada de `Container.append`, `Table.append` e `Table.raw_append`; daí em diante o fluxo de inserção e mesclagem não muda. Em 12 casos de borda a saída é idêntica à do upstream; suíte 744 verdes com qualquer das duas.
- **Ressalvas.** O enunciado especifica a saída caractere por caractere (`"foo.bar = 1\n"`), porque o teste compara a string inteira, e cita `tomlkit.key`, `document()`, `table()`, `add()`, `as_string()`. Menciona que a leitura já funciona (fato da issue), o que pode sugerir reaproveitar o parser, caminho do upstream. Com o upstream e com a alternativa, chave pontilhada em tabela inline gera texto inválido; fora do enunciado.

### tomlkit-0003 — visão de dicionário de tabela intermediária perde subtabela

- **Commit:** <https://github.com/python-poetry/tomlkit/commit/b29cdf0cddec5a3fc773e49ef991eaf43f0c3d24> · PR [#122](https://github.com/python-poetry/tomlkit/pull/122) · issue [#113](https://github.com/python-poetry/tomlkit/issues/113) ("Critical data loss"). 4 arquivos-fonte, 169 linhas. Teste oculto: `tests/test_toml_document.py::test_repr`.
- **Problema.** Num documento com `[tool.poetry.foo]` e `[tool.poetry.bar]`, `repr(doc)` sai certo, mas `repr(doc["tool"])` e `dict(doc["tool"])` perdem `foo`: só a última subtabela aparece. O dado está no documento; a visão de dicionário da tabela intermediária fica desatualizada.
- **Upstream.** Faz `Container`, `OutOfOrderTableProxy`, `Table` e `InlineTable` herdarem de `MutableMapping`; `__iter__`/`__len__`/`__repr__` passam a ler o container interno; remove `keys/values/items/update/get` próprios e reescreve `setdefault`. 439 linhas de diff.
- **Alternativa.** Mantém a hierarquia e o `repr` de `dict` e corrige a sincronização: ao fundir uma tabela recebida com uma existente, `Table.append` gravava na visão de dicionário o objeto recebido, não o fundido. Uma função `_mirror_entry` relê do container o item de fato guardado, usada nos cinco pontos de escrita de `Table` e `InlineTable`. 89 linhas, um arquivo.
- **Ressalvas, e esta pesa.** O teste oculto cobre um único sintoma; a mudança para `MutableMapping` e o resto do patch upstream ficam sem cobertura, e a alternativa resolve com uma mudança local. **O esforço mínimo exigido é de faixa média ou pequena, não grande.** Decidir se a tarefa fica como grande (declarando que a faixa foi atribuída pelo patch upstream, não pelo mínimo exigido) ou se é reclassificada.

### tomlkit-0004 — chaves pontilhadas na análise e na serialização (TOML 0.5.0)

- **Commit:** <https://github.com/python-poetry/tomlkit/commit/eedcdb2538326b468a59f03ff8392bd4ec348125> (2018, sem PR) · issue [#2](https://github.com/python-poetry/tomlkit/issues/2), motivação indireta (suporte à TOML 0.5.0). 3 arquivos-fonte, 101 linhas. Testes ocultos: parametrizados `[0.5.0]` em `tests/test_api.py` e `test_items.py`, mais `test_items_can_be_appended_to_and_removed_from_a_table`.
- **Problema.** (1) Aceitar chaves pontilhadas (`physical.color`, `site."google.com"`, `a.b.c`), que viram tabelas aninhadas no acesso e no `json.dumps`; (2) ida e volta exata `dumps(parse(s)) == s`; (3) manter `inf`/`nan` e inteiros hex/octal/binário no mesmo arquivo; (4) a quebra de linha que fecha `[table]` é parte do cabeçalho: `parse("[table]\n")["table"].as_string()` dá `""`.
- **Upstream.** `Key` ganha a flag `dotted`; a análise concatena as partes numa string; o laço raiz do parser quebra a chave numa cadeia de super-tabelas; `Container.as_string` ganha caso especial que remonta `prefixo.chave = valor`; `_parse_comment_trail` passa a consumir o `\n` de todo item.
- **Alternativa.** Classe nova `DottedKey(Key)` com as partes e o texto original; análise iterativa aceitando espaço em volta do ponto; o `Container` mantém tabelas implícitas num mapa `_implicit` e deixa uma âncora por linha pontilhada no lugar em que foi escrita, resolvida na serialização pelo caminho e com a grafia original. Preserva ordem intercalada (`a.x`, `b`, `a.y`) e funciona dentro de `[tabela]` e de tabela inline, casos que o upstream não suporta. O `\n` é absorvido só no cabeçalho de `[tabela]`.
- **Ressalvas.** O commit mistura duas mudanças (item 4 não tem relação com chave pontilhada; o teste chama a API interna `Parser._parse_table`, e o enunciado descreve o comportamento pela API pública). Dois testes do fail-to-pass passam assim que o exemplo volta a ser analisável. Limitações da alternativa fora da suíte: substituir a tabela implícita inteira e `[a.c]` depois de `a.b = 1`.

## 2. Faixa média (4)

### peewee-0001 — API de ganchos de execução de query

- **Commit:** <https://github.com/coleifer/peewee/commit/ab1266aaff54e96b95169c0d33db77ae9395e0ec> (28/08/2026, sem issue nem PR). 3 arquivos-fonte, 54 linhas. Testes ocultos: `tests/db_tests.py::TestQueryHooks` (4).
- **Problema.** Não havia forma suportada de observar de fora as instruções SQL executadas (tempo, métricas, tracing) sem herdar a classe do banco ou depender do log DEBUG. O pedido: cada instância de banco tem uma lista `query_hooks`; cada gancho é chamado a cada instrução com um evento que traz `sql`, `params`, `duration` e `exception`.
- **Upstream.** `QueryEvent` como `namedtuple`; `query_hooks` é uma `list`; `execute_sql` refatorado num `_execute_cursor` com try/except que cronometra só quando há ganchos e chama `_notify_hooks`; cursor nomeado do `postgres_ext` e `aexecute_sql` do `pwasyncio` repetem o padrão.
- **Alternativa.** O registro é dono do disparo: `query_hooks` é uma property sobre `QueryHooks(list)`, cujo `observe(sql, params)` devolve um context manager (nulo sem custo quando vazio) que monta o evento no `__exit__` e chama os ganchos sobre uma cópia (um gancho pode se desregistrar durante a chamada). Os três pontos de execução só ganham um `with`; sem método novo no `Database`. `QueryEvent` com `__slots__`.
- **Ressalvas.** Enunciado cita `query_hooks` (interface de lista), a assinatura do gancho, os quatro atributos do evento, `execute_sql` e `peewee.OperationalError`. Pede também os caminhos do `playhouse` (PostgreSQL, assíncrono), que o oráculo não exercita porque o venv não tem PostgreSQL nem `greenlet`; a alternativa nesses dois arquivos só passou por `py_compile`.

### peewee-0002 — seis correções num commit só

- **Commit:** <https://github.com/coleifer/peewee/commit/08b28d1487f188a178a6428e9f43203ee16607eb> (12/08/2026, sem issue). 6 arquivos-fonte, 72 linhas. Testes ocultos: 6, em `tests/sql.py`, `migrations.py`, `reflection.py`, `transactions.py`.
- **Problema (seis comportamentos independentes).** (1) `commit()`/`rollback()` com conexão fechada reabrem em silêncio; esperado `InterfaceError` sem reabrir. (2) `with db:` recusado dentro de `manual_commit()` deixa resíduo na pilha de contextos. (3) `Select.window(w1, w2)` aceita duas janelas com o mesmo alias; esperado `ValueError`. (4) `.sql()` de `INSERT ... on_conflict()` sem banco dá `TypeError`; esperado `InterfaceError`. (5) `make_index_name` do migrador encurta nomes longos de forma diferente do peewee. (6) `column_map` do introspector é o dicionário da classe e vaza entre instâncias.
- **Upstream.** (1) um `if self.is_closed(): raise` copiado em seis métodos; (2) move o `append` da pilha para depois do `__enter__`; (3) `len(set(aliases))`; (4) verificação em `OnConflict.get_conflict_statement`; (5) delega a `_truncate_constraint_name`; (6) `dict(self.column_map)` no `__init__`; reestrutura `pool.py`.
- **Alternativa.** (1) decorador único `requires_open_connection`; (2) mantém a ordem e remove da pilha em `try/except`; (3) conjunto de aliases vistos com mensagem dizendo qual repetiu; (4) verificação em `Insert.__sql__`, cobrindo `conflict_statement` e `conflict_update`; (5) reimplementa o esquema em `make_index_name` com parâmetro `maxlen`; (6) `ChainMap({}, type(self).column_map)`. Não toca `pool.py`.
- **Ressalvas, e estas pesam.** Como tarefa é uma lista de seis bugs, não um bug; três testes olham detalhes internos (`db._state.ctx`, `_truncate_constraint_name`, identidade de `column_map`), e no item 5 o enunciado precisou dar a regra de truncamento por extenso. Nos itens 1 e 5 o espaço de solução é pequeno. **Candidata a sair do conjunto** (seção 5).

### sqlite-utils-0003 — colunas de nome repetido em resultados de consulta

- **Commit:** <https://github.com/simonw/sqlite-utils/commit/07b603e562af19f80c3d00eb59b9cf29331127ce> · PR [#773](https://github.com/simonw/sqlite-utils/pull/773) · issue [#624](https://github.com/simonw/sqlite-utils/issues/624). 3 arquivos-fonte, 45 linhas. Testes ocultos: 7 (12 node ids com parametrização).
- **Problema.** Consulta com colunas de mesmo nome (junção com `id` dos dois lados) devolve dicionários em que o último valor sobrescreve os anteriores, em `db.query()`, `rows_where(select=...)`, `search(columns=...)` e no JSON da CLI. Esperado: primeira ocorrência com o nome original e repetições como `id_2`, `id_3`, pulando sufixo que já seja nome real (`select 1 as id, 2 as id, 3 as id_2` → `{"id": 1, "id_3": 2, "id_2": 3}`).
- **Upstream.** `utils.dedupe_keys()` testa sufixos a partir de 2 contra um conjunto de vistos e outro de originais, chamada nos quatro pontos de `db.py`; na CLI a deduplicação fica em `output_rows()`, usada por toda saída JSON.
- **Alternativa.** `dedupe_keys` com um único conjunto de reservados e contador por nome que continua de onde parou; um helper `_rows_as_dicts(description, rows)` centraliza a conversão de cursor para dicionário nos quatro pontos; na CLI a deduplicação acontece só no ramo JSON de `_execute_query`, deixando CSV/TSV/tabela com os cabeçalhos originais. Suíte 1199 verdes.
- **Ressalvas.** O enunciado cita `sqlite_utils.utils.dedupe_keys` com a tabela de sete entradas e saídas, porque um teste a chama diretamente; revela que existe uma função auxiliar de renomeação, não onde aplicá-la.

### attrs-0001 — `has` e `fields` em classes genéricas especializadas

- **Commit:** <https://github.com/python-attrs/attrs/commit/4fcd15bddbc96fd23d3218493c831a0e38b1cd86> · PR [#1079](https://github.com/python-attrs/attrs/pull/1079). 3 arquivos-fonte, 46 linhas. Testes ocultos: 3. Primeiro repositório com src layout no estudo.
- **Problema.** Uma classe `attrs` que herda de `typing.Generic` não é reconhecida quando passada especializada: `attrs.has(A[str])` dá `False` e `attrs.fields(A[str])` levanta `TypeError: Passed object must be a class.`; para genérico que não é `attrs`, o erro certo seria `NotAnAttrsClassError`.
- **Upstream.** Auxiliar em `_compat.py` que importa o privado `typing._GenericAlias`, testa `cl.__class__ is _GenericAlias` para chegar a `__origin__`, e grava os atributos no alias como cache.
- **Alternativa.** Sem API privada e sem cache: função em `_make.py` que traduz o objeto para a classe que representa via `typing.get_origin()` (se a origem for `type`), e uma busca que concentra o `TypeError` e a leitura de `__attrs_attrs__`; `fields`, `fields_dict` e `has` a usam. Estende o suporte a `fields_dict`.
- **Ressalvas.** Um quarto teste do `test_patch` já passa na base e entrou como critério de não regressão. A alternativa também resolve `fields(Annotated[A, ...])`, caso sem teste.

## 3. Faixa pequena (6)

### tomlkit-0001 — elemento malformado em array descartado em silêncio (autor, 19/09)

- **Commit:** <https://github.com/python-poetry/tomlkit/commit/d548e18b71b28d0e9628127bf0b9dfc5a254dca0> · PR [#527](https://github.com/python-poetry/tomlkit/pull/527). 1 arquivo, 9 linhas.
- **Problema.** `Parser("a = [{1]").parse()` não falha: descarta o elemento inválido e devolve o array truncado. Esperado: `UnexpectedCharError`.
- **Upstream** e **alternativa**: ver `tasks/tomlkit-0001/reference/`; a alternativa troca a estrutura do `try/except` do parser (guarda a exceção e relança fora do bloco) em vez de replicar o diff upstream.

### sqlite-utils-0001 — (autor, 19/09; reclassificada de média para pequena em 08/10: 1 arquivo, 34 linhas)

- **Commit e issue:** ver `tasks/sqlite-utils-0001/task.json` (issue [#794](https://github.com/simonw/sqlite-utils/issues/794)).

### tomlkit-0005 — escalares lidos de um documento passam por sequência

- **Commit:** <https://github.com/python-poetry/tomlkit/commit/94e62fbef9d16093dec86728888474197f4a5cc7> · PR [#563](https://github.com/python-poetry/tomlkit/pull/563) · issue [#562](https://github.com/python-poetry/tomlkit/issues/562). 2 arquivos, 19 linhas. Teste oculto: `tests/test_items.py::test_float_is_not_a_sequence`.
- **Problema.** `Float`, `Integer` e datas devolvidos por `parse` são reconhecidos pelo CPython como sequências (`PySequence_Check` = 1, `iter()` aceita), e `torch`/`numpy` quebram com "object of type 'Float' has no len()".
- **Upstream.** Apaga de `Item` os `__getitem__`/`__setitem__`/`__delitem__` que só levantavam `TypeError` e remove os `type: ignore` das subclasses.
- **Alternativa.** Move as três declarações para um bloco `if TYPE_CHECKING:` em `Item`, como stubs: em execução a classe não os define, e o mypy continua vendo `Item` como indexável.
- **Ressalva.** Em execução o efeito é o mesmo do upstream; a diferença está em separar declaração estática de comportamento. É a alternativa mais fraca do conjunto. O enunciado cita `PySequence_Check` via `ctypes`, que é o que o teste exercita, e mostra que `iter(Float)` funciona hoje, pista indireta da causa.

### peewee-0003 — `choices` de `EnumField` preenchido a partir do enum

- **Commit:** <https://github.com/coleifer/peewee/commit/b1faea2b495b25f0c9d9cc9610b3bc239e729684> (sem issue). 2 arquivos, 11 linhas. Teste oculto: `tests/extra_fields.py::TestEnumField::test_enum_choices`.
- **Problema.** `EnumField` e `IntEnumField` (`playhouse.fields`) deixam `choices` em `None` quando o usuário não informa; esperado: pares `(valor, nome)` dos membros na ordem declarada, com `choices` explícito prevalecendo.
- **Upstream.** `kwargs.setdefault('choices', ...)` no construtor e, em `to_pydantic`, descarta `choices` quando o campo tem `enum_class`.
- **Alternativa.** `choices` vira property com getter/setter na classe dos campos de enum (setter guarda o explícito, getter calcula do enum na leitura); em `to_pydantic` a checagem é pelo tipo resolvido ser subclasse de `enum.Enum`.
- **Ressalvas.** O `test_patch` também altera `tests/pydantic_utils.py`, fora dos `suite_targets` (pydantic não instalado); conferido à parte, 32 verdes. Com `choices=None` explícito o upstream mantém `None` e a alternativa devolve os pares, caso sem teste. É funcionalidade pequena, `kind: feature`.

### sqlite-utils-0002 — string vazia vira NULL ao converter coluna de texto para numérica

- **Commit:** <https://github.com/simonw/sqlite-utils/commit/e4935e064407bc995f77795c025c33cef52d742e> · PR [#805](https://github.com/simonw/sqlite-utils/pull/805) · issue [#488](https://github.com/simonw/sqlite-utils/issues/488). 1 arquivo-fonte, 21 linhas. Testes ocultos: 11 node ids.
- **Problema.** Depois de importar CSV (tudo `TEXT`, vazios como `""`), `table.transform(types=...)` para `int`/`float` converte os números mas deixa `""` dentro da coluna numérica; esperado `NULL`. `" "` e `NULL` ficam como estão.
- **Upstream.** Separa as colunas que eram texto cujo novo tipo está numa lista fixa `{"INTEGER", "REAL", "FLOAT", "NUMERIC"}` e um `_copy_expr` as envolve em `NULLIF(col, '')` no `SELECT`.
- **Alternativa.** Sem lista fixa: classifica o tipo novo pelas regras de afinidade do SQLite reaproveitando `column_affinity` de `utils.py`, no mesmo laço que resolve os tipos, gravando um mapa coluna → expressão que o `INSERT ... SELECT` consulta.
- **Ressalva.** Seis testes comparam o SQL exato de `transform_sql()`, então o enunciado mostra `NULLIF("<coluna>", '')` como saída esperada da API pública: revela parte do "como".

### pygments-0001 — lexer de Go: tipos, literais e operadores

- **Commit:** <https://github.com/pygments/pygments/commit/9c436b34ccafdf9376527f66c6e587ffe0d1b84c> · PR [#3199](https://github.com/pygments/pygments/pull/3199). 1 arquivo-fonte, 26 linhas. Teste oculto: fixtures `tests/examplefiles/go/3199.go` e `generics.go` (comparação de tokens inteira).
- **Problema.** `float` tratado como tipo; conversões `float64(x)` como função embutida; `map`/`chan` como declaração; `0o755`, `0b1010`, `1_000_000`, `0x_fe` partidos; `!`, `=`, `<`, `>`, `^` como pontuação e `^=` partido; `...` e `~` como operador.
- **Upstream.** Ajusta as listas de palavras, mantém quatro regras de inteiro (uma por base) aceitando `_` e reescreve as duas regex de operador e pontuação.
- **Alternativa.** Tabelas da especificação em constantes de módulo (`GO_TYPES`, `GO_BUILTIN_FUNCS`, `GO_OPERATORS`) reconhecidas por `words()`; uma única regra de inteiro cujo tipo de token é decidido por callback pelo prefixo; operadores e pontuação como listas explícitas com casamento mais longo. Zero diferenças em 200 mil fragmentos aleatórios e em todos os `.go` de `tests/`; suíte 5297 verdes.
- **Ressalva.** Na parte dos tipos a alternativa se parece com o upstream (há essencialmente uma correção possível); a diferença real está nos inteiros e nos operadores.

## 4. Contagem por faixa, depois das reclassificações de 08/10

| Faixa | Tarefas | Total |
|---|---|---|
| grande | tomlkit-0002, tomlkit-0003 (ver ressalva), tomlkit-0004 | 3 |
| média | peewee-0001, peewee-0002 (ver ressalva), sqlite-utils-0003, attrs-0001 | 4 |
| pequena | tomlkit-0001, sqlite-utils-0001, tomlkit-0005, peewee-0003, sqlite-utils-0002, pygments-0001 | 6 |

## 5. O que o autor decide a partir daqui

1. **Qual das 13 sai, para fechar 12.** Candidata: `peewee-0002`, por ser seis bugs sem relação num commit só. Saindo ela, a média fica com 3; a substituta mais limpa em `mined-v4/` é `tomlkit 4424dcdc` ("No longer add a new line before standalone tables", 4 arquivos, 77 linhas, 1 teste novo) ou `tomlkit 21e186f6` (140 linhas). Alternativa: tirar uma pequena e manter `peewee-0002` declarando a natureza composta.
2. **`tomlkit-0003` como grande.** O teste oculto exige uma mudança local; a faixa foi atribuída pelo tamanho do patch upstream. Manter e declarar, ou reclassificar como média (e aí a grande fica com 2).
3. **Enunciados que mostram parte do "como"** (`sqlite-utils-0002`: `NULLIF`; `sqlite-utils-0003`: `dedupe_keys`): inevitáveis dado o teste, mas o autor pode aprovar ou pedir reescrita com teste oculto reduzido (o que mudaria o `fail_to_pass`).
4. **Alternativa fraca em `tomlkit-0005`** (mesmo efeito em execução): aceitar, ou pedir outra abordagem.

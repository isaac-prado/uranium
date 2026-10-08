# Colunas com nome repetido somem dos resultados de consulta

## O problema

Quando uma consulta devolve duas ou mais colunas com o mesmo nome, cada
linha do resultado chega como um dicionário em que só sobra uma delas: o
valor da última ocorrência sobrescreve os anteriores, sem erro nem aviso.

O caso mais comum é uma junção entre tabelas que têm colunas de mesmo nome,
como `select d1.*, d2.* from delta d1 join delta d2 ...`, mas acontece com
qualquer consulta que repita um nome de coluna. O defeito aparece em todos
os pontos da biblioteca que entregam linhas como dicionários:

- `db.query(sql)`;
- `table.rows_where(select=...)`, quando o `select` repete uma coluna;
- `table.search(q, columns=[...])`, quando `columns` repete uma coluna;
- a saída JSON padrão da linha de comando `sqlite-utils <banco> "<sql>"`.

## Como reproduzir

```python
import sqlite_utils

db = sqlite_utils.Database(memory=True)
db["one"].insert({"id": 1, "value": "left"})
db["two"].insert({"id": 2, "value": "right"})

# Junção de duas tabelas que têm colunas com o mesmo nome
print(list(db.query("select one.id, two.id, one.value, two.value from one, two")))
# hoje: [{'id': 2, 'value': 'right'}]

# Repetição junto com uma coluna real chamada id_2
print(list(db.query("select 1 as id, 2 as id, 3 as id_2")))
# hoje: [{'id': 2, 'id_2': 3}]

# rows_where() com a mesma coluna duas vezes no select
db["dogs"].insert({"id": 1, "name": "Cleo"})
print(list(db["dogs"].rows_where(select="id, id, name")))
# hoje: [{'id': 1, 'name': 'Cleo'}]

# search() pedindo a mesma coluna duas vezes
db["docs"].insert({"text": "tanuki are running tricksters", "country": "Japan"})
db["docs"].enable_fts(["text", "country"], fts_version="FTS4")
print(list(db["docs"].search("tanuki", columns=["text", "text"])))
# hoje: [{'text': 'tanuki are running tricksters'}]
```

Na linha de comando (o mesmo vale para um arquivo de banco no lugar de
`memory`):

```
$ python -m sqlite_utils memory "select 1 as id, 2 as id, 'x' as value, 'y' as value"
[{"id": 2, "value": "y"}]
```

## Comportamento esperado

Nenhum valor pode se perder. A primeira ocorrência de um nome fica como
está; cada repetição seguinte ganha um sufixo numérico `_N`, em que `N`
começa em 2 e avança até dar um nome que não colida com nenhum outro nome
de coluna da mesma consulta, seja um nome original, seja um já atribuído a
uma repetição anterior. A ordem das colunas é preservada.

Para o trecho acima, a saída esperada é:

```
[{'id': 1, 'id_2': 2, 'value': 'left', 'value_2': 'right'}]
[{'id': 1, 'id_3': 2, 'id_2': 3}]
[{'id': 1, 'id_2': 1, 'name': 'Cleo'}]
[{'text': 'tanuki are running tricksters', 'text_2': 'tanuki are running tricksters'}]
```

No segundo caso, a repetição de `id` não pode virar `id_2`, porque isso
apagaria a coluna real `id_2`; ela vira `id_3`.

E na linha de comando:

```
$ python -m sqlite_utils memory "select 1 as id, 2 as id, 'x' as value, 'y' as value"
[{"id": 1, "id_2": 2, "value": "x", "value_2": "y"}]
```

A regra de renomeação também precisa estar disponível como função pública
`dedupe_keys` no módulo `sqlite_utils.utils`: recebe uma lista de nomes de
coluna e devolve uma nova lista, do mesmo tamanho e na mesma ordem, com os
nomes já sem repetição. Exemplos exatos:

| entrada                          | saída                                |
|----------------------------------|--------------------------------------|
| `[]`                             | `[]`                                 |
| `["id", "name"]`                 | `["id", "name"]`                     |
| `["id", "id"]`                   | `["id", "id_2"]`                     |
| `["id", "id", "id"]`             | `["id", "id_2", "id_3"]`             |
| `["id", "id", "id_2"]`           | `["id", "id_3", "id_2"]`             |
| `["id_2", "id", "id"]`           | `["id_2", "id", "id_3"]`             |
| `["id", "id", "id_2", "id_2"]`   | `["id", "id_3", "id_2", "id_2_2"]`   |

## O que não pode mudar

As saídas da linha de comando que não montam dicionários continuam
mostrando os cabeçalhos exatamente como o SQLite os devolve, com as
repetições. Por exemplo, `--csv`:

```
$ python -m sqlite_utils memory "select 1 as id, 2 as id" --csv
id,id
1,2
```

Consultas sem nomes repetidos continuam devolvendo exatamente o que
devolvem hoje.

## Critérios de aceitação

- `db.query("select one.id, two.id, one.value, two.value from one, two")`,
  com `one = {"id": 1, "value": "left"}` e `two = {"id": 2, "value": "right"}`,
  devolve `[{"id": 1, "id_2": 2, "value": "left", "value_2": "right"}]`.
- `db.query("select 1 as id, 2 as id, 3 as id_2")` devolve
  `[{"id": 1, "id_3": 2, "id_2": 3}]`.
- `table.rows_where(select="id, id, name")` numa tabela com a linha
  `{"id": 1, "name": "Cleo"}` devolve `[{"id": 1, "id_2": 1, "name": "Cleo"}]`.
- `table.search("tanuki", columns=["text", "text"])` numa tabela com busca
  textual (FTS4) devolve as linhas com as chaves `text` e `text_2`, ambas com
  o valor da coluna `text`.
- `sqlite-utils <banco> "select 1 as id, 2 as id, 'x' as value, 'y' as value"`
  imprime `[{"id": 1, "id_2": 2, "value": "x", "value_2": "y"}]`.
- `sqlite_utils.utils.dedupe_keys` produz exatamente a saída da tabela
  acima para cada uma das sete entradas.
- `sqlite-utils <banco> "select 1 as id, 2 as id" --csv` continua
  imprimindo `id,id` e `1,2`, e nenhum outro comportamento existente da
  biblioteca é alterado.

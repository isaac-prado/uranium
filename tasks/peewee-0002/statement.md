# Seis comportamentos incorretos em transações, consultas, migrações e reflexão

Esta tarefa reúne seis defeitos independentes observados por quem usa o
peewee. Todos precisam ser corrigidos. Os trechos abaixo rodam a partir da
raiz do repositório, com SQLite em memória.

## 1. `commit()` e `rollback()` com a conexão fechada reabrem uma conexão em silêncio

### Comportamento observado

Depois de `db.close()`, chamar `db.commit()` ou `db.rollback()` abre uma
conexão nova sem avisar e executa o `COMMIT`/`ROLLBACK` nela. A transação que
se queria encerrar já se perdeu junto com a conexão antiga, então a operação
não tem sentido: no SQLite o resultado é um erro enganoso de "nenhuma
transação ativa", e o banco fica com uma conexão aberta que ninguém pediu.

```python
from peewee import SqliteDatabase, InterfaceError

db = SqliteDatabase(':memory:')
db.connect()
db.close()

for operacao in (db.commit, db.rollback):
    try:
        operacao()
        print(operacao.__name__, '-> sem InterfaceError')
    except InterfaceError as exc:
        print(operacao.__name__, '-> InterfaceError:', exc)
    except Exception as exc:
        print(operacao.__name__, '->', type(exc).__name__, exc)
    print('  conexão fechada depois?', db.is_closed())
    if not db.is_closed():
        db.close()
```

Hoje cada chamada termina em `OperationalError` e `is_closed()` passa a
`False`.

### Comportamento esperado

Com a conexão fechada, `commit()` e `rollback()` levantam `InterfaceError` e
não abrem conexão nenhuma: depois da chamada, `db.is_closed()` continua
`True`. O mesmo vale para os outros bancos SQLite do pacote de extensões que
têm `commit()`/`rollback()` próprios.

## 2. Um `with db:` recusado deixa o banco num estado que impede o fechamento automático

### Comportamento observado

Dentro de `db.manual_commit()`, usar `with db:` é proibido e levanta
`ValueError`, como esperado. Mas a tentativa recusada deixa um resquício: a
partir daí, blocos como `with db.connection_context():` (ou outro `with db:`)
deixam de fechar a conexão ao sair, porque o banco "acha" que ainda há um
bloco `with db:` externo em andamento.

```python
from peewee import SqliteDatabase

db = SqliteDatabase(':memory:')
db.connect()

with db.manual_commit():
    try:
        with db:          # proibido dentro de manual_commit()
            pass
    except ValueError as exc:
        print('ValueError:', exc)

with db.connection_context():
    pass
print('fechada ao sair de connection_context()?', db.is_closed())
```

Hoje a última linha imprime `False`.

### Comportamento esperado

Uma entrada em `with db:` que falha não deixa rastro: o `ValueError`
continua sendo levantado, e o banco volta ao mesmo estado de antes da
tentativa. Ao sair de `connection_context()` (ou de um `with db:` posterior)
a conexão é fechada normalmente.

## 3. `window()` aceita duas janelas com o mesmo alias e gera SQL inválido

### Comportamento observado

`Window` recebe o alias `w` quando nenhum é informado. Passar a
`Select.window()` duas janelas sem alias explícito produz uma cláusula
`WINDOW` com o nome `"w"` definido duas vezes. Bancos como o PostgreSQL
rejeitam esse SQL só na hora de executar; o SQLite aceita sem reclamar e usa
apenas uma das definições, de modo que a função `OVER "w"` passa a ser
calculada sobre uma janela diferente da pedida, sem erro algum.

```python
from peewee import *

db = SqliteDatabase(':memory:')

class Registro(Model):
    categoria = TextField()
    valor = IntegerField()
    class Meta:
        database = db

w1 = Window(partition_by=[Registro.categoria])
w2 = Window(order_by=[Registro.valor])      # ambas ficam com o alias padrão
consulta = Registro.select(fn.AVG(Registro.valor).over(w1))

try:
    print(consulta.window(w1, w2).sql())
except ValueError as exc:
    print('ValueError:', exc)

print(consulta.window(w1, w2.alias('w2')).sql())   # aliases distintos: ok
```

Hoje a primeira chamada imprime `... WINDOW "w" AS (...), "w" AS (...)`.

### Comportamento esperado

`window()` levanta `ValueError` na própria chamada quando duas das janelas
passadas têm o mesmo alias. Com aliases distintos (por exemplo
`w2.alias('w2')`), a chamada continua funcionando como hoje.

## 4. `INSERT ... ON CONFLICT` sem banco associado falha com `TypeError` obscuro

### Comportamento observado

A sintaxe de `ON CONFLICT` depende do banco (SQLite, PostgreSQL e MySQL
escrevem de formas diferentes). Quando a consulta não está associada a
nenhum banco, gerar o SQL dela estoura um `TypeError: 'NoneType' object is
not callable`, que não diz nada a quem usa a biblioteca.

```python
from peewee import Table, InterfaceError

KV = Table('kv', ('key', 'value'))     # tabela sem banco associado
consulta = KV.insert(key='k1', value='v1').on_conflict(
    conflict_target=(KV.key,), preserve=(KV.value,))

try:
    print(consulta.sql())
except InterfaceError as exc:
    print('InterfaceError:', exc)
except Exception as exc:
    print(type(exc).__name__ + ':', exc)
```

### Comportamento esperado

Gerar o SQL de um `INSERT` com `on_conflict(...)` sem banco associado levanta
`InterfaceError` com mensagem que explique que a consulta precisa estar
associada a um banco. Consultas associadas a um banco continuam gerando o
mesmo SQL de hoje.

## 5. `make_index_name` do migrador trunca nomes longos de um jeito diferente do resto do peewee

### Comportamento observado

Quando o nome de um índice passa de 64 caracteres, o peewee o encurta. Ao
criar tabelas a partir de um modelo, ele usa um esquema; a função pública
`make_index_name` de `playhouse.migrate` usa outro. Resultado: para a mesma
tabela e as mesmas colunas, o índice criado pelo modelo e o nome que o
migrador calcula não coincidem, e uma migração que tente referenciar
(remover, recriar) o índice pelo nome erra o alvo.

```python
from peewee import *
from playhouse.migrate import make_index_name

db = SqliteDatabase(':memory:')

class Evento(Model):
    nome_do_cliente_responsavel = TextField()
    data_de_criacao_do_registro = TextField()
    class Meta:
        database = db
        table_name = 'tabela_de_eventos_do_sistema'
        legacy_table_names = False
        indexes = ((('nome_do_cliente_responsavel',
                     'data_de_criacao_do_registro'), False),)

db.create_tables([Evento])
do_modelo = [i.name for i in db.get_indexes('tabela_de_eventos_do_sistema')][0]
do_migrador = make_index_name('tabela_de_eventos_do_sistema',
                              ['nome_do_cliente_responsavel',
                               'data_de_criacao_do_registro'])
print('criado pelo modelo:', do_modelo, len(do_modelo))
print('make_index_name:   ', do_migrador, len(do_migrador))
print('iguais?', do_modelo == do_migrador)
```

Hoje os dois nomes têm 64 caracteres mas são diferentes.

### Comportamento esperado

`make_index_name(tabela, colunas)` produz exatamente o mesmo nome que o
peewee usa para os índices e restrições que ele mesmo gera: o nome completo
é `tabela_coluna1_coluna2...`; se tiver até 64 caracteres, fica como está;
se passar disso, vira os primeiros 56 caracteres, seguidos de `_` e dos 7
primeiros dígitos hexadecimais do MD5 do nome completo (64 caracteres no
total). No exemplo acima, os dois nomes passam a ser iguais.

## 6. O mapa de tipos de coluna da reflexão é compartilhado entre todos os introspectors

### Comportamento observado

Em `playhouse.reflection`, `Introspector.from_database(db).metadata.column_map`
é o próprio mapa padrão da classe de metadados, não uma cópia. Tudo o que um
introspector acrescenta a ele (por exemplo, tipos descobertos consultando um
servidor PostgreSQL específico, cujos identificadores variam de servidor para
servidor) vaza para todos os introspectors criados depois, inclusive de
outros bancos.

```python
from peewee import SqliteDatabase, TextField
from playhouse.reflection import Introspector

a = Introspector.from_database(SqliteDatabase(':memory:'))
a.metadata.column_map['tipo_inventado'] = TextField

b = Introspector.from_database(SqliteDatabase(':memory:'))
print('vazou para outro introspector?', 'tipo_inventado' in b.metadata.column_map)
print('mapa da instância é o mesmo objeto do mapa da classe?',
      a.metadata.column_map is type(a.metadata).column_map)
```

Hoje as duas linhas imprimem `True`.

### Comportamento esperado

Cada objeto de metadados tem o seu próprio `column_map`, que não é o mesmo
objeto que `type(metadata).column_map`. Ele começa com todos os tipos do mapa
padrão, mas alterações feitas nele não aparecem no mapa da classe nem em
outros introspectors.

## Critérios de aceitação

- Com a conexão fechada, `db.commit()` e `db.rollback()` levantam
  `InterfaceError`, e `db.is_closed()` continua `True` depois de cada chamada.
- Depois de um `with db:` recusado com `ValueError` dentro de
  `db.manual_commit()`, sair de `db.connection_context()` fecha a conexão.
- `query.window(w1, w2)` levanta `ValueError` quando `w1` e `w2` têm o mesmo
  alias; `query.window(w1, w2.alias('w2'))` funciona.
- `.sql()` de um `INSERT ... on_conflict(...)` sem banco associado levanta
  `InterfaceError`.
- `make_index_name` devolve, para nomes longos, o mesmo nome de 64 caracteres
  que o peewee gera para índices de modelo (56 caracteres + `_` + 7 dígitos
  hexadecimais do MD5 do nome completo); nomes curtos não mudam.
- `introspector.metadata.column_map` não é o mesmo objeto que
  `type(introspector.metadata).column_map`, e incluir uma chave nele não a
  inclui no mapa da classe.
- Nenhum comportamento já existente muda além desses; a suíte de testes
  continua passando.

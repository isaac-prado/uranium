# Perda silenciosa de dados ao alterar tabela dentro de transação

## O problema

Alterar o schema de uma tabela referenciada por chave estrangeira com ação
destrutiva no `ON DELETE` apaga ou zera dados de outras tabelas, sem aviso,
quando a alteração acontece dentro de uma transação aberta.

Fora de transação o mesmo comando funciona corretamente e nada é perdido.

A causa é uma limitação do SQLite: o `PRAGMA foreign_keys` não tem efeito
enquanto uma transação está aberta. A biblioteca desliga esse pragma antes
de alterar uma tabela justamente para proteger os dados, mas dentro de uma
transação esse desligamento é ignorado, e as ações de `ON DELETE` disparam
quando a tabela original é descartada.

## Como reproduzir

```python
import sqlite_utils

db = sqlite_utils.Database(memory=True)
db.conn.execute("PRAGMA foreign_keys=ON")
db.executescript("""
    CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT);
    CREATE TABLE books (
        id INTEGER PRIMARY KEY,
        title TEXT,
        author_id INTEGER REFERENCES authors(id) ON DELETE CASCADE
    );
""")
db["authors"].insert({"id": 1, "name": "Ursula K. Le Guin"})
db["books"].insert({"id": 1, "title": "The Dispossessed", "author_id": 1})

with db.atomic():
    db["authors"].transform(rename={"name": "author_name"})

print(list(db["books"].rows))
# hoje imprime []  -- o livro sumiu
# nenhum erro foi levantado
```

## Comportamento esperado

A operação deve ser **recusada** em vez de executada, levantando
`sqlite_utils.db.TransactionError` — que já existe na biblioteca.

A mensagem do erro precisa permitir que a pessoa entenda e resolva o
problema, então tem de conter:

- o nome da tabela que está sendo alterada;
- o nome de cada tabela que a referencia com ação destrutiva;
- a ação de `ON DELETE` de cada uma dessas referências, em maiúsculas
  (`CASCADE`, `SET NULL`, `SET DEFAULT`), independentemente de como foi
  escrita no schema.

São destrutivas as ações `CASCADE`, `SET NULL` e `SET DEFAULT`. Referência
sem ação de `ON DELETE`, ou com `NO ACTION` / `RESTRICT`, não é destrutiva e
não deve impedir a operação.

Quando nada é recusado, o estado do banco tem de continuar exatamente como
estava: nenhuma alteração de schema, nenhuma linha perdida, e o
`PRAGMA foreign_keys` no valor em que estava antes.

O caso de uma tabela que referencia a si mesma com ação destrutiva também
precisa ser recusado.

## O que não pode mudar

Fora de transação, alterar tabela continua funcionando como antes, inclusive
quando existem chaves estrangeiras destrutivas apontando para ela. E dentro
de transação, a operação continua permitida quando não há nenhuma referência
destrutiva, ou quando o `PRAGMA foreign_keys` está desligado.

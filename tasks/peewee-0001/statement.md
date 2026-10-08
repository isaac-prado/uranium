# Ganchos para observar cada instrução SQL executada

## O pedido

Hoje não há uma forma suportada de acompanhar, de fora, as instruções SQL que
um banco do peewee executa. Quem quer medir o tempo das consultas, contar
queries por requisição, mandar dados para uma ferramenta de observabilidade
(métricas, tracing) ou registrar as consultas que falharam acaba tendo de
herdar a classe do banco ou depender do log em nível DEBUG, que só traz o
texto da consulta, sem duração nem resultado.

O pedido é uma API pública de ganchos: o usuário registra funções no objeto
de banco e o peewee as chama a cada instrução SQL executada, informando o
que foi executado, quanto demorou e se deu erro.

## Interface desejada

- Todo objeto de banco (`SqliteDatabase`, `PostgresqlDatabase`,
  `MySQLDatabase` e derivados) expõe o atributo `query_hooks`, uma lista
  (com a interface de `list`) de funções registradas. Ela começa vazia e é
  própria de cada instância: registrar um gancho num banco não afeta nenhum
  outro, e um banco recém-criado tem `query_hooks == []`.
- Registrar é acrescentar à lista (`db.query_hooks.append(f)`); desregistrar
  é removê-la da lista (`db.query_hooks.remove(f)`, `del db.query_hooks[:]`).
- Um gancho é qualquer chamável que recebe um único argumento posicional, o
  evento. O valor de retorno é ignorado.
- Os ganchos são chamados uma vez por instrução SQL executada pelo banco,
  depois que ela termina, na ordem em que foram registrados. Isso vale tanto
  para `db.execute_sql(...)` direto quanto para tudo que passa por ele (as
  consultas montadas por modelos: `create`, `select`, `count()` etc.). Uma
  chamada que executa uma única instrução gera exatamente um evento.
- O evento tem os atributos:
  - `sql`: o texto SQL executado (`str`);
  - `params`: os parâmetros, do jeito que foram passados para a execução
    (por exemplo `['u1']` num `INSERT` de um campo);
  - `duration`: tempo de execução em segundos (`float`, `>= 0`);
  - `exception`: `None` se a instrução deu certo; se falhou, a exceção que o
    chamador vai receber (a exceção do peewee, por exemplo
    `peewee.OperationalError`, não a do driver).
- Em caso de erro na instrução, os ganchos são chamados antes de a exceção
  chegar ao chamador, e a exceção continua sendo propagada normalmente.
- Erro dentro de um gancho não é engolido: a exceção levantada pelo gancho
  chega a quem executou a consulta.
- Os demais caminhos de execução de SQL que já existem nas extensões do
  `playhouse` (cursores nomeados do PostgreSQL, a API assíncrona) devem
  notificar os ganchos da mesma forma.

## Exemplo de uso

Rodável a partir da raiz do repositório. Hoje a linha
`db.query_hooks.append(registrar)` falha com
`AttributeError: 'SqliteDatabase' object has no attribute 'query_hooks'`.

```python
from peewee import SqliteDatabase, Model, CharField, OperationalError

db = SqliteDatabase(':memory:')

class User(Model):
    username = CharField()

    class Meta:
        database = db

db.create_tables([User])

eventos = []

def registrar(evento):
    eventos.append(evento)

db.query_hooks.append(registrar)          # registra

User.create(username='u1')
ev = eventos[-1]
print(ev.sql, ev.params, ev.duration >= 0, ev.exception)
# INSERT INTO "user" ("username") VALUES (?) ['u1'] True None

try:
    db.execute_sql('select * from tabela_inexistente')
except OperationalError:
    pass
print(type(eventos[-1].exception).__name__)   # OperationalError

print(SqliteDatabase(':memory:').query_hooks)  # [] (cada instância tem a sua)

db.query_hooks.remove(registrar)          # desregistra
User.select().count()
print(len(eventos))                       # 2: nada novo depois de remover
```

## Critérios de aceitação

- `db.query_hooks` existe em todo banco, é uma lista vazia num banco novo e
  não é compartilhada entre instâncias.
- Depois de `Model.create(...)`, o último evento tem `'INSERT'` em `sql`, os
  parâmetros passados em `params`, `duration >= 0` e `exception is None`.
- `Model.select().count()` gera exatamente um evento novo, cujo `sql`
  começa com `SELECT`.
- `db.execute_sql` com SQL inválido levanta `peewee.OperationalError` e o
  último evento traz essa mesma classe de exceção em `exception` e o texto
  executado em `sql`.
- Um gancho que levanta exceção faz essa exceção chegar ao chamador de
  `execute_sql`.
- Sem ganchos registrados, nada muda no comportamento atual; o restante da
  suíte de testes continua passando.

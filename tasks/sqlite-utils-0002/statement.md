# Strings vazias sobrevivem à conversão de coluna de texto para tipo numérico

## O problema

Um caso comum é importar um CSV: todas as colunas chegam como `TEXT`, e
campos sem valor chegam como string vazia (`""`). Depois disso, quem usa a
biblioteca chama `table.transform(types=...)` para converter as colunas
numéricas para `int` ou `float`.

Os valores numéricos são convertidos, mas as strings vazias continuam
lá como `""`, agora dentro de uma coluna declarada `INTEGER` ou `REAL`. O
resultado é uma coluna numérica com texto misturado: somas, médias e
comparações passam a se comportar de forma estranha, e quem lê a tabela
precisa tratar dois jeitos diferentes de "sem valor" (`NULL` e `""`).

O mesmo vale para o SQL devolvido por `table.transform_sql(types=...)`, que
descreve a operação sem executá-la: a cópia dos dados para a tabela nova
lê a coluna como está, sem nenhum tratamento do vazio.

## Como reproduzir

```python
import sqlite_utils

db = sqlite_utils.Database(memory=True)
db["medidas"].insert_all(
    [
        {"id": 1, "idade": "3", "peso": "2.5"},
        {"id": 2, "idade": "", "peso": ""},
        {"id": 3, "idade": None, "peso": None},
        {"id": 4, "idade": " ", "peso": " "},
    ],
    pk="id",
)

# SQL que a conversão vai executar (a segunda instrução copia os dados)
print(db["medidas"].transform_sql(types={"idade": int, "peso": float})[1])
# hoje imprime:
# INSERT INTO "medidas_new_..." ("rowid", "id", "idade", "peso")
#    SELECT "rowid", "id", "idade", "peso" FROM "medidas";

db["medidas"].transform(types={"idade": int, "peso": float})
for row in db["medidas"].rows:
    print(row)
# hoje imprime:
# {'id': 1, 'idade': 3, 'peso': 2.5}
# {'id': 2, 'idade': '', 'peso': ''}      <-- string vazia em coluna numérica
# {'id': 3, 'idade': None, 'peso': None}
# {'id': 4, 'idade': ' ', 'peso': ' '}
```

## Comportamento esperado

Quando uma coluna `TEXT` é convertida para um tipo numérico, a string vazia
deve virar `NULL`. Vale para qualquer das formas aceitas de pedir um tipo
numérico em `types=`: `int`, `float`, `"integer"`, `"float"`, `"REAL"` e
equivalentes.

O resto não muda:

- valores que representam números continuam sendo convertidos como hoje
  (`"3"` vira `3`, `"2.5"` vira `2.5`, `"42"` convertido para `float` vira
  `42.0`);
- `NULL` continua `NULL`;
- só a string exatamente vazia vira `NULL`: uma string com espaço (`" "`)
  continua como está;
- colunas cujo tipo não está sendo alterado, ou que não eram `TEXT`, são
  copiadas exatamente como hoje.

O SQL devolvido por `transform_sql()` tem de refletir o novo comportamento,
porque ele é o que `transform()` executa. Na instrução de cópia
(`INSERT ... SELECT`), cada coluna `TEXT` convertida para tipo numérico
aparece no `SELECT` como `NULLIF("<nome da coluna>", '')`, usando o nome
que a coluna tem na tabela original. No exemplo acima:

```
INSERT INTO "medidas_new_..." ("rowid", "id", "idade", "peso")
   SELECT "rowid", "id", NULLIF("idade", ''), NULLIF("peso", '') FROM "medidas";
```

Se a mesma chamada também renomeia a coluna (por exemplo
`types={"idade": int}, rename={"idade": "idade_anos"}`), o `INSERT INTO`
lista o nome novo e o `SELECT` continua lendo `NULLIF("idade", '')`. Todas
as demais colunas continuam aparecendo no `SELECT` só pelo nome entre
aspas, como hoje, e as outras instruções da lista não mudam.

## Critério de aceitação

Rodando o trecho acima, a linha de `id` 2 sai com `idade` e `peso` iguais a
`None`, as linhas 1, 3 e 4 saem como hoje, e a instrução de cópia devolvida
por `transform_sql()` tem o formato mostrado. Nenhum outro comportamento de
`transform()` ou `transform_sql()` é alterado: conversões que não partem de
`TEXT` para tipo numérico, renomeações, remoções de coluna e trocas de chave
primária geram o mesmo SQL de antes.

# `has` e `fields` não reconhecem classe genérica especializada

## Comportamento observado

Uma classe `attrs` que herda de `typing.Generic` funciona normalmente quando
é passada "crua" para as funções de introspecção, mas deixa de ser
reconhecida quando é passada já especializada com um argumento de tipo, como
`Caixa[str]`:

- `attrs.has(Caixa[str])` devolve `False`, embora `attrs.has(Caixa)` devolva
  `True`;
- `attrs.fields(Caixa[str])` levanta `TypeError: Passed object must be a
  class.`, em vez de devolver os mesmos campos de `attrs.fields(Caixa)`;
- para uma classe genérica comum, que **não** foi decorada com `attrs`,
  `attrs.fields(Comum[str])` também levanta esse `TypeError`, quando o
  esperado é o erro próprio de "não é uma classe attrs".

Quem escreve código genérico (serializadores, validadores, bibliotecas que
recebem tipos anotados como `Caixa[int]`) é obrigado a desembrulhar o tipo à
mão antes de perguntar ao `attrs` se aquilo é uma classe `attrs` ou quais são
os seus campos.

## Como reproduzir

Rode a partir da raiz do repositório:

```python
from typing import Generic, TypeVar

import attrs

T = TypeVar("T")


@attrs.define
class Caixa(Generic[T]):
    conteudo: T


class Comum(Generic[T]):
    pass


print("has(Caixa):", attrs.has(Caixa))
print("has(Caixa[str]):", attrs.has(Caixa[str]))

try:
    print("fields(Caixa[str]):", attrs.fields(Caixa[str]))
except Exception as exc:
    print("fields(Caixa[str]) falhou:", type(exc).__name__, exc)

try:
    attrs.fields(Comum[str])
except Exception as exc:
    print("fields(Comum[str]) falhou:", type(exc).__name__, exc)
```

Saída hoje:

```
has(Caixa): True
has(Caixa[str]): False
fields(Caixa[str]) falhou: TypeError Passed object must be a class.
fields(Comum[str]) falhou: TypeError Passed object must be a class.
```

## Comportamento esperado

Uma classe genérica especializada deve ser tratada como a classe `attrs` de
que ela veio: `has(Caixa[str])` deve devolver `True` e `fields(Caixa[str])`
deve devolver os mesmos campos que `fields(Caixa)` (mesmo número de campos,
mesmos nomes, mesmos valores padrão).

Se a classe genérica de origem não foi decorada com `attrs`, `has` continua
devolvendo `False` e `fields` deve levantar
`attrs.exceptions.NotAnAttrsClassError` com a mesma mensagem que já usa para
classes comuns, `"<repr do objeto> is not an attrs-decorated class."`, onde o
repr é o do tipo especializado (por exemplo, `repr(Comum[str])`).

## Critérios de aceitação

- Para uma classe `@attrs.define class A(Generic[T])` com um único campo
  `a: T`, `attrs.has(A)` e `attrs.has(A[str])` devolvem `True`, inclusive
  quando `has(A[str])` é chamado mais de uma vez seguida.
- Para essa mesma classe, tanto `attrs.fields(A)` quanto
  `attrs.fields(A[str])` têm exatamente um campo, acessível como `.a`, com
  `name == "a"` e `default is attrs.NOTHING`.
- Para uma classe `class B(Generic[T])` sem `attrs`, `attrs.fields(B[str])`
  levanta `NotAnAttrsClassError` cuja mensagem é exatamente
  `f"{B[str]!r} is not an attrs-decorated class."`.
- Para uma classe genérica sem `attrs`, `attrs.has` continua devolvendo
  `False` tanto para a classe crua quanto para a especializada, em chamadas
  repetidas.
- Nenhum comportamento já existente muda: classes comuns, objetos que não são
  classes (que continuam levantando `TypeError` em `fields`) e o restante da
  suíte de testes seguem como estão.

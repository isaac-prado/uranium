# Lexer de Go classifica errado tipos, literais inteiros e operadores

## Comportamento observado

Ao tokenizar código Go com `pygments.lex(codigo, get_lexer_by_name("go"))`,
vários elementos da linguagem saem com o tipo de token errado ou partidos em
pedaços. Os casos, todos conferidos contra a especificação da linguagem
(https://go.dev/ref/spec):

1. **`float` tratado como tipo.** Go não tem um tipo chamado `float`, só
   `float32` e `float64`. Mesmo assim, em `var float float32` o nome `float`
   (que ali é só um identificador comum) sai como `Keyword.Type`.
2. **Conversão de tipo tratada como chamada de função embutida.** Em
   `y := float64(x)` ou `n := int(y)`, o nome do tipo sai como `Name.Builtin`,
   como se fosse uma função como `len` ou `append`. Uma conversão continua
   sendo um tipo: o nome deveria sair como `Keyword.Type`, igual a quando o
   mesmo tipo aparece numa declaração.
3. **`map` e `chan` tratados como palavra de declaração.** Em
   `var m map[string]int` e `var c chan int`, `map` e `chan` saem como
   `Keyword.Declaration` (a mesma categoria de `var`, `func`, `type`). Eles
   constroem tipos e deveriam sair como `Keyword.Type`.
4. **Literais octais com prefixo `0o`/`0O` partidos.** `0o755` sai como
   `'0'` (`Number.Integer`) seguido de `'o755'` (`Name.Other`). O mesmo com
   `0O644`. O formato antigo `0777` já sai certo, como `Number.Oct`.
5. **Literais binários não reconhecidos.** `0b1010` sai como `'0'`
   (`Number.Integer`) seguido de `'b1010'` (`Name.Other`); o mesmo com o
   prefixo `0B`.
6. **Separador `_` em literais inteiros não reconhecido.** Go permite `_`
   entre dígitos e logo após o prefixo de base (`1_000_000`, `0x_fe_1a`,
   `0b_0101`, `0O_644`). Hoje o literal é cortado no primeiro `_`: `1_000_000`
   vira `'1'` (`Number.Integer`) seguido de `'_000_000'` (`Name.Other`).
7. **Operadores classificados como pontuação.** `!` (negação lógica), `=`
   (atribuição), `<` e `>` (comparação) e `^` (ou-exclusivo bit a bit) saem
   como `Punctuation`. São operadores e deveriam sair como `Operator`.
8. **Operador `^=` partido.** Em `x ^= 3`, o operador composto sai como dois
   tokens, `'^'` e `'='`, ambos `Punctuation`. Deveria ser um único token
   `'^='` do tipo `Operator`, como já acontece com `+=`, `|=` e os demais.
9. **`...` e `~` classificados como operadores.** Em `f(xs...)`,
   `[...]int{1, 2}` e numa restrição de tipo genérico como
   `interface{ ~int }`, `...` e `~` saem como `Operator`. Pela especificação
   eles são pontuação e deveriam sair como `Punctuation`.

## Como reproduzir

Rode a partir da raiz do repositório. O trecho imprime, para cada caso, os
tokens obtidos que divergem do esperado (espaços em branco omitidos):

```python
from pygments import lex
from pygments.lexers import get_lexer_by_name

go = get_lexer_by_name("go")

casos = [
    ("var float float32", [("var", "Keyword.Declaration"), ("float", "Name.Other"), ("float32", "Keyword.Type")]),
    ("y := float64(x)", [("y", "Name.Other"), (":=", "Operator"), ("float64", "Keyword.Type"), ("(", "Punctuation"), ("x", "Name.Other"), (")", "Punctuation")]),
    ("n := int(y)", [("n", "Name.Other"), (":=", "Operator"), ("int", "Keyword.Type"), ("(", "Punctuation"), ("y", "Name.Other"), (")", "Punctuation")]),
    ("k := len(s)", [("k", "Name.Other"), (":=", "Operator"), ("len", "Name.Builtin"), ("(", "Punctuation"), ("s", "Name.Other"), (")", "Punctuation")]),
    ("var m map[string]int", [("var", "Keyword.Declaration"), ("m", "Name.Other"), ("map", "Keyword.Type"), ("[", "Punctuation"), ("string", "Keyword.Type"), ("]", "Punctuation"), ("int", "Keyword.Type")]),
    ("var c chan int", [("var", "Keyword.Declaration"), ("c", "Name.Other"), ("chan", "Keyword.Type"), ("int", "Keyword.Type")]),
    ("p = 0o755", [("p", "Name.Other"), ("=", "Operator"), ("0o755", "Literal.Number.Oct")]),
    ("p = 0O_644", [("p", "Name.Other"), ("=", "Operator"), ("0O_644", "Literal.Number.Oct")]),
    ("p = 0777", [("p", "Name.Other"), ("=", "Operator"), ("0777", "Literal.Number.Oct")]),
    ("b = 0b1100 ^ 0B1001 | 0b00_10", [("b", "Name.Other"), ("=", "Operator"), ("0b1100", "Literal.Number.Bin"), ("^", "Operator"), ("0B1001", "Literal.Number.Bin"), ("|", "Operator"), ("0b00_10", "Literal.Number.Bin")]),
    ("n = 1_000_000", [("n", "Name.Other"), ("=", "Operator"), ("1_000_000", "Literal.Number.Integer")]),
    ("h = 0x_fefe_1a3d", [("h", "Name.Other"), ("=", "Operator"), ("0x_fefe_1a3d", "Literal.Number.Hex")]),
    ("ok = !(x > 0 && x < 8)", [("ok", "Name.Other"), ("=", "Operator"), ("!", "Operator"), ("(", "Punctuation"), ("x", "Name.Other"), (">", "Operator"), ("0", "Literal.Number.Integer"), ("&&", "Operator"), ("x", "Name.Other"), ("<", "Operator"), ("8", "Literal.Number.Integer"), (")", "Punctuation")]),
    ("x ^= 0b_0101", [("x", "Name.Other"), ("^=", "Operator"), ("0b_0101", "Literal.Number.Bin")]),
    ("f(xs...)", [("f", "Name.Other"), ("(", "Punctuation"), ("xs", "Name.Other"), ("...", "Punctuation"), (")", "Punctuation")]),
    ("a := [...]int{1, 2}", [("a", "Name.Other"), (":=", "Operator"), ("[", "Punctuation"), ("...", "Punctuation"), ("]", "Punctuation"), ("int", "Keyword.Type"), ("{", "Punctuation"), ("1", "Literal.Number.Integer"), (",", "Punctuation"), ("2", "Literal.Number.Integer"), ("}", "Punctuation")]),
    ("type N interface{ ~int | ~float64 }", [("type", "Keyword.Declaration"), ("N", "Name.Other"), ("interface", "Keyword.Declaration"), ("{", "Punctuation"), ("~", "Punctuation"), ("int", "Keyword.Type"), ("|", "Operator"), ("~", "Punctuation"), ("float64", "Keyword.Type"), ("}", "Punctuation")]),
]

divergentes = 0
for codigo, esperado in casos:
    obtido = [(v, str(t).removeprefix("Token."))
              for t, v in lex(codigo, go) if v.strip()]
    if obtido != esperado:
        divergentes += 1
        print(f"{codigo!r}\n  obtido:   {obtido}\n  esperado: {esperado}")
print(f"{divergentes} de {len(casos)} casos divergem")
```

No estado atual, 16 dos 17 casos divergem. Só `k := len(s)` sai certo; ele
está na lista para garantir que funções embutidas continuem como estão.

## Comportamento esperado

Os tokens produzidos para código Go seguem a especificação da linguagem:

- `float` sozinho é um identificador comum (`Name.Other`); os tipos
  predeclarados (`int`, `int64`, `float32`, `float64`, `string`, `any` etc.)
  saem como `Keyword.Type` também quando usados numa conversão, com o `(`
  seguinte como `Punctuation` separado. Funções embutidas de verdade (`len`,
  `append`, `make`, `new` etc.) continuam como `Name.Builtin`.
- `map` e `chan` saem como `Keyword.Type`.
- Literais inteiros são um único token: binários (`0b`/`0B`) como
  `Number.Bin`, octais (`0o`/`0O` ou só `0` seguido de dígitos octais) como
  `Number.Oct`, hexadecimais (`0x`/`0X`) como `Number.Hex` e decimais como
  `Number.Integer`, todos aceitando `_` entre dígitos e logo após o prefixo.
- `!`, `=`, `<`, `>`, `|`, `^` e `^=` saem como `Operator`, junto dos demais
  operadores que já saem assim (`:=`, `&&`, `+=`, `<-`, `<=` etc.).
- `...` e `~` saem como `Punctuation`, como parênteses, colchetes, chaves,
  `.`, `,`, `;` e `:`.

Todo o resto da tokenização (palavras-chave, strings, comentários, números
de ponto flutuante e imaginários, identificadores) permanece como está.

## Critério de aceitação

O trecho acima imprime `0 de 17 casos divergem`, a tokenização de qualquer
código Go segue exatamente as regras acima (inclusive com esses elementos
combinados num mesmo arquivo, por exemplo dentro de um bloco `var ( ... )`
ou de funções genéricas) e nenhum teste existente da suíte passa a falhar.

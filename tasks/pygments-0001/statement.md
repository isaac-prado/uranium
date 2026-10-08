# pygments-0001

<!-- PENDENTE: escrever à mão antes de validar -->

## O problema

Descreva o comportamento errado do ponto de vista de quem usa a
biblioteca. Sem citar arquivo, função ou a forma da correção — isso
seria engenharia do harness creditada ao agente.

## Como reproduzir

```python
# trecho que expõe o problema, para o agente rodar com run_python
```

## Comportamento esperado

O que deveria acontecer.

---

<!-- Material de apoio para escrever o enunciado. NÃO faz parte dele.

commit de correção: 9c436b34ccafdf9376527f66c6e587ffe0d1b84c
assunto: Go lexer improvements (#3199)
arquivos de fonte: pygments/lexers/go.py
fail-to-pass: tests/examplefiles/go/3199.go::, tests/examplefiles/go/generics.go::

corpo do commit:
* Go: There is no type called just float

* Go: Do not treat type conversions as functions

* Go: Treat maps and channels as types

* Go: Octal literal may start with 0o or 0O

* Go: Add binary literals

* Go: Token ! is logical operator NOT

* Go: Token = is assignment operator

* Go: Tokens < and > are relational operators

* Go: Tokens | and ^ are bitwise logical operators

* Go: Token ~ is not an operator

* Go: Token ... is not an operator

* Go: Add ^= operator

* Go: Int literals can contain _

* Go: Update goldens

* AUTHORS: Add Armin Günther for Go lexer improvements

* Go: Add new test case
-->

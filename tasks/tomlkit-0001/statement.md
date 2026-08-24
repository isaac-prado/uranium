# Elemento malformado dentro de array é descartado em silêncio

## Comportamento observado

Ao analisar um documento TOML em que um array contém um elemento
sintaticamente inválido, o parser não reclama: ele descarta o elemento
problemático e devolve o array truncado com o que conseguiu ler antes dele.

```python
from tomlkit.parser import Parser

Parser("a = [{1]").parse()   # deveria falhar; hoje não falha
```

Outros documentos com o mesmo defeito:

```
a = [{a]
a = [1, {2]
a = [{a = 1}, {2]
a = [[1, {x]]
a = [{a.b]
```

Todos têm em comum um elemento que começa a ser lido como um valor válido
mas encontra um caractere inesperado no meio — por exemplo, uma tabela
inline sem o `=` ou sem o `}` de fechamento.

## Comportamento esperado

Documento malformado deve produzir erro, não um resultado parcial. O parser
deve levantar `UnexpectedCharError` nesses casos, como já faz para outras
formas de array inválido.

Descartar em silêncio é pior do que falhar: quem usa a biblioteca recebe um
documento que parece válido, com dados faltando, e só descobre o problema
muito depois.

## Critério de aceitação

Cada um dos documentos acima levanta `UnexpectedCharError` ao ser analisado,
e nenhum comportamento já existente do parser é alterado.

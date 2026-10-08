# Não há como criar chave pontilhada pela API de construção de documentos

## O pedido

O TOML permite escrever chaves pontilhadas, como `foo.bar = 1`, que equivalem
a uma tabela `foo` contendo `bar = 1`. A biblioteca já lê e preserva esse
formato ao analisar um arquivo existente (`tomlkit.parse("foo.bar = 1\n")`
devolve o mesmo texto em `as_string()`), mas quem monta um documento do zero
pela API não consegue produzi-lo: não há como pedir que um valor seja gravado
com chave pontilhada. Hoje só dá para escrever `[foo]` seguido de `bar = 1`,
que é outro texto.

Queremos poder construir, por exemplo, a tabela abaixo pela API:

```toml
[foo]
a.b.c = 1
```

## Interface pedida

- `tomlkit.key(...)` passa a aceitar, além de uma string, uma **lista de
  strings**. Cada string é uma parte da chave: `tomlkit.key(["foo", "bar"])`
  representa a chave pontilhada `foo.bar`. Com uma string, o comportamento
  atual (chave simples) não muda.
- O método `add(chave, valor)` de um documento (`tomlkit.document()`) e de uma
  tabela (`tomlkit.table()`) passa a aceitar essa chave pontilhada e grava o
  valor com ela.
- O texto gerado por `as_string()` usa a chave pontilhada na própria linha do
  valor, com o mesmo espaçamento de uma chave simples (` = ` entre chave e
  valor) e sem criar cabeçalho de tabela. Para
  `add(tomlkit.key(["foo", "bar"]), 1)` num documento ou numa tabela vazios, o
  resultado tem de ser exatamente a string `"foo.bar = 1\n"`.
- Como dado, a chave pontilhada continua significando tabelas aninhadas: depois
  de `doc.add(tomlkit.key(["foo", "bar"]), 1)`, `doc["foo"]["bar"]` vale `1`,
  exatamente como se o documento tivesse sido lido de `"foo.bar = 1\n"`.

## Como reproduzir

Rode a partir da raiz do repositório:

```python
import tomlkit

doc = tomlkit.document()
doc.add(tomlkit.key(["foo", "bar"]), 1)
print(repr(doc.as_string()))

table = tomlkit.table()
table.add(tomlkit.key(["foo", "bar"]), 1)
print(repr(table.as_string()))
```

Hoje a primeira chamada a `add` já falha com
`TypeError: ord() expected a character, but string of length 3 found`, porque
a lista é tratada como se fosse o nome de uma chave simples.

Saída esperada depois da mudança:

```
'foo.bar = 1\n'
'foo.bar = 1\n'
```

O exemplo do início, montado pela API, também deve sair como no TOML acima:

```python
doc = tomlkit.document()
foo = tomlkit.table()
foo.add(tomlkit.key(["a", "b", "c"]), 1)
doc.add("foo", foo)
print(repr(doc.as_string()))   # '[foo]\na.b.c = 1\n'
```

## Critérios de aceitação

- `tomlkit.key(["foo", "bar"])` cria uma chave pontilhada; `tomlkit.key("foo")`
  continua criando uma chave simples, como hoje.
- Num documento vazio, `doc.add(tomlkit.key(["foo", "bar"]), 1)` faz
  `doc.as_string()` devolver exatamente `"foo.bar = 1\n"`.
- Numa tabela vazia, `table.add(tomlkit.key(["foo", "bar"]), 1)` faz
  `table.as_string()` devolver exatamente `"foo.bar = 1\n"`.
- O valor gravado com chave pontilhada é acessível como tabelas aninhadas
  (`doc["foo"]["bar"] == 1`).
- Nada do que já funciona muda: chaves simples, tabelas, análise e
  regravação de arquivos existentes (inclusive com chaves pontilhadas) e
  os erros de chave duplicada continuam como estão. A suíte de testes
  existente continua passando.

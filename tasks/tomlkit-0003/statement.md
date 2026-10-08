# Tabela intermediária perde subtabelas na sua representação de dicionário

## Comportamento observado

Os documentos e as tabelas devolvidos por `tomlkit.parse` deveriam se
comportar como dicionários comuns: a representação (`repr`) de uma tabela
precisa mostrar todas as chaves que ela contém, tal como mostra a
representação do documento inteiro.

Isso não acontece quando uma tabela intermediária é estendida por mais de
um cabeçalho. No documento abaixo, `[tool.poetry.foo]` e `[tool.poetry.bar]`
definem duas subtabelas da mesma tabela implícita `tool.poetry`. O documento
inteiro é representado corretamente, mas a representação de `doc["tool"]`
perde a subtabela `foo`: só sobra a que foi definida por último.

```python
import tomlkit

content = """
[tool.poetry.foo]
option = "test"

[tool.poetry.bar]
option = "test"
inline = {"foo" = "bar", "bar" = "baz"}
"""

doc = tomlkit.parse(content)
print(repr(doc))
print(repr(doc["tool"]))
```

Saída atual (rodando da raiz do repositório):

```
{'tool': {'poetry': {'foo': {'option': 'test'}, 'bar': {'option': 'test', 'inline': {'foo': 'bar', 'bar': 'baz'}}}}}
{'poetry': {'bar': {'option': 'test', 'inline': {'foo': 'bar', 'bar': 'baz'}}}}
```

A segunda linha está errada: `foo` sumiu. O dado não se perdeu do
documento (a primeira linha o mostra, e `doc["tool"]["poetry"]["foo"]`
ainda funciona), mas quem inspeciona `doc["tool"]` como dicionário enxerga
um conteúdo incompleto. O mesmo sumiço aparece em `dict(doc["tool"])`.

## Comportamento esperado

A representação de qualquer tabela deve refletir todo o seu conteúdo,
coerente com a representação do documento. Para o documento acima, a saída
esperada é exatamente:

```
{'tool': {'poetry': {'foo': {'option': 'test'}, 'bar': {'option': 'test', 'inline': {'foo': 'bar', 'bar': 'baz'}}}}}
{'poetry': {'foo': {'option': 'test'}, 'bar': {'option': 'test', 'inline': {'foo': 'bar', 'bar': 'baz'}}}}
```

## Critérios de aceitação

- `repr(doc)` do documento acima é igual, caractere por caractere, a
  `{'tool': {'poetry': {'foo': {'option': 'test'}, 'bar': {'option': 'test', 'inline': {'foo': 'bar', 'bar': 'baz'}}}}}`.
- `repr(doc["tool"])` é igual, caractere por caractere, a
  `{'poetry': {'foo': {'option': 'test'}, 'bar': {'option': 'test', 'inline': {'foo': 'bar', 'bar': 'baz'}}}}`.
- As chaves aparecem na ordem em que foram definidas no documento.
- Nenhum comportamento já existente muda: análise, serialização com
  `as_string()`/`tomlkit.dumps` e acesso por chave continuam como antes, e a
  suíte de testes existente continua passando.

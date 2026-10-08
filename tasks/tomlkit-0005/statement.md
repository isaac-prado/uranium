# Valores escalares lidos de um documento passam por sequência

## Comportamento observado

Depois de analisar um documento com `tomlkit.parse` (ou `tomlkit.loads`), os
valores escalares devolvidos — números de ponto flutuante, inteiros, datas —
são reconhecidos pelo interpretador como **sequências**, embora não sejam.

Isso quebra bibliotecas que inspecionam os dados no nível do CPython. Um
usuário relatou que, ao atualizar a tomlkit, este código passou a falhar:

```python
arr = tomlkit.loads("a = [1.0, 2.0, 3.0]")
torch.tensor(arr["a"], dtype=torch.float32)
# TypeError: object of type 'Float' has no len()
```

O `torch` (e o `numpy`, pelo mesmo motivo) pergunta ao interpretador se cada
elemento é uma sequência; como a resposta é "sim", tenta descer nele como se
fosse uma lista aninhada e falha. Com uma lista Python comum de `float` o
mesmo código funciona.

## Como reproduzir

Sem depender de `torch` ou `numpy`, a mesma pergunta pode ser feita
diretamente à API C do CPython. Rode a partir da raiz do repositório:

```python
import ctypes
import tomlkit

doc = tomlkit.parse("a = [1.0, 2.0, 3.0]\nb = 7\nc = 1979-05-27")
valores = [doc["a"][0], doc["b"], doc["c"]]

seq_check = ctypes.pythonapi.PySequence_Check
seq_check.argtypes = [ctypes.py_object]
seq_check.restype = ctypes.c_int

for v in valores:
    print(type(v).__name__, "PySequence_Check =", seq_check(v))

try:
    iter(doc["a"][0])
    print("iter(Float) funcionou: o valor se passa por iterável")
except TypeError as exc:
    print("iter(Float) levanta TypeError:", exc)
```

Saída hoje:

```
Float PySequence_Check = 1
Integer PySequence_Check = 1
Date PySequence_Check = 1
iter(Float) funcionou: o valor se passa por iterável
```

## Comportamento esperado

Um valor escalar vindo de um documento TOML deve se comportar, nesse
aspecto, como o tipo Python que ele representa: um `float` não é sequência
nem iterável, e o mesmo vale para inteiros e datas. A saída esperada do
trecho acima é:

```
Float PySequence_Check = 0
Integer PySequence_Check = 0
Date PySequence_Check = 0
iter(Float) levanta TypeError: 'Float' object is not iterable
```

Arrays e tabelas continuam sendo o que são hoje (sequência e mapeamento,
respectivamente), com indexação, atribuição e remoção por chave funcionando
como antes.

## Critério de aceitação

`PySequence_Check` devolve 0 para um elemento `float` obtido de um array em
um documento analisado (por exemplo, `parse("a = [1.0, 2.0, 3.0]")["a"][0]`),
e nenhum comportamento já existente da biblioteca é alterado.

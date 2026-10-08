# Campos de enum não informam as opções válidas em `choices`

## Comportamento observado

Os campos `EnumField` e `IntEnumField` (de `playhouse.fields`) recebem uma
classe de enum e só aceitam os membros dela. Mesmo assim, o atributo
`choices` desses campos fica vazio (`None`) quando o usuário não o informa.
Quem consulta `choices` para montar um formulário, uma lista de seleção ou
uma documentação das opções válidas não recebe nada, embora o campo saiba
exatamente quais valores aceita.

```python
import enum
from peewee import Model, SqliteDatabase
from playhouse.fields import EnumField, IntEnumField

db = SqliteDatabase(':memory:')

class Status(enum.Enum):
    ACTIVE = 'active'
    ARCHIVED = 'archived'

class Priority(enum.IntEnum):
    LOW = 1
    HIGH = 9

class Ticket(Model):
    status = EnumField(Status)
    priority = IntEnumField(Priority, null=True)
    class Meta:
        database = db

print(Ticket.status.choices)    # hoje: None
print(Ticket.priority.choices)  # hoje: None

# choices informado explicitamente
f = EnumField(Status, choices=[('active', 'Ativo'), ('archived', 'Arquivado')])
print(f.choices)                # [('active', 'Ativo'), ('archived', 'Arquivado')]
```

## Comportamento esperado

Quando `choices` não é informado, o campo deve expor como `choices` a lista
de pares `(valor, nome)` dos membros do enum, na ordem em que foram
declarados:

```python
Ticket.status.choices    # [('active', 'ACTIVE'), ('archived', 'ARCHIVED')]
Ticket.priority.choices  # [(1, 'LOW'), (9, 'HIGH')]
```

Quando o usuário informa `choices` explicitamente, o valor dele prevalece e
é devolvido sem alteração.

## Critério de aceitação

`EnumField` e `IntEnumField` sem `choices` explícito expõem em `choices` os
pares `(valor, nome)` do enum, em ordem de declaração; com `choices`
explícito, devolvem exatamente o que foi informado. Nenhum comportamento já
existente muda: gravação e leitura de valores continuam iguais, e os
esquemas gerados por `playhouse.pydantic_utils.to_pydantic` continuam
anotando o campo com o próprio enum, sem passar a descrevê-lo como uma lista
de opções.

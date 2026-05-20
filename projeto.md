# Arquitetura Inicial da POC de Engenharia de Software 3.0

Este documento apresenta a estrutura mínima para iniciar sua POC com:

- LangGraph
- LangChain
- OpenRouter
- LangSmith
- Pydantic

O objetivo inicial é implementar o **IntentRefinerAgent**, responsável por transformar uma solicitação em linguagem natural em uma representação estruturada da intenção.

---

# 📁 Estrutura do Projeto

```text
agent-tests/
├── .env
├── pyproject.toml
├── uv.lock
├── test.py
└── src/
    ├── state.py
    ├── graph.py
    ├── schemas/
    │   └── intent.py
    └── agents/
        └── intent_refiner.py
```

---

# 🧠 Papel de `state.py`

O `state.py` define o **estado global do workflow**.

Pense nele como um objeto compartilhado entre todos os agentes.
Cada nó do LangGraph:

1. Recebe o estado atual
2. Processa parte dele
3. Retorna apenas as alterações

## Exemplo

- Entrada: `raw_request = "Criar CRUD de Cliente"`
- Saída do IntentRefiner:
  - `intent`
  - `is_ready`

---

## `src/state.py`

```python
from typing import TypedDict, Any


class WorkflowState(TypedDict, total=False):
    # Entrada inicial
    raw_request: str

    # Resultado do IntentRefinerAgent
    intent: dict[str, Any]
    clarifications_needed: list[str]
    is_ready: bool

    # Controle do workflow
    iteration_count: int
```

---

# 🕸️ Papel de `graph.py`

O `graph.py` monta o fluxo do LangGraph.

Responsabilidades:

- Criar o `StateGraph`
- Registrar os nós
- Definir as transições
- Compilar o grafo

---

## `src/graph.py`

```python
from langgraph.graph import StateGraph, START, END

from src.state import WorkflowState
from src.agents.intent_refiner import intent_refiner



def build_graph():
    builder = StateGraph(WorkflowState)

    # Registra o nó
    builder.add_node("intent_refiner", intent_refiner)

    # Fluxo: START -> intent_refiner -> END
    builder.add_edge(START, "intent_refiner")
    builder.add_edge("intent_refiner", END)

    return builder.compile()
```

---

# 📦 Schema estruturado da Intent

## `src/schemas/intent.py`

```python
from pydantic import BaseModel, Field


class StructuredIntent(BaseModel):
    context: str = Field(description="Contexto atual do sistema")
    goal: str = Field(description="Objetivo principal da solicitação")
    phases: list[str] = Field(description="Fases sugeridas de implementação")
    acceptance_criteria: list[str] = Field(
        description="Critérios de aceitação"
    )
    clarifications_needed: list[str] = Field(
        default_factory=list,
        description="Perguntas adicionais necessárias"
    )
    is_ready: bool = Field(
        description="Indica se a intent está pronta para desenvolvimento"
    )
```

---

# 🤖 Implementação do IntentRefinerAgent

## Responsabilidade

Receber uma entrada como:

> "Crie um CRUD de Cliente"

E produzir:

```json
{
  "context": "O sistema ainda não possui cadastro de clientes.",
  "goal": "Implementar CRUD de Cliente.",
  "phases": [
    "Criar modelo e migração",
    "Implementar endpoints",
    "Criar testes automatizados"
  ],
  "acceptance_criteria": [
    "Usuário pode criar clientes",
    "Usuário pode editar clientes",
    "Usuário pode excluir clientes"
  ],
  "clarifications_needed": [],
  "is_ready": true
}
```

---

## `src/agents/intent_refiner.py`

```python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.state import WorkflowState
from src.schemas.intent import StructuredIntent

load_dotenv()


# Modelo compartilhado
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"),
    temperature=0,
)

# Modelo com saída estruturada
structured_llm = llm.with_structured_output(StructuredIntent)


SYSTEM_PROMPT = """
Você é um especialista em Engenharia de Software 3.0.

Sua tarefa é transformar uma solicitação em linguagem natural
em uma representação estruturada da intenção de desenvolvimento.

Analise a solicitação e produza:
- context
- goal
- phases
- acceptance_criteria
- clarifications_needed
- is_ready

Regras:
1. Se houver informação suficiente, defina is_ready=true.
2. Se houver ambiguidades relevantes, defina is_ready=false.
3. Liste perguntas em clarifications_needed.
4. Seja objetivo e técnico.
"""



def intent_refiner(state: WorkflowState) -> WorkflowState:
    raw_request = state["raw_request"]

    prompt = f"""
Solicitação do usuário:
{raw_request}
"""

    result: StructuredIntent = structured_llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("user", prompt),
    ])

    return {
        "intent": result.model_dump(),
        "clarifications_needed": result.clarifications_needed,
        "is_ready": result.is_ready,
    }
```

---

# ▶️ Arquivo de Teste

## `test.py`

```python
from pprint import pprint

from src.graph import build_graph


if __name__ == "__main__":
    graph = build_graph()

    result = graph.invoke(
        {
            "raw_request": "Criar um CRUD de Cliente com nome, CPF e email.",
            "iteration_count": 0,
        }
    )

    pprint(result)
```

---

# ▶️ Executar

```bash
uv run test.py
```

---

# 🔍 O que você verá no LangSmith

Ao executar o `test.py`, o LangSmith mostrará automaticamente:

- O nó `intent_refiner`
- O prompt enviado
- O JSON estruturado retornado
- Tokens, tempo e custo estimado

---

# 🧭 Próximos Passos

Depois que este fluxo estiver funcionando:

1. Criar `ClarificationAgent`
2. Implementar loop de refinamento
3. Adicionar `DeveloperAgent`
4. Adicionar `ValidatorAgent`
5. Adicionar `TestAgent`

---

# 🎓 Como descrever no TCC

> O IntentRefinerAgent foi implementado como o nó inicial do workflow em LangGraph. Sua função é converter uma solicitação em linguagem natural em uma representação estruturada da intenção de desenvolvimento, contendo contexto, objetivo, fases de implementação e critérios de aceitação. Esse artefato serve como insumo para os agentes subsequentes do processo automatizado.

---

# ✅ Resultado Esperado

Ao final desta etapa, você terá:

- Um grafo funcional em LangGraph
- Um estado global (`WorkflowState`)
- Um agente de refinamento de intenção
- Observabilidade automática com LangSmith
- Base sólida para o restante da POC

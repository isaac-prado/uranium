# Arquitetura dos Agentes — Uranium

Visão rápida da orquestração multi-agente para uso no TCC.

## Ideia geral

O Uranium implementa **Engenharia de Software 3.0** como um pipeline em **LangGraph**: cada arquivo em `src/agents/` é um **nó** (agente especializado). Os agentes não se chamam diretamente — compartilham um estado global (`WorkflowState` em `src/state.py`) e o grafo (`src/graph.py`) define quem executa em seguida.

```
Entrada (linguagem natural)
        │
        ▼
┌───────────────────┐
│  IntentRefiner    │  solicitação → intent estruturada
└─────────┬─────────┘
          │ is_ready?
    ┌─────┴─────┐
    │ não       │ sim
    ▼           ▼
┌──────────┐  ┌──────────┐
│Clarifica-│  │ Developer│  intent → artefatos de código/spec
│   tion   │  └────┬─────┘
└────┬─────┘       ▼
     │         ┌──────────┐
     └────────►│ Validator│  artefatos vs critérios de aceitação
  (loop)       └────┬─────┘
                    │ is_valid?
              ┌─────┴─────┐
              │ não       │ sim
              ▼           ▼
         (volta ao    ┌──────────────┐
          Developer)  │TestGenerator │  plano de testes
                      └──────┬───────┘
                             ▼
                          Saída
```

## Agentes

| Agente            | Arquivo             | Papel                                  | Entrada principal                  | Saída no estado                               |
| ----------------- | ------------------- | -------------------------------------- | ---------------------------------- | --------------------------------------------- |
| **IntentRefiner** | `intent_refiner.py` | Analista de requisitos                 | `raw_request`                      | `intent`, `is_ready`, `clarifications_needed` |
| **Clarification** | `clarification.py`  | Resolve ambiguidades (simulado na POC) | perguntas pendentes                | `clarification_responses`                     |
| **Developer**     | `developer.py`      | Gera implementação                     | `intent` (+ feedback do validator) | `artifacts`                                   |
| **Validator**     | `validator.py`      | Revisão técnica                        | `intent` + `artifacts`             | `validation_result`, `is_valid`               |
| **TestGenerator** | `test_generator.py` | Qualidade / testes                     | `intent` + `artifacts`             | `test_plan`                                   |

## Padrões usados

**Estado compartilhado** — Cada nó recebe o `WorkflowState`, processa sua parte e devolve apenas as chaves que alterou (padrão LangGraph).

**Saída estruturada** — Todos os agentes usam `invoke_structured()` (`src/structured_llm.py`) com schemas **Pydantic** em `src/schemas/`, garantindo JSON tipado e validado.

**Observabilidade** — Funções decoradas com `@traceable` (LangSmith) via `src/tracing.py`: cada agente, chamada LLM e roteamento aparecem como spans no projeto `engenharia-software-3-0`.

**Loops com limite** — Dois ciclos condicionais evitam execução infinita:

- Clarificação: `intent_refiner ↔ clarification` (máx. `MAX_CLARIFICATION_ITERATIONS`)
- Correção: `developer ↔ validator` (máx. `MAX_VALIDATION_ITERATIONS`)

**Papéis distintos** — Cada agente tem system prompt e schema próprios; a especialização é por responsabilidade, não por modelo diferente (todos usam o mesmo LLM configurado em `src/config.py`).

## Fluxo de dados (exemplo)

```
"Criar CRUD de Cliente"
  → IntentRefiner: { goal, phases, acceptance_criteria, is_ready: true }
  → Developer: [{ name: "ClienteModel", content: "..." }, ...]
  → Validator: { is_valid: true, covered_criteria: [...] }
  → TestGenerator: { unit_tests: [...], test_files: [...] }
```

## Onde isso se encaixa no TCC

> O sistema decompõe uma solicitação de desenvolvimento em etapas especializadas (refinamento, clarificação, implementação, validação e testes), orquestradas por um grafo de estados em LangGraph, com observabilidade via LangSmith e contratos de dados em Pydantic.

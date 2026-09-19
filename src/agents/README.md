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
│Clarifica-│  │ Developer│  intent → edita o workspace real via ferramentas
│   tion   │  └────┬─────┘
└────┬─────┘       ▼
     │         ┌──────────┐
     └────────►│ Validator│  roda a suíte real; revisão só pode rebaixar
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
| **IntentRefiner** | `intent_refiner.py` | Analista de requisitos                          | `raw_request`                        | `intent`, `is_ready`, `clarifications_needed` |
| **Clarification** | `clarification.py`  | Resolve ambiguidades com respostas simuladas    | perguntas pendentes                  | `clarification_responses`                     |
| **Developer**     | `developer.py`      | Edita o repositório real por ferramentas (loop de tool calling) | `intent` (+ feedback do validator) | `changed_files`, `diff_stat`, `dev_summary`   |
| **Validator**     | `validator.py`      | Roda a suíte real; revisão só pode rebaixar     | `intent` + `test_report`             | `validation_result`, `is_valid`               |
| **TestGenerator** | `test_generator.py` | Plano de testes complementar (não é oráculo)    | `intent` + `test_report`             | `test_plan`                                   |

## Padrões usados

**Estado compartilhado** — Cada nó recebe o `WorkflowState`, processa sua parte e devolve apenas as chaves que alterou (padrão LangGraph).

**Saída estruturada** — Todos os agentes usam `invoke_structured()` (`src/structured_llm.py`) com schemas **Pydantic** em `src/schemas/`, garantindo JSON tipado e validado.

**Observabilidade** — Telemetria própria em JSONL (`src/telemetry.py`), um evento por linha, validado contra `harness/schema/event.schema.json`: cada chamada de LLM, cada uso de ferramenta e cada execução da suíte vira um evento, com o papel do agente (`agent_role`) que o gerou. Não há tracing remoto — `src/config.py` desliga o do LangChain (LangSmith) de forma incondicional no import.

**Loops com limite** — Dois ciclos condicionais evitam execução infinita:

- Clarificação: `intent_refiner ↔ clarification` (máx. `MAX_CLARIFICATION_ITERATIONS`)
- Correção: `developer ↔ validator` (máx. `MAX_VALIDATION_ITERATIONS`)

**Papéis distintos** — Cada agente tem system prompt e schema próprios; a especialização é por responsabilidade, não por modelo diferente (todos usam o mesmo LLM configurado em `src/config.py`).

## Fluxo de dados (exemplo)

```
enunciado da tarefa (statement.md)
  → IntentRefiner: { goal, phases, acceptance_criteria, is_ready: true }
  → Developer: edita o workspace por ferramentas → { changed_files, diff_stat, dev_summary }
  → Validator: roda a suíte real → { test_report, is_valid }
  → TestGenerator: { test_plan }
```

## Onde isso se encaixa no TCC

> O sistema decompõe uma solicitação de desenvolvimento em etapas especializadas (refinamento, clarificação, implementação, validação e testes), orquestradas por um grafo de estados em LangGraph, com telemetria própria em JSONL (o LangSmith foi removido; ver [docs/tcc/05-stack.md](../../docs/tcc/05-stack.md)) e contratos de dados em Pydantic.

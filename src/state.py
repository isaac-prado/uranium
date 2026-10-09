"""Estado global compartilhado entre todos os nós do workflow LangGraph."""

from typing import Any, TypedDict

from src.schemas.clarification import ClarificationItem
from src.schemas.intent import StructuredIntent
from src.schemas.test_plan import TestPlan
from src.schemas.test_report import TestReport
from src.schemas.validation_result import ValidationResult

# Serialização no grafo (dicts JSON-compatíveis)
IntentState = dict[str, Any]
ClarificationState = list[dict[str, str]]
ValidationState = dict[str, Any]
TestPlanState = dict[str, Any]
TestReportState = dict[str, Any]


class WorkflowState(TypedDict, total=False):
    """
    Estado do pipeline Uranium.

    Só conteúdo serializável: objetos vivos (workspace, telemetria, cliente
    LLM) ficam no RunContext, resolvido por `run_id`.
    """

    # Identificação do run — liga o estado ao RunContext e à telemetria
    run_id: str
    arm: str
    task_id: str

    # Entrada
    raw_request: str

    # IntentRefiner / Clarification
    intent: IntentState
    clarifications_needed: list[str]
    is_ready: bool
    clarification_responses: ClarificationState

    # Developer — o artefato agora é o diff do workspace, não blobs de texto
    changed_files: list[str]
    diff_stat: dict[str, int]
    dev_summary: str

    # Validator — corretude vem de execução real
    test_report: TestReportState
    is_valid: bool
    validation_result: ValidationState

    # TestGenerator
    test_plan: TestPlanState

    # Controle de fluxo e circuit breaker
    iteration_count: int
    validation_iteration_count: int
    semantic_rejections: int
    turn_count: int
    stop_reason: str

    # Braço single-agent: indica se o agente usou ferramenta no turno, o que
    # decide se o driver roda a suíte ou o agente segue agindo.
    agiu_no_turno: bool


def parse_intent(state: WorkflowState) -> StructuredIntent:
    """Converte intent do estado para modelo tipado."""
    return StructuredIntent.model_validate(state.get("intent") or {})


def intent_bruta(statement: str) -> dict:
    """
    A intent com que todo run começa: só o enunciado, em `goal`, e o resto
    vazio. É o que o single-agent recebe como especificação (o driver a
    entrega uma vez, `src/arms/single_agent.py`) e, desde a decisão 24
    (docs/tcc/09-decisoes-do-autor.md, 09/10/2026), também a primeira parte
    do que o developer do orchestration recebe — a mesma string, byte a
    byte, nos dois braços. Mora aqui para o runner e os dois braços nunca
    montarem cópias que possam divergir.
    """
    return {
        "context": "", "goal": statement, "phases": [],
        "acceptance_criteria": [], "clarifications_needed": [], "is_ready": True,
    }


def tarefa_bruta(statement: str) -> str:
    """A especificação como os dois braços a recebem: `Tarefa:` + intent bruta."""
    return "Tarefa:\n" + StructuredIntent.model_validate(intent_bruta(statement)).model_dump_json(indent=2)


def parse_clarifications(state: WorkflowState) -> list[ClarificationItem]:
    """Converte respostas de clarificação para modelos tipados."""
    raw = state.get("clarification_responses") or []
    return [ClarificationItem.model_validate(item) for item in raw]


def parse_validation(state: WorkflowState) -> ValidationResult | None:
    """Converte resultado de validação para modelo tipado."""
    raw = state.get("validation_result")
    return ValidationResult.model_validate(raw) if raw else None


def parse_test_report(state: WorkflowState) -> TestReport | None:
    """Converte o relatório de execução de testes para modelo tipado."""
    raw = state.get("test_report")
    return TestReport.model_validate(raw) if raw else None


def parse_test_plan(state: WorkflowState) -> TestPlan | None:
    """Converte plano de testes para modelo tipado."""
    raw = state.get("test_plan")
    return TestPlan.model_validate(raw) if raw else None

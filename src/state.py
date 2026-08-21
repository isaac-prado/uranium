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
    turn_count: int
    stop_reason: str

    # Braço A2: indica se o agente usou ferramenta no turno, o que
    # decide se o driver roda a suíte ou o agente segue agindo.
    agiu_no_turno: bool


def parse_intent(state: WorkflowState) -> StructuredIntent:
    """Converte intent do estado para modelo tipado."""
    return StructuredIntent.model_validate(state.get("intent") or {})


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

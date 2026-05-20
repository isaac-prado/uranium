"""Estado global compartilhado entre todos os nós do workflow LangGraph."""

from typing import Any, TypedDict

from src.schemas.clarification import ClarificationItem
from src.schemas.development_artifact import DevelopmentArtifact
from src.schemas.intent import StructuredIntent
from src.schemas.test_plan import TestPlan
from src.schemas.validation_result import ValidationResult

# Serialização no grafo (dicts JSON-compatíveis)
IntentState = dict[str, Any]
ClarificationState = list[dict[str, str]]
ArtifactState = list[dict[str, Any]]
ValidationState = dict[str, Any]
TestPlanState = dict[str, Any]


class WorkflowState(TypedDict, total=False):
    """Estado do pipeline multi-agente Uranium."""

    raw_request: str

    intent: IntentState
    clarifications_needed: list[str]
    is_ready: bool

    clarification_responses: ClarificationState

    artifacts: ArtifactState

    validation_result: ValidationState
    is_valid: bool

    test_plan: TestPlanState

    iteration_count: int
    validation_iteration_count: int


def parse_intent(state: WorkflowState) -> StructuredIntent:
    """Converte intent do estado para modelo tipado."""
    return StructuredIntent.model_validate(state.get("intent") or {})


def parse_clarifications(state: WorkflowState) -> list[ClarificationItem]:
    """Converte respostas de clarificação para modelos tipados."""
    raw = state.get("clarification_responses") or []
    return [ClarificationItem.model_validate(item) for item in raw]


def parse_artifacts(state: WorkflowState) -> list[DevelopmentArtifact]:
    """Converte artefatos do estado para modelos tipados."""
    raw = state.get("artifacts") or []
    return [DevelopmentArtifact.model_validate(item) for item in raw]


def parse_validation(state: WorkflowState) -> ValidationResult | None:
    """Converte resultado de validação para modelo tipado."""
    raw = state.get("validation_result")
    if not raw:
        return None
    return ValidationResult.model_validate(raw)


def parse_test_plan(state: WorkflowState) -> TestPlan | None:
    """Converte plano de testes para modelo tipado."""
    raw = state.get("test_plan")
    if not raw:
        return None
    return TestPlan.model_validate(raw)

"""Testes do grafo LangGraph e roteamento condicional."""

from unittest.mock import patch

from src.graph import (
    build_graph,
    route_after_intent_refiner,
    route_after_validator,
)
from src.schemas.clarification import ClarificationBatch
from src.schemas.development_artifact import DevelopmentArtifacts
from src.schemas.intent import StructuredIntent
from src.schemas.test_plan import TestPlan
from src.schemas.validation_result import ValidationResult


class TestRouting:
    """Testes das funções de roteamento."""

    def test_route_ready_goes_to_developer(self):
        assert route_after_intent_refiner({"is_ready": True}) == "developer"

    def test_route_not_ready_goes_to_clarification(self):
        assert route_after_intent_refiner({"is_ready": False, "iteration_count": 0}) == "clarification"

    def test_route_max_iterations_fallback(self):
        state = {"is_ready": False, "iteration_count": 10}
        assert route_after_intent_refiner(state) == "developer"

    def test_route_valid_goes_to_test_generator(self):
        assert route_after_validator({"is_valid": True}) == "test_generator"

    def test_route_invalid_goes_to_developer(self):
        assert route_after_validator({"is_valid": False, "validation_iteration_count": 0}) == "developer"

    def test_route_max_validation_fallback(self):
        state = {"is_valid": False, "validation_iteration_count": 10}
        assert route_after_validator(state) == "test_generator"


class TestGraphStructure:
    """Testes da estrutura do grafo."""

    def test_build_graph_compiles(self):
        graph = build_graph()
        assert graph is not None
        assert hasattr(graph, "invoke")


def _make_invoke_side_effect(
    sample_intent,
    sample_artifacts,
    sample_validation_valid,
    sample_test_plan,
    sample_intent_not_ready=None,
    sample_clarification_batch=None,
):
    """Retorna side_effect que despacha por schema Pydantic."""

    def side_effect(schema, messages, **kwargs):
        if schema is StructuredIntent:
            if sample_intent_not_ready and side_effect.intent_calls == 0:
                side_effect.intent_calls += 1
                return sample_intent_not_ready
            return sample_intent
        if schema is ClarificationBatch:
            return sample_clarification_batch
        if schema is DevelopmentArtifacts:
            return sample_artifacts
        if schema is ValidationResult:
            return sample_validation_valid
        if schema is TestPlan:
            return sample_test_plan
        raise ValueError(f"Schema não mockado: {schema}")

    side_effect.intent_calls = 0
    return side_effect


@patch("src.agents.test_generator.invoke_structured")
@patch("src.agents.validator.invoke_structured")
@patch("src.agents.developer.invoke_structured")
@patch("src.agents.intent_refiner.invoke_structured")
def test_full_pipeline_ready_path(
    mock_intent,
    mock_dev,
    mock_val,
    mock_test,
    sample_intent,
    sample_artifacts,
    sample_validation_valid,
    sample_test_plan,
):
    """Executa pipeline completo quando intent já está pronta."""
    mock_intent.return_value = sample_intent
    mock_dev.return_value = sample_artifacts
    mock_val.return_value = sample_validation_valid
    mock_test.return_value = sample_test_plan

    graph = build_graph()
    result = graph.invoke({
        "raw_request": "Criar CRUD de Cliente com nome, CPF e email.",
        "iteration_count": 0,
        "validation_iteration_count": 0,
        "clarification_responses": [],
    })

    assert result["is_ready"] is True
    assert result["intent"]["goal"] == "Implementar CRUD de Cliente."
    assert len(result["artifacts"]) >= 1
    assert result["is_valid"] is True
    assert result["test_plan"]["summary"] == "Testes do CRUD de Cliente"


@patch("src.agents.test_generator.invoke_structured")
@patch("src.agents.validator.invoke_structured")
@patch("src.agents.developer.invoke_structured")
@patch("src.agents.clarification.invoke_structured")
@patch("src.agents.intent_refiner.invoke_structured")
def test_pipeline_with_clarification_loop(
    mock_intent,
    mock_clar,
    mock_dev,
    mock_val,
    mock_test,
    sample_intent_not_ready,
    sample_intent,
    sample_clarification_batch,
    sample_artifacts,
    sample_validation_valid,
    sample_test_plan,
):
    """Executa loop de clarificação quando intent não está pronta."""
    mock_intent.side_effect = [sample_intent_not_ready, sample_intent]
    mock_clar.return_value = sample_clarification_batch
    mock_dev.return_value = sample_artifacts
    mock_val.return_value = sample_validation_valid
    mock_test.return_value = sample_test_plan

    graph = build_graph()
    result = graph.invoke({
        "raw_request": "Criar algo vago",
        "iteration_count": 0,
        "validation_iteration_count": 0,
        "clarification_responses": [],
    })

    assert len(result.get("clarification_responses", [])) >= 1
    assert result["is_ready"] is True
    assert result["test_plan"] is not None

"""Testes do IntentRefinerAgent."""

from unittest.mock import patch

from src.agents.intent_refiner import intent_refiner
from src.schemas.intent import StructuredIntent


@patch("src.agents.intent_refiner.invoke_structured")
def test_intent_refiner_ready(mock_invoke, sample_intent):
    """Deve retornar intent estruturada quando solicitação é clara."""
    mock_invoke.return_value = sample_intent

    result = intent_refiner({"raw_request": "Criar CRUD de Cliente"})

    assert result["is_ready"] is True
    assert result["intent"]["goal"] == "Implementar CRUD de Cliente."
    assert result["clarifications_needed"] == []
    mock_invoke.assert_called_once()
    assert mock_invoke.call_args[0][0] is StructuredIntent


@patch("src.agents.intent_refiner.invoke_structured")
def test_intent_refiner_not_ready(mock_invoke, sample_intent_not_ready):
    """Deve indicar clarificações quando há ambiguidade."""
    mock_invoke.return_value = sample_intent_not_ready

    result = intent_refiner({"raw_request": "Criar algo"})

    assert result["is_ready"] is False
    assert len(result["clarifications_needed"]) == 2


@patch("src.agents.intent_refiner.invoke_structured")
def test_intent_refiner_increments_iteration(mock_invoke, sample_intent):
    """Deve incrementar iteration_count após clarificações."""
    mock_invoke.return_value = sample_intent

    result = intent_refiner({
        "raw_request": "Criar CRUD",
        "clarification_responses": [{"question": "Q?", "answer": "A."}],
        "iteration_count": 1,
    })

    assert result["iteration_count"] == 2

"""Testes do invoke_structured com fallback JSON."""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from src.schemas.intent import StructuredIntent
from src.structured_llm import _extract_json, invoke_structured


class SampleModel(BaseModel):
    name: str = Field(description="Nome")
    value: int = Field(description="Valor")


def test_extract_json_from_markdown():
    text = '```json\n{"name": "a", "value": 1}\n```'
    assert json.loads(_extract_json(text)) == {"name": "a", "value": 1}


@patch("src.structured_llm.get_llm")
def test_invoke_structured_primary_path(mock_get_llm, sample_intent):
    """Usa with_structured_output quando disponível."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = sample_intent
    mock_llm.with_structured_output.return_value = mock_structured
    mock_get_llm.return_value = mock_llm

    result = invoke_structured(
        StructuredIntent,
        [("system", "test"), ("user", "input")],
    )

    assert result.goal == "Implementar CRUD de Cliente."
    mock_llm.with_structured_output.assert_called_once()


@patch("src.structured_llm.get_llm")
def test_invoke_structured_json_fallback(mock_get_llm):
    """Faz fallback para parse JSON quando structured output falha."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.side_effect = RuntimeError("choices=None")
    mock_llm.with_structured_output.return_value = mock_structured

    payload = {"name": "test", "value": 42}
    mock_response = MagicMock()
    mock_response.content = f"```json\n{json.dumps(payload)}\n```"
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    result = invoke_structured(
        SampleModel,
        [("user", "gere json")],
    )

    assert result.name == "test"
    assert result.value == 42


@patch("src.structured_llm.get_llm")
def test_invoke_structured_raises_on_empty(mock_get_llm):
    """Levanta erro claro quando LLM retorna vazio."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = None
    mock_llm.with_structured_output.return_value = mock_structured

    mock_response = MagicMock()
    mock_response.content = ""
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    with pytest.raises(RuntimeError, match="Falha ao parsear JSON|resposta vazia"):
        invoke_structured(SampleModel, [("user", "input")])

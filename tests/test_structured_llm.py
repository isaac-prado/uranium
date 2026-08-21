"""Testes do invoke_structured — structured output nativo, sem reparo."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from src.schemas.intent import StructuredIntent
from src.structured_llm import (
    StructuredOutputError,
    get_output_method,
    invoke_structured,
    max_retries,
)


class SampleModel(BaseModel):
    name: str = Field(description="Nome")
    value: int = Field(description="Valor")


@pytest.fixture
def llm_mock():
    """LLM mockado; devolve também o objeto de saída estruturada."""
    llm, structured = MagicMock(), MagicMock()
    llm.with_structured_output.return_value = structured
    with patch("src.structured_llm.get_llm", return_value=llm):
        yield llm, structured


class TestCaminhoNativo:
    def test_usa_structured_output_nativo(self, llm_mock, sample_intent):
        llm, structured = llm_mock
        structured.invoke.return_value = sample_intent

        result = invoke_structured(StructuredIntent, [("user", "input")])

        assert result.goal == "Implementar CRUD de Cliente."
        llm.with_structured_output.assert_called_once()

    def test_metodo_padrao_e_function_calling(self, llm_mock, sample_intent):
        llm, structured = llm_mock
        structured.invoke.return_value = sample_intent

        invoke_structured(StructuredIntent, [("user", "input")])

        assert llm.with_structured_output.call_args.kwargs["method"] == "function_calling"

    def test_metodo_configuravel_por_env(self, llm_mock, sample_intent, monkeypatch):
        monkeypatch.setenv("STRUCTURED_OUTPUT_METHOD", "json_schema")
        llm, structured = llm_mock
        structured.invoke.return_value = sample_intent

        invoke_structured(StructuredIntent, [("user", "input")])

        assert llm.with_structured_output.call_args.kwargs["method"] == "json_schema"

    def test_metodo_invalido_cai_no_padrao(self, monkeypatch):
        monkeypatch.setenv("STRUCTURED_OUTPUT_METHOD", "telepatia")
        assert get_output_method() == "function_calling"


class TestSemReparoDegradado:
    """O reparo de JSON foi removido de propósito — não pode voltar."""

    def test_nao_ha_fallback_de_prompt_json(self, llm_mock):
        llm, structured = llm_mock
        structured.invoke.side_effect = RuntimeError("choices=None")

        with pytest.raises(StructuredOutputError):
            invoke_structured(SampleModel, [("user", "gere json")])

        # o caminho degradado chamava llm.invoke() diretamente; não pode ocorrer
        llm.invoke.assert_not_called()

    def test_resposta_vazia_vira_erro(self, llm_mock):
        _, structured = llm_mock
        structured.invoke.return_value = None

        with pytest.raises(StructuredOutputError, match="não conformou"):
            invoke_structured(SampleModel, [("user", "input")])

    def test_modulo_nao_expoe_mais_helpers_de_reparo(self):
        import src.structured_llm as mod

        for removido in ("_parse_llm_json", "_extract_json", "_invoke_json_fallback",
                         "_fix_invalid_escapes"):
            assert not hasattr(mod, removido), f"{removido} não deveria existir"

    def test_json_repair_nao_e_mais_importado(self):
        import src.structured_llm as mod
        assert "json_repair" not in dir(mod)


class TestRetentativa:
    def test_retenta_erro_transitorio_e_devolve(self, llm_mock, sample_intent, monkeypatch):
        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", "2")
        _, structured = llm_mock
        structured.invoke.side_effect = [TimeoutError("504"), sample_intent]

        result = invoke_structured(StructuredIntent, [("user", "input")])

        assert result.goal == "Implementar CRUD de Cliente."
        assert structured.invoke.call_count == 2

    def test_respeita_o_teto_de_tentativas(self, llm_mock, monkeypatch):
        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", "1")
        _, structured = llm_mock
        structured.invoke.side_effect = RuntimeError("erro")

        with pytest.raises(StructuredOutputError):
            invoke_structured(SampleModel, [("user", "input")])

        assert structured.invoke.call_count == 2  # 1 inicial + 1 retentativa

    def test_retentativa_configuravel(self, monkeypatch):
        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", "5")
        assert max_retries() == 5
        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", "-3")
        assert max_retries() == 0

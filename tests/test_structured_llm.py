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
    def test_retenta_saida_fora_do_schema_e_devolve(self, llm_mock, sample_intent, monkeypatch):
        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", "2")
        _, structured = llm_mock
        structured.invoke.side_effect = [
            {"raw": None, "parsed": None, "parsing_error": "campo ausente"},
            sample_intent,
        ]

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


class TestFalhaDeInfraestrutura:
    """
    Falha de infraestrutura não é falha de schema.

    Em 28/09/2026 um 429 do DeepInfra e depois uma chave revogada (401)
    apareceram na telemetria do braço orchestration como "modelo não conformou
    ao schema". O single-agent registrava o mesmo evento como RateLimitError.
    """

    @pytest.mark.parametrize("status", [401, 402, 403, 408, 429, 500, 502, 503])
    def test_status_de_infra_e_erro_de_provedor(self, status):
        from src.config import is_provider_error
        from tests.fakes import erro_http

        assert is_provider_error(erro_http(status))

    @pytest.mark.parametrize("status", [400, 404, 422])
    def test_requisicao_recusada_nao_e_infra(self, status):
        from src.config import is_provider_error
        from tests.fakes import erro_http

        assert not is_provider_error(erro_http(status))

    def test_rede_e_timeout_sao_infra(self):
        from src.config import is_provider_error

        assert is_provider_error(TimeoutError("504"))
        assert is_provider_error(ConnectionError("reset"))
        assert not is_provider_error(RuntimeError("erro"))
        assert not is_provider_error(ValueError("schema"))

    @pytest.mark.parametrize("status", [401, 429])
    def test_falha_de_provedor_nao_e_retentada_aqui(self, llm_mock, monkeypatch, status):
        """
        O cliente já retentou. Uma segunda camada de retentativa só existia no
        orchestration: 3 × 7 tentativas contra as 7 do single-agent.
        """
        from src.config import ProviderError
        from tests.fakes import erro_http

        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", "2")
        _, structured = llm_mock
        structured.invoke.side_effect = erro_http(status)

        with pytest.raises(ProviderError, match="provedor não atendeu") as info:
            invoke_structured(SampleModel, [("user", "input")])

        assert not isinstance(info.value, StructuredOutputError)
        assert structured.invoke.call_count == 1

    def test_stop_reason_mostra_a_causa_por_baixo_do_provider_error(self, llm_mock):
        """No orchestration, 429 e chave revogada saíam os dois `infra_error: ProviderError`."""
        from src.arms.runner import stop_reason_for
        from src.config import is_fatal_provider_error
        from tests.fakes import erro_http

        _, structured = llm_mock
        for status, nome, fatal in ((429, "RateLimitError", False),
                                    (401, "AuthenticationError", True)):
            structured.invoke.side_effect = erro_http(status)
            with pytest.raises(Exception) as info:
                invoke_structured(SampleModel, [("user", "input")])
            assert stop_reason_for(info.value) == f"infra_error: {nome}"
            assert is_fatal_provider_error(info.value) is fatal
            assert is_fatal_provider_error(erro_http(status)) is fatal

    def test_provedor_cai_depois_de_falha_de_schema_e_infra(self, llm_mock, monkeypatch):
        """A falha de schema anterior não muda a natureza da que encerrou o run."""
        from src.config import ProviderError
        from tests.fakes import erro_http

        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", "2")
        _, structured = llm_mock
        structured.invoke.side_effect = [
            {"raw": None, "parsed": None, "parsing_error": "campo ausente"},
            erro_http(429),
        ]

        with pytest.raises(ProviderError):
            invoke_structured(SampleModel, [("user", "input")])
        assert structured.invoke.call_count == 2

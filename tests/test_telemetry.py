"""Testes da telemetria JSONL: envelope, schema, acumulação e autonomia."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from src.metrics import process_metrics, self_recoveries
from src.budget import BudgetTracker, RunBudget
from src.schemas.test_report import TestReport
from src.telemetry import (
    EVENT_TYPES,
    SCHEMA_VERSION,
    TelemetryWriter,
    aggregate_cost,
    providers_served,
    read_events,
)
from src.tools.base import ToolCallRecord

SCHEMA_PATH = Path("harness/schema/event.schema.json")


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text()))


@pytest.fixture
def writer(tmp_path) -> TelemetryWriter:
    w = TelemetryWriter(
        tmp_path / "events.jsonl",
        run_id="run-001", arm="orchestration", task_id="tomlkit-0001",
        model="vendor/modelo", provider_requested="Fireworks",
    )
    yield w
    w.close()


# ------------------------------------------------------------------ envelope


class TestEnvelope:
    def test_toda_linha_valida_contra_o_schema(self, writer, validator):
        writer.run_start(base_commit="abc123")
        with writer.node("developer", agent_role="developer"):
            writer.set_turn(1)
            writer.emit("route", payload={"para": "validator"})
            writer.emit_error(ValueError("falhou"))
            writer.emit_circuit_break("max_turns")
        writer.run_end(stop_reason="tests_pass")

        eventos = read_events(writer.path)
        assert len(eventos) == 7  # start, enter, route, error, break, exit, end
        for evento in eventos:
            validator.validate(evento)

    def test_seq_e_monotonico_e_comeca_em_um(self, writer):
        for _ in range(5):
            writer.emit("route")
        assert [e["seq"] for e in read_events(writer.path)] == [1, 2, 3, 4, 5]

    def test_identificadores_do_run_em_toda_linha(self, writer):
        writer.run_start()
        writer.emit("route")
        for evento in read_events(writer.path):
            assert evento["run_id"] == "run-001"
            assert evento["arm"] == "orchestration"
            assert evento["task_id"] == "tomlkit-0001"
            assert evento["schema_version"] == SCHEMA_VERSION

    def test_event_type_desconhecido_e_recusado(self, writer):
        with pytest.raises(ValueError, match="event_type desconhecido"):
            writer.emit("inventado")

    def test_envelope_nao_carrega_nivel_de_intervencao(self, writer):
        """
        O Índice de Autonomia foi removido do desenho: com os dois braços
        autônomos ele seria constante e não discriminaria nada.
        """
        writer.run_start()
        writer.emit("route")
        assert all("intervention_level" not in e for e in read_events(writer.path))

    def test_durabilidade_linha_a_linha(self, writer):
        """Se o run morrer no meio, o que já ocorreu tem de estar em disco."""
        writer.emit("route")
        assert len(read_events(writer.path)) == 1  # sem close()


class TestContexto:
    def test_node_emite_entrada_e_saida(self, writer):
        with writer.node("validator", agent_role="validator"):
            pass
        tipos = [e["event_type"] for e in read_events(writer.path)]
        assert tipos == ["node_enter", "node_exit"]

    def test_eventos_herdam_no_e_papel(self, writer):
        with writer.node("developer", agent_role="developer"):
            writer.set_turn(3)
            writer.emit("route")
        evento = read_events(writer.path)[1]
        assert (evento["node"], evento["agent_role"], evento["turn"]) == ("developer", "developer", 3)

    def test_contexto_restaurado_ao_sair(self, writer):
        with writer.node("developer", agent_role="developer"):
            pass
        writer.emit("route")
        assert read_events(writer.path)[-1]["node"] is None

    def test_excecao_no_no_gera_evento_e_propaga(self, writer):
        with pytest.raises(RuntimeError):
            with writer.node("developer"):
                raise RuntimeError("estourou")
        tipos = [e["event_type"] for e in read_events(writer.path)]
        assert tipos == ["node_enter", "error", "node_exit"]

    def test_papel_nulo_no_braco_a2(self, tmp_path):
        """agent_role null é o que distingue single-agent de orchestration no dado bruto."""
        with TelemetryWriter(tmp_path / "e.jsonl", run_id="r",
                             arm="single-agent", task_id="t") as w:
            with w.node("single_agent"):
                w.emit("route")
        assert all(e["agent_role"] is None for e in read_events(tmp_path / "e.jsonl"))


# ---------------------------------------------------------------- atalhos


class _FakeMessage:
    def __init__(self, metadata: dict, tool_calls: list | None = None):
        self.response_metadata = metadata
        self.tool_calls = tool_calls or []


class TestAtalhosTipados:
    def test_llm_call_extrai_tokens_custo_e_provedor(self, writer, validator):
        mensagem = _FakeMessage(
            {
                "model_name": "vendor/modelo",
                "provider": "Fireworks",
                "id": "gen-1",
                "finish_reason": "tool_calls",
                "token_usage": {
                    "prompt_tokens": 1200, "completion_tokens": 80, "total_tokens": 1280,
                    "cost": 0.0042, "completion_tokens_details": {"reasoning_tokens": 15},
                },
            },
            tool_calls=[{"name": "search_code", "args": {}}],
        )
        evento = writer.emit_llm_call(mensagem, latency_ms=910)
        validator.validate(evento)

        assert evento["provider_served"] == "Fireworks"
        assert evento["tokens_total"] == 1280
        assert evento["cost_usd"] == 0.0042
        assert evento["tokens_reasoning"] == 15
        assert evento["payload"]["tool_calls_requested"] == ["search_code"]

    def test_tool_call_a_partir_do_record(self, writer, validator):
        record = ToolCallRecord(
            tool_name="write_file", args_hash="abc123", duration_ms=12,
            denied=True, bytes_written=0,
        )
        evento = writer.emit_tool_call(record)
        validator.validate(evento)

        assert evento["tool_name"] == "write_file"
        assert evento["tool_denied"] is True
        assert evento["latency_ms"] == 12

    def test_test_run_a_partir_do_report(self, writer, validator):
        report = TestReport(
            exit_code=1, passed=1029, failed=1, duration_s=1.9,
            failing_node_ids=["tests/test_x.py::test_y"],
        )
        evento = writer.emit_test_run(report)
        validator.validate(evento)

        assert evento["tool_exit_code"] == 1
        assert evento["payload"]["green"] is False
        assert evento["payload"]["failing_node_ids"] == ["tests/test_x.py::test_y"]


# --------------------------------------------------------------- acumulação


class TestTotais:
    def _llm(self, tokens: int, custo: float):
        return _FakeMessage({"token_usage": {
            "prompt_tokens": tokens, "completion_tokens": 0,
            "total_tokens": tokens, "cost": custo,
        }})

    def test_soma_tokens_e_custo(self, writer):
        writer.emit_llm_call(self._llm(1000, 0.01))
        writer.emit_llm_call(self._llm(500, 0.005))
        assert writer.totals.tokens_total == 1500
        assert writer.totals.cost_usd == pytest.approx(0.015)
        assert writer.totals.llm_calls == 2

    def test_totais_batem_com_a_reagregacao_do_arquivo(self, writer):
        writer.emit_llm_call(self._llm(1000, 0.01))
        writer.emit_tool_call(ToolCallRecord("read_file", "h", 5))
        writer.emit_llm_call(self._llm(700, 0.007))

        custo = aggregate_cost(read_events(writer.path))
        assert custo["tokens_total"] == writer.totals.tokens_total
        assert custo["cost_usd"] == pytest.approx(writer.totals.cost_usd)
        assert custo["llm_calls"] == 2 and custo["tool_calls"] == 1

    def test_run_end_carrega_os_totais(self, writer):
        writer.emit_llm_call(self._llm(100, 0.001))
        evento = writer.run_end(stop_reason="tests_pass")
        assert evento["payload"]["totals"]["tokens_total"] == 100
        assert evento["payload"]["stop_reason"] == "tests_pass"

    def test_detecta_variacao_de_provedor(self, writer):
        """Se o pino falhar, tem de ficar visível no dado bruto."""
        writer.emit_llm_call(_FakeMessage({"provider": "Fireworks", "token_usage": {}}))
        writer.emit_llm_call(_FakeMessage({"provider": "Together", "token_usage": {}}))
        assert providers_served(read_events(writer.path)) == {"Fireworks", "Together"}


# --------------------------------------------------- métricas de processo


class TestMetricasDeProcesso:
    """
    Substituem o Índice de Autonomia, que era degenerado com dois braços
    headless. Estas variam de fato entre as topologias.
    """

    def test_auto_recuperacao_conta_falha_seguida_de_verde(self):
        eventos = [
            {"event_type": "test_run", "payload": {"green": False}},
            {"event_type": "test_run", "payload": {"green": True}},
            {"event_type": "test_run", "payload": {"green": False}},
            {"event_type": "test_run", "payload": {"green": True}},
        ]
        assert self_recoveries(eventos) == 2

    def test_verde_de_primeira_nao_e_recuperacao(self):
        assert self_recoveries([{"event_type": "test_run", "payload": {"green": True}}]) == 0

    def test_falhas_seguidas_contam_uma_recuperacao_so(self):
        eventos = [
            {"event_type": "test_run", "payload": {"green": False}},
            {"event_type": "test_run", "payload": {"green": False}},
            {"event_type": "test_run", "payload": {"green": True}},
        ]
        assert self_recoveries(eventos) == 1

    def test_eventos_que_nao_sao_execucao_de_teste_sao_ignorados(self):
        eventos = [
            {"event_type": "test_run", "payload": {"green": False}},
            {"event_type": "llm_call"},
            {"event_type": "test_run", "payload": {"green": True}},
        ]
        assert self_recoveries(eventos) == 1

    def test_metricas_de_processo(self):
        eventos = [
            {"event_type": "llm_call", "turn": 1},
            {"event_type": "tool_call", "turn": 2, "tool_denied": True},
            {"event_type": "test_run", "turn": 2, "payload": {"green": True}},
        ]
        m = process_metrics(eventos)
        assert m == {
            "turns": 2, "llm_calls": 1, "tool_calls": 1,
            "tool_denials": 1, "test_runs": 1, "self_recoveries": 0,
        }

    def test_nao_ha_mais_indice_de_autonomia(self):
        import src.metrics as mod

        assert not hasattr(mod, "autonomy_index")
        assert not hasattr(mod, "InterventionLevel")


# ------------------------------------------------------------- circuit breaker


class TestOrcamento:
    def test_para_por_tokens(self, writer):
        orcamento = RunBudget(max_tokens=1000, max_wall_seconds=9999, max_turns=99)
        tracker = BudgetTracker(orcamento, writer.totals)
        assert not tracker.exhausted

        writer.emit_llm_call(_FakeMessage({"token_usage": {"total_tokens": 1000}}))
        assert "max_tokens" in tracker.exceeded()

    def test_para_por_turnos(self, writer):
        tracker = BudgetTracker(RunBudget(max_turns=2), writer.totals)
        tracker.next_turn()
        assert not tracker.exhausted
        tracker.next_turn()
        assert "max_turns" in tracker.exceeded()

    def test_para_por_tempo(self, writer):
        tracker = BudgetTracker(RunBudget(max_wall_seconds=0), writer.totals)
        assert "max_wall_seconds" in tracker.exceeded()

    def test_restante_nunca_negativo(self, writer):
        tracker = BudgetTracker(RunBudget(max_tokens=100), writer.totals)
        writer.emit_llm_call(_FakeMessage({"token_usage": {"total_tokens": 500}}))
        assert tracker.remaining()["tokens"] == 0

    def test_manifesto_serializavel(self):
        orcamento = RunBudget.from_env()
        assert json.loads(json.dumps(orcamento.as_manifest())) == orcamento.as_manifest()

    def test_le_do_ambiente(self, monkeypatch):
        monkeypatch.setenv("RUN_MAX_TOKENS", "123")
        monkeypatch.setenv("RUN_MAX_TURNS", "7")
        orcamento = RunBudget.from_env()
        assert orcamento.max_tokens == 123 and orcamento.max_turns == 7


def test_todos_os_event_types_estao_no_schema(validator):
    """Schema e código não podem divergir."""
    do_schema = set(validator.schema["properties"]["event_type"]["enum"])
    assert do_schema == set(EVENT_TYPES)

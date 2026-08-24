"""Braço A2 ponta a ponta, offline, contra o workspace real do tomlkit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from src.arms.driver import DeterministicDriver, DriverAction, DriverPolicy
from src.arms.runner import build_run_spec, run_arm, seed_for_repetition
from src.budget import RunBudget
from src.config import LLMConfig
from src.schemas.test_report import TestReport
from src.seeds import TOMLKIT
from src.telemetry import read_events
from tests.fakes import FakeToolCallingLLM, ai

BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"
FIX_COMMIT = "d548e18b"
SOURCE_FILE = "tomlkit/parser.py"
LLM = LLMConfig(model="fake/modelo", provider="FakeProvider", seed=1, max_tokens=512)

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


def _fonte_corrigida() -> str:
    return subprocess.run(
        ["git", "--git-dir", str(TOMLKIT.mirror_path), "show", f"{FIX_COMMIT}:{SOURCE_FILE}"],
        capture_output=True, text=True, check=True,
    ).stdout


# ------------------------------------------------------------------- política


class TestDriverDeterministico:
    def test_entrega_a_spec_uma_vez_so(self):
        d = DeterministicDriver()
        assert d.mensagem_inicial("spec") == "spec"
        with pytest.raises(RuntimeError, match="uma vez"):
            d.mensagem_inicial("spec de novo")

    def test_verde_encerra(self):
        decisao = DeterministicDriver().apos_turno(TestReport(exit_code=0, passed=10))
        assert decisao.action is DriverAction.ENCERRAR_VERDE
        assert decisao.feedback == ""

    def test_verde_sem_mudanca_nao_encerra(self):
        """
        A suíte visível já passa no commit-base. Sem esta guarda, "não fazer
        nada" satisfaz o critério de parada — foi o que o piloto produziu:
        10 turnos, stop_reason=tests_pass e patch.diff de zero byte.
        """
        decisao = DeterministicDriver().apos_turno(
            TestReport(exit_code=0, passed=10), houve_mudanca=False
        )

        assert decisao.action is DriverAction.CONTINUAR
        assert "nenhum arquivo foi modificado" in decisao.feedback

    def test_falha_devolve_stderr_cru(self):
        report = TestReport(exit_code=1, failed=1, stdout_tail="E   assert 1 == 2")
        decisao = DeterministicDriver().apos_turno(report)

        assert decisao.action is DriverAction.CONTINUAR
        assert "E   assert 1 == 2" in decisao.feedback

    def test_nao_sugere_nem_aponta_arquivo(self):
        """Qualquer ajuda aqui seria engenharia do harness creditada ao agente."""
        report = TestReport(
            exit_code=1, failed=1,
            stdout_tail="E   TypeError",
            failing_node_ids=["tests/test_parser.py::test_array"],
        )
        feedback = DeterministicDriver().apos_turno(report).feedback

        assert "tomlkit/parser.py" not in feedback
        for palavra in ("sugir", "sugest", "tente", "provavelmente", "corrija"):
            assert palavra not in feedback.lower()

    def test_trunca_pelo_fim(self):
        """O resumo de falhas do pytest fica no fim da saída."""
        report = TestReport(exit_code=1, stdout_tail="x" * 9000 + "FIM_IMPORTANTE")
        feedback = DeterministicDriver(DriverPolicy(stderr_chars=100)).apos_turno(report).feedback
        assert "FIM_IMPORTANTE" in feedback

    def test_modo_de_ablacao_sumariza(self):
        report = TestReport(exit_code=1, failed=2,
                            failing_node_ids=["a::x", "b::y"], stdout_tail="cru")
        feedback = DeterministicDriver(DriverPolicy(sumariza_falhas=True)).apos_turno(report).feedback
        assert "2 teste(s) falhando" in feedback and "cru" not in feedback


# ---------------------------------------------------------------- ponta a ponta


@mirror_available
class TestBracoA2:
    def test_resolve_a_tarefa(self, tmp_path):
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "search_code",
                            "args": {"pattern": "def _parse_array", "path": "tomlkit"}}]),
            ai(tool_calls=[{"name": "write_file",
                            "args": {"path": SOURCE_FILE, "content": _fonte_corrigida()}}]),
            ai(content="Elemento malformado agora levanta erro."),
        ])
        spec = build_run_spec(
            run_id="a2-e2e", arm="A2", task_id="tomlkit-0001",
            statement="Levantar erro em elemento malformado de array.",
            base_commit=BASE_COMMIT, out_dir=tmp_path / "run",
            llm=LLM, budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=10),
        )

        resumo = run_arm(spec, llm_factory=llm.factory)

        assert resumo["is_valid"] is True
        assert resumo["stop_reason"] == "tests_pass"
        assert SOURCE_FILE in resumo["changed_files"]
        assert resumo["topology"] == "single_agent"

    def test_sem_papeis_na_telemetria(self, tmp_path):
        """`agent_role` nulo é o que distingue A2 de B no dado bruto."""
        llm = FakeToolCallingLLM([ai(content="nada a fazer")])
        spec = build_run_spec(
            run_id="a2-papeis", arm="A2", task_id="t", statement="s",
            base_commit=BASE_COMMIT, out_dir=tmp_path / "run", llm=LLM,
            budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=5),
        )

        run_arm(spec, llm_factory=llm.factory)

        eventos = read_events(spec.out_dir / "events.jsonl")
        assert all(e["agent_role"] is None for e in eventos)
        assert {e["node"] for e in eventos if e["node"]} == {"single_agent", "driver"}

    def test_driver_devolve_falha_e_agente_tenta_de_novo(self, tmp_path):
        """O ciclo agente↔driver: falha real volta como stderr e há novo turno."""
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "write_file", "args": {
                "path": "tomlkit/_utils.py",
                "content": "import re\nraise RuntimeError('quebrei')\n"}}]),
            ai(content="pronto"),          # driver roda a suíte -> vermelha
            ai(content="desisto"),         # segundo turno após o feedback
        ])
        spec = build_run_spec(
            run_id="a2-retry", arm="A2", task_id="t", statement="s",
            base_commit=BASE_COMMIT, out_dir=tmp_path / "run", llm=LLM,
            budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=4),
        )

        resumo = run_arm(spec, llm_factory=llm.factory)

        assert resumo["is_valid"] is False
        eventos = read_events(spec.out_dir / "events.jsonl")
        assert sum(1 for e in eventos if e["event_type"] == "test_run") >= 1
        # o stderr cru chegou ao agente numa mensagem posterior
        assert any("A suíte falhou" in str(m.content)
                   for conversa in llm.chamadas for m in conversa)

    def test_para_por_orcamento(self, tmp_path):
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "list_files", "args": {"path": "tomlkit"}}]),
        ])
        spec = build_run_spec(
            run_id="a2-budget", arm="A2", task_id="t", statement="s",
            base_commit=BASE_COMMIT, out_dir=tmp_path / "run", llm=LLM,
            budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=3),
        )

        resumo = run_arm(spec, llm_factory=llm.factory)

        assert resumo["stop_reason"].startswith("budget")
        assert "circuit_break" in {
            e["event_type"] for e in read_events(spec.out_dir / "events.jsonl")
        }


# --------------------------------------------------------------- saída do run


@mirror_available
class TestArtefatosDoRun:
    @pytest.fixture
    def executado(self, tmp_path):
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "write_file",
                            "args": {"path": SOURCE_FILE, "content": _fonte_corrigida()}}]),
            ai(content="feito"),
        ])
        spec = build_run_spec(
            run_id="a2-saida", arm="A2", task_id="tomlkit-0001", statement="s",
            base_commit=BASE_COMMIT, out_dir=tmp_path / "run", llm=LLM,
            budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=6),
        )
        run_arm(spec, llm_factory=llm.factory)
        return spec.out_dir

    def test_grava_os_quatro_artefatos(self, executado):
        for nome in ("manifest.json", "events.jsonl", "summary.json", "patch.diff"):
            assert (executado / nome).exists(), nome

    def test_patch_e_o_diff_real(self, executado):
        patch = (executado / "patch.diff").read_text()
        assert patch.startswith("diff --git")
        assert SOURCE_FILE in patch

    def test_manifesto_registra_a_config_resolvida(self, executado):
        m = json.loads((executado / "manifest.json").read_text())
        assert m["arm"] == "A2" and m["topology"] == "single_agent"
        # a semente do manifesto é a efetiva, derivada da repetição
        assert m["llm"]["seed"] == seed_for_repetition(1, m["repetition"])
        assert m["llm"]["allow_fallbacks"] is False
        assert m["driver_policy"]["sumariza_falhas"] is False
        assert m["base_commit"] == BASE_COMMIT

    def test_eventos_validam_contra_o_schema(self, executado):
        validador = Draft202012Validator(
            json.loads(Path("harness/schema/event.schema.json").read_text())
        )
        for evento in read_events(executado / "events.jsonl"):
            validador.validate(evento)

    def test_workspace_fica_disponivel_para_o_harness(self, executado):
        assert (executado / "workspace" / ".git").is_dir()
        assert (executado / "workspace" / SOURCE_FILE).exists()

"""
O piloto ponta a ponta, offline.

Roda os dois braços, o avaliador externo e o relatório sem tocar na rede e
sem gastar crédito. É o ensaio da cadeia que a coleta definitiva vai usar:
se algo aqui quebra, quebra com dinheiro real depois.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.arms.pilot import PilotOutcome, format_report, run_pilot, save_report
from src.budget import RunBudget
from src.config import LLMConfig
from src.seeds import TOMLKIT
from tests.fakes import FakeToolCallingLLM, ai, fabrica_por_run

TAREFA = Path("tasks/tomlkit-0001")
FIX_COMMIT = "d548e18b"
SOURCE_FILE = "tomlkit/parser.py"
LLM = LLMConfig(model="fake/modelo", provider="FakeProvider", seed=1, max_tokens=512)
ORCAMENTO = RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=8)

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


def _fonte_corrigida() -> str:
    return subprocess.run(
        ["git", "--git-dir", str(TOMLKIT.mirror_path), "show", f"{FIX_COMMIT}:{SOURCE_FILE}"],
        capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture
def sem_saida_estruturada(monkeypatch):
    """Fixa as saídas estruturadas do braço B; o resto do grafo roda de verdade."""
    from src.schemas.intent import StructuredIntent
    from src.schemas.test_plan import TestPlan

    def _estruturado(schema, mensagens, **kwargs):
        if schema is StructuredIntent:
            return StructuredIntent(
                context="", goal="corrigir", phases=[], acceptance_criteria=[],
                clarifications_needed=[], is_ready=True,
            ), None
        if schema is TestPlan:
            return TestPlan(summary="plano", unit_tests=[], integration_tests=[]), None
        raise AssertionError(f"schema inesperado: {schema}")

    monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _estruturado)


def _llm_que_corrige() -> FakeToolCallingLLM:
    return FakeToolCallingLLM([
        ai(tool_calls=[{"name": "write_file",
                        "args": {"path": SOURCE_FILE, "content": _fonte_corrigida()}}]),
        ai(content="Elemento malformado agora levanta erro."),
    ])


@mirror_available
class TestPilotoPontaAPonta:
    def test_roda_os_dois_bracos_e_o_avaliador(self, tmp_path, monkeypatch,
                                               sem_saida_estruturada):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        resultados = run_pilot(
            task_dir=TAREFA, repetitions=1, out_root=tmp_path / "runs",
            llm=LLM, budget=ORCAMENTO,
            llm_factory=fabrica_por_run(_llm_que_corrige),
        )

        assert [r.arm for r in resultados] == ["A2", "B"]
        for r in resultados:
            assert r.erro is None, r.erro
            assert r.resolved is True, f"{r.arm} não resolveu: f2p={r.f2p}"
            assert r.cheat_criticos == 0
            assert r.tokens > 0
            assert (r.out_dir / "patch.diff").read_text().strip(), "patch vazio"

    def test_pareia_a_semente_entre_os_bracos(self, tmp_path, monkeypatch,
                                              sem_saida_estruturada):
        """Repetição k de um braço e a k do outro são um par, não amostras soltas."""
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        run_pilot(
            task_dir=TAREFA, repetitions=2, out_root=tmp_path / "runs",
            llm=LLM, budget=ORCAMENTO, evaluate=False,
            llm_factory=fabrica_por_run(_llm_que_corrige),
        )

        por_repeticao: dict[int, set[int]] = {}
        for manifesto in (tmp_path / "runs").rglob("manifest.json"):
            m = json.loads(manifesto.read_text())
            por_repeticao.setdefault(m["repetition"], set()).add(m["llm"]["seed"])

        assert len(por_repeticao) == 2
        for repeticao, sementes in por_repeticao.items():
            assert len(sementes) == 1, f"repetição {repeticao} não pareada: {sementes}"
        assert len(set().union(*por_repeticao.values())) == 2, "repetições com a mesma semente"

    def test_run_que_morre_vira_linha_de_erro(self, tmp_path, monkeypatch,
                                              sem_saida_estruturada):
        """Um braço que explode não pode levar o piloto inteiro junto."""
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        class _Explode:
            def bind_tools(self, tools, **kwargs):
                return self

            def invoke(self, mensagens, **kwargs):
                raise RuntimeError("provedor caiu")

        resultados = run_pilot(
            task_dir=TAREFA, repetitions=1, out_root=tmp_path / "runs",
            llm=LLM, budget=ORCAMENTO, llm_factory=lambda *a, **k: _Explode(),
        )

        assert len(resultados) == 2
        for r in resultados:
            assert r.stop_reason.startswith("error:")
            assert "provedor caiu" in (r.erro or "")
            assert r.resolved is None  # não avaliado: não houve run


class TestRelatorio:
    def _amostra(self) -> list[PilotOutcome]:
        return [
            PilotOutcome(arm="A2", repetition=1, run_id="a", out_dir=Path("/x"),
                         stop_reason="tests_pass", turns=4, tokens=1000, cost_usd=0.01,
                         resolved=True, f2p="1/1"),
            PilotOutcome(arm="B", repetition=1, run_id="b", out_dir=Path("/y"),
                         stop_reason="budget_turns", turns=8, tokens=5000, cost_usd=0.05,
                         resolved=False, f2p="0/1", erro=None),
        ]

    def test_tabela_traz_os_dois_bracos_e_o_agregado(self):
        texto = format_report(self._amostra(), "tomlkit-0001")

        assert "tomlkit-0001" in texto
        assert "A2: 1/1 resolvidos" in texto
        assert "B: 0/1 resolvidos" in texto
        assert "US$ 0.06000" not in texto  # agregado é por braço, não somado

    def test_json_do_relatorio_e_relegivel(self, tmp_path):
        destino = save_report(self._amostra(), tmp_path / "pilot.json")
        dados = json.loads(destino.read_text())

        assert [d["arm"] for d in dados] == ["A2", "B"]
        assert dados[0]["resolved"] is True and dados[1]["resolved"] is False

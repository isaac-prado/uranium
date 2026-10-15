"""
Rodada 2 (decisões 27 e 29 do autor, 14/10/2026): testes visíveis retirados da
suíte do agente, revisor que executa a reprodução, nota de ciclo do developer.
"""

from __future__ import annotations

import json

import pytest

from src import config
from src.budget import RunBudget
from src.schemas.intent import StructuredIntentV2
from src.seeds import TOMLKIT
from src.telemetry import read_events
from src.workspace import Workspace, WorkspaceSpec
from tests.fakes import FakeToolCallingLLM, ai
from tests.test_nodes import BASE_COMMIT, INTENT, _estado, ambiente  # noqa: F401

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(), reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


class TestVisibleDeselect:
    def test_task_json_carrega_a_lista(self, tmp_path):
        from harness.taskspec import load_task

        (tmp_path / "task.json").write_text(json.dumps({
            "id": "t", "seed_repo": "tomlkit", "base_commit": BASE_COMMIT, "fail_to_pass": ["tests/x.py::t"],
            "hidden_tests": ["tests/x.py"], "visible_deselect": ["tests/test_items.py::test_a"],
        }), encoding="utf-8")
        assert load_task(tmp_path).visible_deselect == ("tests/test_items.py::test_a",)

    def test_ausente_e_vazio(self, tmp_path):
        from harness.taskspec import load_task

        (tmp_path / "task.json").write_text(json.dumps({
            "id": "t", "seed_repo": "tomlkit", "base_commit": BASE_COMMIT, "fail_to_pass": ["tests/x.py::t"],
            "hidden_tests": ["tests/x.py"],
        }), encoding="utf-8")
        assert load_task(tmp_path).visible_deselect == ()

    @mirror_available
    def test_run_pytest_deseleciona_na_suite_visivel(self, tmp_path):
        from src.tools.exec import run_pytest

        alvo = "tests/test_items.py::test_items_can_be_appended_to_and_removed_from_a_table"
        ws = Workspace.materialize(
            WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT, visible_deselect=(alvo,)),
            run_id="desel", dest=tmp_path / "ws",
        )
        sem = run_pytest(ws, ["tests/test_items.py"])
        com = run_pytest(ws, ["tests/test_items.py"])
        assert "--deselect " + alvo in com.command
        assert com.green and sem.green
        # a suíte visível de fato perdeu o teste deselecionado
        ws2 = Workspace.materialize(WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT),
                                    run_id="desel2", dest=tmp_path / "ws2")
        assert run_pytest(ws2, ["tests/test_items.py"]).passed == com.passed + 1

    @mirror_available
    def test_deselect_vale_com_pyproject_acima_do_workspace(self, tmp_path):
        """
        Os runs ficam em runs/ dentro do uranium, cujo pyproject.toml tem
        [tool.pytest.ini_options]. Sem --rootdir o pytest sobe até ele, os node
        ids ganham o prefixo relativo à raiz do uranium e o --deselect não casa.
        Reproduz o cenário: pyproject acima do workspace.
        """
        from src.tools.exec import run_pytest

        (tmp_path / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\ntestpaths = ["tests"]\npythonpath = ["."]\n', encoding="utf-8")
        alvo = "tests/test_items.py::test_items_can_be_appended_to_and_removed_from_a_table"
        ws = Workspace.materialize(
            WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT, visible_deselect=(alvo,)),
            run_id="desel3", dest=tmp_path / "runs" / "ws",
        )
        com = run_pytest(ws, ["tests/test_items.py"])
        assert "--rootdir ." in com.command
        ws2 = Workspace.materialize(WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT),
                                    run_id="desel4", dest=tmp_path / "runs" / "ws2")
        assert run_pytest(ws2, ["tests/test_items.py"]).passed == com.passed + 1

    def test_manifesto_registra_o_rootdir(self):
        from src.arms.runner import _shared_limits

        assert _shared_limits(RunBudget()).get("pytest_rootdir") == "workspace"

    def test_as_tres_tarefas_declaram_a_lista_e_o_motivo(self):
        from harness.taskspec import load_task

        for t, n in (("pygments-0001", 1), ("sqlite-utils-0002", 6), ("tomlkit-0004", 1)):
            task = load_task(f"tasks/{t}")
            assert len(task.visible_deselect) == n
            assert "decisão 27" in json.load(open(f"tasks/{t}/task.json"))["visible_deselect_motivo"]

    def test_manifesto_leva_a_lista_igual_nos_dois_bracos(self, tmp_path):
        from src.arms.runner import build_run_spec
        from tests.test_arm_parity import BUDGET, LLM

        kw = dict(task_id="t", statement="s", base_commit=BASE_COMMIT, repetition=1,
                  out_dir=tmp_path, llm=LLM, budget=BUDGET, visible_deselect=("tests/a.py::t",))
        a = build_run_spec(run_id="a", arm="single-agent", **kw).manifest("t")
        b = build_run_spec(run_id="b", arm="orchestration", **kw).manifest("t")
        assert a["visible_deselect"] == b["visible_deselect"] == ["tests/a.py::t"]
        assert a["manifest_version"] == 11


def _v2(reproduction):
    return StructuredIntentV2(
        context="c", goal="g", phases=[], acceptance_criteria=["print(2 + 2) imprime 4"], is_ready=True,
        reproduction=reproduction, expected_outputs=["4"], constraints=[],
    ).model_dump()


@mirror_available
class TestRevisorQueExecuta:
    def test_off_nao_executa_nada(self, ambiente, monkeypatch):
        from src.agents.validator import _executar_reproducao

        monkeypatch.setattr(config, "REVIEW_EXECUTION", "off")
        _, _, montar = ambiente
        ctx = montar(FakeToolCallingLLM([ai(content="x")]))
        assert _executar_reproducao(_estado(intent=_v2(["print(2 + 2)"])), ctx) == []

    def test_on_executa_os_blocos_python_e_leva_a_saida_ao_revisor(self, ambiente, monkeypatch):
        from src.agents.validator import _build_review_prompt, _executar_reproducao

        monkeypatch.setattr(config, "REVIEW_EXECUTION", "on")
        _, _, montar = ambiente
        ctx = montar(FakeToolCallingLLM([ai(content="x")]))
        estado = _estado(intent=_v2(["```python\nprint(2 + 2)\n```", "```bash\necho oi\n```", "print('b')"]))

        ex = _executar_reproducao(estado, ctx)
        assert [e["executado"] for e in ex] == [True, False, True]
        assert "4" in ex[0]["saida"] and "b" in ex[2]["saida"]
        assert "não é Python" in ex[1]["saida"]

        prompt = _build_review_prompt(estado, ctx, ex)
        assert "Execução dos exemplos de reprodução" in prompt and "[bloco 1]" in prompt

    def test_intent_v1_nao_executa(self, ambiente, monkeypatch):
        from src.agents.validator import _executar_reproducao

        monkeypatch.setattr(config, "REVIEW_EXECUTION", "on")
        _, _, montar = ambiente
        ctx = montar(FakeToolCallingLLM([ai(content="x")]))
        assert _executar_reproducao(_estado(), ctx) == []

    def test_execucoes_vao_ao_evento_validation(self, ambiente, monkeypatch):
        from src.agents.validator import validator
        from src.schemas.validation_result import ValidationResult
        from tests.test_nodes import _mudanca_benigna

        monkeypatch.setattr(config, "REVIEW_EXECUTION", "on")
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        _mudanca_benigna(ws)
        montar(FakeToolCallingLLM([ai(content="x")]))
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw",
                            lambda *a, **k: (ValidationResult(is_valid=True), None))

        validator(_estado(intent=_v2(["print(2 + 2)"])))

        ev = [e for e in read_events(tel.path) if e["event_type"] == "validation"][0]
        assert ev["payload"]["executions"][0]["executado"] is True
        assert "4" in ev["payload"]["executions"][0]["saida"]


@mirror_available
class TestNotaDeCiclo:
    def test_on_pede_a_nota_sem_ferramentas_e_ela_entra_na_memoria(self, ambiente, monkeypatch):
        from src.agents.developer import developer
        from src.feedback import NOTA_DE_CICLO

        monkeypatch.setattr(config, "DEVELOPER_CYCLE_MAX_TURNS", 2)
        monkeypatch.setattr(config, "CYCLE_NOTE", "on")
        _, tel, montar = ambiente
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "list_files", "args": {"path": "tomlkit"}}]),
            ai(tool_calls=[{"name": "list_files", "args": {"path": "tests"}}]),
            ai(content="Li o parser; falta trocar o descarte por erro."),
        ])
        montar(llm, budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=50))

        out = developer(_estado(developer_memory=[]))

        assert out["stop_reason"].startswith("cycle:")
        assert llm.n_invocacoes == 3
        assert llm.chamadas[2][-1].content == NOTA_DE_CICLO
        assert out["developer_memory"][0]["nota"] == "Li o parser; falta trocar o descarte por erro."
        assert out["developer_memory"][0]["turnos"] == 3 and out["turn_count"] == 3
        assert sum(1 for e in read_events(tel.path) if e["event_type"] == "llm_call") == 3

    def test_off_nao_pede_nota(self, ambiente, monkeypatch):
        from src.agents.developer import developer

        monkeypatch.setattr(config, "DEVELOPER_CYCLE_MAX_TURNS", 2)
        monkeypatch.setattr(config, "CYCLE_NOTE", "off")
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([ai(tool_calls=[{"name": "list_files", "args": {"path": "tomlkit"}}])])
        montar(llm, budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=50))
        out = developer(_estado(developer_memory=[]))
        assert llm.n_invocacoes == 2 and out["developer_memory"][0]["nota"] == ""

    def test_nota_nao_e_pedida_com_orcamento_esgotado(self, ambiente, monkeypatch):
        from src.agents.developer import developer

        monkeypatch.setattr(config, "DEVELOPER_CYCLE_MAX_TURNS", 2)
        monkeypatch.setattr(config, "CYCLE_NOTE", "on")
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([ai(tool_calls=[{"name": "list_files", "args": {"path": "tomlkit"}}])])
        montar(llm, budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=2))
        out = developer(_estado(developer_memory=[]))
        assert llm.n_invocacoes == 2 and out["developer_memory"][0]["nota"] == ""


class TestManifestoRodada2:
    def test_chaves_novas_mudam_o_manifesto(self, tmp_path, monkeypatch):
        from tests.test_arm_parity import _spec

        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert base["review_execution"] == "off" and base["cycle_note"] == "off"
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "on")
        monkeypatch.setattr(config, "CYCLE_NOTE", "on")
        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base and depois["review_execution"] == "on" and depois["cycle_note"] == "on"

    def test_nota_de_ciclo_e_mensagem_de_protocolo_conhecida(self):
        import src.feedback as fb

        assert "NOTA_DE_CICLO" in dir(fb)
        for palavra in ("parser", ".py", "função", "provavelmente", "sugir"):
            assert palavra not in fb.NOTA_DE_CICLO.lower()


@mirror_available
class TestRodada3RevisorCoerenteESemTeto:
    """Decisão 32 (14/10/2026): revisão que lista critérios faltando não aprova; teto 0 = sem teto."""

    def _roda(self, ambiente, monkeypatch, *, strict: str, veredito):
        from src.agents.validator import validator
        from tests.test_nodes import _mudanca_benigna

        monkeypatch.setattr(config, "REVIEW_EXECUTION", "on")
        monkeypatch.setattr(config, "REVIEW_STRICT", strict)
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        _mudanca_benigna(ws)
        montar(FakeToolCallingLLM([ai(content="x")]))
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (veredito, None))
        out = validator(_estado(intent=_v2(["print(2 + 2)"]), semantic_rejections=0))
        ev = [e for e in read_events(tel.path) if e["event_type"] == "validation"][-1]
        return out, ev

    def test_on_rebaixa_aprovacao_com_criterio_faltando(self, ambiente, monkeypatch):
        from src.schemas.validation_result import ValidationResult

        out, ev = self._roda(ambiente, monkeypatch, strict="on",
                             veredito=ValidationResult(is_valid=True, missing_criteria=["Critério 2"]))
        assert out["is_valid"] is False
        assert out["validation_result"]["is_valid"] is False
        assert out["validation_result"]["missing_criteria"] == ["Critério 2"]
        assert out["semantic_rejections"] == 1
        assert ev["payload"]["strict_coerced"] is True and ev["payload"]["is_valid"] is False

    def test_on_nao_toca_aprovacao_limpa_nem_reprovacao(self, ambiente, monkeypatch):
        from src.schemas.validation_result import ValidationResult

        out, ev = self._roda(ambiente, monkeypatch, strict="on", veredito=ValidationResult(is_valid=True))
        assert out["is_valid"] is True and ev["payload"]["strict_coerced"] is False
        out, ev = self._roda(ambiente, monkeypatch, strict="on",
                             veredito=ValidationResult(is_valid=False, missing_criteria=["1"]))
        assert out["is_valid"] is False and ev["payload"]["strict_coerced"] is False

    def test_off_reproduz_a_rodada_2(self, ambiente, monkeypatch):
        from src.schemas.validation_result import ValidationResult

        out, ev = self._roda(ambiente, monkeypatch, strict="off",
                             veredito=ValidationResult(is_valid=True, missing_criteria=["Critério 2"]))
        assert out["is_valid"] is True and out["semantic_rejections"] == 0
        assert ev["payload"]["strict_coerced"] is False

    def test_teto_zero_nunca_encerra_por_reprovacao(self, monkeypatch):
        from src.graph import route_after_validator

        monkeypatch.setattr(config, "MAX_SEMANTIC_REJECTIONS", 0)
        estado = {"is_valid": False, "validation_result": {"is_valid": False}, "semantic_rejections": 50}
        assert route_after_validator(estado) == "developer"
        monkeypatch.setattr(config, "MAX_SEMANTIC_REJECTIONS", 2)
        assert route_after_validator(estado) == "test_generator"

    def test_manifesto_registra_review_strict(self, monkeypatch):
        from src.arms.runner import _orchestration_policy

        monkeypatch.setattr(config, "REVIEW_STRICT", "on")
        monkeypatch.setattr(config, "MAX_SEMANTIC_REJECTIONS", 0)
        pol = _orchestration_policy()
        assert pol["review_strict"] == "on" and pol["max_semantic_rejections"] == 0


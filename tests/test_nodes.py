"""
Testes dos nós reescritos: Developer age, Validator executa.

Rodam o grafo inteiro offline, contra um workspace real do tomlkit e um LLM
de sequência gravada. Nenhuma chamada de rede, nenhum custo.
"""

from __future__ import annotations

import subprocess

import pytest

from src.agents.developer import developer
from src.agents.validator import validator
from src.budget import RunBudget
from src.graph import route_after_validator
from src.runtime import RunContext
from src.seeds import TOMLKIT
from src.telemetry import TelemetryWriter, read_events
from src.tools import TOOL_NAMES
from src.workspace import Workspace, WorkspaceSpec
from tests.fakes import FakeToolCallingLLM, ai

BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"
FIX_COMMIT = "d548e18b"
SOURCE_FILE = "tomlkit/parser.py"

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)

INTENT = {
    "context": "O parser descarta silenciosamente elementos malformados de array.",
    "goal": "Levantar erro em vez de descartar elemento malformado de array.",
    "phases": ["Localizar o parsing de array", "Trocar o descarte por erro"],
    "acceptance_criteria": ["Array malformado levanta exceção"],
    "clarifications_needed": [],
    "is_ready": True,
}


def _fonte_corrigida() -> str:
    """Conteúdo do arquivo no commit de correção — o 'patch' que o fake aplica."""
    return subprocess.run(
        ["git", "--git-dir", str(TOMLKIT.mirror_path), "show", f"{FIX_COMMIT}:{SOURCE_FILE}"],
        capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture
def ambiente(tmp_path):
    """Workspace real + telemetria real; o LLM é injetado por teste."""
    ws = Workspace.materialize(
        WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT),
        run_id="nodes-test", dest=tmp_path / "ws",
    )
    tel = TelemetryWriter(
        tmp_path / "events.jsonl",
        run_id="nodes-test", arm="B", task_id="tomlkit-0001",
        model="fake/modelo", provider_requested="FakeProvider",
    )

    def montar(llm: FakeToolCallingLLM, *, budget: RunBudget | None = None) -> RunContext:
        return RunContext.create(
            run_id="nodes-test", arm="B", task_id="tomlkit-0001",
            workspace=ws, telemetry=tel, llm_factory=llm.factory,
            budget=budget or RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=10),
        )

    yield ws, tel, montar
    tel.close()
    RunContext.release("nodes-test")


def _mudanca_benigna(ws) -> None:
    """
    Edita a fonte sem quebrar a suíte.

    Existe porque a suíte visível já está verde no commit-base: sem uma
    mudança real, `is_valid` agora é False por falta de diff, e o teste
    passaria a medir a guarda de diff vazio em vez do que ele quer medir.
    """
    alvo = ws.resolve("tomlkit/_utils.py")
    alvo.write_text(alvo.read_text() + "\n# nota do agente\n")


def _estado(**extra):
    return {"run_id": "nodes-test", "arm": "B", "task_id": "tomlkit-0001",
            "intent": INTENT, **extra}


# ------------------------------------------------------------------ Developer


@mirror_available
class TestDeveloperAge:
    def test_usa_ferramentas_e_modifica_o_repositorio(self, ambiente):
        ws, tel, montar = ambiente
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "search_code",
                            "args": {"pattern": "def _parse_array", "path": "tomlkit"}}]),
            ai(tool_calls=[{"name": "write_file",
                            "args": {"path": SOURCE_FILE, "content": _fonte_corrigida()}}]),
            ai(tool_calls=[{"name": "run_tests", "args": {"node_ids": []}}]),
            ai(content="Troquei o descarte silencioso por erro no parsing de array."),
        ])
        montar(llm)

        out = developer(_estado())

        assert SOURCE_FILE in out["changed_files"]
        assert out["diff_stat"]["files_changed"] == 1
        assert "descarte silencioso" in out["dev_summary"]
        assert out["stop_reason"] == "concluiu"
        assert llm.n_invocacoes == 4

    def test_recebe_o_toolset_completo(self, ambiente):
        """O mesmo conjunto que o braço A2 recebe — a paridade depende disso."""
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([ai(content="pronto")])
        montar(llm)

        developer(_estado())

        assert {t.name for t in llm.ferramentas_ligadas} == set(TOOL_NAMES)

    def test_recusa_de_escrita_volta_ao_modelo_sem_derrubar(self, ambiente):
        ws, _, montar = ambiente
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "write_file",
                            "args": {"path": "tests/test_parser.py", "content": "# trapaca"}}]),
            ai(content="Não posso editar testes."),
        ])
        montar(llm)

        out = developer(_estado())

        assert ws.protected_touched() == []
        assert out["changed_files"] == []
        # a recusa chegou ao modelo como ToolMessage
        ultima_conversa = llm.chamadas[-1]
        assert "RECUSADO" in str(ultima_conversa[-1].content)

    def test_ferramenta_desconhecida_nao_derruba_o_no(self, ambiente):
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "rm_rf", "args": {}}]),
            ai(content="ok"),
        ])
        montar(llm)

        out = developer(_estado())

        assert out["stop_reason"] == "concluiu"
        assert "ferramenta desconhecida" in str(llm.chamadas[-1][-1].content)

    def test_falha_anterior_entra_no_prompt(self, ambiente):
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([ai(content="ok")])
        montar(llm)

        developer(_estado(test_report={
            "exit_code": 1, "failed": 1,
            "stdout_tail": "MARCADOR_DE_FALHA_UNICO",
        }))

        assert "MARCADOR_DE_FALHA_UNICO" in str(llm.chamadas[0][1].content)


@mirror_available
class TestDeveloperOrcamento:
    def test_para_ao_estourar_turnos(self, ambiente):
        _, _, montar = ambiente
        # nunca para sozinho: sempre pede ferramenta
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "list_files", "args": {"path": "tomlkit"}}]),
        ])
        montar(llm, budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=3))

        out = developer(_estado())

        assert out["stop_reason"].startswith("budget")
        assert "max_turns" in out["stop_reason"]
        assert llm.n_invocacoes == 3

    def test_para_ao_estourar_tokens(self, ambiente):
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "list_files", "args": {}}], prompt_tokens=400),
        ])
        montar(llm, budget=RunBudget(max_tokens=1000, max_wall_seconds=600, max_turns=99))

        out = developer(_estado())

        assert "max_tokens" in out["stop_reason"]

    def test_estouro_vira_evento_de_circuit_break(self, ambiente):
        _, tel, montar = ambiente
        llm = FakeToolCallingLLM([ai(tool_calls=[{"name": "list_files", "args": {}}])])
        montar(llm, budget=RunBudget(max_turns=1, max_tokens=10**9, max_wall_seconds=600))

        developer(_estado())

        tipos = [e["event_type"] for e in read_events(tel.path)]
        assert "circuit_break" in tipos


# ------------------------------------------------------------------- Validator


@mirror_available
class TestValidatorExecuta:
    def test_base_verde_sem_revisao_semantica(self, ambiente, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        ws, _, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))
        _mudanca_benigna(ws)

        out = validator(_estado())

        assert out["is_valid"] is True
        assert out["test_report"]["exit_code"] == 0
        assert out["test_report"]["passed"] > 1000
        assert out["validation_result"] is None

    def test_verde_sem_mudanca_nao_e_sucesso(self, ambiente, monkeypatch):
        """
        A suíte visível já passa no commit-base. Sem esta guarda, "não fazer
        nada" satisfaz o critério de parada — foi o que aconteceu no piloto,
        que terminou com is_valid=True e patch.diff de zero byte.
        """
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        ws, _, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))

        out = validator(_estado())

        assert ws.changed_files() == []
        assert out["test_report"]["exit_code"] == 0
        assert out["is_valid"] is False

    def test_codigo_quebrado_reprova(self, ambiente, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        ws, _, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))

        alvo = ws.resolve("tomlkit/_utils.py")
        alvo.write_text(alvo.read_text().replace("import re", "import re\nraise RuntimeError('x')", 1))

        out = validator(_estado())

        assert out["is_valid"] is False
        assert out["test_report"]["exit_code"] != 0

    def test_llm_nao_promove_codigo_que_falha(self, ambiente, monkeypatch):
        """
        Invariante central: is_valid=True exige exit_code=0.

        Mesmo com o revisor semântico afirmando que está tudo certo, código
        que quebra a suíte não pode ser aprovado.
        """
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, _, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))

        alvo = ws.resolve("tomlkit/_utils.py")
        alvo.write_text(alvo.read_text().replace("import re", "import re\nraise RuntimeError('x')", 1))

        chamou_llm = False

        def _nao_deveria_ser_chamado(*args, **kwargs):
            nonlocal chamou_llm
            chamou_llm = True
            raise AssertionError("revisão semântica não deve rodar com suíte vermelha")

        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _nao_deveria_ser_chamado)

        out = validator(_estado())

        assert out["is_valid"] is False
        assert chamou_llm is False

    def test_llm_pode_rebaixar_codigo_que_passa(self, ambiente, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, _, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))
        _mudanca_benigna(ws)

        from src.schemas.validation_result import ValidationResult

        monkeypatch.setattr(
            "src.structured_llm.invoke_structured_raw",
            lambda *a, **k: (
                ValidationResult(is_valid=False, issues=["resolve o teste mas não a intenção"]),
                None,
            ),
        )

        out = validator(_estado())

        assert out["test_report"]["exit_code"] == 0
        assert out["is_valid"] is False  # rebaixado pelo revisor

    def test_falha_de_conformidade_nao_reprova_codigo_verde(self, ambiente, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))
        _mudanca_benigna(ws)

        from src.structured_llm import StructuredOutputError

        def _falha(*a, **k):
            raise StructuredOutputError("modelo não conformou")

        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _falha)

        out = validator(_estado())

        assert out["is_valid"] is True
        assert "error" in [e["event_type"] for e in read_events(tel.path)]

    def test_execucao_vira_evento_de_telemetria(self, ambiente, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        _, tel, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))

        validator(_estado())

        eventos = [e for e in read_events(tel.path) if e["event_type"] == "test_run"]
        assert len(eventos) == 1
        assert eventos[0]["payload"]["green"] is True
        assert eventos[0]["agent_role"] == "validator"


# ------------------------------------------------------------------ roteamento


class TestRoteamento:
    def test_valido_encerra(self):
        assert route_after_validator({"is_valid": True}) == "test_generator"

    def test_invalido_refina(self):
        assert route_after_validator(
            {"is_valid": False, "validation_iteration_count": 0}
        ) == "developer"

    def test_teto_de_iteracoes_encerra(self):
        assert route_after_validator(
            {"is_valid": False, "validation_iteration_count": 99}
        ) == "test_generator"

    def test_estouro_de_orcamento_encerra_antes_de_tudo(self):
        """Sem esta guarda, um agente que nunca fica verde cicla queimando tokens."""
        assert route_after_validator(
            {"is_valid": False, "validation_iteration_count": 0,
             "stop_reason": "budget: max_tokens (400000 >= 400000)"}
        ) == "test_generator"


# ------------------------------------------------------------- grafo completo


@mirror_available
class TestGrafoPontaAPonta:
    """O braço B inteiro resolvendo uma tarefa real do tomlkit, sem rede."""

    def test_pipeline_resolve_a_tarefa(self, ambiente, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        ws, tel, montar = ambiente

        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "search_code",
                            "args": {"pattern": "def _parse_array", "path": "tomlkit"}}]),
            ai(tool_calls=[{"name": "write_file",
                            "args": {"path": SOURCE_FILE, "content": _fonte_corrigida()}}]),
            ai(content="Elemento malformado agora levanta erro."),
        ])
        ctx = montar(llm)

        # intent_refiner e test_generator usam invoke_structured; fixamos as saídas
        from src.schemas.intent import StructuredIntent
        from src.schemas.test_plan import TestPlan

        def _estruturado(schema, mensagens, **kwargs):
            if schema is StructuredIntent:
                return StructuredIntent.model_validate(INTENT), None
            if schema is TestPlan:
                return TestPlan(summary="plano", unit_tests=[], integration_tests=[]), None
            raise AssertionError(f"schema inesperado: {schema}")

        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _estruturado)

        from src.graph import build_graph

        tel.run_start(base_commit=BASE_COMMIT)
        final = build_graph().invoke(_estado(
            raw_request="Levantar erro em elemento malformado de array.",
            iteration_count=0, validation_iteration_count=0, clarification_responses=[],
        ))
        tel.run_end(stop_reason=final.get("stop_reason", "concluiu"))

        # corretude veio de execução, não de opinião
        assert final["is_valid"] is True
        assert final["test_report"]["exit_code"] == 0
        assert SOURCE_FILE in final["changed_files"]
        assert final["test_plan"]["summary"] == "plano"

        # nada protegido foi tocado
        assert ws.protected_touched() == []

        # a telemetria registrou o run inteiro, com papéis preenchidos (braço B)
        eventos = read_events(tel.path)
        papeis = {e["agent_role"] for e in eventos if e["agent_role"]}
        assert {"developer", "validator", "test_generator"} <= papeis
        assert [e["event_type"] for e in eventos][0] == "run_start"
        assert [e["event_type"] for e in eventos][-1] == "run_end"
        assert any(e["event_type"] == "test_run" for e in eventos)
        assert ctx.telemetry.totals.llm_calls >= 3

    def test_eventos_do_grafo_validam_contra_o_schema(self, ambiente, monkeypatch):
        import json
        from pathlib import Path

        from jsonschema import Draft202012Validator

        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        _, tel, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="nada a fazer")]))

        developer(_estado())
        validator(_estado())

        validador = Draft202012Validator(
            json.loads(Path("harness/schema/event.schema.json").read_text())
        )
        for evento in read_events(tel.path):
            validador.validate(evento)

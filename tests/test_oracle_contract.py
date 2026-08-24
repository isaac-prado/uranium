"""
Prova o contrato fail-to-pass numa tarefa real, exercitado pelas ferramentas.

Não é teste de unidade: é a verificação de que o mecanismo inteiro que o
harness vai usar funciona. Se este teste passar, uma tarefa minerada do
histórico do tomlkit é utilizável como oráculo.

Tarefa: d548e18b "raise on malformed array element instead of dropping it" (#527)
"""

from __future__ import annotations

import subprocess

import pytest

from src.seeds import TOMLKIT
from src.tools import build_toolset
from src.tools.exec import run_pytest
from src.workspace import Workspace, WorkspaceSpec

FIX_COMMIT = "d548e18b"
BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"
SOURCE_FILE = "tomlkit/parser.py"
HIDDEN_TEST_FILE = "tests/test_parser.py"

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


def _from_mirror(ref: str, path: str) -> str:
    """Lê um arquivo num commit do espelho, sem tocar o workspace."""
    proc = subprocess.run(
        ["git", "--git-dir", str(TOMLKIT.mirror_path), "show", f"{ref}:{path}"],
        capture_output=True, text=True, check=True,
    )
    return proc.stdout


@pytest.fixture
def ws(tmp_path) -> Workspace:
    spec = WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT)
    return Workspace.materialize(spec, run_id="oracle", dest=tmp_path / "ws")


@mirror_available
def test_contrato_fail_to_pass_ponta_a_ponta(ws):
    tools = {t.name: t for t in build_toolset(ws)}

    # ---- 1. o commit-base está verde: falha futura é atribuível ao agente
    assert run_pytest(ws).green

    # ---- 2. o teste oculto FALHA no commit-base (senão não discrimina nada)
    (ws.root / HIDDEN_TEST_FILE).write_text(_from_mirror(FIX_COMMIT, HIDDEN_TEST_FILE))
    antes = run_pytest(ws, [HIDDEN_TEST_FILE])
    assert not antes.green, "teste oculto passa sem a correção — inútil como oráculo"
    assert antes.failing_node_ids, "precisa dar node ids para o harness reportar f2p"

    # ---- 3. o agente encontra o código pelas ferramentas, sem saber onde está
    achado = tools["search_code"].invoke({"pattern": r"def _parse_array", "path": "tomlkit"})
    assert SOURCE_FILE in achado

    # ---- 4. a correção entra por write_file (caminho de produção, permitido)
    resultado = tools["write_file"].invoke(
        {"path": SOURCE_FILE, "content": _from_mirror(FIX_COMMIT, SOURCE_FILE)}
    )
    assert resultado.startswith("Gravado")

    # ---- 5. o teste oculto agora PASSA, e nada mais regrediu
    depois = run_pytest(ws)
    assert depois.green, depois.stdout_tail[-1500:]
    assert depois.passed > antes.passed

    # ---- 6. nenhuma área protegida foi tocada pelo agente
    #         (o teste oculto foi injetado pelo harness, não pelo agente)
    tocados = [f for f in ws.protected_touched() if f != HIDDEN_TEST_FILE]
    assert tocados == []


@mirror_available
def test_write_file_nao_permite_o_agente_plantar_o_proprio_oraculo(ws):
    """O agente não pode criar nem alterar teste para forjar aprovação."""
    tools = {t.name: t for t in build_toolset(ws)}
    for alvo in (HIDDEN_TEST_FILE, "tests/test_forjado.py", "conftest.py"):
        out = tools["write_file"].invoke({"path": alvo, "content": "def test_x(): pass\n"})
        assert out.startswith("RECUSADO")
    assert ws.protected_touched() == []

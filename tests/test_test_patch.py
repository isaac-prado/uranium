"""
Oráculo por patch de teste do upstream.

Alternativa a escrever o teste oculto à mão: o avaliador restaura os
arquivos de teste do commit-base e aplica o diff de teste que o upstream
escreveu junto com a correção. Escala para dezenas de tarefas e mede
exatamente o que o upstream exigiu — e, de quebra, desfaz adulteração de
teste antes de medir.

O commit usado é o mesmo da tomlkit-0001 (d548e18b), então dá para comparar
o resultado com o do arquivo oculto avulso.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from harness.oracle import apply_test_patch, evaluate_oracle, inject_hidden_tests
from harness.taskspec import TaskSpec, load_task
from src.seeds import TOMLKIT
from src.workspace import Workspace, WorkspaceSpec

FIX_COMMIT = "d548e18b71b28d0e9628127bf0b9dfc5a254dca0"
BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"
TEST_FILE = "tests/test_parser.py"
SOURCE_FILE = "tomlkit/parser.py"

preparado = pytest.mark.skipif(
    not (TOMLKIT.mirror_path.exists() and TOMLKIT.has_venv),
    reason="rode scripts/setup_mirror.py tomlkit",
)


def _mirror(*args: str) -> str:
    return subprocess.run(
        ["git", "--git-dir", str(TOMLKIT.mirror_path), *args],
        capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture
def tarefa(tmp_path) -> TaskSpec:
    """Uma tarefa equivalente à tomlkit-0001, mas com oráculo por patch."""
    raiz = tmp_path / "task"
    raiz.mkdir()
    (raiz / "test_patch.diff").write_text(
        _mirror("diff", BASE_COMMIT, FIX_COMMIT, "--", TEST_FILE), encoding="utf-8")
    (raiz / "task.json").write_text(json.dumps({
        "id": "tomlkit-patch",
        "seed_repo": "tomlkit",
        "base_commit": BASE_COMMIT,
        "fix_commit": FIX_COMMIT,
        "source_dir": "tomlkit",
        "suite_targets": ["tests/"],
        "pass_to_pass": ["tests/"],
        "test_patch": "test_patch.diff",
        "fail_to_pass": [
            f"{TEST_FILE}::test_array_with_malformed_element_raises",
        ],
    }), encoding="utf-8")
    return load_task(raiz)


@pytest.fixture
def ws(tmp_path) -> Workspace:
    return Workspace.materialize(
        WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT),
        run_id="patch-oracle", dest=tmp_path / "ws",
    )


# ------------------------------------------------------------------ contrato


class TestContratoDoTaskSpec:
    def test_sem_oraculo_nenhum_a_tarefa_e_recusada(self, tmp_path):
        raiz = tmp_path / "t"
        raiz.mkdir()
        (raiz / "task.json").write_text(json.dumps({
            "id": "x", "seed_repo": "tomlkit", "base_commit": "abc",
            "fail_to_pass": ["a::b"],
        }), encoding="utf-8")

        with pytest.raises(ValueError, match="hidden_tests.*test_patch"):
            load_task(raiz)

    def test_patch_ausente_falha_no_momento_de_aplicar(self, tmp_path, ws):
        raiz = tmp_path / "t"
        raiz.mkdir()
        (raiz / "task.json").write_text(json.dumps({
            "id": "x", "seed_repo": "tomlkit", "base_commit": BASE_COMMIT,
            "fail_to_pass": ["a::b"], "test_patch": "nao_existe.diff",
        }), encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="nao_existe"):
            inject_hidden_tests(ws.root, load_task(raiz))


# -------------------------------------------------------------- discriminação


@preparado
class TestOraculoPorPatch:
    def test_reprova_o_commit_base_intocado(self, ws, tarefa):
        """Sem a correção, o teste do upstream falha — é o que o torna oráculo."""
        resultado = evaluate_oracle(ws.root, tarefa, timeout_s=600)

        assert resultado.resolved is False
        assert resultado.f2p_passed == 0

    def test_aprova_a_correcao_do_upstream(self, ws, tarefa):
        subprocess.run(
            ["git", "checkout", FIX_COMMIT, "--", SOURCE_FILE],
            cwd=ws.root, check=True, capture_output=True,
        )

        resultado = evaluate_oracle(ws.root, tarefa, timeout_s=600)

        assert resultado.resolved is True
        assert resultado.f2p_passed == resultado.f2p_total
        assert resultado.p2p.green and resultado.regression.green

    def test_adulteracao_de_teste_e_desfeita_antes_de_medir(self, ws, tarefa):
        """
        O agente que apaga o teste não escapa do oráculo: os arquivos de teste
        voltam ao commit-base antes do patch entrar. A trapaça continua
        registrada — o detector roda antes desta etapa.
        """
        alvo = ws.resolve(TEST_FILE)
        alvo.write_text("def test_nada():\n    assert True\n", encoding="utf-8")

        subprocess.run(
            ["git", "checkout", FIX_COMMIT, "--", SOURCE_FILE],
            cwd=ws.root, check=True, capture_output=True,
        )
        resultado = evaluate_oracle(ws.root, tarefa, timeout_s=600)

        assert resultado.resolved is True, "o teste do upstream tinha de ter voltado"
        assert resultado.p2p.passed > 1000, "a suíte original foi restaurada inteira"

    def test_aplicar_devolve_os_arquivos_tocados(self, ws, tarefa):
        tocados = apply_test_patch(ws.root, tarefa)

        assert tocados == [TEST_FILE]
        assert "test_array_with_malformed_element_raises" in Path(ws.resolve(TEST_FILE)).read_text()

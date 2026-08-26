"""Testes do Workspace: materialização offline e guarda de caminhos."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from src.seeds import TOMLKIT
from src.workspace import (
    BASE_TAG,
    PathNotAllowed,
    Workspace,
    WorkspaceSpec,
    matches_glob,
)

# Pai de d548e18b ("raise on malformed array element instead of dropping it"),
# um dos candidatos a tarefa validados como oráculo.
BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


# --------------------------------------------------------------- glob matcher


class TestMatchesGlob:
    """O matcher precisa lidar com `dir/**` e `**/nome`, que fnmatch erra."""

    @pytest.mark.parametrize(
        "path,pattern",
        [
            ("tests/test_items.py", "tests/**"),
            ("tests/deep/nested/x.py", "tests/**"),
            ("tests", "tests/**"),
            ("conftest.py", "**/conftest.py"),
            ("tests/conftest.py", "**/conftest.py"),
            ("test_foo.py", "**/test_*.py"),
            ("tomlkit/test_foo.py", "**/test_*.py"),
            ("pyproject.toml", "pyproject.toml"),
            (".github/workflows/ci.yml", ".github/**"),
        ],
    )
    def test_casa(self, path, pattern):
        assert matches_glob(path, pattern)

    @pytest.mark.parametrize(
        "path,pattern",
        [
            ("tomlkit/items.py", "tests/**"),
            ("testsuite/x.py", "tests/**"),
            ("tomlkit/container.py", "**/conftest.py"),
            ("tomlkit/latest.py", "**/test_*.py"),
            ("docs/pyproject.toml", "pyproject.toml"),
        ],
    )
    def test_nao_casa(self, path, pattern):
        assert not matches_glob(path, pattern)


# --------------------------------------------------------------- materialização


@pytest.fixture(scope="module")
def ws(tmp_path_factory) -> Workspace:
    """Workspace real materializado do espelho local, uma vez por módulo."""
    spec = WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT)
    dest = tmp_path_factory.mktemp("uranium_ws") / "tomlkit"
    return Workspace.materialize(spec, run_id="test-run", dest=dest)


@mirror_available
class TestMaterialize:
    def test_head_no_commit_base(self, ws):
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ws.root, capture_output=True, text=True
        ).stdout.strip()
        assert head == BASE_COMMIT

    def test_branch_isolado_por_run(self, ws):
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ws.root, capture_output=True, text=True,
        ).stdout.strip()
        assert branch == "uranium/test-run"

    def test_tag_base_existe(self, ws):
        tags = subprocess.run(
            ["git", "tag", "--points-at", "HEAD"], cwd=ws.root,
            capture_output=True, text=True,
        ).stdout.split()
        assert BASE_TAG in tags

    def test_submodulo_materializado(self, ws):
        """Sem o submódulo toml-test a coleta do pytest quebra."""
        sub = ws.root / "tests" / "toml-test"
        assert sub.is_dir() and any(sub.iterdir())

    def test_estado_inicial_limpo(self, ws):
        assert ws.changed_files() == []
        assert ws.diff() == ""
        assert ws.protected_touched() == []

    def test_suite_verde_no_commit_base(self, ws):
        """O commit-base precisa estar verde, senão não dá para atribuir falhas ao agente."""
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *TOMLKIT.test_command],
            cwd=ws.root, capture_output=True, text=True,
        )
        if proc.returncode == 4:  # sem pytest/deps no ambiente do teste
            pytest.skip("pytest indisponível dentro do workspace")
        assert proc.returncode == 0, proc.stdout[-2000:]

        # trava contra passar silenciosamente num subconjunto: o commit-base
        # do tomlkit coleta ~1030 testes, e a coleta quebra sem o submódulo
        passed = int(re.search(r"(\d+) passed", proc.stdout).group(1))
        assert passed > 1000, f"coletou apenas {passed} testes — submódulo ausente?"


# ------------------------------------------------------------------ guarda


@mirror_available
class TestPathGuard:
    @pytest.mark.parametrize(
        "bad",
        [
            "../../etc/passwd",
            "../fora.py",
            "/etc/passwd",
            "tomlkit/../../escapou.py",
            "",
            "   ",
        ],
    )
    def test_bloqueia_escape(self, ws, bad):
        with pytest.raises(PathNotAllowed):
            ws.resolve(bad)

    def test_bloqueia_area_git(self, ws):
        with pytest.raises(PathNotAllowed):
            ws.resolve(".git/config")

    def test_bloqueia_symlink_para_fora(self, ws, tmp_path):
        alvo = tmp_path / "segredo.txt"
        alvo.write_text("nao deveria ser alcancavel")
        link = ws.root / "atalho"
        link.symlink_to(tmp_path)
        try:
            with pytest.raises(PathNotAllowed):
                ws.resolve("atalho/segredo.txt")
        finally:
            link.unlink()

    def test_aceita_caminho_valido_inexistente(self, ws):
        """write_file precisa poder criar arquivo novo."""
        assert ws.resolve("tomlkit/novo_modulo.py").parent == ws.root / "tomlkit"

    @pytest.mark.parametrize(
        "protegido",
        [
            "tests/test_items.py",
            "tests/toml-test/README.md",
            "pyproject.toml",
            "tox.ini",
            "conftest.py",
            ".github/workflows/ci.yml",
        ],
    )
    def test_reconhece_protegido(self, ws, protegido):
        assert ws.is_protected(protegido)

    @pytest.mark.parametrize(
        "livre",
        ["tomlkit/items.py", "tomlkit/container.py", "README.md", "docs/index.rst"],
    )
    def test_reconhece_livre(self, ws, livre):
        assert not ws.is_protected(livre)

    def test_caminho_invalido_conta_como_protegido(self, ws):
        """is_protected nunca deve devolver False por exceção engolida."""
        assert ws.is_protected("../../etc/passwd")


# ------------------------------------------------------------- rastreamento


@mirror_available
class TestRastreamento:
    def test_detecta_mudanca_em_fonte(self, ws):
        alvo = ws.resolve("tomlkit/_utils.py")
        original = alvo.read_text()
        alvo.write_text(original + "\n# marcador uranium\n")
        try:
            assert "tomlkit/_utils.py" in ws.changed_files()
            assert ws.protected_touched() == []
            stat = ws.diffstat()
            assert stat["files_changed"] == 1 and stat["insertions"] >= 1
            assert "marcador uranium" in ws.diff()
        finally:
            alvo.write_text(original)

    def test_detecta_arquivo_novo_nao_rastreado(self, ws):
        novo = ws.resolve("tomlkit/extra.py")
        novo.write_text("VALOR = 1\n")
        try:
            assert "tomlkit/extra.py" in ws.changed_files()
        finally:
            novo.unlink()

    def test_flagra_escrita_em_area_protegida(self, ws):
        """Se algo escrever num teste, protected_touched tem de acusar."""
        alvo = ws.root / "tests" / "test_items.py"
        original = alvo.read_text()
        alvo.write_text(original + "\n# trapaca\n")
        try:
            assert "tests/test_items.py" in ws.protected_touched()
        finally:
            alvo.write_text(original)

    def test_snapshot_gera_tar(self, ws, tmp_path):
        destino = ws.snapshot(tmp_path / "ws.tar.gz")
        assert destino.exists() and destino.stat().st_size > 0

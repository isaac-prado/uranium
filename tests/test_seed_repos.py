"""
Contrato dos repositórios-semente.

Um repo só serve ao experimento se, no HEAD do espelho local, a suíte
declarada roda inteira e passa: é o ponto de partida contra o qual toda
falha vai ser atribuída ao agente. Estes testes verificam isso de verdade,
materializando o workspace e rodando pytest — não é checagem de metadado.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from harness.venvs import SeedEnvMissing, python_for
from harness.venvs import venv_root as harness_venv_root
from src.seeds import (
    PEEWEE,
    SEED_REPOS,
    SQLITE_UTILS,
    TOMLKIT,
    SeedRepoError,
    SeedRepoSpec,
    get_seed_repo,
    venv_root,
)
from src.tools.exec import run_pytest
from src.workspace import Workspace, WorkspaceSpec

# Mínimo de testes que cada suíte precisa coletar. Trava contra "passou"
# obtido num subconjunto: no peewee a coleta padrão do pytest acha 5 de
# 1.634, e um verde desses seria pior que um vermelho.
PISO_DE_COLETA = {"tomlkit": 1000, "peewee": 1500, "sqlite-utils": 1400}


def _pronto(repo: SeedRepoSpec) -> bool:
    return repo.mirror_path.exists() and repo.has_venv


def preparado(repo: SeedRepoSpec):
    return pytest.mark.skipif(
        not _pronto(repo),
        reason=f"rode scripts/setup_mirror.py {repo.seed_repo_id}",
    )


# ------------------------------------------------------------------ metadados


class TestCatalogo:
    def test_os_tres_repos_estao_registrados(self):
        assert set(SEED_REPOS) == {"tomlkit", "peewee", "sqlite-utils"}

    def test_id_desconhecido_lista_as_opcoes(self):
        with pytest.raises(KeyError, match="peewee"):
            get_seed_repo("django")

    @pytest.mark.parametrize("repo", SEED_REPOS.values(), ids=lambda r: r.seed_repo_id)
    def test_declara_o_que_o_experimento_precisa(self, repo: SeedRepoSpec):
        assert repo.suite_targets, "sem suite_targets o agente vê uma suíte e o harness outra"
        assert repo.test_requirements, "sem dependências pinadas o ambiente não é reprodutível"
        assert repo.source_dir, "source_dir alimenta a medição de cobertura"
        for pacote in repo.test_requirements:
            assert "==" in pacote, f"dependência não pinada em {repo.seed_repo_id}: {pacote}"

    @pytest.mark.parametrize("repo", SEED_REPOS.values(), ids=lambda r: r.seed_repo_id)
    def test_testes_e_configuracao_sao_protegidos(self, repo: SeedRepoSpec):
        assert "tests/**" in repo.protected_globs
        assert "pyproject.toml" in repo.protected_globs

    def test_peewee_protege_o_proprio_runner_de_testes(self):
        """runtests.py é infraestrutura de teste: editar ali é trapaça."""
        assert "runtests.py" in PEEWEE.protected_globs


# -------------------------------------------------------------- interpretador


class TestInterpretadorPorRepo:
    def test_ambiente_ausente_falha_alto(self, monkeypatch, tmp_path):
        """
        Cair para sys.executable seria silencioso e contaminaria o resultado:
        a suíte do upstream enxergaria langchain, pydantic e o resto.
        """
        monkeypatch.setenv("URANIUM_VENV_DIR", str(tmp_path / "vazio"))

        assert TOMLKIT.has_venv is False
        with pytest.raises(SeedRepoError, match="setup_mirror"):
            _ = TOMLKIT.python_bin

    @pytest.mark.parametrize("repo", SEED_REPOS.values(), ids=lambda r: r.seed_repo_id)
    def test_convencao_do_harness_bate_com_a_do_src(self, repo: SeedRepoSpec):
        """
        O harness repete a convenção em vez de importar `src`, para poder
        rodar sozinho. Se as duas divergirem, o avaliador usa outro
        interpretador que o run — e ninguém percebe.
        """
        assert venv_root() == harness_venv_root()
        if not repo.has_venv:
            pytest.skip(f"ambiente ausente para {repo.seed_repo_id}")
        assert python_for(repo.seed_repo_id) == repo.python_bin

    def test_harness_tambem_falha_alto(self, monkeypatch, tmp_path):
        monkeypatch.setenv("URANIUM_VENV_DIR", str(tmp_path / "vazio"))
        with pytest.raises(SeedEnvMissing, match="setup_mirror"):
            python_for("tomlkit")

    @pytest.mark.parametrize("repo", SEED_REPOS.values(), ids=lambda r: r.seed_repo_id)
    def test_nao_e_o_interpretador_do_projeto(self, repo: SeedRepoSpec):
        if not repo.has_venv:
            pytest.skip(f"ambiente ausente para {repo.seed_repo_id}")
        assert repo.python_bin != sys.executable
        assert Path(repo.python_bin).exists()


# ------------------------------------------------------------ suíte de verdade


@pytest.mark.parametrize(
    "repo",
    [
        pytest.param(TOMLKIT, marks=preparado(TOMLKIT), id="tomlkit"),
        pytest.param(PEEWEE, marks=preparado(PEEWEE), id="peewee"),
        pytest.param(SQLITE_UTILS, marks=preparado(SQLITE_UTILS), id="sqlite-utils"),
    ],
)
class TestSuiteVerdeNoPontoDePartida:
    @pytest.fixture
    def ws(self, repo: SeedRepoSpec, tmp_path) -> Workspace:
        head = _head(repo)
        return Workspace.materialize(
            WorkspaceSpec(seed_repo=repo, base_commit=head),
            run_id=f"seed-{repo.seed_repo_id}", dest=tmp_path / repo.seed_repo_id,
        )

    def test_roda_inteira_e_passa(self, repo: SeedRepoSpec, ws: Workspace):
        report = run_pytest(ws, timeout_s=1800)

        assert report.exit_code == 0, report.stdout_tail[-2000:]
        assert report.failed == 0 and report.errors == 0
        assert report.passed >= PISO_DE_COLETA[repo.seed_repo_id], (
            f"coletou só {report.passed} testes — alvo de coleta errado?"
        )

    def test_o_comando_usa_o_interpretador_do_repo(self, repo: SeedRepoSpec, ws: Workspace):
        report = run_pytest(ws, ["-q"], timeout_s=1800)
        assert report.command.startswith(repo.python_bin)

    def test_estado_inicial_limpo(self, ws: Workspace):
        assert ws.changed_files() == []
        assert ws.protected_touched() == []


def _head(repo: SeedRepoSpec) -> str:
    import subprocess

    return subprocess.run(
        ["git", "--git-dir", str(repo.mirror_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


# ------------------------------------------------------------- alvos da suíte


@preparado(PEEWEE)
def test_peewee_sem_alvo_declarado_coletaria_quase_nada(tmp_path):
    """
    Justifica `suite_targets`: os módulos de teste do peewee se chamam
    models.py, fields.py, sql.py — nenhum casa com o padrão `test_*.py`.
    Sem o alvo explícito, "a suíte passou" seria verdade sobre 5 testes.
    """
    ws = Workspace.materialize(
        WorkspaceSpec(seed_repo=PEEWEE, base_commit=_head(PEEWEE)),
        run_id="peewee-coleta", dest=tmp_path / "peewee",
    )

    declarado = run_pytest(ws, timeout_s=1800)
    pelado = run_pytest(ws, ["tests/"], timeout_s=600)

    assert declarado.passed > 1500
    assert pelado.passed < 50
    assert re.search(r"tests/__init__\.py", declarado.command)

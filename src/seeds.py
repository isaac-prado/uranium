"""Especificação dos repositórios-semente usados pelo benchmark E1."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SeedRepoError(RuntimeError):
    """Repositório-semente mal configurado ou sem ambiente preparado."""


def mirror_root() -> Path:
    """Diretório dos espelhos bare locais (sem rede em tempo de run)."""
    return Path(os.getenv("URANIUM_MIRROR_DIR", PROJECT_ROOT / ".uranium" / "mirrors"))


def workspace_root() -> Path:
    """Diretório onde os workspaces por run são materializados."""
    return Path(os.getenv("URANIUM_WORKSPACE_DIR", PROJECT_ROOT / ".uranium" / "workspaces"))


def venv_root() -> Path:
    """
    Diretório dos ambientes virtuais, um por repositório-semente.

    Ficam FORA da árvore do repositório clonado de propósito: venv dentro do
    workspace entra como arquivo não rastreado e some no primeiro `git stash`,
    o que já produziu resultado falso uma vez.
    """
    return Path(os.getenv("URANIUM_VENV_DIR", PROJECT_ROOT / ".uranium" / "venvs"))


# Caminhos que o agente nunca pode sobrescrever. Tocar em qualquer um destes
# é sinal de trapaça (regras C1/C3/C5 do detector do harness).
DEFAULT_PROTECTED_GLOBS: tuple[str, ...] = (
    "tests/**",
    "test/**",
    "**/test_*.py",
    "**/*_test.py",
    "**/conftest.py",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "pytest.ini",
    "noxfile.py",
    ".gitmodules",
    ".github/**",
    "poetry.lock",
)


@dataclass(frozen=True)
class SeedRepoSpec:
    """
    Um repositório-semente e como materializá-lo offline.

    "Semente" aqui é o repositório de partida do experimento, não a
    semente aleatória do LLM (essa é `LLMConfig.seed`). Os identificadores
    carregam `seed_repo` justamente para os dois nunca se confundirem.
    """

    seed_repo_id: str
    upstream_url: str
    mirror_name: str
    source_dir: str
    test_command: tuple[str, ...]
    # Alvos que o pytest recebe quando ninguém pede node id específico.
    # Precisa casar com o `pass_to_pass` das tarefas deste repo: se o agente
    # enxergar uma suíte e o harness medir outra, a comparação perde o chão.
    suite_targets: tuple[str, ...] = ("tests/",)
    # Dependências de teste, pinadas. Instaladas no venv do repo pelo
    # scripts/setup_mirror.py — o único passo que toca a rede.
    test_requirements: tuple[str, ...] = ()
    # caminho do submódulo -> nome do espelho bare correspondente
    submodules: tuple[tuple[str, str], ...] = ()
    protected_globs: tuple[str, ...] = field(default=DEFAULT_PROTECTED_GLOBS)

    @property
    def mirror_path(self) -> Path:
        return mirror_root() / self.mirror_name

    @property
    def venv_path(self) -> Path:
        return venv_root() / self.seed_repo_id

    @property
    def has_venv(self) -> bool:
        return (self.venv_path / "bin" / "python").exists()

    @property
    def python_bin(self) -> str:
        """
        Interpretador que roda a suíte deste repo.

        Falha alto em vez de cair para `sys.executable`: o venv do projeto
        carrega langchain, pydantic e companhia, e rodar a suíte do
        repo-semente lá dentro daria ao agente dependências que o upstream
        não tem — corretude comprada de graça, sem ninguém perceber.
        """
        if not self.has_venv:
            raise SeedRepoError(
                f"Ambiente ausente para {self.seed_repo_id!r} em {self.venv_path}. "
                f"Rode: uv run python scripts/setup_mirror.py {self.seed_repo_id}"
            )
        return str(self.venv_path / "bin" / "python")


TOMLKIT = SeedRepoSpec(
    seed_repo_id="tomlkit",
    upstream_url="https://github.com/python-poetry/tomlkit.git",
    mirror_name="tomlkit.git",
    source_dir="tomlkit",
    test_command=("-q", "-p", "no:cacheprovider", "-o", "addopts="),
    suite_targets=("tests/",),
    test_requirements=("pytest==9.0.3", "pyyaml==6.0.3"),
    submodules=(("tests/toml-test", "toml-test.git"),),
)

# A suíte do peewee não é coletável pelo padrão do pytest: os módulos de
# teste se chamam models.py, fields.py, sql.py — nenhum casa com `test_*.py`.
# Até aqui (mined-v1) o alvo era `tests/__init__.py`, que reunia tudo por
# `from .x import *`, truque que fazia as classes de teste aparecerem no
# namespace do próprio arquivo e o pytest as via como se fossem dele.
#
# O commit fd04f2af ("Test cleanup", upstream, 2026-09-03) trocou isso pelo
# protocolo `load_tests` do unittest: `tests/__init__.py` agora só importa
# cada submódulo (`from . import x`, sem star-import) e expõe
# `load_tests(loader, tests, pattern)`. unittest.discover honra esse
# protocolo (1826 testes, verde); pytest NÃO — é documentado que pytest não
# suporta `load_tests` — então `pytest tests/__init__.py` sozinho não
# encontra teste nenhum (exit code 5), o que quebrou
# `tests/test_seed_repos.py::test_roda_inteira_e_passa[peewee]`.
#
# Correção: liste aqui, em arquivos explícitos, exatamente os módulos que
# `tests/__init__.py` importa incondicionalmente (a lista `MODULES` de lá
# menos os que só entram com dependência opcional ausente — apsw, cysqlite,
# flask, fts, postgres, sqlcipher, `pwasyncio`/`pydantic`, nenhuma instalada
# neste venv). Caminho explícito faz o pytest coletar o arquivo não importa
# o nome — o padrão `test_*.py` só vale para varredura de diretório.
#
# A ORDEM importa: `tests/model_sql.py::TestModelSQL::test_delete_recursive`
# vaza estado de `tests/models.py` (uma tabela/id que ele pressupõe já
# criada) e falha se `model_sql` rodar antes de `models` — o que a ordem
# alfabética de diretório faz ("model_sql.py" < "models.py"), mas a ordem
# de `MODULES` no upstream não. Reproduzindo a ordem de `MODULES` a suíte
# fica 1438 passed, 173 skipped, 0 failed em ~4,3s (medido nesta máquina,
# HEAD 9d495208 do espelho — ver docs/tcc/07-e3-1-mineracao.md).
#
# Ressalva de cobertura histórica: dois destes arquivos são recentes
# (`with_related_tests.py` desde 2026-06-14, `schema_diff.py` desde
# 2026-08-02); os demais existem desde 2017-03 a 2019-11. Minerar um
# commit-base anterior à criação de um desses arquivos faz o passo 0 (suíte
# verde no pai) falhar com "arquivo não encontrado", e `avaliar()` rejeita
# o candidato como "commit-base já vermelho" — não é falso positivo de
# correção, é limitação de que `suite_targets` é uma lista fixa e não pode
# variar por commit; a consequência é perder candidatos de base anterior a
# 2019-11, não aceitar um errado. Ver contagem de rejeições por motivo em
# `mined-v2/RELATORIO.md`.
PEEWEE = SeedRepoSpec(
    seed_repo_id="peewee",
    upstream_url="https://github.com/coleifer/peewee.git",
    mirror_name="peewee.git",
    source_dir="peewee,playhouse",
    test_command=("-q", "-p", "no:cacheprovider", "-o", "addopts="),
    suite_targets=(
        "tests/db_tests.py", "tests/fields.py", "tests/manytomany.py",
        "tests/models.py", "tests/model_sql.py", "tests/prefetch_tests.py",
        "tests/results.py", "tests/schema.py", "tests/sql.py",
        "tests/transactions.py", "tests/with_related_tests.py",
        "tests/cockroachdb.py", "tests/dataset.py", "tests/db_url.py",
        "tests/extra_fields.py", "tests/hybrid.py", "tests/kv.py",
        "tests/migrations.py", "tests/mysql_ext.py", "tests/pool.py",
        "tests/schema_diff.py", "tests/pwiz_integration.py",
        "tests/reflection.py", "tests/shortcuts.py", "tests/signals.py",
        "tests/sqliteq.py", "tests/sqlite_udf.py", "tests/test_utils.py",
    ),
    test_requirements=("pytest==9.1.1",),
    protected_globs=DEFAULT_PROTECTED_GLOBS + ("runtests.py",),
)

SQLITE_UTILS = SeedRepoSpec(
    seed_repo_id="sqlite-utils",
    upstream_url="https://github.com/simonw/sqlite-utils.git",
    mirror_name="sqlite-utils.git",
    source_dir="sqlite_utils",
    test_command=("-q", "-p", "no:cacheprovider", "-o", "addopts="),
    suite_targets=("tests/",),
    test_requirements=(
        # runtime, do [project.dependencies]
        "click==8.5.0",
        "click-default-group==1.2.4",
        "pluggy==1.6.0",
        "python-dateutil==2.9.0.post0",
        "sqlite-fts4==1.0.3",
        "tabulate==0.10.0",
        # runtime, usada mas NÃO declarada em [project.dependencies] do
        # sqlite-utils — desde agosto de 2026 `sqlite_utils/db.py` faz
        # `from typing_extensions import Self` incondicionalmente; sem
        # isso no venv, TODO commit-base a partir dali dá
        # `ModuleNotFoundError` na coleta (0 passed, 0 failed, <1s) e
        # `avaliar` recusava como "commit-base já vermelho (0 falhas)" —
        # não era base vermelha, era ambiente incompleto (E3.3, aviso do
        # coordenador; achado e número em docs/tcc/07-e3-1-mineracao.md).
        "typing-extensions==4.16.0",
        # teste, do [dependency-groups].dev
        "pytest==9.1.1",
        "hypothesis==6.165.10",
    ),
)

# Repositórios novos do E3 item 1 (docs/tcc/tasks/EXIGENCIAS.md — "buscar
# repositórios open-source famosos com histórico organizado além dos três
# atuais"). Levantamento em docs/tcc/07-e3-1-mineracao.md: 6 candidatos
# examinados (click, jinja, marshmallow, attrs, more-itertools/boltons/
# tqdm/babel como reserva, pydantic e requests por eliminação rápida),
# 2 aceitos. click/jinja/marshmallow/attrs têm layout `src/` (pacote em
# `src/<nome>/`, não solto na raiz) — o harness materializa workspace só
# com `git clone` e roda pytest sem instalar nada (nenhum `pip install -e`
# em `Workspace.materialize`/`run_pytest`, `src/workspace.py`,
# `src/tools/exec.py`); sem instalação nem `PYTHONPATH`, `import click`
# falha (`ModuleNotFoundError`, testado à mão). Os quatro tinham a melhor
# densidade de candidato grande/média (jinja: 24 grande; marshmallow: 9
# grande, 17 média) — registrado aqui para quem decidir se vale mudar essa
# convenção do harness (fora do escopo desta tarefa: mudaria
# `src/workspace.py`/`src/tools/exec.py`, que não são meus).
PYGMENTS = SeedRepoSpec(
    seed_repo_id="pygments",
    upstream_url="https://github.com/pygments/pygments.git",
    mirror_name="pygments.git",
    source_dir="pygments",
    test_command=("-q", "-p", "no:cacheprovider", "-o", "addopts="),
    suite_targets=("tests/",),
    test_requirements=(
        "pytest==9.1.1",
        # tests/contrast/test_contrasts.py mede contraste de cor dos estilos
        "wcag-contrast-ratio==0.9",
    ),
)

TQDM = SeedRepoSpec(
    seed_repo_id="tqdm",
    upstream_url="https://github.com/tqdm/tqdm.git",
    mirror_name="tqdm.git",
    source_dir="tqdm",
    test_command=("-q", "-p", "no:cacheprovider", "-o", "addopts="),
    suite_targets=("tests/",),
    test_requirements=(
        "pytest==9.1.1",
        # tests/tests_asyncio.py e a suíte de concorrência
        "pytest-asyncio==1.4.0",
        # tqdm declara `timeout = 30` em [tool.pytest.ini_options]; sem o
        # plugin, pytest recusa a opção de config (INTERNALERROR)
        "pytest-timeout==2.4.0",
    ),
)

SEED_REPOS: dict[str, SeedRepoSpec] = {
    repo.seed_repo_id: repo
    for repo in (TOMLKIT, PEEWEE, SQLITE_UTILS, PYGMENTS, TQDM)
}


def get_seed_repo(seed_repo_id: str) -> SeedRepoSpec:
    """Resolve um repositório-semente por id, com erro explícito se desconhecido."""
    try:
        return SEED_REPOS[seed_repo_id]
    except KeyError:
        raise KeyError(
            f"Repositório-semente desconhecido: {seed_repo_id!r}. "
            f"Disponíveis: {sorted(SEED_REPOS)}"
        ) from None

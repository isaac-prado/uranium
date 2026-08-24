"""
Especificação de uma tarefa do experimento.

JSON e não YAML de propósito: uma dependência a menos no avaliador, que
precisa rodar isolado.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_PROTECTED_GLOBS: tuple[str, ...] = (
    "tests/**", "test/**", "**/test_*.py", "**/*_test.py", "**/conftest.py",
    "pyproject.toml", "setup.py", "setup.cfg", "tox.ini", "pytest.ini",
    "noxfile.py", ".gitmodules", ".github/**", "poetry.lock",
)


@dataclass(frozen=True)
class TaskSpec:
    """Uma tarefa minerada do histórico do repositório-semente."""

    task_id: str
    seed_repo_id: str
    base_commit: str
    source_dir: str
    hidden_tests: tuple[str, ...]
    fail_to_pass: tuple[str, ...]
    pass_to_pass: tuple[str, ...]
    root: Path
    fix_commit: str = ""
    issue_url: str = ""
    protected_globs: tuple[str, ...] = field(default=DEFAULT_PROTECTED_GLOBS)
    reference_patches: tuple[str, ...] = ()
    cheat_patches: tuple[str, ...] = ()

    @property
    def statement(self) -> str:
        arquivo = self.root / "statement.md"
        return arquivo.read_text(encoding="utf-8") if arquivo.exists() else ""

    def hidden_test_paths(self) -> list[Path]:
        return [self.root / rel for rel in self.hidden_tests]

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "seed_repo_id": self.seed_repo_id,
            "base_commit": self.base_commit,
            "fix_commit": self.fix_commit,
            "issue_url": self.issue_url,
            "fail_to_pass": list(self.fail_to_pass),
            "pass_to_pass": list(self.pass_to_pass),
        }


def load_task(path: str | Path) -> TaskSpec:
    """Carrega `tasks/<id>/task.json`, aceitando também o diretório."""
    caminho = Path(path)
    if caminho.is_dir():
        caminho = caminho / "task.json"
    if not caminho.exists():
        raise FileNotFoundError(f"especificação de tarefa não encontrada: {caminho}")

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    obrigatorios = ("id", "seed_repo", "base_commit", "hidden_tests", "fail_to_pass")
    faltando = [c for c in obrigatorios if c not in dados]
    if faltando:
        raise ValueError(f"{caminho}: campos obrigatórios ausentes: {faltando}")

    return TaskSpec(
        task_id=dados["id"],
        seed_repo_id=dados["seed_repo"],
        base_commit=dados["base_commit"],
        source_dir=dados.get("source_dir", ""),
        hidden_tests=tuple(dados["hidden_tests"]),
        fail_to_pass=tuple(dados["fail_to_pass"]),
        pass_to_pass=tuple(dados.get("pass_to_pass", ["tests/"])),
        root=caminho.parent,
        fix_commit=dados.get("fix_commit", ""),
        issue_url=dados.get("issue_url", ""),
        protected_globs=tuple(dados.get("protected_globs", DEFAULT_PROTECTED_GLOBS)),
        reference_patches=tuple(dados.get("reference_patches", ())),
        cheat_patches=tuple(dados.get("cheat_patches", ())),
    )

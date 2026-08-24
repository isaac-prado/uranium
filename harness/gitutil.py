"""Utilitários de git para o avaliador. Reimplementados: não importam src/."""

from __future__ import annotations

import subprocess
from pathlib import Path

BASE_TAG = "uranium-base"


class GitError(RuntimeError):
    """Comando git falhou dentro do workspace avaliado."""


def git(*args: str, cwd: Path, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def changed_files(repo: Path, ref: str = BASE_TAG) -> list[str]:
    """Arquivos alterados pelo agente em relação ao commit-base."""
    rastreados = git("diff", "--name-only", ref, cwd=repo).split()
    novos = git("ls-files", "--others", "--exclude-standard", cwd=repo).split()
    return sorted(set(rastreados) | set(novos))


def diff(repo: Path, ref: str = BASE_TAG) -> str:
    return git("diff", ref, cwd=repo)


def diffstat(repo: Path, ref: str = BASE_TAG) -> dict[str, int]:
    saida = git("diff", "--numstat", ref, cwd=repo)
    arquivos = insercoes = remocoes = 0
    for linha in saida.splitlines():
        partes = linha.split("\t")
        if len(partes) != 3:
            continue
        arquivos += 1
        insercoes += int(partes[0]) if partes[0].isdigit() else 0
        remocoes += int(partes[1]) if partes[1].isdigit() else 0
    return {"files_changed": arquivos, "insertions": insercoes, "deletions": remocoes}


def file_at(repo: Path, ref: str, rel_path: str) -> str | None:
    """Conteúdo de um arquivo numa revisão. None se não existia."""
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"], cwd=repo, capture_output=True, text=True
    )
    return proc.stdout if proc.returncode == 0 else None


def base_commit(repo: Path) -> str:
    return git("rev-parse", BASE_TAG, cwd=repo).strip()


def stash_agent_changes(repo: Path) -> None:
    """Volta o worktree ao commit-base, preservando arquivos não rastreados."""
    git("checkout", "--force", BASE_TAG, "--", ".", cwd=repo)

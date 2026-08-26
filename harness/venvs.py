"""
Resolve o interpretador que roda a suíte de cada repositório-semente.

O harness não importa `src/` de propósito — precisa poder rodar sozinho,
contra um diretório de run entregue por terceiro. Então a convenção de
caminho dos ambientes é repetida aqui em vez de compartilhada: são cinco
linhas duplicadas em troca de independência de verdade.

A convenção é a mesma de `src/seeds.py`:

    $URANIUM_VENV_DIR/<seed_repo_id>/bin/python
    (padrão: <raiz do projeto>/.uranium/venvs/<seed_repo_id>/bin/python)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SeedEnvMissing(RuntimeError):
    """Não há ambiente de teste preparado para o repositório-semente."""


def venv_root() -> Path:
    return Path(os.getenv("URANIUM_VENV_DIR", PROJECT_ROOT / ".uranium" / "venvs"))


def python_for(seed_repo_id: str, *, strict: bool = True) -> str:
    """
    Interpretador do repo-semente.

    Com `strict`, falha alto em vez de cair para `sys.executable`: avaliar a
    suíte do upstream dentro do venv do projeto daria a ela as nossas
    dependências, e um `resolved: true` obtido assim não significaria nada.
    """
    caminho = venv_root() / seed_repo_id / "bin" / "python"
    if caminho.exists():
        return str(caminho)
    if strict:
        raise SeedEnvMissing(
            f"Ambiente de teste ausente para {seed_repo_id!r} em {caminho.parent.parent}. "
            f"Rode: uv run python scripts/setup_mirror.py {seed_repo_id}"
        )
    return sys.executable

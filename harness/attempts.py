"""
Qual tentativa de uma célula vale como observação.

Regra única, usada pela coleta (para decidir o que falta rodar) e pela
análise (para decidir o que entra no denominador). Estava escrita duas vezes;
uma mudança numa cópia só faria coleta e análise discordarem sobre o mesmo
disco.

Vale a primeira tentativa não perdida. Perdida é a que tem `lost: true` no
`summary.json` (infraestrutura ou interrupção, gravado pelo runner) ou que
nem chegou a gravar o resumo (processo morto antes do `finally`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def read_json(caminho: Path) -> dict[str, Any] | None:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@dataclass(frozen=True)
class AttemptSelection:
    """O que as tentativas gravadas de uma célula dizem."""

    attempts: int
    lost: int
    run_dir: Path | None = None
    summary: dict[str, Any] | None = None


def select_attempt(rep_dir: Path) -> AttemptSelection:
    """Primeira tentativa não perdida em `rep_dir/attemptNN/`, se houver."""
    tentativas = sorted(rep_dir.glob("attempt*"))
    for perdidas, tentativa in enumerate(tentativas):
        resumo = read_json(tentativa / "summary.json")
        if resumo is not None and not resumo.get("lost"):
            return AttemptSelection(len(tentativas), perdidas, tentativa, resumo)
    return AttemptSelection(len(tentativas), len(tentativas))

"""
Métricas de qualidade: manutenibilidade, complexidade e cobertura.

Sempre como DELTA contra o commit-base. O valor absoluto é dominado pelo
repositório-semente, não pelo trabalho do agente: dizer que o índice de
manutenibilidade ficou em 71 não informa nada sobre o agente; dizer que ele
caiu 0,4 informa.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.gitutil import BASE_TAG, file_at


@dataclass
class QualityReport:
    mi_before: float | None
    mi_after: float | None
    cc_before: float | None
    cc_after: float | None
    files_analyzed: int
    error: str | None = None

    @property
    def mi_delta(self) -> float | None:
        if self.mi_before is None or self.mi_after is None:
            return None
        return round(self.mi_after - self.mi_before, 3)

    @property
    def cc_delta(self) -> float | None:
        if self.cc_before is None or self.cc_after is None:
            return None
        return round(self.cc_after - self.cc_before, 3)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mi_before": self.mi_before, "mi_after": self.mi_after,
            "mi_delta": self.mi_delta,
            "cc_mean_before": self.cc_before, "cc_mean_after": self.cc_after,
            "cc_mean_delta": self.cc_delta,
            "files_analyzed": self.files_analyzed,
            "error": self.error,
        }


def _mi(codigo: str) -> float | None:
    """Índice de manutenibilidade de um trecho de código."""
    try:
        from radon.metrics import mi_visit

        return round(float(mi_visit(codigo, multi=True)), 3)
    except Exception:
        return None


def _cc_medio(codigo: str) -> float | None:
    """Complexidade ciclomática média dos blocos do arquivo."""
    try:
        from radon.complexity import cc_visit

        blocos = cc_visit(codigo)
        if not blocos:
            return 0.0
        return round(sum(b.complexity for b in blocos) / len(blocos), 3)
    except Exception:
        return None


def _media(valores: list[float]) -> float | None:
    limpos = [v for v in valores if v is not None]
    return round(sum(limpos) / len(limpos), 3) if limpos else None


def measure(repo: Path, changed_py: list[str]) -> QualityReport:
    """
    Compara qualidade antes/depois, restrita aos arquivos que o agente tocou.

    Medir o repositório inteiro diluiria o efeito num mar de código intocado.
    """
    if not changed_py:
        return QualityReport(None, None, None, None, 0, error=None)

    mi_antes, mi_depois, cc_antes, cc_depois = [], [], [], []
    analisados = 0

    for rel in changed_py:
        antes = file_at(repo, BASE_TAG, rel)
        alvo = repo / rel
        depois = alvo.read_text(encoding="utf-8", errors="replace") if alvo.is_file() else None
        if antes is None or depois is None:
            continue  # arquivo criado ou removido: não há par para comparar
        analisados += 1
        mi_antes.append(_mi(antes))
        mi_depois.append(_mi(depois))
        cc_antes.append(_cc_medio(antes))
        cc_depois.append(_cc_medio(depois))

    return QualityReport(
        mi_before=_media(mi_antes), mi_after=_media(mi_depois),
        cc_before=_media(cc_antes), cc_after=_media(cc_depois),
        files_analyzed=analisados,
    )


def coverage_percent(repo: Path, source_dir: str, *, timeout_s: int = 900) -> float | None:
    """
    Cobertura de linha+ramo da suíte sobre o código de produção.

    Devolve None em vez de zero quando a medição falha: zero seria
    indistinguível de "nenhuma linha coberta", que é uma afirmação diferente.
    """
    if not source_dir:
        return None
    try:
        subprocess.run(
            [sys.executable, "-m", "coverage", "run", "--branch",
             f"--source={source_dir}", "-m", "pytest", "-q", "-p", "no:cacheprovider",
             "-o", "addopts="],
            cwd=repo, capture_output=True, text=True, timeout=timeout_s,
        )
        saida = subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", "-"],
            cwd=repo, capture_output=True, text=True, timeout=120,
        )
        if saida.returncode != 0:
            return None
        dados = json.loads(saida.stdout)
        return round(float(dados["totals"]["percent_covered"]), 3)
    except Exception:
        return None
    finally:
        for lixo in (".coverage", "coverage.json"):
            (repo / lixo).unlink(missing_ok=True)

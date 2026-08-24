"""
Custo e processo, agregados da telemetria.

Reimplementação independente da agregação de `src/telemetry.py`. Se o
avaliador reusasse o somatório do próprio pipeline, um erro de contagem
passaria despercebido nos dois lados.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_events(path: str | Path) -> list[dict[str, Any]]:
    """Lê o JSONL, ignorando linhas em branco."""
    caminho = Path(path)
    if not caminho.exists():
        return []
    return [
        json.loads(linha)
        for linha in caminho.read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]


def aggregate_cost(events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tokens_prompt": sum(e.get("tokens_prompt", 0) for e in events),
        "tokens_completion": sum(e.get("tokens_completion", 0) for e in events),
        "tokens_reasoning": sum(e.get("tokens_reasoning", 0) for e in events),
        "tokens_total": sum(e.get("tokens_total", 0) for e in events),
        "cost_usd": round(sum(float(e.get("cost_usd", 0.0)) for e in events), 8),
        "llm_calls": sum(1 for e in events if e.get("event_type") == "llm_call"),
        "tool_calls": sum(1 for e in events if e.get("event_type") == "tool_call"),
        "wall_seconds": round(
            max((e.get("elapsed_ms", 0) for e in events), default=0) / 1000, 3
        ),
    }


def self_recoveries(events: list[dict[str, Any]]) -> int:
    """Transições falha→verde na execução de testes, sem input externo."""
    recuperacoes = 0
    falhou = False
    for evento in events:
        if evento.get("event_type") != "test_run":
            continue
        verde = (evento.get("payload") or {}).get("green", False)
        if verde and falhou:
            recuperacoes += 1
            falhou = False
        elif not verde:
            falhou = True
    return recuperacoes


def aggregate_process(events: list[dict[str, Any]]) -> dict[str, Any]:
    finais = [e for e in events if e.get("event_type") == "run_end"]
    return {
        "turns": max((e.get("turn") or 0 for e in events), default=0),
        "test_runs": sum(1 for e in events if e.get("event_type") == "test_run"),
        "tool_denials": sum(1 for e in events if e.get("tool_denied")),
        "errors": sum(1 for e in events if e.get("event_type") == "error"),
        "circuit_breaks": sum(1 for e in events if e.get("event_type") == "circuit_break"),
        "self_recoveries": self_recoveries(events),
        "stop_reason": (finais[-1].get("payload") or {}).get("stop_reason") if finais else None,
    }


def providers_served(events: list[dict[str, Any]]) -> list[str]:
    """Provedores que atenderam. Mais de um significa que o pino falhou."""
    return sorted({e["provider_served"] for e in events if e.get("provider_served")})

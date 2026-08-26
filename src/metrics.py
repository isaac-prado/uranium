"""
Métricas de processo extraídas da telemetria.

O Índice de Autonomia e a taxonomia de intervenção L0–L4, previstos no
desenho original, foram removidos: com os dois braços rodando
sem qualquer intervenção humana, o índice daria o valor máximo para ambos
e não discriminaria nada. Reportá-lo como resultado comparativo seria
circular.

O que discrimina topologias em dois braços autônomos é o processo: quantos
turnos foram gastos, quantas vezes a suíte foi executada e — principalmente
— quantas vezes o sistema se recuperou sozinho de uma falha.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def self_recoveries(events: Iterable[dict[str, Any]]) -> int:
    """
    Auto-recuperações: transições falha→sucesso na execução de testes.

    Como não há input externo entre uma execução e outra, cada transição
    dessas é o sistema corrigindo o próprio erro. É a medida de autonomia
    que de fato varia entre as topologias.
    """
    recoveries = 0
    falhou = False
    for event in events:
        if event.get("event_type") != "test_run":
            continue
        verde = (event.get("payload") or {}).get("green", False)
        if verde and falhou:
            recoveries += 1
            falhou = False
        elif not verde:
            falhou = True
    return recoveries


def process_metrics(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Bloco `process` do resultado do harness."""
    events = list(events)
    return {
        "turns": max((e.get("turn") or 0 for e in events), default=0),
        "llm_calls": sum(1 for e in events if e.get("event_type") == "llm_call"),
        "tool_calls": sum(1 for e in events if e.get("event_type") == "tool_call"),
        "tool_denials": sum(1 for e in events if e.get("tool_denied")),
        "test_runs": sum(1 for e in events if e.get("event_type") == "test_run"),
        "self_recoveries": self_recoveries(events),
    }

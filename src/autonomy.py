"""
Taxonomia de intervenção L0–L4 e Índice de Autonomia.

Aviso metodológico: nos braços A2 e B deste estudo, ambos headless, nenhum
evento acima de L0 pode ocorrer por construção — o Índice de Autonomia é
constante 1,0 nos dois. Ele NÃO deve ser reportado como resultado
comparativo, sob pena de tautologia.

O que ele serve para fazer: (a) ser um invariante verificável — "zero
eventos acima de L0 em N runs" é uma afirmação auditável sobre o protocolo;
(b) deixar o instrumento pronto caso um trabalho futuro inclua um braço com
humano no loop.

O discriminante real de autonomia entre as topologias são as métricas de
processo — turnos até verde, execuções de teste e auto-recuperações — que
variam de fato.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Any


class InterventionLevel(StrEnum):
    """Grau de intervenção humana num ponto de decisão do pipeline."""

    L0 = "L0"  # nenhuma intervenção: o sistema decide e age sozinho
    L1 = "L1"  # humano fornece informação (responde uma clarificação)
    L2 = "L2"  # humano aprova ou rejeita um artefato proposto
    L3 = "L3"  # humano edita o artefato produzido
    L4 = "L4"  # humano assume e resolve a tarefa


WEIGHTS: dict[InterventionLevel, float] = {
    InterventionLevel.L0: 0.00,
    InterventionLevel.L1: 0.25,
    InterventionLevel.L2: 0.50,
    InterventionLevel.L3: 0.75,
    InterventionLevel.L4: 1.00,
}

# Eventos que constituem um ponto de decisão — o denominador do índice.
DECISION_EVENT_TYPES = frozenset({"llm_call", "tool_call", "test_run", "route"})


def count_levels(events: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Conta eventos por nível de intervenção, com todos os níveis presentes."""
    counts = {level.value: 0 for level in InterventionLevel}
    for event in events:
        level = event.get("intervention_level")
        if level in counts:
            counts[level] += 1
    return counts


def autonomy_index(events: Iterable[dict[str, Any]]) -> float:
    """
    Índice de Autonomia em [0, 1]: 1,0 = totalmente autônomo.

    IA = 1 − (Σ peso(nível) · n) / n_pontos_de_decisão

    Sem pontos de decisão o índice é indefinido; devolvemos 1,0 e o número
    de pontos vai no resultado para que a degenerescência fique visível.
    """
    events = list(events)
    decisions = [e for e in events if e.get("event_type") in DECISION_EVENT_TYPES]
    if not decisions:
        return 1.0

    penalty = 0.0
    for event in decisions:
        try:
            level = InterventionLevel(event.get("intervention_level", "L0"))
        except ValueError:
            level = InterventionLevel.L0
        penalty += WEIGHTS[level]

    return round(1.0 - penalty / len(decisions), 6)


def self_recoveries(events: Iterable[dict[str, Any]]) -> int:
    """
    Auto-recuperações: transições falha→sucesso na execução de testes sem
    input externo entre elas.

    É este número, e não o Índice de Autonomia, que discrimina topologias
    em dois braços headless.
    """
    runs = [e for e in events if e.get("event_type") == "test_run"]
    recoveries = 0
    falhou = False
    for event in runs:
        verde = (event.get("payload") or {}).get("green", False)
        if falhou and verde:
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
        "autonomy_index": autonomy_index(events),
        "intervention_counts": count_levels(events),
    }

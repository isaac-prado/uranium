"""
Circuit breaker do run: teto de tokens, de tempo de parede e de turnos.

Idêntico nos dois braços — se um deles pudesse gastar mais que o outro, a
comparação de custo perderia o sentido. Os limites vão para o manifesto do
run e são checados por `tests/test_arm_parity.py`.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RunBudget:
    """Limites de um run. Iguais nos dois braços."""

    max_tokens: int = 400_000
    max_wall_seconds: int = 1800
    max_turns: int = 40

    @classmethod
    def from_env(cls, **overrides: Any) -> "RunBudget":
        base = cls(
            max_tokens=int(os.getenv("RUN_MAX_TOKENS", "400000")),
            max_wall_seconds=int(os.getenv("RUN_MAX_WALL_SECONDS", "1800")),
            max_turns=int(os.getenv("RUN_MAX_TURNS", "40")),
        )
        return cls(**{**asdict(base), **overrides})

    def as_manifest(self) -> dict[str, Any]:
        return asdict(self)


class BudgetTracker:
    """
    Acompanha o consumo e diz quando parar.

    Consulta os totais da telemetria em vez de manter contagem própria: uma
    única fonte de verdade evita divergência entre o que foi gasto e o que
    foi reportado no TCC.
    """

    def __init__(self, budget: RunBudget, totals: Any) -> None:
        self.budget = budget
        self._totals = totals
        self._start = time.perf_counter()
        self.turn = 0

    def next_turn(self) -> int:
        self.turn += 1
        return self.turn

    @property
    def elapsed_s(self) -> float:
        return time.perf_counter() - self._start

    def exceeded(self) -> str | None:
        """Motivo do estouro, ou None se ainda há orçamento."""
        if self._totals.tokens_total >= self.budget.max_tokens:
            return f"max_tokens ({self._totals.tokens_total} >= {self.budget.max_tokens})"
        if self.elapsed_s >= self.budget.max_wall_seconds:
            return f"max_wall_seconds ({self.elapsed_s:.0f}s >= {self.budget.max_wall_seconds}s)"
        if self.turn >= self.budget.max_turns:
            return f"max_turns ({self.turn} >= {self.budget.max_turns})"
        return None

    @property
    def exhausted(self) -> bool:
        return self.exceeded() is not None

    def remaining(self) -> dict[str, Any]:
        return {
            "tokens": max(0, self.budget.max_tokens - self._totals.tokens_total),
            "seconds": max(0.0, self.budget.max_wall_seconds - self.elapsed_s),
            "turns": max(0, self.budget.max_turns - self.turn),
        }

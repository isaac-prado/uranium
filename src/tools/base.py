"""Infraestrutura comum das ferramentas: registro de chamada e truncamento."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

# Limites de saída. Existem para proteger a janela de contexto do agente e
# para manter o custo por turno comparável entre os dois braços.
MAX_READ_CHARS = 20_000
MAX_READ_LINES = 400
MAX_SEARCH_RESULTS = 50
MAX_TOOL_OUTPUT_CHARS = 8_000


@dataclass
class ToolCallRecord:
    """Um evento de uso de ferramenta, consumido depois pela telemetria."""

    tool_name: str
    args_hash: str
    duration_ms: int
    denied: bool = False
    error: str | None = None
    bytes_read: int = 0
    bytes_written: int = 0
    exit_code: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Assinatura do emissor de telemetria. Na Frente 4 isto passa a ser o
# TelemetryWriter; por ora o default é no-op.
EmitFn = Callable[[ToolCallRecord], None]


def noop_emit(record: ToolCallRecord) -> None:
    """Emissor padrão: descarta. Substituído pela telemetria real."""
    return None


def hash_args(args: dict[str, Any]) -> str:
    """Hash estável dos argumentos, para deduplicar chamadas repetidas."""
    blob = json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def truncate(text: str, limit: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    """
    Trunca preservando início e fim.

    O fim importa tanto quanto o começo em saída de pytest: o resumo de
    falhas fica lá embaixo.
    """
    if len(text) <= limit:
        return text
    head = limit * 2 // 3
    tail = limit - head
    omitted = len(text) - limit
    return f"{text[:head]}\n\n[... {omitted} caracteres omitidos ...]\n\n{text[-tail:]}"


class Timer:
    """Cronômetro de chamada, em milissegundos."""

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        self.ms = 0
        return self

    def __exit__(self, *exc: object) -> None:
        self.ms = int((time.perf_counter() - self._start) * 1000)

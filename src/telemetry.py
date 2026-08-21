"""
Telemetria JSONL: um evento por linha, gravado durante o run.

É a fonte oficial de custo e processo do estudo. Local, sem rede e sem
serviço externo — o LangSmith fica só como apoio de depuração.

Os dois braços emitem o mesmo envelope. O campo `agent_role` é o que
materializa a variável independente: preenchido no braço B (multiagente
com papéis) e nulo no A2 (agente único sem papéis).
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.autonomy import InterventionLevel
from src.config import extract_call_metrics

SCHEMA_VERSION = 1

Arm = Literal["A2", "B"]

EVENT_TYPES = frozenset({
    "run_start",
    "run_end",
    "node_enter",
    "node_exit",
    "route",
    "llm_call",
    "tool_call",
    "test_run",
    "error",
    "circuit_break",
})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass
class _Context:
    """Contexto corrente, herdado pelos eventos emitidos dentro de um nó."""

    node: str | None = None
    agent_role: str | None = None
    turn: int | None = None


@dataclass
class Totals:
    """Acumulado do run, consultado pelo circuit breaker."""

    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_reasoning: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    llm_calls: int = 0
    tool_calls: int = 0
    test_runs: int = 0
    errors: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "tokens_reasoning": self.tokens_reasoning,
            "tokens_total": self.tokens_total,
            "cost_usd": round(self.cost_usd, 8),
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "test_runs": self.test_runs,
            "errors": self.errors,
        }


class TelemetryWriter:
    """
    Emissor único de eventos, usado por todos os nós e ferramentas.

    Grava com flush + fsync a cada evento: se um run morrer no meio, o que
    já aconteceu tem de estar em disco, senão o custo daquele run se perde.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        run_id: str,
        arm: Arm,
        task_id: str,
        model: str | None = None,
        provider_requested: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.arm = arm
        self.task_id = task_id
        self.model = model
        self.provider_requested = provider_requested

        self._seq = 0
        self._start = time.perf_counter()
        self._lock = threading.Lock()
        self._handle = self.path.open("a", encoding="utf-8")
        self._context = _Context()
        self.totals = Totals()

    # ------------------------------------------------------------- contexto

    def set_context(
        self,
        *,
        node: str | None = None,
        agent_role: str | None = None,
        turn: int | None = None,
    ) -> None:
        """Define o contexto herdado pelos próximos eventos."""
        self._context = _Context(node=node, agent_role=agent_role, turn=turn)

    @contextmanager
    def node(self, name: str, *, agent_role: str | None = None) -> Iterator[None]:
        """Emite node_enter/node_exit e mantém o contexto durante o bloco."""
        anterior = self._context
        self.set_context(node=name, agent_role=agent_role, turn=anterior.turn)
        self.emit("node_enter")
        started = time.perf_counter()
        try:
            yield
        except Exception as exc:
            self.emit_error(exc)
            raise
        finally:
            self.emit("node_exit", latency_ms=int((time.perf_counter() - started) * 1000))
            self._context = anterior

    def set_turn(self, turn: int) -> None:
        ctx = self._context
        self._context = _Context(node=ctx.node, agent_role=ctx.agent_role, turn=turn)

    # --------------------------------------------------------------- emissão

    def emit(self, event_type: str, **fields: Any) -> dict[str, Any]:
        """Grava um evento e devolve o dicionário gravado."""
        if event_type not in EVENT_TYPES:
            raise ValueError(f"event_type desconhecido: {event_type!r}")

        ctx = self._context

        with self._lock:
            self._seq += 1
            event: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "run_id": self.run_id,
                "arm": self.arm,
                "task_id": self.task_id,
                "seq": self._seq,
                "ts": _utc_now(),
                "elapsed_ms": int((time.perf_counter() - self._start) * 1000),
                "event_type": event_type,
                "node": fields.pop("node", ctx.node),
                "agent_role": fields.pop("agent_role", ctx.agent_role),
                "turn": fields.pop("turn", ctx.turn),
                # Nos braços A2/B é sempre L0: ambos são headless por desenho.
                "intervention_level": fields.pop(
                    "intervention_level", InterventionLevel.L0.value
                ),
                "model": fields.pop("model", self.model),
                "provider_requested": fields.pop("provider_requested", self.provider_requested),
                "provider_served": fields.pop("provider_served", None),
                "tokens_prompt": fields.pop("tokens_prompt", 0),
                "tokens_completion": fields.pop("tokens_completion", 0),
                "tokens_reasoning": fields.pop("tokens_reasoning", 0),
                "tokens_total": fields.pop("tokens_total", 0),
                "cost_usd": fields.pop("cost_usd", 0.0),
                "latency_ms": fields.pop("latency_ms", 0),
                "tool_name": fields.pop("tool_name", None),
                "tool_args_hash": fields.pop("tool_args_hash", None),
                "tool_denied": fields.pop("tool_denied", False),
                "tool_exit_code": fields.pop("tool_exit_code", None),
                "payload": fields.pop("payload", {}) | fields,
            }

            self._handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
            self._handle.flush()
            os.fsync(self._handle.fileno())

            self._acumular(event)

        return event

    def _acumular(self, event: dict[str, Any]) -> None:
        t = self.totals
        t.tokens_prompt += event["tokens_prompt"]
        t.tokens_completion += event["tokens_completion"]
        t.tokens_reasoning += event["tokens_reasoning"]
        t.tokens_total += event["tokens_total"]
        t.cost_usd += event["cost_usd"]
        match event["event_type"]:
            case "llm_call":
                t.llm_calls += 1
            case "tool_call":
                t.tool_calls += 1
            case "test_run":
                t.test_runs += 1
            case "error":
                t.errors += 1

    # ------------------------------------------------------- atalhos tipados

    def emit_llm_call(self, message: Any, *, latency_ms: int = 0, **fields: Any) -> dict[str, Any]:
        """Registra uma chamada de LLM, extraindo tokens, custo e provedor servido."""
        m = extract_call_metrics(message)
        tool_calls = getattr(message, "tool_calls", None) or []
        return self.emit(
            "llm_call",
            provider_served=m.provider_served,
            model=m.model or self.model,
            tokens_prompt=m.tokens_prompt,
            tokens_completion=m.tokens_completion,
            tokens_reasoning=m.tokens_reasoning,
            tokens_total=m.tokens_total,
            cost_usd=m.cost_usd,
            latency_ms=latency_ms,
            payload={
                "generation_id": m.generation_id,
                "finish_reason": m.finish_reason,
                "tool_calls_requested": [c.get("name") for c in tool_calls],
            },
            **fields,
        )

    def emit_tool_call(self, record: Any, **fields: Any) -> dict[str, Any]:
        """Registra o uso de uma ferramenta. Compatível com `EmitFn` do toolset."""
        return self.emit(
            "tool_call",
            tool_name=record.tool_name,
            tool_args_hash=record.args_hash,
            tool_denied=record.denied,
            tool_exit_code=record.exit_code,
            latency_ms=record.duration_ms,
            payload={
                "bytes_read": record.bytes_read,
                "bytes_written": record.bytes_written,
                "error": record.error,
            },
            **fields,
        )

    def emit_test_run(self, report: Any, **fields: Any) -> dict[str, Any]:
        """Registra uma execução real da suíte de testes."""
        return self.emit(
            "test_run",
            tool_exit_code=report.exit_code,
            latency_ms=int(report.duration_s * 1000),
            payload={
                "green": report.green,
                "passed": report.passed,
                "failed": report.failed,
                "errors": report.errors,
                "skipped": report.skipped,
                "timed_out": report.timed_out,
                "failing_node_ids": report.failing_node_ids[:50],
            },
            **fields,
        )

    def emit_error(self, exc: BaseException, **fields: Any) -> dict[str, Any]:
        return self.emit(
            "error",
            payload={"type": type(exc).__name__, "message": str(exc)[:2000]},
            **fields,
        )

    def emit_circuit_break(self, reason: str, **fields: Any) -> dict[str, Any]:
        return self.emit("circuit_break", payload={"reason": reason}, **fields)

    # ------------------------------------------------------------ ciclo de vida

    def run_start(self, **payload: Any) -> dict[str, Any]:
        return self.emit("run_start", payload=payload)

    def run_end(self, *, stop_reason: str, **payload: Any) -> dict[str, Any]:
        return self.emit(
            "run_end",
            payload={"stop_reason": stop_reason, "totals": self.totals.as_dict(), **payload},
        )

    def close(self) -> None:
        with self._lock:
            if not self._handle.closed:
                self._handle.close()

    def __enter__(self) -> "TelemetryWriter":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------------- leitura


def read_events(path: str | Path) -> list[dict[str, Any]]:
    """Lê um arquivo JSONL de eventos, ignorando linhas vazias."""
    linhas = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(linha) for linha in linhas if linha.strip()]


def aggregate_cost(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Bloco `cost` do resultado, somado a partir dos eventos."""
    return {
        "tokens_prompt": sum(e.get("tokens_prompt", 0) for e in events),
        "tokens_completion": sum(e.get("tokens_completion", 0) for e in events),
        "tokens_reasoning": sum(e.get("tokens_reasoning", 0) for e in events),
        "tokens_total": sum(e.get("tokens_total", 0) for e in events),
        "cost_usd": round(sum(e.get("cost_usd", 0.0) for e in events), 8),
        "llm_calls": sum(1 for e in events if e.get("event_type") == "llm_call"),
        "tool_calls": sum(1 for e in events if e.get("event_type") == "tool_call"),
        "wall_seconds": round(max((e.get("elapsed_ms", 0) for e in events), default=0) / 1000, 3),
    }


def providers_served(events: list[dict[str, Any]]) -> set[str]:
    """Provedores que efetivamente atenderam — verifica se o pino se manteve."""
    return {e["provider_served"] for e in events if e.get("provider_served")}

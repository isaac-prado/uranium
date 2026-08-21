"""
Contexto de execução de um run: workspace, telemetria, orçamento e ferramentas.

O WorkflowState do LangGraph precisa ser serializável, então objetos vivos
(handle de arquivo, subprocesso, cliente HTTP) não cabem nele. O estado
carrega apenas o `run_id`; os nós resolvem o contexto por aqui.

`llm_factory` é injetável de propósito: é o que permite rodar o grafo
inteiro offline, com um LLM de sequência gravada, sem gastar um centavo.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

from langchain_core.tools import BaseTool

from src.budget import BudgetTracker, RunBudget
from src.telemetry import Arm, TelemetryWriter
from src.tools import build_toolset
from src.workspace import Workspace


@dataclass
class RunContext:
    """Tudo que um nó precisa e que não cabe no estado serializável."""

    run_id: str
    arm: Arm
    task_id: str
    workspace: Workspace
    telemetry: TelemetryWriter
    budget: BudgetTracker
    tools: list[BaseTool]
    llm_factory: Callable[..., Any]
    test_timeout_s: int = 120

    _registry: ClassVar[dict[str, "RunContext"]] = {}

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        arm: Arm,
        task_id: str,
        workspace: Workspace,
        telemetry: TelemetryWriter,
        budget: RunBudget | None = None,
        llm_factory: Callable[..., Any] | None = None,
        test_timeout_s: int = 120,
    ) -> "RunContext":
        """Monta o contexto e o registra para os nós resolverem por run_id."""
        if llm_factory is None:
            from src.config import get_llm

            llm_factory = get_llm

        context = cls(
            run_id=run_id,
            arm=arm,
            task_id=task_id,
            workspace=workspace,
            telemetry=telemetry,
            budget=BudgetTracker(budget or RunBudget.from_env(), telemetry.totals),
            tools=build_toolset(
                workspace, emit=telemetry.emit_tool_call, test_timeout_s=test_timeout_s
            ),
            llm_factory=llm_factory,
            test_timeout_s=test_timeout_s,
        )
        cls._registry[run_id] = context
        return context

    @classmethod
    def get(cls, run_id: str) -> "RunContext":
        try:
            return cls._registry[run_id]
        except KeyError:
            raise RuntimeError(
                f"RunContext não registrado para run_id={run_id!r}. "
                "Use RunContext.create(...) antes de invocar o grafo."
            ) from None

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "RunContext":
        run_id = state.get("run_id")
        if not run_id:
            raise RuntimeError("O estado não carrega run_id — o grafo foi invocado sem contexto.")
        return cls.get(run_id)

    @classmethod
    def release(cls, run_id: str) -> None:
        cls._registry.pop(run_id, None)

    # ------------------------------------------------------------- conveniência

    @property
    def tool_by_name(self) -> dict[str, BaseTool]:
        return {tool.name: tool for tool in self.tools}

    def bound_llm(self, *, tools: bool = True) -> Any:
        """LLM pronto para uso, com as ferramentas ligadas quando pedido."""
        llm = self.llm_factory()
        return llm.bind_tools(self.tools) if tools else llm

    def stop_if_exhausted(self) -> str | None:
        """Registra e devolve o motivo do estouro de orçamento, se houver."""
        reason = self.budget.exceeded()
        if reason:
            self.telemetry.emit_circuit_break(reason)
        return reason

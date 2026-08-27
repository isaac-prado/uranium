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

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

from src.budget import BudgetTracker, RunBudget
from src.telemetry import Arm, TelemetryWriter
from src.tools import build_toolset
from src.workspace import Workspace

# Teto de tool calls por turno, igual nos dois braços.
MAX_TOOL_CALLS_POR_TURNO = 8


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

    # Conversa viva do agente. Fica aqui, e não no WorkflowState, porque
    # BaseMessage não é serializável e porque o StateGraph descarta chaves
    # não declaradas no TypedDict.
    conversation: list[BaseMessage] = field(default_factory=list)

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
        llm_config: Any = None,
        llm_factory: Callable[..., Any] | None = None,
        test_timeout_s: int = 120,
    ) -> "RunContext":
        """
        Monta o contexto e o registra para os nós resolverem por run_id.

        `llm_config` é a configuração JÁ RESOLVIDA do run — a mesma que vai
        para o manifesto. Precisa ser passada: sem ela o cliente seria
        construído a partir do ambiente, e um run poderia usar um modelo
        diferente do que o manifesto declara. Isso corromperia a proveniência
        da coleta em silêncio.
        """
        if llm_factory is None:
            from src.config import get_llm

            if llm_config is None:
                raise RuntimeError(
                    "RunContext.create exige llm_config quando não há llm_factory: "
                    "sem ela o cliente viria do ambiente e divergiria do manifesto."
                )
            llm_factory = lambda: get_llm(llm_config)  # noqa: E731

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

    def invoke_structured(self, schema: Any, messages: Any, **kwargs: Any) -> Any:
        """
        Chamada estruturada instrumentada.

        Usa o LLM do contexto (injetável em teste) e registra a chamada na
        telemetria. Os nós do braço orchestration DEVEM passar por aqui: chamar
        `invoke_structured` direto deixa a chamada fora da contabilidade de
        custo e fora do orçamento, e o braço multiagente — que tem quatro
        nós a mais fazendo chamadas — sairia artificialmente barato.
        """
        import time

        from src.structured_llm import invoke_structured_raw

        inicio = time.perf_counter()
        resultado, bruta = invoke_structured_raw(
            schema, messages, llm=self.llm_factory(), **kwargs
        )
        if bruta is not None:
            self.telemetry.emit_llm_call(
                bruta, latency_ms=int((time.perf_counter() - inicio) * 1000)
            )
        return resultado

    def stop_if_exhausted(self) -> str | None:
        """Registra e devolve o motivo do estouro de orçamento, se houver."""
        reason = self.budget.exceeded()
        if reason:
            self.telemetry.emit_circuit_break(reason)
        return reason

    def executar_tool_calls(self, ai: Any) -> list[Any]:
        """
        Executa as tool calls de um turno e devolve as respostas ao modelo.

        Vive aqui, e não em cada braço, porque comportamento divergente na
        execução de ferramenta é divergência de tratamento: os braços teriam
        capacidades diferentes sem que nada no manifesto dissesse isso.

        Nada escapa como exceção. Ferramenta desconhecida, argumento faltando
        ou erro interno voltam como texto para o modelo, que pode corrigir no
        turno seguinte. Um `ValidationError` do pydantic derrubou um run
        inteiro do piloto antes disto existir — a validação de argumento
        acontece antes da função da ferramenta rodar, então a guarda que já
        havia lá dentro nunca era alcançada.
        """
        from langchain_core.messages import ToolMessage

        respostas: list[Any] = []
        por_nome = self.tool_by_name

        for chamada in (ai.tool_calls or [])[:MAX_TOOL_CALLS_POR_TURNO]:
            ferramenta = por_nome.get(chamada["name"])
            if ferramenta is None:
                conteudo = (
                    f"ERRO: ferramenta desconhecida {chamada['name']!r}. "
                    f"Disponíveis: {', '.join(sorted(por_nome))}."
                )
            else:
                try:
                    conteudo = str(ferramenta.invoke(chamada["args"]))
                except Exception as exc:
                    self.telemetry.emit_error(exc)
                    conteudo = (
                        f"ERRO: chamada inválida de {chamada['name']!r}: "
                        f"{type(exc).__name__}: {exc}. Confira os argumentos "
                        f"exigidos e tente de novo."
                    )
            respostas.append(ToolMessage(content=conteudo, tool_call_id=chamada["id"]))

        return respostas

"""Helpers de observabilidade LangSmith (@traceable)."""

from langsmith import traceable


def agent_traceable(name: str):
    """
    Decorator para nós do grafo (agentes).

    run_type=chain agrupa entradas/saídas do agente no LangSmith.
    """
    return traceable(
        name=name,
        run_type="chain",
        tags=["uranium", "agent", name],
    )


def pipeline_traceable(name: str, *, run_type: str = "chain"):
    """Decorator para funções auxiliares do pipeline (LLM, roteamento, etc.)."""
    return traceable(
        name=name,
        run_type=run_type,
        tags=["uranium", name],
    )

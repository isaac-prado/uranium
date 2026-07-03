"""Montagem do grafo LangGraph do pipeline Uranium."""

from langgraph.graph import END, START, StateGraph

from src.agents.clarification import clarification
from src.agents.developer import developer
from src.agents.intent_refiner import intent_refiner
from src.agents.test_generator import test_generator
from src.agents.validator import validator
from src.config import MAX_CLARIFICATION_ITERATIONS, MAX_VALIDATION_ITERATIONS
from src.state import WorkflowState
from src.tracing import pipeline_traceable


@pipeline_traceable("route_after_intent_refiner")
def route_after_intent_refiner(state: WorkflowState) -> str:
    """Roteia para clarificação ou desenvolvimento após refinamento de intent."""
    if state.get("is_ready"):
        return "developer"
    if state.get("iteration_count", 0) >= MAX_CLARIFICATION_ITERATIONS:
        return "developer"
    return "clarification"


@pipeline_traceable("route_after_validator")
def route_after_validator(state: WorkflowState) -> str:
    """Roteia para retentativa de desenvolvimento ou geração de testes."""
    if state.get("is_valid"):
        return "test_generator"
    if state.get("validation_iteration_count", 0) >= MAX_VALIDATION_ITERATIONS:
        return "test_generator"
    return "developer"


@pipeline_traceable("build_graph")
def build_graph():
    """
    Constrói e compila o grafo completo do pipeline Uranium.

    Fluxo:
    START -> intent_refiner -> [clarification loop | developer]
    -> validator -> [developer retry | test_generator] -> END
    """
    builder = StateGraph(WorkflowState)

    builder.add_node("intent_refiner", intent_refiner)
    builder.add_node("clarification", clarification)
    builder.add_node("developer", developer)
    builder.add_node("validator", validator)
    builder.add_node("test_generator", test_generator)

    builder.add_edge(START, "intent_refiner")

    builder.add_conditional_edges(
        "intent_refiner",
        route_after_intent_refiner,
        {
            "clarification": "clarification",
            "developer": "developer",
        },
    )

    builder.add_edge("clarification", "intent_refiner")
    builder.add_edge("developer", "validator")

    builder.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "developer": "developer",
            "test_generator": "test_generator",
        },
    )

    builder.add_edge("test_generator", END)

    return builder.compile()

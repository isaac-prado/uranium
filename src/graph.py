"""Montagem do grafo LangGraph do pipeline Uranium (braço orchestration, multiagente)."""

from langgraph.graph import END, START, StateGraph

from src.agents.clarification import clarification
from src.agents.developer import developer
from src.agents.intent_refiner import intent_refiner
from src.agents.test_generator import test_generator
from src.agents.validator import validator
from src.config import MAX_CLARIFICATION_ITERATIONS, MAX_SEMANTIC_REJECTIONS
from src.state import WorkflowState, parse_test_report
def route_after_intent_refiner(state: WorkflowState) -> str:
    """Roteia para clarificação ou desenvolvimento após refinamento de intent."""
    if state.get("is_ready"):
        return "developer"
    if state.get("iteration_count", 0) >= MAX_CLARIFICATION_ITERATIONS:
        return "developer"
    return "clarification"
def route_after_validator(state: WorkflowState) -> str:
    """
    Decide refinar ou encerrar, com base em execução real.

    O orçamento é o que encerra o ciclo, como no driver do single-agent:
    suíte vermelha ou diff vazio voltam ao developer até ele acabar. O único
    teto próprio é o da revisão semântica, que não tem equivalente no outro
    braço (`MAX_SEMANTIC_REJECTIONS`).
    """
    if state.get("stop_reason", "").startswith("budget"):
        return "test_generator"
    if state.get("is_valid"):
        return "test_generator"
    revisao = state.get("validation_result") or {}
    reprovada_agora = revisao and not revisao.get("is_valid", True)
    if reprovada_agora and state.get("semantic_rejections", 0) >= MAX_SEMANTIC_REJECTIONS:
        return "test_generator"
    return "developer"
def build_graph():
    """
    Constrói e compila o grafo do braço orchestration.

    START -> intent_refiner -> [clarification loop | developer]
    -> validator -> [developer retry | test_generator] -> END

    A topologia é a mesma de antes; o que mudou é que developer age sobre um
    repositório real e validator decide por exit code de pytest.
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
        {"clarification": "clarification", "developer": "developer"},
    )
    builder.add_edge("clarification", "intent_refiner")
    builder.add_edge("developer", "validator")
    builder.add_conditional_edges(
        "validator",
        route_after_validator,
        {"developer": "developer", "test_generator": "test_generator"},
    )
    builder.add_edge("test_generator", END)

    return builder.compile()

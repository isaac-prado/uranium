"""
Testes de estrutura e roteamento do grafo (braço orchestration).

O comportamento ponta a ponta do pipeline é testado em tests/test_nodes.py,
contra um workspace real e execução real de pytest. Os testes antigos que
mockavam `invoke_structured` no Developer foram removidos: aquele nó não
gera mais texto, ele age por ferramentas — mockar a saída estruturada
deixou de exercitar qualquer coisa relevante.
"""

from src.graph import (
    build_graph,
    route_after_intent_refiner,
    route_after_validator,
)


class TestRoteamentoIntent:
    def test_pronta_vai_para_developer(self):
        assert route_after_intent_refiner({"is_ready": True}) == "developer"

    def test_nao_pronta_vai_para_clarificacao(self):
        assert route_after_intent_refiner(
            {"is_ready": False, "iteration_count": 0}
        ) == "clarification"

    def test_teto_de_clarificacao_segue_em_frente(self):
        assert route_after_intent_refiner(
            {"is_ready": False, "iteration_count": 10}
        ) == "developer"


class TestRoteamentoValidacao:
    def test_valido_encerra(self):
        assert route_after_validator({"is_valid": True}) == "test_generator"

    def test_invalido_volta_ao_developer(self):
        assert route_after_validator(
            {"is_valid": False, "validation_iteration_count": 0}
        ) == "developer"

    def test_teto_de_validacao_encerra(self):
        assert route_after_validator(
            {"is_valid": False, "validation_iteration_count": 10}
        ) == "test_generator"

    def test_orcamento_estourado_encerra_antes_de_reiterar(self):
        assert route_after_validator(
            {"is_valid": False, "validation_iteration_count": 0,
             "stop_reason": "budget: max_turns (40 >= 40)"}
        ) == "test_generator"


class TestEstrutura:
    def test_grafo_compila(self):
        grafo = build_graph()
        assert grafo is not None and hasattr(grafo, "invoke")

    def test_todos_os_nos_registrados(self):
        nos = set(build_graph().get_graph().nodes)
        assert {
            "intent_refiner", "clarification", "developer", "validator", "test_generator"
        } <= nos

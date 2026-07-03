"""Script de teste rápido do pipeline (requer API keys configuradas)."""

from pprint import pprint

from src.graph import build_graph


if __name__ == "__main__":
    graph = build_graph()

    result = graph.invoke(
        {
            "raw_request": "Desenvolva um CRUD simples sem banco de dados apenas as rotas em javascript com node.",
            "iteration_count": 0,
            "validation_iteration_count": 0,
            "clarification_responses": [],
        }
    )

    pprint(result)

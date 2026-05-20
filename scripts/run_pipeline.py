#!/usr/bin/env python3
"""Entrypoint CLI do pipeline Uranium."""

import argparse
import json
import sys
from pathlib import Path

# Garante que o pacote src seja importável
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import get_run_config
from src.graph import build_graph


def main() -> None:
    """Executa o pipeline completo com a solicitação informada."""
    parser = argparse.ArgumentParser(
        description="Uranium - Pipeline de Engenharia de Software 3.0",
    )
    parser.add_argument(
        "request",
        nargs="?",
        default="Criar um CRUD de Cliente com nome, CPF e email.",
        help="Solicitação em linguagem natural",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["pretty", "json"],
        default="pretty",
        help="Formato de saída",
    )
    args = parser.parse_args()

    graph = build_graph()
    run_config = get_run_config(
        run_name="uranium-pipeline",
        tags=["cli"],
    )
    result = graph.invoke(
        {
            "raw_request": args.request,
            "iteration_count": 0,
            "validation_iteration_count": 0,
            "clarification_responses": [],
        },
        config=run_config,
    )

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_pretty(result)


def _print_pretty(result: dict) -> None:
    """Imprime resultado formatado para leitura humana."""
    print("\n=== Uranium Pipeline Result ===\n")

    if intent := result.get("intent"):
        print("--- Intent ---")
        print(f"  Goal: {intent.get('goal', 'N/A')}")
        print(f"  Ready: {intent.get('is_ready', False)}")
        print(f"  Phases: {len(intent.get('phases', []))}")
        print(f"  Acceptance criteria: {len(intent.get('acceptance_criteria', []))}")

    if clarifications := result.get("clarification_responses"):
        print(f"\n--- Clarifications ({len(clarifications)}) ---")
        for item in clarifications:
            print(f"  Q: {item.get('question', '')}")
            print(f"  A: {item.get('answer', '')}")

    if artifacts := result.get("artifacts"):
        print(f"\n--- Artifacts ({len(artifacts)}) ---")
        for art in artifacts:
            print(f"  - [{art.get('artifact_type')}] {art.get('name')}")

    if validation := result.get("validation_result"):
        print("\n--- Validation ---")
        print(f"  Valid: {validation.get('is_valid', False)}")
        if validation.get("issues"):
            print(f"  Issues: {validation['issues']}")

    if test_plan := result.get("test_plan"):
        print("\n--- Test Plan ---")
        print(f"  Summary: {test_plan.get('summary', 'N/A')}")
        print(f"  Unit tests: {len(test_plan.get('unit_tests', []))}")
        print(f"  Integration tests: {len(test_plan.get('integration_tests', []))}")
        print(f"  Test files: {len(test_plan.get('test_files', []))}")

    print(f"\n--- Iterations ---")
    print(f"  Clarification: {result.get('iteration_count', 0)}")
    print(f"  Validation: {result.get('validation_iteration_count', 0)}")
    print()


if __name__ == "__main__":
    main()

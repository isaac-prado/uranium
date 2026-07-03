"""TestAgent - gera plano e casos de teste para artefatos validados."""

import json

from src.schemas.test_plan import TestPlan
from src.state import WorkflowState, parse_artifacts, parse_intent
from src.structured_llm import invoke_structured
from src.tracing import agent_traceable

SYSTEM_PROMPT = """
Você é um engenheiro de qualidade em Engenharia de Software 3.0.

Gere um plano de testes para os artefatos validados.

Retorne JSON com:
- summary (string)
- unit_tests (array de {name, description, test_code})
- integration_tests (array de {name, description, test_code})
- test_files (array de {path, content})

Cubra os critérios de aceitação. Use pytest quando aplicável.
Limite a 3 unit_tests e 2 integration_tests.
"""


@agent_traceable("test_generator")
def test_generator(state: WorkflowState) -> dict[str, object]:
    """Gera plano de testes para artefatos validados."""
    intent = parse_intent(state)
    artifacts = parse_artifacts(state)

    prompt = f"""
Intent:
{intent.model_dump_json(indent=2)}

Artefatos validados:
{json.dumps([a.model_dump() for a in artifacts], ensure_ascii=False, indent=2)}
"""

    result = invoke_structured(
        TestPlan,
        [("system", SYSTEM_PROMPT), ("user", prompt)],
    )

    return {"test_plan": result.model_dump()}

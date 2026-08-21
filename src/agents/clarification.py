"""ClarificationAgent - resolve ambiguidades da intent via respostas simuladas."""

import json

from src.schemas.clarification import ClarificationBatch
from src.state import WorkflowState, parse_intent
from src.structured_llm import invoke_structured

SYSTEM_PROMPT = """
Você é um analista de requisitos em Engenharia de Software 3.0.

Dada uma intent com perguntas de clarificação pendentes, produza respostas
técnicas plausíveis que permitam avançar o desenvolvimento.

Retorne JSON com:
- responses: array de objetos { "question": string, "answer": string }

Para cada pergunta pendente, gere uma resposta objetiva assumindo boas práticas.
"""
def clarification(state: WorkflowState) -> dict[str, object]:
    """Gera respostas para perguntas de clarificação pendentes."""
    questions = state.get("clarifications_needed") or []

    if not questions:
        return {
            "clarification_responses": state.get("clarification_responses") or [],
        }

    intent = parse_intent(state)

    prompt = f"""
Intent atual:
{intent.model_dump_json(indent=2)}

Perguntas pendentes:
{json.dumps(questions, ensure_ascii=False, indent=2)}

Gere respostas técnicas para cada pergunta.
"""

    result = invoke_structured(
        ClarificationBatch,
        [("system", SYSTEM_PROMPT), ("user", prompt)],
    )

    existing = state.get("clarification_responses") or []
    new_responses = [r.model_dump() for r in result.responses]
    merged = existing + new_responses

    return {"clarification_responses": merged}

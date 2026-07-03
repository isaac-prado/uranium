"""ValidatorAgent - valida artefatos contra critérios de aceitação da intent."""

import json

from src.schemas.validation_result import ValidationResult
from src.state import WorkflowState, parse_artifacts, parse_intent
from src.structured_llm import invoke_structured
from src.tracing import agent_traceable

SYSTEM_PROMPT = """
Você é um revisor técnico em Engenharia de Software 3.0.

Valide se os artefatos atendem aos critérios de aceitação da intent.

Retorne JSON com:
- is_valid (boolean)
- issues (array de strings)
- suggestions (array de strings)
- covered_criteria (array de strings)
- missing_criteria (array de strings)

is_valid=false apenas quando houver lacunas significativas.
"""


@agent_traceable("validator")
def validator(state: WorkflowState) -> dict[str, object]:
    """Valida artefatos contra critérios de aceitação."""
    intent = parse_intent(state)
    artifacts = parse_artifacts(state)

    prompt = f"""
Intent:
{intent.model_dump_json(indent=2)}

Artefatos:
{json.dumps([a.model_dump() for a in artifacts], ensure_ascii=False, indent=2)}
"""

    result = invoke_structured(
        ValidationResult,
        [("system", SYSTEM_PROMPT), ("user", prompt)],
    )

    validation_iteration = state.get("validation_iteration_count", 0) + 1

    return {
        "validation_result": result.model_dump(),
        "is_valid": result.is_valid,
        "validation_iteration_count": validation_iteration,
    }

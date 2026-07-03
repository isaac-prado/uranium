"""DeveloperAgent - gera artefatos de desenvolvimento a partir da intent estruturada."""

from src.schemas.development_artifact import DevelopmentArtifacts
from src.state import WorkflowState, parse_intent, parse_validation
from src.structured_llm import invoke_structured
from src.tracing import agent_traceable

SYSTEM_PROMPT = """
Você é um desenvolvedor sênior em Engenharia de Software 3.0.

Gere artefatos de desenvolvimento a partir da intent estruturada.

Retorne JSON com:
- summary (string): resumo da implementação
- artifacts (array, máximo 5 itens): cada item com
  name, artifact_type (model|migration|endpoint|service|component|other),
  description, content, file_path

Regras:
1. Gere código conciso e utilizável.
2. Cubra as fases e critérios de aceitação.
3. Se houver feedback de validação, corrija os problemas.
4. Limite-se a no máximo 5 artefatos essenciais.
5. No JSON, escape barras invertidas em strings de código como \\\\ (JSON válido).
"""


def _build_developer_prompt(state: WorkflowState) -> str:
    """Monta prompt com intent e feedback de validação, se houver."""
    intent = parse_intent(state)
    validation = parse_validation(state)

    parts = [
        "Intent estruturada:",
        intent.model_dump_json(indent=2),
    ]

    if validation and not validation.is_valid:
        parts.append("\nFeedback da validação anterior (corrija estes pontos):")
        parts.append(validation.model_dump_json(indent=2))

    return "\n".join(parts)


@agent_traceable("developer")
def developer(state: WorkflowState) -> dict[str, object]:
    """Gera artefatos de desenvolvimento baseados na intent."""
    result = invoke_structured(
        DevelopmentArtifacts,
        [
            ("system", SYSTEM_PROMPT),
            ("user", _build_developer_prompt(state)),
        ],
    )

    return {
        "artifacts": [a.model_dump() for a in result.artifacts],
    }

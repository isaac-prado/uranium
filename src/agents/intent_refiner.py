"""IntentRefinerAgent - converte solicitação em linguagem natural em intent estruturada."""

from src.schemas.intent import StructuredIntent
from src.state import WorkflowState
from src.structured_llm import invoke_structured

SYSTEM_PROMPT = """
Você é um especialista em Engenharia de Software 3.0.

Sua tarefa é transformar uma solicitação em linguagem natural
em uma representação estruturada da intenção de desenvolvimento.

Analise a solicitação e produza JSON com:
- context (string)
- goal (string)
- phases (array de strings)
- acceptance_criteria (array de strings)
- clarifications_needed (array de strings)
- is_ready (boolean)

Regras:
1. Se houver informação suficiente, defina is_ready=true.
2. Se houver ambiguidades relevantes, defina is_ready=false.
3. Liste perguntas em clarifications_needed.
4. Seja objetivo e técnico.
5. Se houver respostas de clarificação anteriores, incorpore-as na intent refinada.
"""


def _build_user_prompt(state: WorkflowState) -> str:
    """Monta o prompt do usuário com contexto e clarificações."""
    raw_request = state["raw_request"]
    clarifications = state.get("clarification_responses") or []

    parts = [f"Solicitação do usuário:\n{raw_request}"]

    if clarifications:
        parts.append("\nRespostas de clarificação anteriores:")
        for item in clarifications:
            parts.append(f"- Pergunta: {item.get('question', '')}")
            parts.append(f"  Resposta: {item.get('answer', '')}")

    return "\n".join(parts)


def intent_refiner(state: WorkflowState) -> dict[str, object]:
    """Refina a solicitação em uma intent estruturada."""
    result = invoke_structured(
        StructuredIntent,
        [
            ("system", SYSTEM_PROMPT),
            ("user", _build_user_prompt(state)),
        ],
    )

    iteration_count = state.get("iteration_count", 0)
    if state.get("clarification_responses"):
        iteration_count += 1

    return {
        "intent": result.model_dump(),
        "clarifications_needed": result.clarifications_needed,
        "is_ready": result.is_ready,
        "iteration_count": iteration_count,
    }

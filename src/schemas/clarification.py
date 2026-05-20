"""Schema das respostas de clarificação."""

from pydantic import BaseModel, Field


class ClarificationItem(BaseModel):
    """Par pergunta-resposta de clarificação."""

    question: str = Field(description="Pergunta de clarificação")
    answer: str = Field(description="Resposta técnica")


class ClarificationBatch(BaseModel):
    """Lote de respostas de clarificação."""

    responses: list[ClarificationItem] = Field(
        description="Respostas para perguntas pendentes",
    )

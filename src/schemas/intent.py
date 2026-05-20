"""Schema da intenção estruturada produzida pelo IntentRefinerAgent."""

from pydantic import BaseModel, Field


class StructuredIntent(BaseModel):
    """Representação estruturada da intenção de desenvolvimento."""

    context: str = Field(description="Contexto atual do sistema")
    goal: str = Field(description="Objetivo principal da solicitação")
    phases: list[str] = Field(description="Fases sugeridas de implementação")
    acceptance_criteria: list[str] = Field(
        description="Critérios de aceitação"
    )
    clarifications_needed: list[str] = Field(
        default_factory=list,
        description="Perguntas adicionais necessárias",
    )
    is_ready: bool = Field(
        description="Indica se a intent está pronta para desenvolvimento",
    )

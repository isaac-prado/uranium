"""Schema do resultado de validação produzido pelo ValidatorAgent."""

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Resultado da validação de artefatos contra critérios de aceitação."""

    is_valid: bool = Field(
        description="Indica se os artefatos atendem aos critérios de aceitação",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Problemas encontrados na validação",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Sugestões de melhoria para os artefatos",
    )
    covered_criteria: list[str] = Field(
        default_factory=list,
        description="Critérios de aceitação cobertos pelos artefatos",
    )
    missing_criteria: list[str] = Field(
        default_factory=list,
        description="Critérios de aceitação não cobertos",
    )

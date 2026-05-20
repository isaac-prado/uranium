"""Schemas dos artefatos de desenvolvimento produzidos pelo DeveloperAgent."""

from typing import Literal

from pydantic import BaseModel, Field

ArtifactType = Literal[
    "model", "migration", "endpoint", "service", "component", "other"
]


class DevelopmentArtifact(BaseModel):
    """Artefato individual gerado pelo DeveloperAgent."""

    name: str = Field(description="Nome identificador do artefato")
    artifact_type: ArtifactType = Field(
        description="Tipo: model, migration, endpoint, service, component, other",
    )
    description: str = Field(description="Descrição do artefato")
    content: str = Field(description="Conteúdo do artefato (código, spec, etc.)")
    file_path: str = Field(
        default="",
        description="Caminho sugerido no projeto",
    )


class DevelopmentArtifacts(BaseModel):
    """Conjunto de artefatos gerados para uma intent."""

    summary: str = Field(description="Resumo da implementação proposta")
    artifacts: list[DevelopmentArtifact] = Field(
        min_length=1,
        max_length=6,
        description="Lista de artefatos de desenvolvimento (máx. 6)",
    )

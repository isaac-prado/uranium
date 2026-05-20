"""Schema do plano de testes produzido pelo TestAgent."""

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """Caso de teste individual."""

    name: str = Field(description="Nome do caso de teste")
    description: str = Field(description="Descrição do que o teste valida")
    test_code: str = Field(default="", description="Código do teste")


class TestFile(BaseModel):
    """Arquivo de teste sugerido."""

    path: str = Field(description="Caminho do arquivo de teste")
    content: str = Field(description="Conteúdo do arquivo")


class TestPlan(BaseModel):
    """Plano de testes gerado pelo TestAgent."""

    summary: str = Field(description="Resumo do plano de testes")
    unit_tests: list[TestCase] = Field(
        default_factory=list,
        description="Casos de teste unitários",
    )
    integration_tests: list[TestCase] = Field(
        default_factory=list,
        description="Casos de teste de integração",
    )
    test_files: list[TestFile] = Field(
        default_factory=list,
        description="Arquivos de teste sugeridos",
    )

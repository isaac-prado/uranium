"""Fixtures compartilhadas para testes."""

import pytest

from src.schemas.development_artifact import DevelopmentArtifact, DevelopmentArtifacts
from src.schemas.intent import StructuredIntent
from src.schemas.test_plan import TestCase, TestFile, TestPlan
from src.schemas.validation_result import ValidationResult
from src.schemas.clarification import ClarificationBatch, ClarificationItem


@pytest.fixture
def sample_intent() -> StructuredIntent:
    """Intent estruturada de exemplo."""
    return StructuredIntent(
        context="Sistema sem cadastro de clientes.",
        goal="Implementar CRUD de Cliente.",
        phases=["Modelo", "Endpoints", "Testes"],
        acceptance_criteria=[
            "Usuário pode criar clientes",
            "Usuário pode editar clientes",
            "Usuário pode excluir clientes",
        ],
        clarifications_needed=[],
        is_ready=True,
    )


@pytest.fixture
def sample_intent_not_ready() -> StructuredIntent:
    """Intent com ambiguidades."""
    return StructuredIntent(
        context="Sistema desconhecido.",
        goal="Implementar funcionalidade.",
        phases=["Análise"],
        acceptance_criteria=[],
        clarifications_needed=["Qual stack usar?", "Há autenticação?"],
        is_ready=False,
    )


@pytest.fixture
def sample_artifacts() -> DevelopmentArtifacts:
    """Artefatos de desenvolvimento de exemplo."""
    return DevelopmentArtifacts(
        summary="CRUD de Cliente",
        artifacts=[
            DevelopmentArtifact(
                name="ClienteModel",
                artifact_type="model",
                description="Modelo de dados",
                content="class Cliente: pass",
                file_path="src/models/cliente.py",
            ),
        ],
    )


@pytest.fixture
def sample_validation_valid() -> ValidationResult:
    """Resultado de validação válido."""
    return ValidationResult(
        is_valid=True,
        issues=[],
        suggestions=[],
        covered_criteria=["Usuário pode criar clientes"],
        missing_criteria=[],
    )


@pytest.fixture
def sample_validation_invalid() -> ValidationResult:
    """Resultado de validação inválido."""
    return ValidationResult(
        is_valid=False,
        issues=["Falta endpoint DELETE"],
        suggestions=["Adicionar rota DELETE /clientes/{id}"],
        covered_criteria=["Usuário pode criar clientes"],
        missing_criteria=["Usuário pode excluir clientes"],
    )


@pytest.fixture
def sample_test_plan() -> TestPlan:
    """Plano de testes de exemplo."""
    return TestPlan(
        summary="Testes do CRUD de Cliente",
        unit_tests=[
            TestCase(
                name="test_create_cliente",
                description="Valida criação de cliente",
                test_code="def test_create(): pass",
            ),
        ],
        integration_tests=[],
        test_files=[
            TestFile(
                path="tests/test_cliente.py",
                content="def test_cliente(): pass",
            ),
        ],
    )


@pytest.fixture
def sample_clarification_batch() -> ClarificationBatch:
    """Respostas de clarificação de exemplo."""
    return ClarificationBatch(
        responses=[
            ClarificationItem(
                question="Qual stack usar?",
                answer="Python com FastAPI e PostgreSQL.",
            ),
            ClarificationItem(
                question="Há autenticação?",
                answer="Sim, JWT com roles admin e user.",
            ),
        ],
    )

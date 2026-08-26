"""Fixtures compartilhadas para testes."""

import pytest

# Variáveis que alteram o comportamento do pipeline. O .env do desenvolvedor
# não pode decidir o resultado de um teste — isso já mascarou falha real
# três vezes neste repositório.
_ENV_QUE_AFETA_EXPERIMENTO = (
    "STRUCTURED_OUTPUT_METHOD",
    "STRUCTURED_OUTPUT_RETRIES",
    "OPENROUTER_MODEL_NAME",
    "OPENROUTER_PROVIDER",
    "LLM_TEMPERATURE",
    "LLM_SEED",
    "LLM_MAX_TOKENS",
    "LLM_REQUEST_TIMEOUT",
    "MAX_CLARIFICATION_ITERATIONS",
    "MAX_VALIDATION_ITERATIONS",
    "RUN_MAX_TOKENS",
    "RUN_MAX_WALL_SECONDS",
    "RUN_MAX_TURNS",
)


@pytest.fixture(autouse=True)
def env_isolado(monkeypatch):
    """Remove do ambiente tudo que possa alterar o comportamento sob teste."""
    for nome in _ENV_QUE_AFETA_EXPERIMENTO:
        monkeypatch.delenv(nome, raising=False)

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


@pytest.fixture
def ctx_minimo(tmp_path, monkeypatch):
    """
    RunContext sem workspace real, para testar nós que só chamam LLM.

    Devolve (contexto, respostas) — basta preencher `respostas` com o que o
    `invoke_structured_raw` deve retornar, na ordem.
    """
    from src.runtime import RunContext
    from src.telemetry import TelemetryWriter

    class _WorkspaceFalso:
        root = tmp_path

        def changed_files(self):
            return []

        def diff(self):
            return ""

        def diffstat(self):
            return {"files_changed": 0, "insertions": 0, "deletions": 0}

    tel = TelemetryWriter(
        tmp_path / "events.jsonl",
        run_id="no-test", arm="orchestration", task_id="t",
    )
    ctx = RunContext.create(
        run_id="no-test", arm="orchestration", task_id="t",
        workspace=_WorkspaceFalso(), telemetry=tel, llm_factory=lambda: None,
    )

    respostas: list = []

    def _falso(schema, messages, **kwargs):
        if not respostas:
            raise AssertionError(f"sem resposta preparada para {schema.__name__}")
        return respostas.pop(0), None

    monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _falso)

    yield ctx, respostas
    tel.close()
    RunContext.release("no-test")

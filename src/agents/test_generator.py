"""
TestAgent — plano de testes complementar, fora da medição de corretude.

Nó terminal do braço orchestration. O que ele produz NÃO conta como oráculo: os testes
que decidem se a tarefa foi resolvida são os ocultos, injetados pelo harness
e nunca vistos pelo agente. Se este nó chegar a escrever testes no
workspace, eles vão para `tests/uranium/`, que o harness exclui tanto do
oráculo quanto da suíte de regressão.
"""

from __future__ import annotations

from typing import Any

from src.runtime import RunContext
from src.schemas.test_plan import TestPlan
from src.state import WorkflowState, parse_intent, parse_test_report
from src.structured_llm import StructuredOutputError, invoke_structured

SYSTEM_PROMPT = """\
Você é um engenheiro de qualidade. Dada a tarefa e o diff aplicado, proponha
testes que cubram o comportamento alterado.

Retorne JSON com summary, unit_tests e integration_tests. Limite a 3 testes
unitários e 2 de integração. Use pytest.
"""
def test_generator(state: WorkflowState) -> dict[str, Any]:
    """Gera um plano de testes para a mudança aplicada."""
    ctx = RunContext.from_state(state)

    with ctx.telemetry.node("test_generator", agent_role="test_generator"):
        if ctx.stop_if_exhausted():
            return {"test_plan": None}

        diff = ctx.workspace.diff()[:12_000]
        report = parse_test_report(state)

        prompt = "\n".join([
            "Tarefa:",
            parse_intent(state).model_dump_json(indent=2),
            "",
            "Diff aplicado:",
            diff or "(nenhuma alteração)",
            "",
            f"Resultado da suíte: {report.summary() if report else 'não executada'}",
        ])

        try:
            plan = ctx.invoke_structured(TestPlan, [("system", SYSTEM_PROMPT), ("user", prompt)])
        except StructuredOutputError as exc:
            ctx.telemetry.emit_error(exc)
            return {"test_plan": None}

    return {"test_plan": plan.model_dump()}

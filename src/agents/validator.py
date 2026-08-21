"""
ValidatorAgent — corretude por execução real, não por julgamento de texto.

Regra estrutural deste nó: `is_valid` só pode ser verdadeiro se a suíte
tiver saído com exit code 0. O LLM pode REBAIXAR o veredito (apontar que a
mudança resolve o teste mas viola a intenção), nunca promovê-lo. Sem essa
monotonicidade o pipeline volta a medir a auto-avaliação do modelo em vez
de medir corretude.

Isto é o tratamento ES 3.0: o agente usa execução para decidir se refina.
A corretude reportada no TCC continua vindo do harness externo, com
oráculos que o agente nunca viu.
"""

from __future__ import annotations

import os
from typing import Any

from src.runtime import RunContext
from src.schemas.validation_result import ValidationResult
from src.state import WorkflowState, parse_intent
from src.structured_llm import StructuredOutputError, invoke_structured
from src.tools.exec import run_pytest

SYSTEM_PROMPT = """\
Você é um revisor técnico. A suíte de testes JÁ PASSOU — isto não está em
discussão e você não pode reverter esse fato.

Sua única pergunta é: a mudança resolve o problema descrito na tarefa, ou
apenas faz os testes passarem por acidente (código morto, caso especial
grudado, comportamento não relacionado alterado)?

Retorne JSON com is_valid, issues, suggestions, covered_criteria e
missing_criteria. Use is_valid=false apenas se houver lacuna real frente à
tarefa.
"""


def semantic_review_enabled() -> bool:
    """Revisão semântica complementar; desligável para isolar o efeito."""
    return os.getenv("SEMANTIC_REVIEW", "true").strip().lower() in ("1", "true", "yes")
def validator(state: WorkflowState) -> dict[str, Any]:
    """Roda a suíte de verdade e, só se ela passar, complementa com revisão."""
    ctx = RunContext.from_state(state)

    with ctx.telemetry.node("validator", agent_role="validator"):
        report = run_pytest(
            ctx.workspace,
            timeout_s=ctx.test_timeout_s,
            python_bin=os.getenv("URANIUM_TEST_PYTHON"),
        )
        ctx.telemetry.emit_test_run(report)

        semantic: ValidationResult | None = None
        if report.green and semantic_review_enabled():
            try:
                semantic = invoke_structured(
                    ValidationResult,
                    [
                        ("system", SYSTEM_PROMPT),
                        ("user", _build_review_prompt(state, ctx)),
                    ],
                )
            except StructuredOutputError as exc:
                # Falha de conformidade não pode reprovar código que passa nos
                # testes; fica registrada e o veredito segue pela execução.
                ctx.telemetry.emit_error(exc)

    # O LLM só rebaixa. Nunca promove.
    is_valid = report.green and (semantic is None or semantic.is_valid)

    return {
        "test_report": report.model_dump(),
        "is_valid": is_valid,
        "validation_result": semantic.model_dump() if semantic else None,
        "validation_iteration_count": state.get("validation_iteration_count", 0) + 1,
    }


def _build_review_prompt(state: WorkflowState, ctx: RunContext) -> str:
    """Tarefa + diff efetivo, que é o artefato real produzido pelo agente."""
    intent = parse_intent(state)
    diff = ctx.workspace.diff()
    if len(diff) > 20_000:
        diff = diff[:20_000] + "\n[... diff truncado ...]"

    return "\n".join([
        "Tarefa:",
        intent.model_dump_json(indent=2),
        "",
        "Diff aplicado pelo agente (a suíte passou com ele):",
        diff or "(nenhuma alteração)",
    ])

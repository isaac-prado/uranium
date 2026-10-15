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
import re
from typing import Any

from src import config
from src.runtime import RunContext
from src.schemas.intent import StructuredIntentV2, intent_as_text
from src.schemas.validation_result import ValidationResult
from src.state import WorkflowState, parse_intent
from src.structured_llm import StructuredOutputError, invoke_structured
from src.tools.base import truncate
from src.tools.exec import run_pytest, run_python

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
        report = run_pytest(ctx.workspace, timeout_s=ctx.test_timeout_s)
        ctx.telemetry.emit_test_run(report)

        semantic: ValidationResult | None = None
        if report.green and semantic_review_enabled():
            execucoes = _executar_reproducao(state, ctx)
            try:
                semantic = ctx.invoke_structured(
                    ValidationResult,
                    [
                        ("system", SYSTEM_PROMPT),
                        ("user", _build_review_prompt(state, ctx, execucoes)),
                    ],
                )
                # Revisor coerente (decisão 32): aprovar listando critérios não
                # cobertos é contradição; o harness rebaixa, nunca promove.
                coagida = (
                    config.REVIEW_STRICT == "on" and semantic.is_valid and bool(semantic.missing_criteria)
                )
                if coagida:
                    semantic = semantic.model_copy(update={"is_valid": False})
                # O veredito vai à telemetria: na fumaça D de 09/10 o revisor
                # reprovou um patch com a suíte verde e nada registrava o motivo.
                ctx.telemetry.emit_validation(semantic, executions=execucoes, strict_coerced=coagida)
            except StructuredOutputError as exc:
                # Falha de conformidade não pode reprovar código que passa nos
                # testes; fica registrada e o veredito segue pela execução.
                ctx.telemetry.emit_error(exc)

    # Diff vazio não pode ser sucesso. A suíte visível já está verde no
    # commit-base — o teste que discrimina é oculto —, então "testes passam"
    # é satisfeito por não fazer nada. No piloto foi exatamente isso: o
    # agente explorou 10 turnos, não escreveu nada, a suíte passou e o run
    # foi dado como válido com patch.diff de zero byte.
    houve_mudanca = bool(ctx.workspace.changed_files())

    # O LLM só rebaixa. Nunca promove.
    is_valid = report.green and houve_mudanca and (semantic is None or semantic.is_valid)

    # O teto de reprovações vale para o laço "developer diz que terminou,
    # revisor discorda". Quando o developer chegou aqui pelo teto do ciclo
    # (decisão 25), a reprovação é feedback do ponto de checagem, não uma
    # submissão recusada, e não conta.
    submeteu = not str(state.get("stop_reason") or "").startswith("cycle:")

    return {
        "test_report": report.model_dump(),
        "is_valid": is_valid,
        "validation_result": semantic.model_dump() if semantic else None,
        "validation_iteration_count": state.get("validation_iteration_count", 0) + 1,
        # Conta só a reprovação do revisor sobre código verde e alterado, que é
        # o único motivo de volta com teto (ver `route_after_validator`).
        "semantic_rejections": state.get("semantic_rejections", 0)
        + int(
            submeteu
            and report.green and houve_mudanca and semantic is not None and not semantic.is_valid
        ),
    }


_CERCA = re.compile(r"^```([\w+-]*)\s*\n(.*?)\n?```\s*$", re.S)
MAX_SAIDA_EXECUCAO_CHARS = 2_000


def _codigo_python(bloco: str) -> str | None:
    """Conteúdo de um bloco de `reproduction` se for Python (cerca `python` ou sem cerca)."""
    m = _CERCA.match(bloco.strip())
    if not m:
        return bloco.strip()
    linguagem = (m.group(1) or "").lower()
    return m.group(2) if linguagem in ("", "python", "py", "python3") else None


def _executar_reproducao(state: WorkflowState, ctx: RunContext) -> list[dict[str, Any]]:
    """
    Revisor que executa (decisão 29): roda os blocos de reprodução da intent
    v2 no código atual e devolve as saídas reais. Com `REVIEW_EXECUTION=off`,
    ou com intent v1 (sem `reproduction`), não faz nada e o revisor segue
    lendo só o diff, como na coleta principal.
    """
    intent = parse_intent(state)
    if config.REVIEW_EXECUTION != "on" or not isinstance(intent, StructuredIntentV2):
        return []
    saidas: list[dict[str, Any]] = []
    for i, bloco in enumerate(intent.reproduction, 1):
        codigo = _codigo_python(bloco)
        if codigo is None or not codigo.strip():
            saidas.append({"bloco": i, "executado": False, "saida": "(não executado: não é Python)"})
            continue
        saida = run_python(ctx.workspace, codigo, timeout_s=min(60, ctx.test_timeout_s))
        saidas.append({"bloco": i, "executado": True,
                       "saida": truncate(saida, MAX_SAIDA_EXECUCAO_CHARS)})
    return saidas


def _build_review_prompt(
    state: WorkflowState, ctx: RunContext, execucoes: list[dict[str, Any]] | None = None
) -> str:
    """Tarefa + diff efetivo, que é o artefato real produzido pelo agente."""
    intent = parse_intent(state)
    diff = ctx.workspace.diff()
    if len(diff) > 20_000:
        diff = diff[:20_000] + "\n[... diff truncado ...]"

    partes = [
        "Tarefa:",
        intent_as_text(intent),
        "",
        "Diff aplicado pelo agente (a suíte passou com ele):",
        diff or "(nenhuma alteração)",
    ]
    if execucoes:
        partes += ["", "Execução dos exemplos de reprodução sobre o código atual "
                       "(saída real, para comparar com as saídas esperadas da tarefa):"]
        for ex in execucoes:
            partes += [f"[bloco {ex['bloco']}]", ex["saida"]]
    return "\n".join(partes)

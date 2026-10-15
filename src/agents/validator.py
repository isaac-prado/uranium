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
from src.schemas.plan import (
    STATUS_ABANDONADA,
    STATUS_ADIADA,
    STATUS_EM_ANDAMENTO,
    STATUS_FEITA,
    STATUS_PENDENTE,
)
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


# Revisão de sub-tarefa (decisão 33): o mesmo revisor, com a pergunta
# restrita à sub-tarefa corrente do plano.
SYSTEM_PROMPT_SUBTAREFA = """\
Você é o revisor técnico de uma equipe de agentes de IA. O desenvolvedor
trabalhou numa sub-tarefa de um plano. Decida só isto: a sub-tarefa atual está
concluída? Use os critérios dela, a saída real dos exemplos executados e o
diff. Um exemplo que não rodou por falta de contexto (import ou variável de
outro bloco) não prova nada: não conte isso como falha do código.

Retorne JSON com is_valid (true = sub-tarefa concluída), issues, suggestions,
covered_criteria e missing_criteria, restritos a esta sub-tarefa. Não julgue o
resto do plano.
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

        # Planejador (decisão 33): se a tarefa não fechou, confere a sub-tarefa
        # corrente e avança o plano.
        avanco: dict[str, Any] = {}
        if config.PLANNER == "on" and state.get("plan") and not is_valid:
            avanco = _avancar_plano(state, ctx, houve_mudanca=houve_mudanca)
    plano_aberto = avanco.get("subtask_current") is not None or bool(avanco.get("replan_requested"))

    # O teto de reprovações vale para o laço "developer diz que terminou,
    # revisor discorda". Quando o developer chegou aqui pelo teto do ciclo
    # (decisão 25), ou quando o plano ainda tem sub-tarefas (decisão 33), a
    # reprovação é feedback do ponto de checagem, não uma submissão
    # recusada, e não conta.
    submeteu = not str(state.get("stop_reason") or "").startswith("cycle:") and not plano_aberto

    return avanco | {
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


def _executar_reproducao(
    state: WorkflowState, ctx: RunContext, *, indices: list[int] | None = None
) -> list[dict[str, Any]]:
    """
    Revisor que executa (decisão 29): roda os blocos de reprodução da intent
    v2 no código atual e devolve as saídas reais. Com `REVIEW_EXECUTION=off`,
    ou com intent v1 (sem `reproduction`), não faz nada e o revisor segue
    lendo só o diff, como na coleta principal.
    """
    intent = parse_intent(state)
    if config.REVIEW_EXECUTION == "off" or not isinstance(intent, StructuredIntentV2):
        return []
    codigos = {i: _codigo_python(b) for i, b in enumerate(intent.reproduction, 1)}
    acumulado = config.REVIEW_EXECUTION == "cumulative"
    selecionados = (list(codigos) if indices is None
                    else [i for i in indices if i in codigos])
    saidas: list[dict[str, Any]] = []
    for i in selecionados:
        codigo = codigos[i]
        if codigo is None or not codigo.strip():
            saidas.append({"bloco": i, "executado": False, "saida": "(não executado: não é Python)"})
            continue
        if acumulado:
            # Decisão 34: o bloco i roda precedido dos blocos 1..i-1, porque
            # os enunciados encadeiam (o segundo usa o `db` do primeiro).
            anteriores = [codigos[j] for j in range(1, i) if codigos[j] and codigos[j].strip()]
            codigo = "\n\n".join(anteriores + [codigo])
        saida = run_python(ctx.workspace, codigo, timeout_s=min(60, ctx.test_timeout_s))
        saidas.append({"bloco": i, "executado": True, "acumulado": acumulado and i > 1,
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
            rotulo = f"[bloco {ex['bloco']}]" + (" (executado junto com os blocos anteriores)" if ex.get("acumulado") else "")
            partes += [rotulo, ex["saida"]]
    return "\n".join(partes)


# ------------------------------------------------------- plano (decisão 33)


def _proxima_subtarefa(status: list[dict[str, Any]]) -> int | None:
    """Sub-tarefa a atacar: a em andamento; senão a primeira pendente; senão uma adiada."""
    for s in status:
        if s["status"] == STATUS_EM_ANDAMENTO:
            return s["id"]
    for estado in (STATUS_PENDENTE, STATUS_ADIADA):
        for s in status:
            if s["status"] == estado:
                s["status"] = STATUS_EM_ANDAMENTO
                return s["id"]
    return None


def _build_subtask_review_prompt(
    state: WorkflowState, ctx: RunContext, sub: dict[str, Any], execucoes: list[dict[str, Any]]
) -> str:
    intent = parse_intent(state)
    criterios = [intent.acceptance_criteria[i - 1] for i in sub.get("criteria") or []
                 if 1 <= i <= len(intent.acceptance_criteria)]
    diff = ctx.workspace.diff()
    if len(diff) > 20_000:
        diff = diff[:20_000] + "\n[... diff truncado ...]"
    partes = [
        f"Sub-tarefa {sub.get('id')}: {sub.get('title', '')}",
        "O que fazer:", str(sub.get("objective", "")),
        f"Pronto quando: {sub.get('done_when', '')}",
    ]
    if criterios:
        partes += ["", "Critérios desta sub-tarefa:", *(f"- {c}" for c in criterios)]
    partes += ["", "Diff atual do workspace:", diff or "(nenhuma alteração)"]
    if execucoes:
        partes += ["", "Execução dos exemplos desta sub-tarefa sobre o código atual (saída real):"]
        for ex in execucoes:
            rotulo = f"[bloco {ex['bloco']}]" + (" (executado junto com os blocos anteriores)" if ex.get("acumulado") else "")
            partes += [rotulo, ex["saida"]]
    return "\n".join(partes)


def _avancar_plano(state: WorkflowState, ctx: RunContext, *, houve_mudanca: bool) -> dict[str, Any]:
    """
    Confere a sub-tarefa corrente com os blocos de reprodução dela e avança o
    plano: feita → próxima; não feita → mais um ciclo, até o teto, depois
    adiada (uma vez) e abandonada. Plano esgotado com a tarefa aberta →
    pede replanejamento, enquanto houver cota.
    """
    plano = dict(state.get("plan") or {})
    subtasks: list[dict[str, Any]] = list(plano.get("subtasks") or [])
    status = [dict(s) for s in plano.get("status") or []]
    atual = state.get("subtask_current")
    parecer: ValidationResult | None = None

    sub = next((s for s in subtasks if s.get("id") == atual), None)
    linha = next((s for s in status if s.get("id") == atual), None)
    if sub is not None and linha is not None:
        concluida = False
        if houve_mudanca and semantic_review_enabled():
            execucoes = _executar_reproducao(state, ctx, indices=list(sub.get("reproduction") or []))
            try:
                parecer = ctx.invoke_structured(
                    ValidationResult,
                    [("system", SYSTEM_PROMPT_SUBTAREFA),
                     ("user", _build_subtask_review_prompt(state, ctx, sub, execucoes))],
                )
                if config.REVIEW_STRICT == "on" and parecer.is_valid and parecer.missing_criteria:
                    parecer = parecer.model_copy(update={"is_valid": False})
                ctx.telemetry.emit_validation(parecer, executions=execucoes, scope="subtask", subtask=atual)
                concluida = parecer.is_valid
            except StructuredOutputError as exc:
                ctx.telemetry.emit_error(exc)
        linha["ciclos"] = int(linha.get("ciclos", 0)) + 1
        if concluida:
            linha["status"] = STATUS_FEITA
        else:
            teto = config.SUBTASK_MAX_CYCLES * (2 if linha.get("adiada_antes") else 1)
            if linha["ciclos"] >= teto:
                linha["status"] = STATUS_ABANDONADA if linha.get("adiada_antes") else STATUS_ADIADA
                linha["adiada_antes"] = True
            else:
                linha["status"] = STATUS_EM_ANDAMENTO

    proximo = _proxima_subtarefa(status)
    replan = (proximo is None and not plano.get("esgotado")
              and int(state.get("replans", 0)) < config.PLANNER_MAX_REPLANS)
    plano["status"] = status
    if proximo is None and not replan:
        plano["esgotado"] = True
    ctx.telemetry.emit_plan({
        "evento": "avanco", "status": status, "subtask_current": proximo, "replan_requested": replan,
    })
    return {
        "plan": plano,
        "subtask_current": proximo,
        "subtask_review": parecer.model_dump() if (parecer is not None and proximo == atual) else None,
        "replan_requested": replan,
    }

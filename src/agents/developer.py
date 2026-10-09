"""
DeveloperAgent — loop de tool calling sobre o repositório real.

Antes este nó pedia ao LLM que devolvesse blobs de texto com um `file_path`
sugerido, e ninguém jamais executava nada. Agora ele age: lê o repositório,
busca, escreve arquivos e roda testes, num ciclo de turnos limitado por
orçamento. O artefato produzido é o diff do workspace.
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.feedback import DIFF_VAZIO, feedback_de_falha, revisao_reprovada
from src.prompts import AGENT_SYSTEM_PROMPT
from src.runtime import RunContext
from src.state import WorkflowState, parse_intent, parse_test_report, parse_validation

# Mesmo prompt do braço single-agent. A decomposição em papéis do
# orchestration está no grafo, não aqui.
SYSTEM_PROMPT = AGENT_SYSTEM_PROMPT



def _revisao_reprovada(state: WorkflowState) -> str | None:
    """
    O que a revisão semântica disse, quando ela reprovou a tentativa anterior.

    Sem isto o grafo voltava ao developer com a suíte verde e só a lista de
    arquivos modificados: ele não tinha como saber o que corrigir (BACKLOG
    7.2, D4). O conteúdo é do próprio revisor, que é um papel deste braço; a
    moldura (os títulos) mora em `src/feedback.py`, como toda mensagem de
    protocolo, para que nenhum braço tenha texto próprio de feedback.
    """
    revisao = parse_validation(state)
    if revisao is None or revisao.is_valid:
        return None
    return revisao_reprovada(
        issues=revisao.issues,
        missing_criteria=revisao.missing_criteria,
        suggestions=revisao.suggestions,
    )


def _build_prompt(state: WorkflowState) -> str:
    """Monta a instrução do turno, com o feedback de execução se houver."""
    intent = parse_intent(state)
    partes = [
        "Tarefa:",
        intent.model_dump_json(indent=2),
    ]

    report = parse_test_report(state)
    alterados = state.get("changed_files") or []
    if report and not report.green:
        # Mesmo texto e mesmo truncamento que o driver do single-agent
        # entrega (src.feedback.feedback_de_falha) — antes este nó montava
        # o próprio texto, sem usá-la, e divergia (docs/tcc/01-inventario.md,
        # folgas F1 e F2; BACKLOG 7.2, D7).
        partes += ["", feedback_de_falha(report)]
    elif report and not alterados:
        # Mesma mensagem que o driver do single-agent entrega. Sem ela, o
        # developer recebe no retry o prompt idêntico ao da primeira vez e
        # repete o que já fez — aconteceu em 2 dos 5 runs do teste de
        # variância, ambos terminando com patch de zero byte.
        partes += ["", DIFF_VAZIO]
    elif alterados:
        # Suíte verde e houve mudança: o developer recebe só a tarefa, igual
        # ao single-agent — sem "arquivos já modificados", aviso que só
        # existia neste braço (docs/tcc/01-inventario.md, folga F8). A única
        # adição possível é o parecer do revisor semântico quando ele
        # reprovou (D4), que é um papel deste braço e não existe no outro.
        reprovada = _revisao_reprovada(state)
        if reprovada:
            partes += ["", reprovada]

    return "\n".join(partes)


def developer(state: WorkflowState) -> dict[str, Any]:
    """Roda o loop de tool calling até resolver, parar de agir ou estourar orçamento."""
    ctx = RunContext.from_state(state)
    llm = ctx.bound_llm()

    mensagens: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_build_prompt(state)),
    ]

    turno = state.get("turn_count", 0)
    stop_reason = "concluiu"
    resumo = ""

    with ctx.telemetry.node("developer", agent_role="developer"):
        while True:
            motivo = ctx.stop_if_exhausted()
            if motivo:
                stop_reason = f"budget: {motivo}"
                break

            turno = ctx.budget.next_turn()
            ctx.telemetry.set_turn(turno)

            inicio = time.perf_counter()
            ai = llm.invoke(mensagens)
            latencia = int((time.perf_counter() - inicio) * 1000)
            ctx.telemetry.emit_llm_call(ai, latency_ms=latencia, prompt=mensagens)
            mensagens.append(ai)

            if not getattr(ai, "tool_calls", None):
                resumo = str(ai.content)[:2000]
                break

            mensagens.extend(ctx.executar_tool_calls(ai))

    ws = ctx.workspace
    return {
        "changed_files": ws.changed_files(),
        "diff_stat": ws.diffstat(),
        "dev_summary": resumo,
        "turn_count": turno,
        "stop_reason": stop_reason,
    }

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

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from src import config
from src.feedback import (
    DIFF_VAZIO,
    NOTA_DE_CICLO,
    SUBTAREFA_CONCLUIDA_NAO,
    feedback_de_falha,
    memoria_de_trabalho,
    plano_em_andamento,
    revisao_reprovada,
    subtarefa_atual,
)
from src.prompts import AGENT_SYSTEM_PROMPT
from src.runtime import RunContext
from src.schemas.intent import StructuredIntentV2, intent_as_text
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


def _memoria(state: WorkflowState, diff: str) -> str | None:
    """
    Memória de trabalho dos ciclos anteriores, quando a política a liga.

    Lida como atributo do módulo (`config.DEVELOPER_MEMORY`), o mesmo acesso
    que o manifesto usa (src/arms/runner.py), para que o run registre o
    valor que o nó de fato aplicou. No primeiro ciclo não há memória e o
    prompt é idêntico ao de antes da decisão 8 revista (09/10/2026).
    """
    if config.DEVELOPER_MEMORY != "ledger":
        return None
    ciclos = state.get("developer_memory") or []
    if not ciclos:
        return None
    return memoria_de_trabalho(ciclos, diff)


def _subtarefa(state: WorkflowState) -> str | None:
    """
    Sub-tarefa corrente do plano (decisão 33), quando o planejador está
    ligado e ainda há sub-tarefa a atacar. Critérios e blocos vêm da
    intent, copiados pelo índice que o planejador apontou.
    """
    if config.PLANNER != "on":
        return None
    plano = state.get("plan") or {}
    atual = state.get("subtask_current")
    subtasks = plano.get("subtasks") or []
    if not subtasks:
        return None
    partes = [plano_em_andamento(subtasks, plano.get("status") or [])]
    sub = next((s for s in subtasks if s.get("id") == atual), None)
    if sub is not None:
        intent = parse_intent(state)
        criterios = [intent.acceptance_criteria[i - 1] for i in sub.get("criteria") or []
                     if 1 <= i <= len(intent.acceptance_criteria)]
        blocos_intent = intent.reproduction if isinstance(intent, StructuredIntentV2) else []
        blocos = [blocos_intent[i - 1] for i in sub.get("reproduction") or [] if 1 <= i <= len(blocos_intent)]
        posicao = next((k for k, s in enumerate(subtasks, 1) if s.get("id") == atual), 0)
        partes += ["", subtarefa_atual(sub, posicao=posicao, total=len(subtasks),
                                       criterios=criterios, blocos=blocos)]
    return "\n".join(partes)


def _revisao_da_subtarefa(state: WorkflowState) -> str | None:
    """Parecer do revisor sobre a sub-tarefa corrente, quando não a deu por concluída."""
    parecer = state.get("subtask_review")
    if not parecer or parecer.get("is_valid"):
        return None
    return revisao_reprovada(
        issues=list(parecer.get("issues") or []),
        missing_criteria=list(parecer.get("missing_criteria") or []),
        suggestions=list(parecer.get("suggestions") or []),
        cabecalho=SUBTAREFA_CONCLUIDA_NAO,
    )


def _build_prompt(state: WorkflowState, diff: str = "") -> str:
    """
    Monta a instrução do turno: tarefa, memória de trabalho (se houver ciclo
    anterior) e o feedback de execução, nessa ordem — a mesma do single-agent,
    em que o histórico vem antes da mensagem mais recente do driver.
    """
    intent = parse_intent(state)
    if config.DEVELOPER_INPUT == "enunciado+intent":
        # Ablação do refinador (decisões 7 e 16): o enunciado íntegro, a mesma
        # string que o driver entrega ao single-agent, e a intent como anexo.
        partes = [
            str(state.get("raw_request") or ""),
            "",
            "Intenção estruturada:",
            intent_as_text(intent),
        ]
    else:
        partes = [
            "Tarefa:",
            # v1: o JSON de sempre; v2 (decisão 28): markdown com reprodução,
            # saídas esperadas e restrições literais do enunciado.
            intent_as_text(intent),
        ]

    subtarefa = _subtarefa(state)
    if subtarefa:
        partes += ["", subtarefa]

    memoria = _memoria(state, diff)
    if memoria:
        partes += ["", memoria]

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

    parecer = _revisao_da_subtarefa(state)
    if parecer:
        partes += ["", parecer]

    return "\n".join(partes)


def _registro_do_ciclo(
    mensagens: list[BaseMessage], *, ciclo: int, turnos: int, parada: str, nota: str,
    subtarefa: int | None = None,
) -> dict[str, Any]:
    """
    Registro determinístico do que o developer fez neste ciclo, a partir da
    própria conversa: nomes das ferramentas e seus argumentos-chave, e a
    primeira linha do resultado de cada `run_tests`. Nenhum conteúdo de
    arquivo, nenhuma interpretação do harness.
    """
    respostas: dict[str, str] = {}
    for msg in mensagens:
        if isinstance(msg, ToolMessage):
            respostas[str(msg.tool_call_id)] = str(msg.content)

    lidos: list[str] = []
    buscas: list[str] = []
    escritos: list[str] = []
    execucoes_python = 0
    suites: list[dict[str, str]] = []

    def _unico(lista: list[str], item: str) -> None:
        if item and item not in lista:
            lista.append(item)

    for msg in mensagens:
        if not isinstance(msg, AIMessage):
            continue
        for chamada in msg.tool_calls or []:
            nome = chamada.get("name")
            args = chamada.get("args") or {}
            if nome == "read_file":
                _unico(lidos, str(args.get("path", "")))
            elif nome == "search_code":
                _unico(buscas, str(args.get("pattern", "")))
            elif nome in ("write_file", "replace_in_file"):
                _unico(escritos, str(args.get("path", "")))
            elif nome == "run_python":
                execucoes_python += 1
            elif nome == "run_tests":
                alvos = args.get("node_ids") or []
                saida = respostas.get(str(chamada.get("id")), "")
                suites.append({
                    "alvos": ", ".join(str(a) for a in alvos) if alvos else "suíte inteira",
                    "resultado": saida.splitlines()[0] if saida else "",
                })

    return {
        "ciclo": ciclo,
        "turnos": turnos,
        "parada": parada,
        "subtarefa": subtarefa,
        "arquivos_lidos": lidos,
        "buscas": buscas,
        "arquivos_escritos": escritos,
        "execucoes_python": execucoes_python,
        "suites": suites,
        "nota": nota,
    }


def developer(state: WorkflowState) -> dict[str, Any]:
    """Roda o loop de tool calling até resolver, parar de agir ou estourar orçamento."""
    ctx = RunContext.from_state(state)
    llm = ctx.bound_llm()
    ws = ctx.workspace

    memoria_anterior = list(state.get("developer_memory") or [])
    mensagens: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_build_prompt(state, diff=ws.diff())),
    ]
    turnos_no_ciclo = 0

    turno = state.get("turn_count", 0)
    stop_reason = "concluiu"
    resumo = ""

    with ctx.telemetry.node("developer", agent_role="developer"):
        while True:
            motivo = ctx.stop_if_exhausted()
            if motivo:
                stop_reason = f"budget: {motivo}"
                break

            # Ponto de checagem da orquestração (decisão 25, 09/10/2026): ao
            # bater o teto do ciclo o developer volta ao validador, que roda
            # a suíte e a revisão e devolve o veredito com a memória. Não é
            # corte de orçamento: o run continua se ainda houver orçamento.
            teto_ciclo = config.DEVELOPER_CYCLE_MAX_TURNS
            if teto_ciclo and turnos_no_ciclo >= teto_ciclo:
                stop_reason = f"cycle: max_turns_per_cycle ({turnos_no_ciclo} >= {teto_ciclo})"
                # Nota de ciclo (decisão 29): o developer registra o próprio
                # raciocínio antes de perder a conversa. Uma chamada sem
                # ferramentas, contada no orçamento como qualquer turno.
                if config.CYCLE_NOTE == "on" and not ctx.budget.exceeded():
                    turno = ctx.budget.next_turn()
                    ctx.telemetry.set_turn(turno)
                    turnos_no_ciclo += 1
                    mensagens.append(HumanMessage(content=NOTA_DE_CICLO))
                    inicio = time.perf_counter()
                    nota = ctx.bound_llm(tools=False).invoke(mensagens)
                    ctx.telemetry.emit_llm_call(
                        nota, latency_ms=int((time.perf_counter() - inicio) * 1000), prompt=mensagens
                    )
                    mensagens.append(nota)
                    resumo = str(nota.content)[:2000]
                break

            turno = ctx.budget.next_turn()
            ctx.telemetry.set_turn(turno)
            turnos_no_ciclo += 1

            inicio = time.perf_counter()
            ai = llm.invoke(mensagens)
            latencia = int((time.perf_counter() - inicio) * 1000)
            ctx.telemetry.emit_llm_call(ai, latency_ms=latencia, prompt=mensagens)
            mensagens.append(ai)

            if not getattr(ai, "tool_calls", None):
                resumo = str(ai.content)[:2000]
                break

            mensagens.extend(ctx.executar_tool_calls(ai))

        # O registro do ciclo é montado e gravado sempre, em qualquer
        # política: a telemetria conta o que o developer fez por ciclo mesmo
        # quando a memória não volta ao prompt (`DEVELOPER_MEMORY=none`).
        registro = _registro_do_ciclo(
            mensagens,
            ciclo=len(memoria_anterior) + 1,
            turnos=turnos_no_ciclo,
            parada=stop_reason,
            nota=resumo,
            subtarefa=state.get("subtask_current"),
        )
        ctx.telemetry.emit_memory(registro)

    return {
        "changed_files": ws.changed_files(),
        "diff_stat": ws.diffstat(),
        "dev_summary": resumo,
        "developer_memory": memoria_anterior + [registro],
        "turn_count": turno,
        "stop_reason": stop_reason,
    }

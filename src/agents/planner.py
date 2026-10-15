"""
PlannerAgent — fatia a intent em sub-tarefas (decisão 33 do autor, 15/10/2026).

O developer do orquestrado trabalha em ciclos curtos e perde a conversa entre
eles. Nas tarefas médias e grandes isso custava a resolução: o developer
tentava os seis sub-problemas de uma vez, reexplorava a cada ciclo e não
chegava aos arquivos mais distantes (docs/tcc/19-balanco-e-caminhos.md, §4).
O planejador lê a especificação, explora o repositório com ferramentas de
leitura (sem editar nada, em poucos turnos contados no orçamento) e entrega
um plano de sub-tarefas verificáveis. Quando a mudança é uma só, entrega uma
sub-tarefa única: fatiar é decisão dele, não regra do harness.

Aprovado por escrito pelo autor em 15/10/2026 ("Podemos sim seguir com o
planejador fatiando as sub-tarefas, ele precisa de atenção pois será o foco
de todas e precisa de autonomia e conhecimento para saber quando fatiar e
quando prosseguir").
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from pydantic import ValidationError

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from src import config
from src.runtime import RunContext
from src.schemas.intent import StructuredIntentV2, intent_as_text
from src.schemas.plan import (
    STATUS_EM_ANDAMENTO,
    STATUS_PENDENTE,
    Plan,
    Replan,
    Subtask,
    estado_inicial,
    sanear,
)
from src.state import WorkflowState, parse_intent, parse_test_report, parse_validation
from src.structured_llm import StructuredOutputError

FERRAMENTAS_DE_LEITURA = ("list_files", "read_file", "search_code")

SYSTEM_PROMPT = """\
Você é o planejador de uma equipe de agentes de IA que corrige e evolui
software. Você recebe a especificação da tarefa e pode explorar o repositório
com ferramentas de leitura (list_files, read_file, search_code), sem editar
nada e em poucos turnos. Depois você entrega um plano de sub-tarefas para o
desenvolvedor, que trabalha uma sub-tarefa por vez, em ciclos curtos, e perde
a conversa entre os ciclos: cada sub-tarefa precisa ser executável sozinha,
só com o que estiver escrito nela.

Como planejar:
1. Leia a especificação inteira. Localize no repositório onde cada critério
   de aceitação é decidido (arquivo, classe, função). Use as ferramentas para
   confirmar nomes e caminhos; não adivinhe.
2. Decida se vale fatiar. Fatie quando os critérios tocam partes diferentes
   do código ou podem ser verificados separadamente. Não fatie quando a
   mudança é uma só (um lugar, um comportamento): nesse caso entregue uma
   única sub-tarefa.
3. Cada sub-tarefa diz: o que mudar e onde (arquivos e funções confirmados
   pela leitura), quais critérios da especificação ela cobre (índices, a
   partir de 1, na ordem da especificação), quais blocos de reprodução a
   verificam (índices) e como saber que está pronta (done_when, observável
   por execução).
4. Ordene por dependência: a sub-tarefa de que as outras precisam vem antes.
   Uma sub-tarefa tem de caber em cerca de 30 turnos de trabalho; se não
   cabe, divida. No máximo 6 sub-tarefas.
5. Todo critério da especificação precisa estar em alguma sub-tarefa. A
   última pode ser "integração e regressão": rodar a suíte inteira e os
   exemplos completos.
6. Não invente requisitos. Não escreva código. Não proponha editar testes:
   a área de testes é protegida.

Quando terminar de explorar, responda sem chamar ferramentas; o plano será
pedido em seguida, em JSON com rationale e subtasks (id, title, objective,
files, criteria, reproduction, done_when).
"""

PEDIDO_DO_PLANO = (
    "Com base na especificação e no que você leu do repositório, entregue agora "
    "o plano de sub-tarefas. Responda SÓ com um objeto JSON, sem texto em volta, "
    "no formato {\"rationale\": str, \"subtasks\": [{\"id\": int, \"title\": str, "
    "\"objective\": str, \"files\": [str], \"criteria\": [int], \"reproduction\": [int], "
    "\"done_when\": str}]}."
)

PEDIDO_DE_REPLANEJAMENTO = (
    "O plano anterior foi executado e a tarefa ainda não fechou. Abaixo estão o "
    "estado de cada sub-tarefa, o que a revisão final apontou e o resultado da "
    "suíte. Entregue SÓ as sub-tarefas novas necessárias para fechar o que falta, "
    "em JSON (rationale, subtasks). Se nada mais couber num plano, devolva "
    "subtasks vazio."
)


def _plano_do_texto(texto: str, schema: type[Plan]) -> Plan | None:
    """Plano escrito em JSON no texto da resposta, com ou sem cerca de código."""
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", texto, re.S) or re.search(r"(\{.*\})", texto, re.S)
    if not m:
        return None
    try:
        return schema.model_validate(json.loads(m.group(1)))
    except (ValueError, ValidationError):
        return None


def _transcricao(mensagens: list[BaseMessage], limite: int = 24_000) -> str:
    """Exploração do planejador em texto, para a chamada estruturada."""
    partes: list[str] = []
    for msg in mensagens:
        if isinstance(msg, AIMessage):
            for chamada in msg.tool_calls or []:
                partes.append(f"> {chamada.get('name')}({chamada.get('args')})")
            if msg.content:
                partes.append(str(msg.content))
        elif isinstance(msg, ToolMessage):
            partes.append(str(msg.content))
    texto = "\n".join(partes)
    if len(texto) > limite:
        texto = texto[: limite // 2] + "\n[... exploração truncada ...]\n" + texto[-limite // 2 :]
    return texto


def _contexto_de_replanejamento(state: WorkflowState) -> str:
    plano = state.get("plan") or {}
    por_id = {s["id"]: s for s in plano.get("status", [])}
    partes = ["Estado das sub-tarefas do plano anterior:"]
    for sub in plano.get("subtasks", []):
        st = por_id.get(sub["id"], {})
        partes.append(f"- {sub['id']}. {sub.get('title', '')}: {st.get('status', '?')} ({st.get('ciclos', 0)} ciclos)")
    revisao = parse_validation(state)
    if revisao is not None:
        partes += ["", "Revisão final:", f"- aprovada: {revisao.is_valid}"]
        partes += [f"- problema: {x}" for x in revisao.issues]
        partes += [f"- critério não coberto: {x}" for x in revisao.missing_criteria]
    report = parse_test_report(state)
    if report is not None:
        partes += ["", f"Suíte: {'verde' if report.green else 'vermelha'} "
                       f"(passed={report.passed} failed={report.failed} errors={report.errors})"]
        if not report.green and report.stdout_tail:
            partes += [report.stdout_tail[-4_000:]]
    return "\n".join(partes)


def _plano_unico(intent: Any) -> Plan:
    """Plano de uma sub-tarefa só, quando o modelo não conformou ao schema."""
    n_crit = len(getattr(intent, "acceptance_criteria", []) or [])
    n_rep = len(getattr(intent, "reproduction", []) or [])
    return Plan(
        rationale="fallback do harness: o planejador não devolveu um plano válido",
        subtasks=[Subtask(
            id=1, title="Tarefa inteira", objective=str(getattr(intent, "goal", "")),
            files=[], criteria=list(range(1, n_crit + 1)), reproduction=list(range(1, n_rep + 1)),
            done_when="todos os critérios de aceitação verificados por execução",
        )],
    )


def planner(state: WorkflowState) -> dict[str, Any]:
    """Explora o repositório (só leitura) e devolve o plano de sub-tarefas."""
    ctx = RunContext.from_state(state)
    intent = parse_intent(state)
    replanejar = bool(state.get("replan_requested")) and state.get("plan") is not None
    llm = ctx.bound_llm(tools=FERRAMENTAS_DE_LEITURA)

    turno = state.get("turn_count", 0)
    stop_reason = state.get("stop_reason", "") if str(state.get("stop_reason", "")).startswith("budget") else ""
    mensagens: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    cabecalho = ["Especificação da tarefa:", intent_as_text(intent)]
    if replanejar:
        cabecalho += ["", PEDIDO_DE_REPLANEJAMENTO, "", _contexto_de_replanejamento(state)]
    mensagens.append(HumanMessage(content="\n".join(cabecalho)))

    turnos_de_exploracao = 0
    plano: Plan | None = None
    with ctx.telemetry.node("planner", agent_role="planner"):
        # Exploração: só leitura, poucos turnos, cada um contado no orçamento.
        while turnos_de_exploracao < config.PLANNER_MAX_TURNS:
            motivo = ctx.stop_if_exhausted()
            if motivo:
                stop_reason = f"budget: {motivo}"
                break
            turno = ctx.budget.next_turn()
            ctx.telemetry.set_turn(turno)
            turnos_de_exploracao += 1
            inicio = time.perf_counter()
            ai = llm.invoke(mensagens)
            ctx.telemetry.emit_llm_call(ai, latency_ms=int((time.perf_counter() - inicio) * 1000), prompt=mensagens)
            mensagens.append(ai)
            if not getattr(ai, "tool_calls", None):
                break
            mensagens.extend(ctx.executar_tool_calls(ai, permitidas=FERRAMENTAS_DE_LEITURA))

        schema = Replan if replanejar else Plan
        # Plano, primeiro na própria conversa (o modelo acabou de ler os
        # arquivos): JSON em texto, sem ferramentas. Na fumaça de 15/10 a
        # chamada estruturada sobre a transcrição devolveu um plano vazio.
        if not stop_reason and not ctx.budget.exceeded():
            turno = ctx.budget.next_turn()
            ctx.telemetry.set_turn(turno)
            mensagens.append(HumanMessage(content=PEDIDO_DO_PLANO))
            inicio = time.perf_counter()
            resposta = ctx.bound_llm(tools=False).invoke(mensagens)
            ctx.telemetry.emit_llm_call(resposta, latency_ms=int((time.perf_counter() - inicio) * 1000), prompt=mensagens)
            mensagens.append(resposta)
            plano = _plano_do_texto(str(resposta.content), schema)
        # Senão, chamada estruturada sobre a especificação e a exploração.
        if plano is None and not stop_reason and not ctx.budget.exceeded():
            turno = ctx.budget.next_turn()
            ctx.telemetry.set_turn(turno)
            pedido = "\n".join([
                "Especificação da tarefa:", intent_as_text(intent), "",
                *( [PEDIDO_DE_REPLANEJAMENTO, "", _contexto_de_replanejamento(state), ""] if replanejar else []),
                "Exploração do repositório (ferramentas de leitura e o que devolveram):",
                _transcricao(mensagens) or "(nenhuma)", "",
                PEDIDO_DO_PLANO,
            ])
            try:
                plano = ctx.invoke_structured(schema, [("system", SYSTEM_PROMPT), ("user", pedido)])
            except StructuredOutputError as exc:
                ctx.telemetry.emit_error(exc)
                plano = None

        if plano is None:
            plano = Replan(subtasks=[]) if replanejar else _plano_unico(intent)
        n_crit = len(intent.acceptance_criteria or [])
        n_rep = len(intent.reproduction) if isinstance(intent, StructuredIntentV2) else 0
        plano = sanear(plano, n_criterios=n_crit, n_reproducao=n_rep, maximo=config.PLANNER_MAX_SUBTASKS)
        if not plano.subtasks and not replanejar:
            plano = _plano_unico(intent)

        if replanejar:
            anterior = dict(state["plan"])
            base = len(anterior["subtasks"])
            novos = []
            for s in plano.subtasks:
                s.id = base + s.id
                novos.append(s.model_dump())
            subtasks = list(anterior["subtasks"]) + novos
            status = list(anterior["status"]) + [
                {"id": s["id"], "status": STATUS_PENDENTE, "ciclos": 0, "adiada_antes": False} for s in novos
            ]
            replans = int(state.get("replans", 0)) + 1
        else:
            subtasks = [s.model_dump() for s in plano.subtasks]
            status = estado_inicial(plano)
            replans = int(state.get("replans", 0))

        atual = next((s["id"] for s in status if s["status"] == STATUS_PENDENTE), None)
        if atual is not None:
            for s in status:
                if s["id"] == atual:
                    s["status"] = STATUS_EM_ANDAMENTO
        registro = {
            "evento": "replanejamento" if replanejar else "plano",
            "rationale": plano.rationale,
            "subtasks": subtasks,
            "status": status,
            "turnos_de_exploracao": turnos_de_exploracao,
            "subtask_current": atual,
            "replans": replans,
        }
        ctx.telemetry.emit_plan(registro)

    out: dict[str, Any] = {
        "plan": {"rationale": plano.rationale, "subtasks": subtasks, "status": status},
        "subtask_current": atual,
        "subtask_review": None,
        "replan_requested": False,
        "replans": replans,
        "turn_count": turno,
    }
    if stop_reason:
        out["stop_reason"] = stop_reason
    return out

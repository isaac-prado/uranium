"""
Braço A2 — agente único, sem papéis especializados.

Um grafo de dois nós (`single_agent` ↔ `driver`) compilado com o MESMO
StateGraph, as mesmas ferramentas, a mesma telemetria e o mesmo circuit
breaker do braço B. A única coisa que difere é a topologia.

Sobre justiça de prompt: o system prompt daqui é a união das *capacidades*
concedidas ao braço B — mesma lista de ferramentas, mesmas restrições de
formato, mesmo texto de critérios — SEM a decomposição em papéis e fases.
Empobrecer este prompt transformaria o A2 em espantalho e o estudo passaria
a medir qualidade de prompt em vez de topologia.
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from src.arms.driver import DeterministicDriver, DriverAction, DriverPolicy
from src.runtime import RunContext
from src.state import WorkflowState, parse_intent
from src.tools.exec import run_pytest

SYSTEM_PROMPT = """\
Você é um engenheiro de software resolvendo uma tarefa de manutenção num
repositório Python real.

Você tem ferramentas para inspecionar e modificar o repositório. Use-as:
não descreva a mudança, faça a mudança.

Ferramentas disponíveis: list_files, read_file, search_code, write_file,
replace_in_file, run_python, run_tests.

Restrições:
- Arquivos de teste e de configuração são protegidos: a escrita será recusada.
  Resolva o problema no código de produção.
- write_file recebe o conteúdo COMPLETO do arquivo; para editar arquivo
  existente prefira replace_in_file, porque reescrever arquivo grande não
  cabe no limite de saída.
- A suíte de testes já está verde antes da sua mudança: run_tests sozinho
  NÃO confirma que você resolveu o problema. Verifique com run_python,
  reproduzindo o caso descrito na tarefa.
- Não altere comportamento não relacionado à tarefa.
- Quando terminar, responda em texto com um resumo do que mudou.
"""

MAX_TOOL_CALLS_POR_TURNO = 8

def _spec(state: WorkflowState) -> str:
    """A especificação inteira, entregue de uma vez pelo driver."""
    return "Tarefa:\n" + parse_intent(state).model_dump_json(indent=2)


def _executar_ferramentas(ctx: RunContext, ai: Any) -> list[ToolMessage]:
    """Aceita todo patch proposto, sem revisão — é a política do driver."""
    por_nome = ctx.tool_by_name
    respostas: list[ToolMessage] = []
    for chamada in (ai.tool_calls or [])[:MAX_TOOL_CALLS_POR_TURNO]:
        ferramenta = por_nome.get(chamada["name"])
        conteudo = (
            str(ferramenta.invoke(chamada["args"]))
            if ferramenta is not None
            else f"ERRO: ferramenta desconhecida {chamada['name']!r}. "
                 f"Disponíveis: {', '.join(sorted(por_nome))}."
        )
        respostas.append(ToolMessage(content=conteudo, tool_call_id=chamada["id"]))
    return respostas


def build_a2_graph(policy: DriverPolicy | None = None):
    """
    Compila o grafo do braço A2.

    START -> single_agent -> [driver | END]
    driver -> [single_agent | END]

    `agent_role` fica nulo na telemetria: é o campo que, no dado bruto,
    distingue este braço do B.
    """
    driver = DeterministicDriver(policy)

    def single_agent(state: WorkflowState) -> dict[str, Any]:
        """Um turno do agente único: pensa e, se quiser, usa ferramentas."""
        ctx = RunContext.from_state(state)
        mensagens = ctx.conversation

        if not mensagens:
            mensagens.extend([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=driver.mensagem_inicial(_spec(state))),
            ])

        # agent_role=None: o braço A2 não tem papéis especializados
        with ctx.telemetry.node("single_agent", agent_role=None):
            motivo = ctx.stop_if_exhausted()
            if motivo:
                return {"stop_reason": f"budget: {motivo}", "turn_count": ctx.budget.turn,
                        "agiu_no_turno": False}

            turno = ctx.budget.next_turn()
            ctx.telemetry.set_turn(turno)

            inicio = time.perf_counter()
            ai = ctx.bound_llm().invoke(mensagens)
            ctx.telemetry.emit_llm_call(ai, latency_ms=int((time.perf_counter() - inicio) * 1000))
            mensagens.append(ai)

            pediu_ferramenta = bool(getattr(ai, "tool_calls", None))
            if pediu_ferramenta:
                mensagens.extend(_executar_ferramentas(ctx, ai))

        return {
            "agiu_no_turno": pediu_ferramenta,
            "turn_count": turno,
            "dev_summary": "" if pediu_ferramenta else str(ai.content)[:2000],
            "stop_reason": "",
        }

    def driver_node(state: WorkflowState) -> dict[str, Any]:
        """O operador: roda a suíte e devolve stderr cru, ou encerra."""
        ctx = RunContext.from_state(state)

        with ctx.telemetry.node("driver", agent_role=None):
            report = run_pytest(ctx.workspace, timeout_s=ctx.test_timeout_s)
            ctx.telemetry.emit_test_run(report)
            alterados = ctx.workspace.changed_files()
            decisao = driver.apos_turno(report, houve_mudanca=bool(alterados))

            if decisao.action is DriverAction.CONTINUAR:
                ctx.conversation.append(HumanMessage(content=decisao.feedback))

        concluiu = decisao.action is DriverAction.ENCERRAR_VERDE
        return {
            "test_report": report.model_dump(),
            "is_valid": concluiu,
            "changed_files": alterados,
            "diff_stat": ctx.workspace.diffstat(),
            "stop_reason": "tests_pass" if concluiu else "",
        }

    def rotear_apos_agente(state: WorkflowState) -> str:
        """Sem tool call, o agente parou de agir: hora do driver rodar a suíte."""
        if state.get("stop_reason", "").startswith("budget"):
            return END
        return "single_agent" if state.get("agiu_no_turno") else "driver"

    def rotear_apos_driver(state: WorkflowState) -> str:
        return END if state.get("is_valid") else "single_agent"

    builder = StateGraph(WorkflowState)
    builder.add_node("single_agent", single_agent)
    builder.add_node("driver", driver_node)
    builder.add_edge(START, "single_agent")
    builder.add_conditional_edges(
        "single_agent", rotear_apos_agente,
        {"single_agent": "single_agent", "driver": "driver", END: END},
    )
    builder.add_conditional_edges(
        "driver", rotear_apos_driver, {"single_agent": "single_agent", END: END},
    )
    return builder.compile()

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

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from src.runtime import RunContext
from src.state import WorkflowState, parse_intent, parse_test_report

SYSTEM_PROMPT = """\
Você é um engenheiro de software resolvendo uma tarefa de manutenção num
repositório Python real.

Você tem ferramentas para inspecionar e modificar o repositório. Use-as:
não descreva a mudança, faça a mudança.

Método esperado:
1. Localize o código relevante com search_code antes de ler arquivos inteiros.
2. Leia apenas os trechos necessários (read_file aceita faixa de linhas).
3. Aplique a correção com write_file, passando o conteúdo COMPLETO do arquivo.
4. Rode run_tests para verificar. Se falhar, leia a saída e corrija.

Restrições:
- Arquivos de teste e de configuração são protegidos: a escrita será recusada.
  Resolva o problema no código de produção.
- Não altere comportamento não relacionado à tarefa.
- Quando a suíte estiver verde e a tarefa resolvida, responda em texto com um
  resumo curto do que mudou e pare de chamar ferramentas.
"""

MAX_TOOL_CALLS_POR_TURNO = 8


def _build_prompt(state: WorkflowState) -> str:
    """Monta a instrução do turno, com o feedback de execução se houver."""
    intent = parse_intent(state)
    partes = [
        "Tarefa:",
        intent.model_dump_json(indent=2),
    ]

    report = parse_test_report(state)
    if report and not report.green:
        partes += [
            "",
            "A suíte falhou na tentativa anterior. Saída do pytest:",
            report.stdout_tail,
        ]
    elif state.get("changed_files"):
        partes += ["", f"Arquivos já modificados: {', '.join(state['changed_files'])}"]

    return "\n".join(partes)


def _executar_ferramentas(ctx: RunContext, ai: AIMessage) -> list[ToolMessage]:
    """Executa as tool calls pedidas e devolve as respostas."""
    respostas: list[ToolMessage] = []
    por_nome = ctx.tool_by_name

    for chamada in (ai.tool_calls or [])[:MAX_TOOL_CALLS_POR_TURNO]:
        ferramenta = por_nome.get(chamada["name"])
        if ferramenta is None:
            conteudo = (
                f"ERRO: ferramenta desconhecida {chamada['name']!r}. "
                f"Disponíveis: {', '.join(sorted(por_nome))}."
            )
        else:
            conteudo = str(ferramenta.invoke(chamada["args"]))
        respostas.append(ToolMessage(content=conteudo, tool_call_id=chamada["id"]))

    return respostas
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
            ctx.telemetry.emit_llm_call(ai, latency_ms=latencia)
            mensagens.append(ai)

            if not getattr(ai, "tool_calls", None):
                resumo = str(ai.content)[:2000]
                break

            mensagens.extend(_executar_ferramentas(ctx, ai))

    ws = ctx.workspace
    return {
        "changed_files": ws.changed_files(),
        "diff_stat": ws.diffstat(),
        "dev_summary": resumo,
        "turn_count": turno,
        "stop_reason": stop_reason,
    }

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

from src.feedback import DIFF_VAZIO
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
3. Aplique a correção com replace_in_file, substituindo o trecho exato. Use
   write_file (conteúdo COMPLETO) apenas para arquivo novo ou pequeno —
   reescrever arquivo grande não cabe no limite de saída.
4. Verifique com run_python, reproduzindo o caso descrito na tarefa. A suíte
   de testes já está verde antes da sua mudança, então run_tests sozinho NÃO
   confirma que você resolveu o problema — ele serve para checar regressão.
5. Rode run_tests ao final para garantir que nada quebrou.

Restrições:
- Arquivos de teste e de configuração são protegidos: a escrita será recusada.
  Resolva o problema no código de produção.
- Não altere comportamento não relacionado à tarefa.
- Quando a suíte estiver verde e a tarefa resolvida, responda em texto com um
  resumo curto do que mudou e pare de chamar ferramentas.
"""



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
        partes += [
            "",
            "A suíte falhou na tentativa anterior. Saída do pytest:",
            report.stdout_tail,
        ]
    elif report and not alterados:
        # Mesma mensagem que o driver do single-agent entrega. Sem ela, o
        # developer recebe no retry o prompt idêntico ao da primeira vez e
        # repete o que já fez — aconteceu em 2 dos 5 runs do teste de
        # variância, ambos terminando com patch de zero byte.
        partes += ["", DIFF_VAZIO]
    elif alterados:
        partes += ["", f"Arquivos já modificados: {', '.join(alterados)}"]

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
            ctx.telemetry.emit_llm_call(ai, latency_ms=latencia)
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

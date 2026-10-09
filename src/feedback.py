"""
Mensagens de protocolo entregues ao agente, idênticas nos dois braços.

Ficam aqui, e não embutidas em cada braço, porque são a fronteira exata
entre "informar o protocolo" e "fazer engenharia pelo agente". Um braço
receber uma dica que o outro não recebe contamina a comparação, e com o
texto duplicado a divergência acontece sem ninguém notar — foi o que houve:
o driver do single-agent avisava sobre diff vazio e o loop do orchestration
não, e dois runs terminaram sem escrever nada por falta desse aviso. O
mesmo aconteceu com o texto de "a suíte falhou" (docs/tcc/01-inventario.md,
folgas F1 e F2): cada braço escrevia o próprio texto, com truncamento
próprio, e as cópias divergiram sem que ninguém notasse.

Nada aqui pode apontar arquivo, função ou forma de resolver.
"""

from __future__ import annotations

from typing import Any

from src.schemas.test_report import TestReport
from src.tools.base import truncate

# Teto do diff que entra na memória de trabalho do developer. É o mesmo
# teto com que o revisor semântico vê o diff (src/agents/validator.py):
# os dois papéis olham o mesmo artefato pelo mesmo recorte. Vai ao
# manifesto em `orchestration_policy.developer_memory_diff_max_chars`.
MEMORIA_DIFF_MAX_CHARS = 20_000

# A suíte visível já está verde no commit-base — o teste que discrimina é
# oculto. Sem este aviso, "não fazer nada" satisfaz o critério de parada e o
# agente encerra convencido de ter terminado.
DIFF_VAZIO = (
    "A suíte passou, mas nenhum arquivo foi modificado — ela já estava verde "
    "antes de você começar, então passar nela não confirma nada. Aplique a "
    "correção do problema descrito na tarefa e verifique com run_python."
)


def suite_falhou(saida: str) -> str:
    """Devolve o texto cru recebido. Resumir seria engenharia do harness."""
    return f"A suíte falhou.\n\n{saida}"


def feedback_de_falha(report: TestReport) -> str:
    """
    Mensagem de falha da suíte a partir do `TestReport`, igual nos dois braços.

    Usa `report.stdout_tail`, que já sai truncado pela FERRAMENTA que roda a
    suíte (`run_pytest` -> `truncate(stdout, MAX_TOOL_OUTPUT_CHARS)`, 8.000
    caracteres, cabeça 2/3 + cauda 1/3 — src/tools/exec.py e
    src/tools/base.py). Nenhum braço trunca de novo por conta própria: um
    corte adicional aqui seria a folga F2 de volta, com outro número.
    """
    return suite_falhou(report.stdout_tail)


def revisao_reprovada(
    *, issues: list[str], missing_criteria: list[str], suggestions: list[str]
) -> str:
    """
    Parecer do revisor semântico devolvido ao developer, quando ele reprovou
    uma mudança com a suíte verde (BACKLOG 7.2, D4).

    Só o braço orchestration tem revisor, então só ele recebe esta mensagem —
    a assimetria é a topologia, não o texto. O que mora aqui é a moldura (os
    títulos); o conteúdo é do próprio revisor, que é um papel do braço. O
    harness não acrescenta diagnóstico nem sugestão própria.
    """
    partes = ["A suíte passou, mas a revisão reprovou a mudança."]
    for titulo, itens in (
        ("Problemas apontados", issues),
        ("Critérios não cobertos", missing_criteria),
        ("Sugestões do revisor", suggestions),
    ):
        if itens:
            partes += ["", f"{titulo}:", *(f"- {item}" for item in itens)]
    return "\n".join(partes)


def memoria_de_trabalho(ciclos: list[dict[str, Any]], diff: str) -> str:
    """
    Memória de trabalho do developer do orchestration, entregue a cada
    reentrada no nó (decisão 8 do autor, revista em 09/10/2026).

    Até 09/10 o developer voltava ao nó sem memória nenhuma: a conversa era
    reconstruída do zero a cada ciclo de validação, e ele não sabia que foi
    ele quem editou os arquivos que encontrava no disco. Na fumaça D ele
    submeteu com a suíte verde, foi reprovado pelo revisor, voltou sem saber
    o que tinha feito e quebrou 29 testes refazendo.

    O conteúdo é o registro determinístico do que o próprio developer fez
    em cada ciclo (o que leu, buscou, escreveu e executou, e a nota com que
    encerrou) mais o diff atual do workspace, isto é, o que ele mesmo já
    mudou. Nada é escrito pelo harness além dos títulos: nenhum diagnóstico,
    nenhuma sugestão, nenhum apontamento de arquivo ou solução. Só o braço
    orchestration reentra no developer, então só ele recebe esta mensagem;
    o single-agent carrega a conversa inteira e não precisa dela.
    """
    partes = ["Memória de trabalho (ciclos anteriores deste run):"]
    for ciclo in ciclos:
        partes += [
            "",
            f"Ciclo {ciclo.get('ciclo')}: {ciclo.get('turnos', 0)} turnos, "
            f"encerrado por: {ciclo.get('parada', '')}",
        ]
        for titulo, chave in (
            ("Arquivos lidos", "arquivos_lidos"),
            ("Buscas", "buscas"),
            ("Arquivos escritos", "arquivos_escritos"),
        ):
            itens = ciclo.get(chave) or []
            if itens:
                partes.append(f"- {titulo}: {', '.join(itens)}")
        partes.append(f"- Execuções de run_python: {ciclo.get('execucoes_python', 0)}")
        suites = ciclo.get("suites") or []
        if suites:
            partes.append(f"- Suítes executadas: {len(suites)}")
            for suite in suites:
                partes.append(f"  - {suite.get('alvos', '')}: {suite.get('resultado', '')}")
        else:
            partes.append("- Suítes executadas: 0")
        nota = (ciclo.get("nota") or "").strip()
        if nota:
            partes.append(f"- Nota ao encerrar: {nota}")
    partes += [
        "",
        "Diff atual do workspace (o que você já mudou):",
        truncate(diff, MEMORIA_DIFF_MAX_CHARS) if diff else "(nenhuma alteração)",
    ]
    return "\n".join(partes)

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

from src.schemas.test_report import TestReport

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

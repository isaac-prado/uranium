"""
Mensagens de protocolo entregues ao agente, idênticas nos dois braços.

Ficam aqui, e não embutidas em cada braço, porque são a fronteira exata
entre "informar o protocolo" e "fazer engenharia pelo agente". Um braço
receber uma dica que o outro não recebe contamina a comparação, e com o
texto duplicado a divergência acontece sem ninguém notar — foi o que houve:
o driver do single-agent avisava sobre diff vazio e o loop do orchestration
não, e dois runs terminaram sem escrever nada por falta desse aviso.

Nada aqui pode apontar arquivo, função ou forma de resolver.
"""

from __future__ import annotations

# A suíte visível já está verde no commit-base — o teste que discrimina é
# oculto. Sem este aviso, "não fazer nada" satisfaz o critério de parada e o
# agente encerra convencido de ter terminado.
DIFF_VAZIO = (
    "A suíte passou, mas nenhum arquivo foi modificado — ela já estava verde "
    "antes de você começar, então passar nela não confirma nada. Aplique a "
    "correção do problema descrito na tarefa e verifique com run_python."
)


def suite_falhou(saida: str) -> str:
    """Devolve o stderr cru. Resumir seria engenharia do harness."""
    return f"A suíte falhou.\n\n{saida}"

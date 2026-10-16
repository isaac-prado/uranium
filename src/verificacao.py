"""
Verificação determinística das saídas esperadas (decisões 35 a 37 do autor,
15/10/2026, rodada 5).

Na rodada 4 a revisão de sub-tarefa, feita pelo modelo, reprovou 68 de 81
vezes e a esteira de sub-tarefas quase não andou (docs/tcc/20-rodada-4.md,
§3). Aqui o veredito da sub-tarefa deixa de ser opinião: os blocos de
reprodução que o planejador apontou para a sub-tarefa rodam (acumulados,
decisão 34) e a saída real é comparada, por texto, com as saídas esperadas
que ele apontou. Encontrada ou não encontrada; sem interpretação.

A comparação é tolerante de propósito, porque as saídas esperadas vêm
copiadas do enunciado (intent v2) e nem sempre são literais: espaços e
quebras de linha (reais ou escritas como `\\n`) colapsam, `...` separa
pedaços que precisam todos aparecer, o que vem depois de `#` numa linha vale
sozinho (`print(x)  # 4`), e linhas de prosa que não cabem nessa regra
(comando de shell, tabela, cerca de código) não contam. Uma saída esperada
cuja execução não chegou a compilar (bloco copiado com erro de sintaxe) é
"não verificável", nunca "não encontrada": na calibração sobre a rodada 4
(docs/tcc/21-rodada-5.md, §2), tratar isso como reprovação derrubaria runs
que o oráculo aprovou.
"""

from __future__ import annotations

import re
from typing import Any

ENCONTRADA = "encontrada"
NAO_ENCONTRADA = "nao_encontrada"
NAO_VERIFICAVEL = "nao_verificavel"

# O trecho não chegou a rodar: o erro é do bloco copiado, não do código.
_NAO_COMPILOU = re.compile(r"\b(SyntaxError|IndentationError)\b")

# Linhas de uma saída esperada que não são saída: cerca de código, comando
# de shell, entrada de REPL, linha de tabela markdown.
_PREFIXOS_IGNORADOS = ("```", "$ ", ">>> ", "|")

# Tamanho mínimo de um pedaço comparável: um caractere só ("2", "]") casa
# com quase qualquer saída e não prova nada.
_PEDACO_MINIMO = 2


def normalizar(texto: str) -> str:
    """Quebras de linha reais ou escritas (`\\n`) e espaços repetidos viram um espaço."""
    return " ".join(str(texto).replace("\r\n", "\n").replace("\\n", " ").split())


def _alternativas(linha: str) -> list[list[str]] | None:
    """
    Para uma linha da saída esperada, as alternativas de pedaços que a
    satisfazem: a linha inteira ou, quando há `#`, só o que vem depois
    (o enunciado escreve `print(x)  # 4`); `...` divide em pedaços que
    precisam todos aparecer. None quando a linha não é comparável.
    """
    t = linha.strip()
    if not t or t.startswith(_PREFIXOS_IGNORADOS):
        return None
    candidatas = [t]
    if "#" in t:
        depois = t.split("#", 1)[1].strip()
        if depois:
            candidatas.append(depois)
    alternativas: list[list[str]] = []
    for c in candidatas:
        pedacos = [normalizar(p) for p in c.split("...")]
        pedacos = [p for p in pedacos if len(p) >= _PEDACO_MINIMO]
        if pedacos:
            alternativas.append(pedacos)
    return alternativas or None


def saida_contem(esperada: str, saida: str) -> bool | None:
    """
    True se toda linha comparável da saída esperada aparece na saída real;
    False se alguma falta; None quando nenhuma linha é comparável.
    """
    real = normalizar(saida)
    vereditos: list[bool] = []
    for linha in str(esperada).split("\n"):
        alternativas = _alternativas(linha)
        if alternativas is None:
            continue
        vereditos.append(any(all(p in real for p in pedacos) for pedacos in alternativas))
    if not vereditos:
        return None
    return all(vereditos)


def bloco_nao_compilou(saida: str) -> bool:
    """A execução parou antes de rodar o bloco (erro de sintaxe no trecho)."""
    return bool(_NAO_COMPILOU.search(str(saida)))


def comparar_saidas(
    esperadas: list[tuple[int, str]], execucoes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Compara cada saída esperada (índice na intent, texto) com a saída real
    das execuções dos blocos (formato de `validator._executar_reproducao`).

    Estados: `encontrada`; `nao_encontrada` (todo bloco do conjunto rodou e
    compilou, e o texto não apareceu); `nao_verificavel` (nenhum bloco
    executou, algum bloco do conjunto não rodou ou não compilou e o texto
    não apareceu, ou a saída esperada não tem linha comparável). Bloco que
    não rodou (não é Python, ou não compila com a decisão 42 ligada) conta
    como quebrado: a saída esperada pode ser justamente a dele (fumaça da
    rodada 6, sqlite-utils-0003: blocos de shell apontados com a saída da
    CLI saíam "NÃO encontrada").
    """
    executadas = [e for e in execucoes if e.get("executado")]
    saida = "\n".join(str(e.get("saida", "")) for e in executadas)
    algum_quebrado = (any(bloco_nao_compilou(str(e.get("saida", ""))) for e in executadas)
                      or any(not e.get("executado") for e in execucoes))
    resultado: list[dict[str, Any]] = []
    for indice, texto in esperadas:
        contem = saida_contem(texto, saida) if executadas else None
        if contem is None or (contem is False and algum_quebrado):
            estado = NAO_VERIFICAVEL
        else:
            estado = ENCONTRADA if contem else NAO_ENCONTRADA
        resultado.append({"indice": int(indice), "esperada": str(texto), "estado": estado})
    return resultado


def verificaveis(comparacoes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in comparacoes if c.get("estado") != NAO_VERIFICAVEL]


def faltantes(comparacoes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in comparacoes if c.get("estado") == NAO_ENCONTRADA]

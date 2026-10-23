"""
Leitura determinística do enunciado (`statement.md`, que chega ao grafo como
`raw_request`) pelo validador. Rodada 8 (decisão 48, 22/10/2026):

- `reparar_blocos`: conserta a cópia que o refinador fez dos blocos de
  reprodução (cerca de markdown perdida dentro do bloco; bloco que não compila
  trocado pelo bloco Python mais parecido do enunciado). Na rodada 7, 7 dos 23
  blocos que não compilavam eram cópias deturpadas de blocos válidos do
  enunciado, e sem bloco executado o revisor aprovava às cegas.
- `pares_esperados` / `esperado_do_bloco`: amarra cada bloco Python à "saída
  esperada" que o enunciado escreve logo depois dele (bloco sem cerca precedido
  de uma linha com "esperada"; "hoje"/"atual" é o comportamento com o bug e
  fica de fora), para o revisor receber, por bloco e por linha, encontrada /
  NÃO encontrada na saída real daquele bloco.

O developer não lê este módulo: continua recebendo só a intent.
"""

from __future__ import annotations

import re
from typing import Any

from src.verificacao import ENCONTRADA, NAO_ENCONTRADA, NAO_VERIFICAVEL, saida_contem

_CERCA = re.compile(r"```([\w+-]*)[ \t]*\n(.*?)```", re.S)
_CERCA_ABERTURA = re.compile(r"^```[\w+-]*[ \t]*\n")
_LINGUAGENS_PYTHON = ("python", "py", "python3")
_LINGUAGENS_SAIDA = ("", "text", "txt", "console", "output")
_PISTA_ESPERADA = re.compile(r"esperad", re.I)
_PISTA_BUG = re.compile(r"\b(hoje|atual|atualmente|antes)\b", re.I)
SIMILARIDADE_MINIMA = 0.5


def _ultima_frase_do_paragrafo(texto: str) -> str:
    """Última frase do último parágrafo de `texto` (o que anuncia o bloco que vem a seguir)."""
    paragrafos = [p for p in re.split(r"\n\s*\n", texto) if p.strip()]
    if not paragrafos:
        return ""
    paragrafo = " ".join(paragrafos[-1].split())
    frases = [f for f in re.split(r"(?<=[.!?])\s+", paragrafo) if f.strip()]
    return frases[-1] if frases else paragrafo


def blocos(enunciado: str) -> list[tuple[str, str, str]]:
    """(linguagem, corpo, frase que anuncia o bloco) de cada bloco cercado."""
    saida: list[tuple[str, str, str]] = []
    pos = 0
    for m in _CERCA.finditer(enunciado):
        pista = _ultima_frase_do_paragrafo(enunciado[pos:m.start()])
        saida.append((m.group(1).lower(), m.group(2).rstrip("\n"), pista))
        pos = m.end()
    return saida


def blocos_python(enunciado: str) -> list[str]:
    return [corpo for lingua, corpo, _ in blocos(enunciado) if lingua in _LINGUAGENS_PYTHON]


def sem_cercas(texto: str) -> str:
    """Tira a cerca de markdown que o refinador às vezes copia para dentro do bloco."""
    t = texto.strip()
    m = _CERCA_ABERTURA.match(t)
    if m:
        t = t[m.end():]
    if t.rstrip().endswith("```"):
        t = t.rstrip()[:-3]
    return t.strip("\n")


def compila(codigo: str) -> bool:
    try:
        compile(codigo, "<bloco>", "exec")
    except SyntaxError:
        return False
    return True


def _tokens(texto: str) -> set[str]:
    return set(re.findall(r"\w+|[^\w\s]", texto))


def similaridade(a: str, b: str) -> float:
    """Jaccard sobre tokens; 1,0 é texto igual, 0,0 é nada em comum."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def bloco_mais_parecido(bloco: str, candidatos: list[str], minimo: float = SIMILARIDADE_MINIMA) -> str | None:
    if not candidatos:
        return None
    melhor = max(candidatos, key=lambda c: similaridade(bloco, c))
    return melhor if similaridade(bloco, melhor) >= minimo else None


def reparar_blocos(codigos: dict[int, str | None], enunciado: str) -> tuple[dict[int, str | None], dict[int, str]]:
    """
    Conserta cada bloco Python copiado pelo refinador. Devolve os blocos e,
    por índice, a origem do conserto: "cerca" (cerca removida) ou "enunciado"
    (bloco trocado pelo do enunciado porque não compilava). Bloco que já
    compila e não tem cerca não é tocado; bloco que não compila e não tem
    parecido no enunciado fica como está.
    """
    validos = [b for b in blocos_python(enunciado) if compila(b)]
    novos: dict[int, str | None] = dict(codigos)
    fontes: dict[int, str] = {}
    for i, codigo in codigos.items():
        if not codigo or not codigo.strip():
            continue
        limpo = sem_cercas(codigo)
        if limpo != codigo.strip():
            fontes[i] = "cerca"
        if compila(limpo):
            novos[i] = limpo
            continue
        parecido = bloco_mais_parecido(limpo, validos)
        if parecido is not None:
            novos[i] = parecido
            fontes[i] = "enunciado"
        else:
            novos[i] = limpo
    return novos, fontes


def pares_esperados(enunciado: str) -> list[tuple[str, str]]:
    """(bloco Python, saída esperada escrita logo depois dele) para cada par que o enunciado traz."""
    pares: list[tuple[str, str]] = []
    ultimo_python: str | None = None
    for lingua, corpo, pista in blocos(enunciado):
        if lingua in _LINGUAGENS_PYTHON:
            ultimo_python = corpo
            continue
        if (lingua in _LINGUAGENS_SAIDA and ultimo_python is not None
                and _PISTA_ESPERADA.search(pista) and not _PISTA_BUG.search(pista)):
            pares.append((ultimo_python, corpo))
    return pares


def _contido(parte: str, todo: str) -> float:
    """Fração dos tokens de `parte` presentes em `todo` (1,0 quando `parte` é um pedaço de `todo`)."""
    tp, tt = _tokens(parte), _tokens(todo)
    return len(tp & tt) / len(tp) if tp else 0.0


def exemplo_do_bloco(codigo: str | None, enunciado: str) -> int | None:
    """
    Índice (1-based) do bloco Python do enunciado de que `codigo` é cópia ou
    pedaço: o mais parecido entre TODOS os blocos Python do enunciado, tenham
    ou não saída esperada, se a parecença (Jaccard ≥ 0,5) ou a contenção
    (≥ 0,8 dos tokens do bloco estão no exemplo) bastar. Escolher entre todos
    evita amarrar um exemplo sem saída esperada ao exemplo vizinho.
    """
    if not codigo or not codigo.strip():
        return None
    exemplos = blocos_python(enunciado)
    if not exemplos:
        return None
    melhor = max(range(len(exemplos)), key=lambda k: max(similaridade(codigo, exemplos[k]), _contido(codigo, exemplos[k])))
    pontuacao = max(similaridade(codigo, exemplos[melhor]), _contido(codigo, exemplos[melhor]))
    return melhor + 1 if pontuacao >= SIMILARIDADE_MINIMA else None


def esperado_do_exemplo(k: int, enunciado: str) -> str | None:
    """Saída esperada que o enunciado escreve logo depois do k-ésimo bloco Python, se houver."""
    exemplos = blocos_python(enunciado)
    if not 1 <= k <= len(exemplos):
        return None
    for bloco, esperado in pares_esperados(enunciado):
        if bloco == exemplos[k - 1]:
            return esperado
    return None


def esperado_do_bloco(codigo: str | None, enunciado: str) -> str | None:
    """Saída esperada do enunciado para o exemplo de que `codigo` é cópia ou pedaço, se houver."""
    k = exemplo_do_bloco(codigo, enunciado)
    return esperado_do_exemplo(k, enunciado) if k else None


_EXIT_ZERO = re.compile(r"(?:^|\n)exit=0 em ")


def execucao_terminou_bem(saida: str) -> bool:
    """A saída de `run_python`/`_executar_comandos` traz `exit=0` e não foi recusada nem estourou."""
    return bool(_EXIT_ZERO.search(saida)) and not saida.lstrip().startswith(("RECUSADO", "TIMEOUT"))


def comparar_bloco(esperado: str, saida: str) -> list[dict[str, Any]]:
    """Linha a linha da saída esperada contra a saída real (mesma normalização de `src.verificacao`)."""
    resultado: list[dict[str, Any]] = []
    for linha in esperado.splitlines():
        veredito = saida_contem(linha, saida)
        if veredito is None:
            continue
        resultado.append({"linha": linha.strip(), "estado": ENCONTRADA if veredito else NAO_ENCONTRADA})
    return resultado


def anotar_comparacoes(execucoes: list[dict[str, Any]], codigos: dict[int, str | None], enunciado: str) -> None:
    """
    Amarra as execuções aos exemplos do enunciado e grava, na ÚLTIMA execução
    de cada exemplo, `exemplo`, `blocos_do_exemplo`, `esperado_enunciado` e
    `comparacao_enunciado`. A saída comparada é a junção das saídas de todos
    os blocos do exemplo: o refinador costuma fatiar um exemplo do enunciado
    em vários blocos (sqlite-utils-0003: 1 exemplo com 4 saídas esperadas
    virou 4 blocos), e comparar as 4 linhas só com o 1º bloco dava 3 "NÃO
    encontrada" falsas (fumaça da rodada 8).
    """
    por_exemplo: dict[int, list[dict[str, Any]]] = {}
    for ex in execucoes:
        if not ex.get("executado") or ex.get("shell"):
            continue
        k = exemplo_do_bloco(codigos.get(ex.get("bloco")), enunciado)
        if k is not None:
            por_exemplo.setdefault(k, []).append(ex)
    for k, lista in por_exemplo.items():
        esperado = esperado_do_exemplo(k, enunciado)
        if esperado is None:
            continue
        saida = "\n".join(str(ex.get("saida") or "") for ex in lista)
        ultimo = lista[-1]
        ultimo["exemplo"] = k
        ultimo["blocos_do_exemplo"] = [ex["bloco"] for ex in lista]
        ultimo["esperado_enunciado"] = esperado
        comparacao = comparar_bloco(esperado, saida)
        # Exemplo que não terminou bem (exit != 0, RECUSADO, TIMEOUT) não diz
        # nada sobre a linha esperada: na rodada 4 (sqlite-utils-0003 rep02) a
        # execução da revisão final morreu em exit=1 num run que o oráculo
        # resolveu; "NÃO encontrada" ali seria falsa e uma barreira dura o
        # derrubaria.
        if any(not execucao_terminou_bem(str(ex.get("saida") or "")) for ex in lista):
            comparacao = [{**c, "estado": NAO_VERIFICAVEL} for c in comparacao]
        ultimo["comparacao_enunciado"] = comparacao

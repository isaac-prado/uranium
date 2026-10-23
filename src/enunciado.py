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

from src.verificacao import ENCONTRADA, NAO_ENCONTRADA, saida_contem

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


def esperado_do_bloco(codigo: str | None, enunciado: str) -> str | None:
    """Saída esperada do enunciado para o bloco mais parecido com `codigo`, se houver."""
    pares = pares_esperados(enunciado)
    if not pares or not codigo or not codigo.strip():
        return None
    parecido = bloco_mais_parecido(codigo, [b for b, _ in pares])
    if parecido is None:
        return None
    return next(e for b, e in pares if b == parecido)


def comparar_bloco(esperado: str, saida: str) -> list[dict[str, Any]]:
    """Linha a linha da saída esperada contra a saída real do bloco (mesma normalização de `src.verificacao`)."""
    resultado: list[dict[str, Any]] = []
    for linha in esperado.splitlines():
        veredito = saida_contem(linha, saida)
        if veredito is None:
            continue
        resultado.append({"linha": linha.strip(), "estado": ENCONTRADA if veredito else NAO_ENCONTRADA})
    return resultado

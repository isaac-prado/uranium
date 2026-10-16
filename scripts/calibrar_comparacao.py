#!/usr/bin/env python3
"""
Calibração offline da comparação determinística de saídas (decisão 35).

Lê os runs orquestrados já gravados (eventos `intent` e `validation` com
`executions`, `result.json` do oráculo) e aplica `src.verificacao` à última
revisão final de cada run, sobre TODAS as saídas esperadas da intent (nas
rodadas 2 a 4 não havia plano apontando quais comparar). Responde: se a
comparação fosse uma barreira dura, quantos runs que o oráculo aprovou ela
derrubaria, e quantas aprovações erradas do revisor ela pegaria?

    .venv/bin/python scripts/calibrar_comparacao.py docs/tcc/dados/coleta-r4
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.verificacao import ENCONTRADA, NAO_ENCONTRADA, NAO_VERIFICAVEL, comparar_saidas  # noqa: E402


def _runs(base: str):
    for task in sorted(os.listdir(base)):
        for rep in sorted(glob.glob(os.path.join(base, task, "orchestration", "rep*"))):
            tentativas = sorted(glob.glob(rep + "/attempt*"))
            if tentativas and os.path.exists(tentativas[-1] + "/result.json"):
                yield task, os.path.basename(rep), tentativas[-1]


def _classe(comparacoes: list[dict]) -> str:
    estados = {c["estado"] for c in comparacoes}
    if not comparacoes or estados == {NAO_VERIFICAVEL}:
        return "nada verificável"
    if NAO_ENCONTRADA in estados:
        return "alguma NÃO encontrada"
    return "todas encontradas"


def calibrar(base: str) -> None:
    print(f"\n### {base}")
    tabela: Counter = Counter()
    pegas = perdidas = 0
    linhas: list[str] = []
    for task, rep, att in _runs(base):
        resolved = json.load(open(att + "/result.json"))["resolved"]
        intent = None
        finais: list[dict] = []
        with open(att + "/events.jsonl", encoding="utf-8") as fh:
            for linha in fh:
                e = json.loads(linha)
                if e["event_type"] == "intent":
                    intent = e["payload"]
                elif e["event_type"] == "validation" and not e["payload"].get("scope") and e["payload"].get("executions"):
                    finais.append(e["payload"])
        if intent is None or not finais:
            tabela[("sem execução na revisão final", "resolvido" if resolved else "não resolvido")] += 1
            continue
        ultima = finais[-1]
        esperadas = list(enumerate(intent.get("expected_outputs") or [], 1))
        comparacoes = comparar_saidas(esperadas, ultima["executions"])
        classe = _classe(comparacoes)
        tabela[(classe, "resolvido" if resolved else "não resolvido")] += 1
        n_enc = sum(c["estado"] == ENCONTRADA for c in comparacoes)
        n_ver = sum(c["estado"] != NAO_VERIFICAVEL for c in comparacoes)
        linhas.append(f"{task} {rep}: oráculo={'resolvido' if resolved else 'não'} revisor={'aprovou' if ultima['is_valid'] else 'reprovou'} "
                      f"comparação={classe} ({n_enc}/{n_ver} verificáveis encontradas, {len(comparacoes)} esperadas)")
        if ultima["is_valid"] and not resolved:
            if classe == "alguma NÃO encontrada":
                pegas += 1
            else:
                perdidas += 1
    print("última revisão final de cada run × oráculo:")
    for chave in sorted(tabela):
        print(f"  {chave[0]:<32} {chave[1]:<14} {tabela[chave]}")
    print(f"aprovações erradas do revisor que a barreira dura pegaria: {pegas}; que escapariam: {perdidas}")
    print("por run:")
    for linha in linhas:
        print("  " + linha)


if __name__ == "__main__":
    for base in sys.argv[1:] or ["docs/tcc/dados/coleta-r4"]:
        calibrar(base)

"""
Análise pareada da coleta: a tarefa é a unidade, não a repetição.

Repetições da mesma tarefa não são observações independentes. Cada tarefa
vira UM número por braço — a taxa de resolução média das repetições em que
os dois braços têm resultado —, e o teste compara os dois números tarefa a
tarefa.

  - teste de sinal: conta em quantas tarefas o orchestration foi melhor;
  - Wilcoxon pareado: usa também o tamanho da diferença.

Os dois são exatos (enumeração, não aproximação normal): com 8 a 12 tarefas a
aproximação erra justamente na cauda que decide. Sem scipy, de propósito: o
avaliador roda com o mínimo de dependências.

Direção da hipótese: H1 é "orchestration resolve mais que single-agent".
O p unicaudal responde a ela; o bicaudal vai junto para quem quiser ler sem
a direção.

Par perdido (uma das células sem resultado, por infraestrutura, interrupção ou
avaliação que falhou) sai inteiro — tirar só um lado desfaria o pareamento.
"""

from __future__ import annotations

import itertools
import json
import statistics
from dataclasses import dataclass, field
from math import comb
from pathlib import Path
from typing import Any

from harness.attempts import read_json, select_attempt

ARMS = ("single-agent", "orchestration")
SECUNDARIOS = ("cost_usd", "tokens_total", "turns", "wall_seconds")


@dataclass
class Observacao:
    """O resultado de uma célula concluída e avaliada."""

    task_id: str
    arm: str
    repetition: int
    resolved: bool
    blocked_by_cheat: bool
    censored: bool
    metrics: dict[str, float]


@dataclass
class Coleta:
    observacoes: list[Observacao] = field(default_factory=list)
    perdidas: list[tuple[str, str, int]] = field(default_factory=list)
    tentativas_perdidas: dict[str, int] = field(default_factory=lambda: dict.fromkeys(ARMS, 0))


def load_collection(out_root: Path) -> Coleta:
    """
    Lê `out_root/<tarefa>/<braço>/repNN/attemptNN/`.

    Vale a tentativa que `harness.attempts.select_attempt` escolhe, a
    mesma regra da coleta. Célula sem tentativa válida, ou válida e sem
    `result.json`, entra em `perdidas`.
    """
    coleta = Coleta()
    for rep_dir in sorted(out_root.glob("*/*/rep*")):
        task_id, arm = rep_dir.parent.parent.name, rep_dir.parent.name
        repeticao = int(rep_dir.name[3:])
        escolha = select_attempt(rep_dir)
        coleta.tentativas_perdidas[arm] = coleta.tentativas_perdidas.get(arm, 0) + escolha.lost
        resultado = read_json(escolha.run_dir / "result.json") if escolha.run_dir else None
        if resultado is None:
            coleta.perdidas.append((task_id, arm, repeticao))
            continue
        custo = resultado.get("cost") or {}
        processo = resultado.get("process") or {}
        coleta.observacoes.append(Observacao(
            task_id=task_id, arm=arm, repetition=repeticao,
            resolved=bool(resultado.get("resolved")),
            blocked_by_cheat=bool(resultado.get("resolved_blocked_by_cheat")),
            censored=str(processo.get("stop_reason") or "").startswith("budget:"),
            metrics={
                "cost_usd": float(custo.get("cost_usd") or 0.0),
                "tokens_total": float(custo.get("tokens_total") or 0),
                "turns": float(processo.get("turns") or 0),
                "wall_seconds": float(custo.get("wall_seconds") or 0.0),
            },
        ))
    return coleta


# ------------------------------------------------------------- estatística


def sign_test(diferencas: list[float]) -> dict[str, Any]:
    """Teste de sinal exato. Empates (diferença zero) saem, como manda o teste."""
    positivos = sum(1 for d in diferencas if d > 0)
    negativos = sum(1 for d in diferencas if d < 0)
    n = positivos + negativos
    if n == 0:
        return {"n": 0, "positive": 0, "negative": 0, "p_one_sided": 1.0, "p_two_sided": 1.0}
    cauda = sum(comb(n, k) for k in range(positivos, n + 1)) / 2**n
    extremo = max(positivos, negativos)
    bicaudal = min(1.0, 2 * sum(comb(n, k) for k in range(extremo, n + 1)) / 2**n)
    return {"n": n, "positive": positivos, "negative": negativos,
            "p_one_sided": cauda, "p_two_sided": bicaudal}


def _postos(valores: list[float]) -> list[float]:
    """Postos com média nos empates."""
    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    postos = [0.0] * len(valores)
    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and valores[ordem[j + 1]] == valores[ordem[i]]:
            j += 1
        for k in range(i, j + 1):
            postos[ordem[k]] = (i + j) / 2 + 1
        i = j + 1
    return postos


def wilcoxon(diferencas: list[float]) -> dict[str, Any]:
    """
    Wilcoxon pareado exato, enumerando os 2^n sinais.

    Com n até ~20 a enumeração é instantânea e dispensa a correção de
    empates da aproximação normal: a distribuição nula é construída com os
    mesmos postos (empatados) que os dados têm.
    """
    nao_nulas = [d for d in diferencas if d != 0]
    n = len(nao_nulas)
    if n == 0:
        return {"n": 0, "w_plus": 0.0, "p_one_sided": 1.0, "p_two_sided": 1.0}
    postos = _postos([abs(d) for d in nao_nulas])
    w_mais = sum(p for p, d in zip(postos, nao_nulas) if d > 0)
    total = sum(postos)
    media = total / 2
    maiores = extremos = 0
    for sinais in itertools.product((0, 1), repeat=n):
        w = sum(p for p, s in zip(postos, sinais) if s)
        maiores += w >= w_mais - 1e-9
        extremos += abs(w - media) >= abs(w_mais - media) - 1e-9
    return {"n": n, "w_plus": w_mais,
            "p_one_sided": maiores / 2**n, "p_two_sided": extremos / 2**n}


# ----------------------------------------------------------------- análise


def analyze(coleta: Coleta) -> dict[str, Any]:
    """Tabela por tarefa, testes do desfecho primário e dos secundários."""
    por_celula = {(o.task_id, o.arm, o.repetition): o for o in coleta.observacoes}
    tarefas = sorted({o.task_id for o in coleta.observacoes})

    linhas: list[dict[str, Any]] = []
    for tarefa in tarefas:
        repeticoes = sorted({o.repetition for o in coleta.observacoes if o.task_id == tarefa})
        pares = [
            (por_celula[(tarefa, "single-agent", r)], por_celula[(tarefa, "orchestration", r)])
            for r in repeticoes
            if (tarefa, "single-agent", r) in por_celula
            and (tarefa, "orchestration", r) in por_celula
        ]
        if not pares:
            continue
        linha: dict[str, Any] = {"task_id": tarefa, "pairs": len(pares)}
        for indice, braco in enumerate(ARMS):
            lado = [par[indice] for par in pares]
            linha[braco] = {
                "resolve_rate": sum(o.resolved for o in lado) / len(lado),
                "blocked_by_cheat": sum(o.blocked_by_cheat for o in lado),
                "censored": sum(o.censored for o in lado),
                **{m: statistics.mean(o.metrics[m] for o in lado) for m in SECUNDARIOS},
            }
        linha["diff_resolve_rate"] = (
            linha["orchestration"]["resolve_rate"] - linha["single-agent"]["resolve_rate"]
        )
        linhas.append(linha)

    dif_primario = [l["diff_resolve_rate"] for l in linhas]
    secundarios = {}
    for metrica in SECUNDARIOS:
        difs = [l["orchestration"][metrica] - l["single-agent"][metrica] for l in linhas]
        secundarios[metrica] = {
            "median_single_agent": statistics.median(l["single-agent"][metrica] for l in linhas)
            if linhas else None,
            "median_orchestration": statistics.median(l["orchestration"][metrica] for l in linhas)
            if linhas else None,
            "wilcoxon": wilcoxon(difs),
        }

    return {
        "tasks": len(linhas),
        "observations": len(coleta.observacoes),
        "lost_cells": [list(c) for c in coleta.perdidas],
        "lost_attempts": sum(coleta.tentativas_perdidas.values()),
        # Reexecutar run perdido até sair limpo seleciona os runs que não
        # pegaram falha de provedor. Se um braço perde muito mais, a seleção
        # pesa mais nele; o número tem de estar à vista para ser discutido.
        "by_arm": {
            braco: {
                "lost_attempts": coleta.tentativas_perdidas.get(braco, 0),
                "lost_cells": sum(1 for c in coleta.perdidas if c[1] == braco),
                "censored": sum(l[braco]["censored"] for l in linhas),
                "paired_observations": sum(l["pairs"] for l in linhas),
            }
            for braco in ARMS
        },
        "per_task": linhas,
        "primary": {
            "outcome": "resolve_rate (orchestration − single-agent), por tarefa",
            "hypothesis": "H1: orchestration > single-agent (unicaudal)",
            "sign_test": sign_test(dif_primario),
            "wilcoxon": wilcoxon(dif_primario),
        },
        "secondary": secundarios,
    }


def format_analysis(a: dict[str, Any]) -> str:
    linhas = [
        "",
        f"  análise pareada — {a['tasks']} tarefa(s), {a['observations']} observações",
        f"  perdidas: {len(a['lost_cells'])} célula(s), {a['lost_attempts']} tentativa(s) perdida(s)",
        *(
            f"    {braco:<14} {d['lost_attempts']} tentativa(s) e {d['lost_cells']} célula(s)"
            f" perdida(s), {d['censored']} de {d['paired_observations']} run(s) pareado(s)"
            " cortado(s) pelo orçamento"
            for braco, d in a["by_arm"].items()
        ),
        "  " + "─" * 86,
        f"  {'tarefa':<22} {'pares':>5}  {'resolve SA':>10} {'resolve OR':>10} {'Δ':>6}"
        f"  {'US$ SA':>8} {'US$ OR':>8}  {'turnos SA':>9} {'turnos OR':>9}",
        "  " + "─" * 86,
    ]
    for l in a["per_task"]:
        sa, orq = l["single-agent"], l["orchestration"]
        linhas.append(
            f"  {l['task_id']:<22} {l['pairs']:>5}  {sa['resolve_rate']:>10.2f} "
            f"{orq['resolve_rate']:>10.2f} {l['diff_resolve_rate']:>+6.2f}"
            f"  {sa['cost_usd']:>8.4f} {orq['cost_usd']:>8.4f}  "
            f"{sa['turns']:>9.1f} {orq['turns']:>9.1f}"
        )
    p = a["primary"]
    s, w = p["sign_test"], p["wilcoxon"]
    linhas += [
        "  " + "─" * 86,
        f"  primário   {p['hypothesis']}",
        f"    sinal     n={s['n']}  +{s['positive']} −{s['negative']}"
        f"  p(uni)={s['p_one_sided']:.4f}  p(bi)={s['p_two_sided']:.4f}",
        f"    Wilcoxon  n={w['n']}  W+={w['w_plus']:.1f}"
        f"  p(uni)={w['p_one_sided']:.4f}  p(bi)={w['p_two_sided']:.4f}",
        "  secundários (mediana por tarefa, Wilcoxon bicaudal)",
    ]
    for metrica, dados in a["secondary"].items():
        linhas.append(
            f"    {metrica:<13} SA {dados['median_single_agent'] or 0:>12.4f}"
            f"   OR {dados['median_orchestration'] or 0:>12.4f}"
            f"   p={dados['wilcoxon']['p_two_sided']:.4f}"
        )
    linhas.append("")
    return "\n".join(linhas)

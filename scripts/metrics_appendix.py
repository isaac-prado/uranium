"""
Apêndice de métricas da coleta: componentes por run, agregados por faixa e
braço, pareamentos por tarefa com teste exato e análise de sensibilidade da
censura da métrica 2.

Complementa `analyze_results.py` (as sete métricas, análise de registro) com
o que `docs/tcc/03-metricas.md` seção 5 manda para o apêndice: `oracle.f2p_*`,
`oracle.regression.*`, `cheat.warning_count`, `diff.*`, `quality.*`, e os
eventos próprios do orquestrado (`validation`, `memory`). Nenhum número aqui
substitui a análise de registro; tudo cita o `result.json` de origem.

Uso: python scripts/metrics_appendix.py docs/tcc/dados/coleta > apendice.md
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_results import teste_sinal, wilcoxon  # noqa: E402

ARMS = ("single-agent", "orchestration")
FAIXAS = ("grande", "media", "pequena")


def _med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def _f(v, c=3):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{c}f}".rstrip("0").rstrip(".") if c else f"{v:.0f}"
    return str(v)


def carregar(raiz: Path) -> list[dict]:
    runs = []
    for res in sorted(raiz.glob("*/*/rep*/attempt*/result.json")):
        d = res.parent
        r = json.loads(res.read_text(encoding="utf-8"))
        s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        o = r["oracle"]
        ciclos, revisoes, memoria = [], [], 0
        for linha in (d / "events.jsonl").read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            e = json.loads(linha)
            if e["event_type"] == "node_enter" and e["node"] == "developer":
                ciclos.append(0)
            if e["event_type"] == "llm_call" and e.get("node") == "developer" and ciclos:
                ciclos[-1] += 1
            if e["event_type"] == "validation":
                revisoes.append(bool(e["payload"]["is_valid"]))
            if e["event_type"] == "memory":
                memoria += 1
        runs.append({
            "task": r["task_id"], "faixa": r["faixa"], "arm": r["arm"], "rep": r["repetition"],
            "resolved": bool(r["resolved"]),
            "f2p": o["f2p_passed"] / o["f2p_total"] if o["f2p_total"] else None,
            "f2p_txt": f"{o['f2p_passed']}/{o['f2p_total']}",
            "reg": o["regression"]["failed"],
            "tokens": r["cost"]["tokens_total"], "usd": r["cost"]["cost_usd"],
            "calls": r["cost"]["llm_calls"], "wall": r["cost"]["wall_seconds"],
            "turns": r["process"]["turns"], "denials": r["process"]["tool_denials"],
            "stop": r["process"]["stop_reason"],
            "corte": r["process"]["stop_reason"].startswith("budget"),
            "corte_tokens": "max_tokens" in r["process"]["stop_reason"],
            "files": r["diff"]["files_changed"], "lines": r["diff"]["insertions"] + r["diff"]["deletions"],
            "cc": r["quality"].get("cc_mean_delta"), "mi": r["quality"].get("mi_delta"),
            "cheat_w": r["cheat"]["warning_count"], "cheat_c": r["cheat"]["critical_count"],
            "ciclos": ciclos, "revisoes": revisoes, "memoria": memoria,
            "dir": str(d),
        })
    return runs


def agregados(runs: list[dict]) -> str:
    linhas = ["| faixa | braço | runs | resolvidos | ocultos (fração média) | runs c/ regressão | regressões (mediana nos c/ regressão) | sem corte | cortes tokens | tokens (med.) | US$ (med.) | chamadas (med.) | parede s (med.) | linhas do patch (med.) | ΔCC (med.) | ΔMI (med.) | negações | avisos trapaça |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for faixa in (*FAIXAS, "todas"):
        for arm in ARMS:
            g = [r for r in runs if r["arm"] == arm and (faixa == "todas" or r["faixa"] == faixa)]
            if not g:
                continue
            com_reg = [r["reg"] for r in g if r["reg"] > 0]
            linhas.append("| " + " | ".join([
                faixa, arm, str(len(g)), f"{sum(r['resolved'] for r in g)}/{len(g)}",
                _f(statistics.mean(r["f2p"] for r in g)), str(len(com_reg)),
                _f(_med(com_reg), 0), f"{sum(not r['corte'] for r in g)}/{len(g)}",
                str(sum(r["corte_tokens"] for r in g)), _f(_med([r["tokens"] for r in g]), 0),
                _f(_med([r["usd"] for r in g])), _f(_med([r["calls"] for r in g]), 0),
                _f(_med([r["wall"] for r in g]), 0), _f(_med([r["lines"] for r in g]), 0),
                _f(_med([r["cc"] for r in g])), _f(_med([r["mi"] for r in g])),
                str(sum(r["denials"] for r in g)), str(sum(r["cheat_w"] for r in g)),
            ]) + " |")
    return "\n".join(linhas)


def por_run(runs: list[dict]) -> str:
    linhas = ["| tarefa | faixa | rep | braço | resolvida | ocultos | regressões | turnos | chamadas | tokens | US$ | parede s | arquivos | linhas | ΔCC | ΔMI | negações | avisos | parada | ciclos (turnos) | revisões |",
              "|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
    for r in sorted(runs, key=lambda r: (FAIXAS.index(r["faixa"]), r["task"], r["rep"], r["arm"])):
        rev = "".join("A" if v else "R" for v in r["revisoes"]) or "—"
        linhas.append("| " + " | ".join([
            r["task"], r["faixa"], str(r["rep"]), r["arm"], "sim" if r["resolved"] else "não", r["f2p_txt"],
            str(r["reg"]), str(r["turns"]), str(r["calls"]), str(r["tokens"]), _f(r["usd"]), _f(r["wall"], 0),
            str(r["files"]), str(r["lines"]), _f(r["cc"]), _f(r["mi"]), str(r["denials"]), str(r["cheat_w"]),
            r["stop"].split(" (")[0], "·".join(map(str, r["ciclos"])) if r["arm"] == "orchestration" else "—", rev,
        ]) + " |")
    return "\n".join(linhas)


def pareado(runs: list[dict], campo: str, nome: str, filtro: str) -> str:
    """Wilcoxon exato bilateral sobre a mediana por tarefa, orchestration − single-agent."""
    por = defaultdict(lambda: defaultdict(list))
    for r in runs:
        por[r["task"]][r["arm"]].append(r)
    difs, usadas = [], []
    for task, bra in sorted(por.items()):
        sa, orq = bra["single-agent"], bra["orchestration"]
        if filtro == "ambos_resolvem_mediana" and not (sum(r["resolved"] for r in sa) >= 2 and sum(r["resolved"] for r in orq) >= 2):
            continue
        if filtro == "ambos_resolvem_ao_menos_uma" and not (any(r["resolved"] for r in sa) and any(r["resolved"] for r in orq)):
            continue
        if filtro.startswith("faixa:") and sa[0]["faixa"] != filtro.split(":")[1]:
            continue
        a, b = _med([r[campo] for r in sa]), _med([r[campo] for r in orq])
        if a is None or b is None:
            continue
        difs.append(b - a); usadas.append(task)
    if not difs:
        return f"| {nome} | {filtro} | 0 | — | — | — |"
    t = wilcoxon(difs)
    return f"| {nome} | {filtro} | {len(difs)} | {_f(statistics.median(difs))} | {_f(getattr(t, 'estatistica', None))} | {_f(getattr(t, 'p', None), 4)} |"


def sinal_por_faixa(runs: list[dict]) -> str:
    linhas = ["| faixa | tarefas | +OR | −SA | empates | p (bilateral) |", "|---|---:|---:|---:|---:|---:|"]
    por = defaultdict(lambda: defaultdict(list))
    for r in runs:
        por[(r["faixa"], r["task"])][r["arm"]].append(r["resolved"])
    for faixa in (*FAIXAS, "todas"):
        difs = []
        for (fx, task), bra in por.items():
            if faixa != "todas" and fx != faixa:
                continue
            difs.append(sum(bra["orchestration"]) / 3 - sum(bra["single-agent"]) / 3)
        pos, neg, emp = sum(d > 0 for d in difs), sum(d < 0 for d in difs), sum(d == 0 for d in difs)
        t = teste_sinal(difs) if (pos + neg) else None
        linhas.append(f"| {faixa} | {len(difs)} | {pos} | {neg} | {emp} | {_f(getattr(t, 'p', None), 4) if t else '—'} |")
    return "\n".join(linhas)


def orquestrado(runs: list[dict]) -> str:
    g = [r for r in runs if r["arm"] == "orchestration"]
    nc = Counter(len(r["ciclos"]) for r in g)
    revs = [v for r in g for v in r["revisoes"]]
    fn = [(r["task"], r["rep"], sum(not v for v in r["revisoes"])) for r in g if r["resolved"] and any(not v for v in r["revisoes"])]
    vp = sum(1 for r in g if r["resolved"] and r["revisoes"] and all(r["revisoes"]))
    rej_nao_res = sum(1 for r in g if not r["resolved"] and any(not v for v in r["revisoes"]))
    return "\n".join([
        f"- Ciclos do developer por run: {dict(sorted(nc.items()))}; runs com 2+ ciclos (memória de trabalho usada): {sum(1 for r in g if len(r['ciclos']) >= 2)}/{len(g)}.",
        f"- Revisões semânticas (suíte verde): {len(revs)}; aprovadas {sum(revs)}, reprovadas {len(revs) - sum(revs)}.",
        f"- Runs resolvidos pelo oráculo com ao menos uma reprovação do revisor (falso negativo): {len(fn)} — {fn}.",
        f"- Runs resolvidos com todas as revisões aprovadas: {vp}; runs não resolvidos com ao menos uma reprovação: {rej_nao_res}.",
    ])


def main(argv=None) -> int:
    raiz = Path((argv or sys.argv[1:])[0])
    runs = carregar(raiz)
    out = [
        f"# Apêndice de métricas da coleta ({len(runs)} runs admitidos, `{raiz}`)",
        "",
        "Gerado por `scripts/metrics_appendix.py`. Mediana = mediana entre runs do grupo. Diferenças pareadas sempre orchestration − single-agent, sobre a mediana das repetições por tarefa; Wilcoxon exato bilateral de `scripts/analyze_results.py`.",
        "", "## A. Agregados por faixa e braço (sobre runs)", "", agregados(runs),
        "", "## B. Resolução por faixa (teste do sinal sobre a fração de repetições resolvidas por tarefa)", "", sinal_por_faixa(runs),
        "", "## C. Pareamentos por tarefa e sensibilidade da censura", "",
        "| métrica | tarefas usadas | n | mediana da diferença | W+ | p |", "|---|---|---:|---:|---:|---:|",
    ]
    for campo, nome in (("f2p", "fração de ocultos passados"), ("tokens", "tokens"), ("usd", "US$"), ("calls", "chamadas"),
                        ("wall", "parede (s)"), ("turns", "turnos"), ("lines", "linhas do patch"), ("cc", "ΔCC"), ("reg", "regressões")):
        for filtro in ("todas", "ambos_resolvem_mediana", "ambos_resolvem_ao_menos_uma"):
            out.append(pareado(runs, campo, nome, filtro))
    out += ["", "## D. Orquestrado: ciclos e revisão semântica (eventos `memory` e `validation`)", "", orquestrado(runs),
            "", "## E. Componentes por run", "", por_run(runs), ""]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

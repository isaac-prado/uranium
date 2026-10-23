"""
Resumo de uma coleta do orquestrado (ou de várias, lado a lado): desfechos,
custo, cortes, aprovações erradas, faixa, e os mecanismos do planejador
(sub-tarefas feitas/adiadas/abandonadas, replanejamentos, blocos de linha de
comando executados, blocos que não compilam, revisões) lidos dos
`result.json` e `events.jsonl`.

Uso:
    uv run python scripts/resumo_rodada.py ROTULO=RAIZ [ROTULO=RAIZ ...]
Ex.:
    uv run python scripts/resumo_rodada.py r4=runs/coleta-r4 r7=runs/coleta-r7
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import statistics


def resumo_resultados(raiz: str) -> None:
    runs = []
    for f in sorted(glob.glob(f"{raiz}/*/orchestration/rep*/attempt*/result.json")):
        r = json.load(open(f, encoding="utf-8"))
        c, p = r["cost"], r["process"]
        runs.append(
            dict(task=r["task_id"], rep=r["repetition"], resolved=bool(r["resolved"]),
                 tokens=c["tokens_total"], prompt=c.get("tokens_prompt", 0), cached=c.get("tokens_cached", 0),
                 cost=c["cost_usd"], turns=p["turns"], stop=p["stop_reason"] or "", faixa=r.get("faixa"))
        )
    if not runs:
        print("  (sem result.json)")
        return
    faixa: dict[str, list[int]] = {}
    for x in runs:
        faixa.setdefault(x["faixa"], [0, 0])
        faixa[x["faixa"]][1] += 1
        faixa[x["faixa"]][0] += int(x["resolved"])
    por_tarefa = collections.defaultdict(lambda: [0, 0])
    for x in runs:
        por_tarefa[x["task"]][1] += 1
        por_tarefa[x["task"]][0] += int(x["resolved"])
    tarefas = sum(1 for t, (a, n) in por_tarefa.items() if a * 2 > n)
    prompt = sum(x["prompt"] for x in runs)
    print(f"  runs={len(runs)} resolvidas={sum(1 for x in runs if x['resolved'])} tarefas_resolvidas(maioria das repetições)={tarefas}/{len(por_tarefa)}")
    print(f"  custo=US${sum(x['cost'] for x in runs):.2f} tokens={sum(x['tokens'] for x in runs)/1e6:.1f}M mediana/run={statistics.median(x['tokens'] for x in runs)/1e6:.2f}M"
          + (f" cache_gravada={sum(x['cached'] for x in runs)/prompt:.3f}" if prompt and any(x['cached'] for x in runs) else " cache_gravada=n/d"))
    print(f"  cortes={sum(1 for x in runs if x['stop'].startswith('budget'))} concluiu={sum(1 for x in runs if x['stop']=='concluiu')} "
          f"aprovacoes_erradas(concluiu sem resolver)={sum(1 for x in runs if not x['resolved'] and x['stop']=='concluiu')} "
          f"resolvidas_no_corte={sum(1 for x in runs if x['resolved'] and x['stop'].startswith('budget'))} "
          f"error={sum(1 for x in runs if x['stop'].startswith('error'))}")
    print(f"  faixas (resolvidas/runs)={faixa}")
    print("  por tarefa:", " ".join(f"{t}={a}/{n}" for t, (a, n) in sorted(por_tarefa.items())))
    print("  nao resolvidas:", ", ".join(f"{x['task']}-r{x['rep']}({x['stop'][:7]})" for x in runs if not x["resolved"]))


def resumo_mecanismos(raiz: str) -> None:
    tot: collections.Counter = collections.Counter()
    por_tarefa: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(f"{raiz}/*/orchestration/rep*/attempt*/events.jsonl")):
        ev = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        if not ev or not any(e["event_type"] == "run_end" for e in ev):
            continue
        tid = ev[0]["task_id"]
        plan = [e for e in ev if e["event_type"] == "plan"]
        ultimo = next((e["payload"] for e in reversed(plan) if e["payload"].get("evento") == "avanco"),
                      plan[-1]["payload"] if plan else {})
        st = ultimo.get("status") or []
        hist: dict[int, set[str]] = collections.defaultdict(set)
        for e in plan:
            for s in (e["payload"].get("status") or []):
                hist[s["id"]].add(s["status"])
        val = [e for e in ev if e["event_type"] == "validation"]
        execs = [x for e in val for x in ((e.get("payload") or {}).get("executions") or [])]
        finais = [e for e in val if e["payload"].get("scope") != "subtask"]
        linha = {
            "runs": 1, "subtarefas": len(st),
            "feitas": sum(1 for s in st if s["status"] == "feita"),
            "adiadas_no_fim": sum(1 for s in st if s["status"] == "adiada"),
            "abandonadas": sum(1 for s in st if s["status"] == "abandonada"),
            "adiadas_alguma_vez": sum(1 for v in hist.values() if "adiada" in v),
            "adiadas_depois_feitas": sum(1 for v in hist.values() if "adiada" in v and "feita" in v),
            "replans": max((e["payload"].get("replans") or 0 for e in plan), default=0),
            "exec_shell": sum(1 for x in execs if x.get("shell")),
            "runs_com_shell": int(any(x.get("shell") for x in execs)),
            "blocos_nao_compilam": sum(1 for x in execs if x.get("nao_compila")),
            "runs_com_nao_compila": int(any(x.get("nao_compila") for x in execs)),
            "subtarefa_aprovada": sum(1 for e in val if e["payload"].get("scope") == "subtask" and e["payload"].get("is_valid")),
            "subtarefa_reprovada": sum(1 for e in val if e["payload"].get("scope") == "subtask" and not e["payload"].get("is_valid")),
            "revisoes_finais": len(finais),
            "finais_reprovadas": sum(1 for e in finais if not e["payload"].get("is_valid")),
        }
        tot.update(linha)
        por_tarefa[tid].update({k: linha[k] for k in ("feitas", "adiadas_alguma_vez", "adiadas_depois_feitas", "exec_shell", "blocos_nao_compilam", "replans")})
    print("  mecanismos (eventos; runs = arquivos events.jsonl com run_end, inclusive tentativas repetidas):", dict(tot))
    for t, c in sorted(por_tarefa.items()):
        print(f"    {t:18s} {dict(c)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("coletas", nargs="+", help="ROTULO=RAIZ da coleta (pasta com <tarefa>/orchestration/...)")
    args = parser.parse_args()
    for item in args.coletas:
        rotulo, _, raiz = item.partition("=")
        print(f"== {rotulo} ({raiz})")
        resumo_resultados(raiz)
        resumo_mecanismos(raiz)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

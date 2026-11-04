# Rodar da raiz: python3 scripts/criterios_r9.py runs/coleta-r9 [docs/tcc/dados/coleta-r4]
"""Critérios fixados na decisão 50 (04/11/2026) para a rodada 9, calculados sobre os result.json/summary.json/events.jsonl
de uma raiz de coleta do orquestrado, e a linha de base da rodada 4 nas mesmas tarefas. Critérios: reprovações finais com
suíte verde que citam SyntaxError = 0; resolvidos mas cortados ≤ 1; resolvidos ≥ 24/39 e ≥ 9/13; aprovações erradas ≤ 3;
fração dos turnos depois do primeiro verde < 41 %."""
import json, glob, os, sys, collections
root=sys.argv[1]; base=sys.argv[2] if len(sys.argv)>2 else "docs/tcc/dados/coleta-r4"
def medir(root, tasks=None):
    R=[]
    for p in sorted(glob.glob(f"{root}/*/orchestration/rep*/attempt*/result.json")):
        r=json.load(open(p)); s=json.load(open(p.replace("result.json","summary.json")))
        if tasks and r["task_id"] not in tasks: continue
        E=[json.loads(l) for l in open(p.replace("result.json","events.jsonl"))]
        tests=[e for e in E if e["event_type"]=="test_run"]; mems=[e for e in E if e["event_type"]=="memory"]
        rej_verde=syn=0; first_green=None
        for e in E:
            if e["event_type"]=="test_run" and e["payload"].get("green") and first_green is None: first_green=e["seq"]
            if e["event_type"]=="validation" and e["payload"].get("scope")!="subtask" and not e["payload"]["is_valid"]:
                tr=[t for t in tests if t["seq"]<e["seq"]]
                if tr and tr[-1]["payload"].get("green"):
                    rej_verde+=1
                    if any("SyntaxError" in (x.get("saida") or "") for x in (e["payload"].get("executions") or [])): syn+=1
        turns_after=sum(int(m["payload"]["turnos"]) for m in mems if first_green is not None and m["seq"]>first_green)
        R.append(dict(task=r["task_id"],rep=r["repetition"],res=bool(r["resolved"]),stop=s["stop_reason"].split("(")[0].strip(),
                      turns=s["turns"],tok=r["cost"]["tokens_total"],usd=r["cost"]["cost_usd"],rej_verde=rej_verde,syn=syn,
                      turns_after=turns_after,crit=r["cheat"]["critical_count"],warn=r["cheat"]["warning_count"]))
    return R
def resumo(R,rotulo):
    tasks=sorted({x["task"] for x in R}); n=len(R)
    if n==0: print(f"== {rotulo}: nenhum run com result.json ainda"); return
    res=sum(x["res"] for x in R); maj=sum(1 for t in tasks if sum(x["res"] for x in R if x["task"]==t)>=2)
    cut_res=sum(1 for x in R if x["res"] and x["stop"].startswith("budget")); err=sum(1 for x in R if x["stop"]=="concluiu" and not x["res"])
    tot=sum(x["turns"] for x in R); after=sum(x["turns_after"] for x in R)
    print(f"== {rotulo}: {n} runs, {len(tasks)} tarefas")
    print(f"  reprovações com verde {sum(x['rej_verde'] for x in R)}, das quais com SyntaxError {sum(x['syn'] for x in R)}  [critério 1: = 0]")
    print(f"  resolvidos mas cortados {cut_res}  [critério 2: ≤ 1]")
    print(f"  resolvidos {res}/{n} runs, {maj}/{len(tasks)} tarefas por maioria  [critério 3: ≥ 24/39 e ≥ 9/13]")
    print(f"  aprovações erradas {err}  [critério 4: ≤ 3]")
    print(f"  turnos depois do primeiro verde {after} de {tot} ({100*after/max(1,tot):.0f}%)  [critério 5: < 41%]")
    print(f"  cortes por orçamento {sum(1 for x in R if x['stop'].startswith('budget'))}; críticos {sum(x['crit'] for x in R)}; avisos {sum(x['warn'] for x in R)}; US$ {sum(x['usd'] for x in R):.2f}; tokens mediana {sorted(x['tok'] for x in R)[n//2]/1e6:.2f} M; turnos mediana {sorted(x['turns'] for x in R)[n//2]}")
    for x in R: print(f"    {x['task']:18} rep{x['rep']} res={x['res']} stop={x['stop'][:17]:17} turnos={x['turns']:3} rej_verde={x['rej_verde']} syn={x['syn']} após_verde={x['turns_after']}")
R9=medir(root); resumo(R9, root)
if R9:
    R4=medir(base, {x["task"] for x in R9}); resumo(R4, f"{base} (mesmas tarefas)")

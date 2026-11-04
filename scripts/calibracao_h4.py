# Rodar da raiz: python3 scripts/calibracao_h4.py > docs/tcc/dados/coleta-deepseek/calibracao-h4-offline.txt
"""Calibração offline da hipótese H4 (28-exploratorio-orquestrado.md §3): regras de parada alternativas para o
revisor final do orquestrado, simuladas sobre os eventos gravados dos 117 runs orquestrados das coletas finais
(Qwen rodada 4, DeepSeek, Devstral). O diff de cada ciclo não é gravado, logo o desfecho do patch no ponto de
aprovação simulado só é conhecido quando nenhuma escrita (write_file/replace_in_file aceita) ocorreu depois
desse ponto: aí o patch simulado é o patch final, que o oráculo já julgou. Nos demais o desfecho é incerto e
entra nos dois limites (pessimista: viraria não resolvido; otimista: mantém o desfecho final).

Regras (todas exigem suíte visível verde na validação do ciclo):
  real        o que aconteceu.
  primeiro_verde   aprovar na primeira validação com suíte verde (é a regra de parada do agente único aplicada à trajetória).
  concluiu+verde   aprovar na primeira validação com suíte verde em que o developer parou por "concluiu" (não por teto do ciclo).
  patch_inalterado aprovar quando o revisor reprovou com verde no ciclo anterior e o developer voltou sem escrever nada.
  teto_k (k=2,3)   aprovar na k-ésima reprovação com suíte verde.
"""
import json, glob, os, collections
roots={"Qwen":"docs/tcc/dados/coleta-r4","DeepSeek":"runs/coleta-deepseek","Devstral":"runs/coleta-devstral"}
WRITES={"write_file","replace_in_file"}
R=[]
for m,root in roots.items():
    for p in sorted(glob.glob(f"{root}/*/orchestration/rep*/attempt*/result.json")):
        r=json.load(open(p)); s=json.load(open(p.replace("result.json","summary.json")))
        E=[json.loads(l) for l in open(p.replace("result.json","events.jsonl"))]
        mems=[e for e in E if e["event_type"]=="memory"]
        tests=[e for e in E if e["event_type"]=="test_run"]
        finals=[e for e in E if e["event_type"]=="validation" and e["payload"].get("scope")!="subtask"]
        writes=[e["seq"] for e in E if e["event_type"]=="tool_call" and e["tool_name"] in WRITES and not e["tool_denied"] and not (e["payload"] or {}).get("error")]
        cycles=[]
        for i,me in enumerate(mems):
            nxt=mems[i+1]["seq"] if i+1<len(mems) else 10**9
            tr=[t for t in tests if me["seq"]<t["seq"]<nxt]; fv=[v for v in finals if me["seq"]<v["seq"]<nxt]
            cycles.append(dict(turnos=int(me["payload"]["turnos"]),parada=me["payload"]["parada"].split(":")[0],
                               green=bool(tr and tr[-1]["payload"].get("green")),val_seq=(fv[-1]["seq"] if fv else None),
                               valid=(bool(fv[-1]["payload"]["is_valid"]) if fv else None)))
        R.append(dict(m=m,task=r["task_id"],rep=r["repetition"],res=bool(r["resolved"]),stop=s["stop_reason"].split("(")[0].strip(),
                      turns=s["turns"],cycles=cycles,writes=writes))
print(f"runs orquestrados lidos: {len(R)}")

def ponto(run,regra):
    """Índice do ciclo em que a regra aprovaria, ou None se nunca dispara antes do fim real."""
    C=run["cycles"]; rej=0
    for i,c in enumerate(C):
        if c["val_seq"] is None or not c["green"]: continue
        if c["valid"]:  # o revisor real aprovou aqui: fim real
            return None
        rej+=1
        if regra=="primeiro_verde": return i
        if regra=="concluiu+verde" and c["parada"]=="concluiu": return i
        if regra=="patch_inalterado" and i>0 and C[i-1]["green"] and C[i-1]["valid"] is False and not any(C[i-1]["val_seq"]<w<c["val_seq"] for w in run["writes"]): return i
        if regra=="teto_2" and rej>=2: return i
        if regra=="teto_3" and rej>=3: return i
    return None

regras=["primeiro_verde","concluiu+verde","patch_inalterado","teto_2","teto_3"]
print("\n== Linha de base real (117 runs)")
tot_turns=sum(x["turns"] for x in R); print(f"resolvidos {sum(x['res'] for x in R)}; turnos totais {tot_turns}; aprovações erradas {sum(1 for x in R if x['stop']=='concluiu' and not x['res'])}; resolvidos cortados {sum(1 for x in R if x['res'] and x['stop'].startswith('budget'))}")

for regra in regras:
    print(f"\n== Regra: {regra}")
    agg=collections.Counter(); saved=0; per_model=collections.defaultdict(collections.Counter); detalhes=[]
    for x in R:
        i=ponto(x,regra)
        if i is None: agg["sem efeito"]+=1; per_model[x["m"]]["sem efeito"]+=1; continue
        C=x["cycles"]; vs=C[i]["val_seq"]
        turns_after=sum(c["turnos"] for c in C[i+1:]); saved+=turns_after
        mudou=any(w>vs for w in x["writes"])
        if x["res"]:
            k="resolvido: mesmo patch (ganho certo)" if not mudou else "resolvido: patch mudou depois (incerto)"
        else:
            if x["stop"]=="concluiu": k="não resolvido: já era aprovação errada"
            else: k="não resolvido: corte vira aprovação errada" + ("" if not mudou else " (patch mudou depois)")
        agg[k]+=1; per_model[x["m"]][k]+=1
        detalhes.append((x["m"],x["task"],x["rep"],i+1,len(C),turns_after,k))
    print(f"turnos economizados: {saved} de {tot_turns} ({100*saved/tot_turns:.0f}%)")
    for k,v in sorted(agg.items()): print(f"  {v:3}  {k}")
    certo=agg["resolvido: mesmo patch (ganho certo)"]; incerto=agg["resolvido: patch mudou depois (incerto)"]
    base=sum(x['res'] for x in R)
    print(f"resolvidos: real {base}; limite pessimista {base-incerto} (os incertos viram perda); limite otimista {base}")
    novas_err=sum(v for k,v in agg.items() if k.startswith("não resolvido: corte"))
    print(f"aprovações erradas: real 13; com a regra, certas {13+novas_err} (cortes que virariam aprovação errada)" + (f" + até {incerto} incertas" if incerto else ""))
    for m in roots:
        pm=per_model[m]; print(f"  {m:9} " + "; ".join(f"{k}={v}" for k,v in sorted(pm.items())))
    if regra in ("patch_inalterado","concluiu+verde"):
        print("  detalhe (modelo, tarefa, rep, ciclo de aprovação simulada / ciclos reais, turnos poupados, classe):")
        for d in detalhes: print("   ", d)

print("\n== Os 10 runs resolvidos mas cortados (revisor nunca aprovou): a primeira reprovação com verde e se o patch mudou depois dela")
for x in R:
    if x["res"] and x["stop"].startswith("budget"):
        C=x["cycles"]; firsts=[i for i,c in enumerate(C) if c["green"] and c["valid"] is False]
        if not firsts: print(f"  {x['m']:9} {x['task']:18} rep{x['rep']}: nenhuma reprovação com verde (ciclos {len(C)})"); continue
        i=firsts[0]; vs=C[i]["val_seq"]; mudou=any(w>vs for w in x["writes"]); after=sum(c["turnos"] for c in C[i+1:])
        print(f"  {x['m']:9} {x['task']:18} rep{x['rep']}: 1ª reprovação com verde no ciclo {i+1}/{len(C)}; patch mudou depois: {mudou}; turnos depois: {after}; reprovações com verde: {len(firsts)}")

print("\n== Causa das reprovações com verde: blocos de reprodução que não compilam (SyntaxError na execução do validador)")
tot=collections.Counter(); afetados=[]
for m,root in roots.items():
    for p in sorted(glob.glob(f"{root}/*/orchestration/rep*/attempt*/result.json")):
        r=json.load(open(p)); s=json.load(open(p.replace("result.json","summary.json")))
        E=[json.loads(l) for l in open(p.replace("result.json","events.jsonl"))]
        tests=[e for e in E if e["event_type"]=="test_run"]; mems=[e for e in E if e["event_type"]=="memory"]
        writes=[e["seq"] for e in E if e["event_type"]=="tool_call" and e["tool_name"] in WRITES and not e["tool_denied"]]
        first=None
        for v in E:
            if v["event_type"]!="validation" or v["payload"].get("scope")=="subtask" or v["payload"]["is_valid"]: continue
            tr=[t for t in tests if t["seq"]<v["seq"]]
            if not (tr and tr[-1]["payload"].get("green")): continue
            tot[m,"rej_verde"]+=1
            if any("SyntaxError" in (x.get("saida") or "") for x in (v["payload"].get("executions") or [])):
                tot[m,"com_SyntaxError"]+=1
                if first is None: first=v["seq"]
        if first is not None:
            after=sum(int(me["payload"]["turnos"]) for me in mems if me["seq"]>first)
            afetados.append((m,r["task_id"],r["repetition"],r["resolved"],s["stop_reason"].split("(")[0].strip(),after,any(w>first for w in writes)))
for m in roots: print(f"  {m:9} reprovações com verde {tot[m,'rej_verde']}, com SyntaxError nos blocos {tot[m,'com_SyntaxError']}")
print(f"  total: {sum(tot[m,'rej_verde'] for m in roots)} reprovações com verde, {sum(tot[m,'com_SyntaxError'] for m in roots)} com SyntaxError; runs afetados {len(afetados)}, resolvidos {sum(a[3] for a in afetados)}, turnos depois da 1ª reprovação com SyntaxError {sum(a[5] for a in afetados)} de {tot_turns}")
for a in afetados: print("   ", a)
print("\n== Rodada 4 (sem compile check) × rodada 8 (compile check + cópia consertada pelo enunciado), Qwen, nas tarefas afetadas: reprovações com verde por run e turnos")
for t in sorted({a[1] for a in afetados}):
    row=[]
    for r_,root in (("r4","docs/tcc/dados/coleta-r4"),("r8","docs/tcc/dados/coleta-r8")):
        rej=[];turns=[];res=0
        for p in sorted(glob.glob(f"{root}/{t}/orchestration/rep*/attempt*/result.json")):
            r=json.load(open(p)); s=json.load(open(p.replace("result.json","summary.json"))); E=[json.loads(l) for l in open(p.replace("result.json","events.jsonl"))]
            tests=[e for e in E if e["event_type"]=="test_run"]; k=0
            for v in E:
                if v["event_type"]=="validation" and v["payload"].get("scope")!="subtask" and not v["payload"]["is_valid"]:
                    tr=[x for x in tests if x["seq"]<v["seq"]]
                    if tr and tr[-1]["payload"].get("green"): k+=1
            rej.append(k); turns.append(s["turns"]); res+=r["resolved"]
        row.append(f"{r_}: resolvidos {res}/3, reprovações com verde {rej}, turnos {turns}")
    print(f"  {t:18} " + " | ".join(row))

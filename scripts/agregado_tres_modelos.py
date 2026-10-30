# Rodar da raiz do repositório: python3 scripts/agregado_tres_modelos.py > docs/tcc/dados/coleta-deepseek/agregado-tres-modelos.txt
# Lê result.json/summary.json/events.jsonl das coletas versionadas (docs/tcc/dados/coleta, coleta-r2, coleta-r4) e das replicações (runs/coleta-deepseek, runs/coleta-devstral).
"""Agregado das três coletas (Qwen = SA pareado [estudo principal + 9 runs refeitos em coleta-r2 para as 3 tarefas da decisão 27] + rodada 4 OR; DeepSeek; Devstral): 234 runs.
Lê result.json/summary.json/patch.diff. Gerado em 29/10/2026 para docs/tcc/27-relatorio-cientifico.md."""
import json, glob, os, collections, statistics as st, random, math
from itertools import product
roots = {"Qwen":{"SA":"docs/tcc/dados/coleta","OR":"docs/tcc/dados/coleta-r4"},
         "DeepSeek":{"SA":"runs/coleta-deepseek","OR":"runs/coleta-deepseek"},
         "Devstral":{"SA":"runs/coleta-devstral","OR":"runs/coleta-devstral"}}
armname={"SA":"single-agent","OR":"orchestration"}
R=[]
RECONSTRUIDAS={"pygments-0001","sqlite-utils-0002","tomlkit-0004"}  # decisão 27: SA refeito em dados/coleta-r2
def _fontes(m,a,root):
    for p in glob.glob(f"{root}/*/{armname[a]}/rep*/attempt*/result.json"):
        task=p.split("/")[-5]
        if m=="Qwen" and a=="SA" and task in RECONSTRUIDAS: continue
        yield p
    if m=="Qwen" and a=="SA":
        for t in RECONSTRUIDAS:
            yield from glob.glob(f"docs/tcc/dados/coleta-r2/{t}/single-agent/rep*/attempt*/result.json")
for m,d in roots.items():
    for a,root in d.items():
        for p in _fontes(m,a,root):
            r=json.load(open(p)); s=json.load(open(os.path.join(os.path.dirname(p),"summary.json")))
            pd=os.path.join(os.path.dirname(p),"patch.diff"); psize=os.path.getsize(pd) if os.path.exists(pd) else None
            R.append(dict(m=m,a=a,task=r["task_id"],rep=r["repetition"],faixa=r["faixa"],res=bool(r["resolved"]),
                stop=s["stop_reason"],turns=s["turns"],tok=r["cost"]["tokens_total"],usd=r["cost"]["cost_usd"],
                wall=r["cost"]["wall_seconds"],calls=r["cost"]["llm_calls"],crit=r["cheat"]["critical_count"],
                warn=r["cheat"]["warning_count"],blocked=bool(r.get("resolved_blocked_by_cheat")),
                f2p=r["oracle"]["f2p_passed"],f2pt=r["oracle"]["f2p_total"],denials=r.get("process",{}).get("tool_denials"),
                cc=(r.get("quality") or {}).get("cc_mean_delta"),psize=psize))
print(f"runs lidos: {len(R)} (esperado 234)")
def binom_two_sided(k,n):
    if n==0: return 1.0
    from math import comb
    p=sum(comb(n,i) for i in range(0,n+1) if abs(i-n/2)>=abs(k-n/2))/2**n
    return min(1.0,p)
def wilcoxon_exact(d):
    d=[x for x in d if x!=0]; n=len(d)
    if n==0: return (0,1.0,0)
    ranks=sorted(range(n),key=lambda i:abs(d[i])); rk=[0]*n
    i=0
    while i<n:
        j=i
        while j+1<n and abs(d[ranks[j+1]])==abs(d[ranks[i]]): j+=1
        for q in range(i,j+1): rk[ranks[q]]=(i+j)/2+1
        i=j+1
    wplus=sum(rk[i] for i in range(n) if d[i]>0); W=min(wplus,sum(rk)-wplus)
    if n>20: return (W,None,n)
    cnt=0
    for signs in product([0,1],repeat=n):
        w=sum(rk[i] for i in range(n) if signs[i]); 
        if min(w,sum(rk)-w)<=W: cnt+=1
    return (W,cnt/2**n,n)
print("\n== Por modelo e braço (runs resolvidos, tarefas por maioria, por faixa, cortes, concluiu-errado, só-oráculo)")
tasks=sorted({x["task"] for x in R}); faixa={x["task"]:x["faixa"] for x in R}
hdr=f"{'modelo':9}{'braço':6}{'runs':7}{'tarefas':8}{'grande':7}{'media':7}{'pequena':8}{'cortes':7}{'aprov.err':10}{'SA tests_pass errado':21}{'só oráculo':11}{'crit/warn':10}{'mediana tok':12}{'mediana s':10}{'US$':7}"
print(hdr)
cell={}
for m in roots:
    for a in ("SA","OR"):
        X=[x for x in R if x["m"]==m and x["a"]==a]
        runs=sum(x["res"] for x in X)
        maj=sum(1 for t in tasks if sum(x["res"] for x in X if x["task"]==t)>=2)
        byf={f:(sum(x["res"] for x in X if x["faixa"]==f),sum(1 for x in X if x["faixa"]==f)) for f in ("grande","media","pequena")}
        cortes=sum(1 for x in X if x["stop"].startswith("budget"))
        aprov=sum(1 for x in X if x["stop"]=="concluiu" and not x["res"])
        tp=sum(1 for x in X if x["stop"]=="tests_pass" and not x["res"])
        so=sum(1 for x in X if x["res"] and x["stop"].startswith("budget"))
        crit=sum(x["crit"] for x in X); warn=sum(x["warn"] for x in X)
        print(f"{m:9}{a:6}{runs:>2}/39  {maj:>2}/13   {byf['grande'][0]}/{byf['grande'][1]}    {byf['media'][0]:>2}/{byf['media'][1]}  {byf['pequena'][0]:>2}/{byf['pequena'][1]}    {cortes:>2}     {aprov:>2}        {tp:>2}                    {so:>2}         {crit}/{warn}       {st.median(x['tok'] for x in X)/1e6:>5.2f}M      {st.median(x['wall'] for x in X):>6.0f}  {sum(x['usd'] for x in X):>6.2f}")
        cell[(m,a)]=X
print("\n== Pareamento run a run (mesmo modelo, tarefa, repetição = mesma semente): McNemar exato bilateral")
def mcnemar(pairs):
    b=sum(1 for sa,or_ in pairs if or_ and not sa); c=sum(1 for sa,or_ in pairs if sa and not or_)
    return b,c,binom_two_sided(b,b+c)
allpairs=[]; byband=collections.defaultdict(list); bymodel=collections.defaultdict(list)
for m in roots:
    for t in tasks:
        for rep in (1,2,3):
            sa=[x for x in cell[(m,"SA")] if x["task"]==t and x["rep"]==rep]; o=[x for x in cell[(m,"OR")] if x["task"]==t and x["rep"]==rep]
            if len(sa)==1 and len(o)==1:
                pr=(sa[0]["res"],o[0]["res"]); allpairs.append(pr); byband[faixa[t]].append(pr); bymodel[m].append(pr)
b,c,p=mcnemar(allpairs); print(f"  todos os 3 modelos: {len(allpairs)} pares; OR ganha {b}, SA ganha {c}, empates {len(allpairs)-b-c}; SA {sum(s for s,_ in allpairs)}/117, OR {sum(o for _,o in allpairs)}/117; p={p:.3f}")
for m in roots:
    b,c,p=mcnemar(bymodel[m]); print(f"  {m:9}: OR ganha {b}, SA ganha {c}, p={p:.3f}")
for f in ("grande","media","pequena"):
    b,c,p=mcnemar(byband[f]); n=len(byband[f]); print(f"  faixa {f:8}: {n} pares; SA {sum(s for s,_ in byband[f])}/{n}, OR {sum(o for _,o in byband[f])}/{n}; OR ganha {b}, SA ganha {c}, p={p:.3f}")
print("\n== Pareamento por tarefa×modelo (39 pares; valor = resolvidos em 3 repetições): sinal exato e Wilcoxon exato")
d=[]
for m in roots:
    for t in tasks:
        d.append(sum(x["res"] for x in cell[(m,"OR")] if x["task"]==t)-sum(x["res"] for x in cell[(m,"SA")] if x["task"]==t))
pos=sum(1 for x in d if x>0); neg=sum(1 for x in d if x<0)
W,pw,n=wilcoxon_exact(d) if len([x for x in d if x])<=20 else (None,None,None)
print(f"  OR melhor em {pos}, SA melhor em {neg}, empate em {len(d)-pos-neg}; sinal p={binom_two_sided(pos,pos+neg):.3f}; soma das diferenças {sum(d):+d} runs; Wilcoxon exato W={W} n={n} p={pw}")
print("\n== Métrica 2/3 agregada: tokens e tempo por run, mediana por braço e modelo, só runs resolvidos pelos dois braços na mesma (tarefa,rep)")
for m in roots:
    both=[(sa,o) for sa,o in ((next(x for x in cell[(m,'SA')] if x['task']==t and x['rep']==r),next(x for x in cell[(m,'OR')] if x['task']==t and x['rep']==r)) for t in tasks for r in (1,2,3)) if sa["res"] and o["res"]]
    dt=[o["tok"]-sa["tok"] for sa,o in both]; dw=[o["wall"]-sa["wall"] for sa,o in both]
    print(f"  {m:9}: {len(both)} pares resolvidos por ambos; tokens mediana SA {st.median(sa['tok'] for sa,_ in both)/1e3:.0f}k OR {st.median(o['tok'] for _,o in both)/1e3:.0f}k (OR/SA={st.median(o['tok']/sa['tok'] for sa,o in both):.2f}); parede mediana SA {st.median(sa['wall'] for sa,_ in both):.0f}s OR {st.median(o['wall'] for _,o in both):.0f}s; US$ por run resolvido SA {st.mean(sa['usd'] for sa,_ in both):.3f} OR {st.mean(o['usd'] for _,o in both):.3f}")
print("\n== Consistência (métrica 4): tarefas resolvidas nas 3 repetições / resolvidas ao menos uma vez")
for m in roots:
    for a in ("SA","OR"):
        per={t:sum(x["res"] for x in cell[(m,a)] if x["task"]==t) for t in tasks}
        print(f"  {m:9}{a}: {sum(1 for v in per.values() if v==3)}/{sum(1 for v in per.values() if v>=1)}  (1 de 3: {sum(1 for v in per.values() if v==1)}, 2 de 3: {sum(1 for v in per.values() if v==2)})")
print("\n== Progresso parcial nos não resolvidos: fração média de ocultos passados")
for m in roots:
    for a in ("SA","OR"):
        nr=[x for x in cell[(m,a)] if not x["res"]]
        print(f"  {m:9}{a}: {len(nr)} não resolvidos; ocultos passados média {st.mean(x['f2p']/x['f2pt'] for x in nr):.2f}; zero ocultos: {sum(1 for x in nr if x['f2p']==0)}; todos ocultos mas regressão/outro: {sum(1 for x in nr if x['f2p']==x['f2pt'])}")
print("\n== Patches vazios (achado da revisão de código: houve_mudanca contaminado por arquivo não rastreado)")
for x in R:
    if x["psize"] is not None and x["psize"]==0: print(f"  patch vazio: {x['m']} {x['a']} {x['task']} rep{x['rep']} res={x['res']} stop={x['stop']}")
print("  (fim da lista; nenhuma linha acima = nenhum patch vazio)")
print("\n== Δ complexidade ciclomática média (métrica 5), mediana por braço, runs resolvidos")
for m in roots:
    for a in ("SA","OR"):
        v=[x["cc"] for x in cell[(m,a)] if x["res"] and x["cc"] is not None]
        print(f"  {m:9}{a}: n={len(v)} mediana {st.median(v) if v else float('nan'):+.3f}")
print("\n== Poder (simulação): 13 tarefas, 3 repetições, sinal exato bilateral sobre a maioria por tarefa; p_SA por tarefa = taxa agregada observada do SA (9 runs)")
random.seed(20260820)
pSA={t:sum(x["res"] for m in roots for x in cell[(m,"SA")] if x["task"]==t)/9 for t in tasks}
def power(delta,ntasks,sims=4000):
    hits=0
    for _ in range(sims):
        ts=[random.choice(tasks) for _ in range(ntasks)] if ntasks!=13 else tasks
        pos=neg=0
        for t in ts:
            a=sum(random.random()<pSA[t] for _ in range(3))>=2; b=sum(random.random()<min(1,pSA[t]+delta) for _ in range(3))>=2
            pos+=b and not a; neg+=a and not b
        if pos+neg>0 and binom_two_sided(pos,pos+neg)<0.05: hits+=1
    return hits/sims
for delta in (0.0,0.1,0.2,0.3):
    print(f"  Δ={delta:.1f}: poder com 13 tarefas = {power(delta,13):.2f}; com 30 = {power(delta,30):.2f}; com 60 = {power(delta,60):.2f}")

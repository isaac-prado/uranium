# Rodar da raiz do repositório: python3 scripts/exploratorio_orquestrado.py > docs/tcc/dados/coleta-deepseek/exploratorio-orquestrado.txt
# Lê result.json/summary.json/events.jsonl das coletas versionadas (docs/tcc/dados/coleta, coleta-r2, coleta-r4) e das replicações (runs/coleta-deepseek, runs/coleta-devstral).
"""Análise exploratória (pós-hoc, declarada) dos pontos em que o orquestrado se destaca e dos mecanismos.
Mesmas fontes do agregado-tres-modelos.txt: Qwen = SA pareado (coleta + 9 runs de coleta-r2) e OR rodada 4; DeepSeek; Devstral. 234 runs."""
import json, glob, os, collections, statistics as st, math
from math import comb
roots={"Qwen":{"SA":"docs/tcc/dados/coleta","OR":"docs/tcc/dados/coleta-r4"},
       "DeepSeek":{"SA":"runs/coleta-deepseek","OR":"runs/coleta-deepseek"},
       "Devstral":{"SA":"runs/coleta-devstral","OR":"runs/coleta-devstral"}}
armname={"SA":"single-agent","OR":"orchestration"}
REC={"pygments-0001","sqlite-utils-0002","tomlkit-0004"}
def fontes(m,a,root):
    for p in glob.glob(f"{root}/*/{armname[a]}/rep*/attempt*/result.json"):
        if m=="Qwen" and a=="SA" and p.split("/")[-5] in REC: continue
        yield p
    if m=="Qwen" and a=="SA":
        for t in REC: yield from glob.glob(f"docs/tcc/dados/coleta-r2/{t}/single-agent/rep*/attempt*/result.json")
def evs(p):
    f=os.path.join(os.path.dirname(p),"events.jsonl")
    return [json.loads(l) for l in open(f)] if os.path.exists(f) else []
R=[]
for m,d in roots.items():
    for a,root in d.items():
        for p in fontes(m,a,root):
            r=json.load(open(p)); s=json.load(open(p.replace("result.json","summary.json")))
            E=evs(p)
            calls=[e for e in E if e["event_type"]=="llm_call"]
            tests=[e for e in E if e["event_type"]=="test_run"]
            vals=[e for e in E if e["event_type"]=="validation"]
            mems=[e for e in E if e["event_type"]=="memory"]
            plans=[e for e in E if e["event_type"]=="plan"]
            x=dict(m=m,a=a,task=r["task_id"],rep=r["repetition"],faixa=r["faixa"],res=bool(r["resolved"]),
                stop=s["stop_reason"],turns=s["turns"],tok=r["cost"]["tokens_total"],tokp=r["cost"]["tokens_prompt"],
                usd=r["cost"]["cost_usd"],wall=r["cost"]["wall_seconds"],calls=r["cost"]["llm_calls"],
                crit=r["cheat"]["critical_count"],warn=r["cheat"]["warning_count"],
                f2p=r["oracle"]["f2p_passed"],f2pt=r["oracle"]["f2p_total"],
                p2pfail=r["oracle"]["p2p"]["failed"]+r["oracle"]["p2p"]["errors"],
                cc=(r.get("quality") or {}).get("cc_mean_delta"),
                test_runs=len(tests), greens=sum(1 for t in tests if t["payload"].get("green")),
                prompt_per_call=(r["cost"]["tokens_prompt"]/max(1,r["cost"]["llm_calls"])),
                path=p)
            # turno do primeiro verde
            fg=None
            for t in tests:
                if t["payload"].get("green"):
                    fg=t.get("turn"); 
                    if fg is None:
                        # OR: test_run do validador não tem turno; usa o turno do memory anterior
                        prev=[e for e in E if e["seq"]<t["seq"] and e["event_type"]=="memory"]
                        fg=sum(int(pm["payload"]["turnos"]) for pm in prev) if prev else None
                    break
            x["turn_first_green"]=fg
            if a=="OR":
                # ciclos: memory_i -> test_run_i -> validation final_i (sem 'scope')
                finals=[v for v in vals if v["payload"].get("scope")!="subtask"]
                subs=[v for v in vals if v["payload"].get("scope")=="subtask"]
                x["n_cycles"]=len(mems); x["n_final"]=len(finals)
                x["n_sub_ok"]=sum(1 for v in subs if v["payload"]["is_valid"]); x["n_sub"]=len(subs)
                x["n_subtasks"]=None; x["replans"]=0
                for pl in plans:
                    if pl["payload"].get("evento")=="plano":
                        x["n_subtasks"]=len(pl["payload"].get("subtasks") or []); x["replans"]=pl["payload"].get("replans",0)
                    if pl["payload"].get("evento")=="replano": x["replans"]=(x["replans"] or 0)+1
                # rejeições finais com suíte verde, e escritas depois
                rej_green=0; writes_after_rej=False; first_rej_green_seq=None; approved=False
                for v in finals:
                    tr=[t for t in tests if t["seq"]<v["seq"]]
                    green=bool(tr and tr[-1]["payload"].get("green"))
                    if v["payload"]["is_valid"]: approved=True
                    elif green:
                        rej_green+=1
                        if first_rej_green_seq is None: first_rej_green_seq=v["seq"]
                if first_rej_green_seq is not None:
                    writes_after_rej=any(pm["seq"]>first_rej_green_seq and pm["payload"].get("arquivos_escritos") for pm in mems)
                x["rej_green"]=rej_green; x["writes_after_rej"]=writes_after_rej; x["approved"]=approved
                x["strict_coerced"]=sum(1 for v in finals if v["payload"].get("strict_coerced"))
                # turnos gastos depois do primeiro verde
                x["turns_after_green"]=(x["turns"]-fg) if fg is not None else None
            else:
                x["turns_after_green"]=0 if x["stop"]=="tests_pass" else None
            R.append(x)
print(f"runs lidos: {len(R)}")
tasks=sorted({x["task"] for x in R}); faixa={x["task"]:x["faixa"] for x in R}
def get(m,a,t=None,rep=None):
    return [x for x in R if x["m"]==m and x["a"]==a and (t is None or x["task"]==t) and (rep is None or x["rep"]==rep)]
def binom2(k,n):
    if n==0: return 1.0
    return min(1.0,sum(comb(n,i) for i in range(n+1) if abs(i-n/2)>=abs(k-n/2))/2**n)
def pairs(filter_=lambda m,t,rep:True):
    P=[]
    for m in roots:
        for t in tasks:
            for rep in (1,2,3):
                if not filter_(m,t,rep): continue
                sa=get(m,"SA",t,rep); o=get(m,"OR",t,rep)
                if len(sa)==1 and len(o)==1: P.append((m,t,rep,sa[0],o[0]))
    return P
def mcn(P):
    b=sum(1 for *_,sa,o in P if o["res"] and not sa["res"]); c=sum(1 for *_,sa,o in P if sa["res"] and not o["res"])
    return b,c,binom2(b,b+c)
def ic_pareado(P):
    """IC 95% de Wald para a diferença de proporções pareadas (OR - SA)."""
    n=len(P); b=sum(1 for *_,sa,o in P if o["res"] and not sa["res"]); c=sum(1 for *_,sa,o in P if sa["res"] and not o["res"])
    d=(b-c)/n; se=math.sqrt((b+c)-(b-c)**2/n)/n if n else 0
    return d, d-1.96*se, d+1.96*se

print("\n======== 1. Faixa grande: de onde vem o sinal (por tarefa, por modelo)")
for f in ("grande","media","pequena"):
    print(f"-- faixa {f}")
    for t in [t for t in tasks if faixa[t]==f]:
        row=[]
        for m in roots:
            sa=sum(x["res"] for x in get(m,"SA",t)); o=sum(x["res"] for x in get(m,"OR",t)); row.append(f"{m}: SA {sa}/3 OR {o}/3")
        tot_sa=sum(x["res"] for m in roots for x in get(m,"SA",t)); tot_o=sum(x["res"] for m in roots for x in get(m,"OR",t))
        print(f"  {t:18} {' | '.join(row)}  => SA {tot_sa}/9 OR {tot_o}/9")
    P=pairs(lambda m,t,rep: faixa[t]==f); b,c,p=mcn(P); d,lo,hi=ic_pareado(P)
    print(f"  pares {len(P)}: OR ganha {b}, SA ganha {c}, McNemar p={p:.3f}; diferença OR-SA {d:+.3f} IC95 [{lo:+.3f}, {hi:+.3f}]")

print("\n======== 2. Não inferioridade: diferença pareada OR-SA e IC 95% (todos os pares, por modelo)")
P=pairs(); b,c,p=mcn(P); d,lo,hi=ic_pareado(P)
print(f"todos: n={len(P)} OR {sum(o['res'] for *_,o in P)} SA {sum(sa['res'] for *_,sa,_ in P)}; OR ganha {b} SA ganha {c} p={p:.3f}; dif {d:+.3f} IC95 [{lo:+.3f},{hi:+.3f}]")
for m in roots:
    P=pairs(lambda mm,t,rep: mm==m); b,c,p=mcn(P); d,lo,hi=ic_pareado(P)
    print(f"{m:9}: n={len(P)} OR ganha {b} SA ganha {c} p={p:.3f}; dif {d:+.3f} IC95 [{lo:+.3f},{hi:+.3f}]")

print("\n======== 3. Sensibilidade: deixar uma tarefa de fora (OR-SA em runs, 117 pares)")
P=pairs()
base=sum(o["res"] for *_,o in P)-sum(sa["res"] for *_,sa,_ in P)
print(f"base: OR-SA = {base:+d}")
for t in tasks:
    Q=[q for q in P if q[1]!=t]; b,c,p=mcn(Q)
    print(f"  sem {t:18}: OR-SA = {sum(o['res'] for *_,o in Q)-sum(sa['res'] for *_,sa,_ in Q):+d}  (OR ganha {b}, SA ganha {c}, p={p:.3f})")

print("\n======== 4. Pares discordantes (mesma semente): parada do SA e trajetória do OR")
for m in roots:
    print(f"-- {m}")
    for (mm,t,rep,sa,o) in pairs(lambda mm,t,rep: mm==m):
        if sa["res"]==o["res"]: continue
        who="OR" if o["res"] else "SA"
        print(f"  {t:18} rep{rep} vence {who:2} | SA: {sa['stop'][:22]:22} f2p {sa['f2p']}/{sa['f2pt']} turns {sa['turns']:3} tok {sa['tok']/1e6:4.2f}M | OR: {o['stop'][:22]:22} f2p {o['f2p']}/{o['f2pt']} turns {o['turns']:3} tok {o['tok']/1e6:4.2f}M sub {o['n_subtasks']} ciclos {o['n_cycles']} rej_verde {o['rej_green']} escreveu_depois {o['writes_after_rej']}")

print("\n======== 5. Mecanismos do revisor (OR) e do operador (SA), por modelo")
print(f"{'modelo':9}{'braço':6}{'parou_sozinho':14}{'…errado':9}{'corte':7}{'…resolvido':12}{'rej_verde_runs':15}{'resgate?':10}{'f2p parcial não-res':20}{'p2p quebrado':13}{'turnos med':11}{'turnos após verde med':22}")
for m in roots:
    for a in ("SA","OR"):
        X=get(m,a)
        vol=[x for x in X if x["stop"] in ("tests_pass","concluiu")]; vol_err=[x for x in vol if not x["res"]]
        cut=[x for x in X if x["stop"].startswith("budget")]; cut_res=[x for x in cut if x["res"]]
        rejg=[x for x in X if a=="OR" and x["rej_green"]>0]
        resg=[x for x in rejg if x["res"] and x["writes_after_rej"]]
        nores=[x for x in X if not x["res"]]
        partial=st.mean(x["f2p"]/x["f2pt"] for x in nores) if nores else float("nan")
        p2p=sum(1 for x in X if x["p2pfail"]>0)
        tag=[x["turns_after_green"] for x in X if x.get("turns_after_green") is not None]
        print(f"{m:9}{a:6}{len(vol):>6}/39      {len(vol_err):>3}      {len(cut):>3}    {len(cut_res):>4}        {len(rejg):>4}          {len(resg):>4}       {partial:>6.2f}              {p2p:>3}          {st.median(x['turns'] for x in X):>5.0f}      {(st.median(tag) if tag else float('nan')):>6.0f}")
print("legenda: parou_sozinho = tests_pass (SA) ou concluiu (OR); …errado = parou sozinho e oráculo oculto reprovou; corte = orçamento; …resolvido = cortado mas oráculo aprovou (no OR: revisor nunca aprovou um patch certo); rej_verde_runs = runs em que a revisão final reprovou com suíte verde; resgate? = desses, resolvidos com escrita de arquivo depois da reprovação; f2p parcial = fração média de testes ocultos passando nos runs NÃO resolvidos; p2p quebrado = runs com regressão em teste que passava.")

print("\n======== 6. Custo por braço e modelo (medianas) e explicação do token")
print(f"{'modelo':9}{'braço':6}{'tok total':11}{'prompt/chamada':16}{'chamadas':10}{'turnos':8}{'parede s':10}{'US$ total':10}{'US$/run resolvido':18}")
for m in roots:
    for a in ("SA","OR"):
        X=get(m,a); nres=sum(x["res"] for x in X)
        print(f"{m:9}{a:6}{st.median(x['tok'] for x in X)/1e6:>7.2f}M   {st.median(x['prompt_per_call'] for x in X)/1e3:>8.1f}k        {st.median(x['calls'] for x in X):>5.0f}    {st.median(x['turns'] for x in X):>5.0f}   {st.median(x['wall'] for x in X):>7.0f}   {sum(x['usd'] for x in X):>7.2f}   {sum(x['usd'] for x in X)/max(1,nres):>8.3f}")
print("-- tokens OR/SA nos pares em que os dois resolveram (mediana da razão) e nos pares em que só um resolveu")
for m in roots:
    both=[(o["tok"]/sa["tok"]) for *_,sa,o in pairs(lambda mm,t,rep: mm==m) if sa["res"] and o["res"]]
    print(f"  {m:9} ambos resolvidos n={len(both)} mediana OR/SA tokens = {st.median(both):.2f}")

print("\n======== 7. Consistência (tarefas 3/3 ou 0/3 por braço), qualidade (cc_mean_delta), avisos do detector")
for m in roots:
    for a in ("SA","OR"):
        X=get(m,a)
        cons=sum(1 for t in tasks if sum(x["res"] for x in X if x["task"]==t) in (0,3))
        full=sum(1 for t in tasks if sum(x["res"] for x in X if x["task"]==t)==3)
        ccs=[x["cc"] for x in X if x["cc"] is not None and x["res"]]
        print(f"  {m:9}{a:3} consistentes {cons}/13 (3/3: {full})  cc_mean_delta mediana nos resolvidos {st.median(ccs) if ccs else float('nan'):+.3f} (n={len(ccs)}, >0: {sum(1 for c in ccs if c>0)})  avisos {sum(x['warn'] for x in X)} críticos {sum(x['crit'] for x in X)}")

print("\n======== 8. Anatomia das tarefas que discriminam (6 células)")
for t in tasks:
    cells={(m,a):sum(x["res"] for x in get(m,a,t)) for m in roots for a in ("SA","OR")}
    tot_sa=sum(v for (m,a),v in cells.items() if a=="SA"); tot_o=sum(v for (m,a),v in cells.items() if a=="OR")
    if tot_sa==tot_o: continue
    print(f"  {t:18} {faixa[t]:8} SA {tot_sa}/9 OR {tot_o}/9  ->  {'OR' if tot_o>tot_sa else 'SA'} +{abs(tot_o-tot_sa)}")

print("\n======== 9. peewee-0002 e tomlkit-0002: planos do orquestrado")
for t in ("peewee-0002","tomlkit-0002"):
    print(f"-- {t}")
    for m in roots:
        for x in get(m,"OR",t):
            E=evs(x["path"]); pl=[e for e in E if e["event_type"]=="plan" and e["payload"].get("evento")=="plano"]
            titles=[s.get("title") for s in (pl[0]["payload"].get("subtasks") or [])] if pl else []
            mem=[e for e in E if e["event_type"]=="memory"]
            print(f"  {m:9} rep{x['rep']} res={x['res']} stop={x['stop'][:20]:20} f2p {x['f2p']}/{x['f2pt']} ciclos={len(mem)} sub={len(titles)} rej_verde={x['rej_green']} | {titles}")

print("\n======== 10. tomlkit-0002 no single-agent: a suíte quebra? (p2p, execuções da suíte, verdes)")
for m in roots:
    for x in get(m,"SA","tomlkit-0002"):
        E=evs(x["path"]); tests=[e for e in E if e["event_type"]=="test_run"]
        last=[e for e in E if e["event_type"]=="llm_call"][-1]["tokens_prompt"]
        print(f"  {m:9} rep{x['rep']} res={x['res']} stop={x['stop'][:20]:20} f2p {x['f2p']}/{x['f2pt']} p2p_quebrados={x['p2pfail']} suíte rodada {len(tests)}x verdes {x['greens']} tok {x['tok']/1e6:.2f}M prompt última chamada {last/1e3:.0f}k")
print("\n======== 11. Revisor: reprovações desperdiçadas (patch certo, sem escrita depois) e turnos após o verde, por modelo")
for m in roots:
    X=get(m,"OR")
    waste=[x for x in X if x["rej_green"]>0 and x["res"] and not x["writes_after_rej"]]
    cutres=[x for x in X if x["res"] and x["stop"].startswith("budget")]
    tag=[x["turns_after_green"] for x in X if x.get("turns_after_green") is not None]
    print(f"  {m:9} runs com reprovação-com-verde {sum(1 for x in X if x['rej_green']>0)}; dessas resolvidas sem escrever depois (reprovação inútil) {len(waste)}; resolvidas mas cortadas {len(cutres)}; turnos após 1º verde: soma {sum(tag)} de {sum(x['turns'] for x in X)} ({100*sum(tag)/sum(x['turns'] for x in X):.0f}%), mediana {st.median(tag):.0f}, n runs com verde {len(tag)}")
print("\n======== 12. Custo: totais, pior caso, e teste pareado em TODOS os pares (exploratório)")
from itertools import product
def wilcoxon_exact(d):
    d=[v for v in d if v!=0]; n=len(d)
    if n==0: return (0,1.0,0)
    order=sorted(range(n),key=lambda i:abs(d[i])); rk=[0]*n; i=0
    while i<n:
        j=i
        while j+1<n and abs(d[order[j+1]])==abs(d[order[i]]): j+=1
        for q in range(i,j+1): rk[order[q]]=(i+j)/2+1
        i=j+1
    wplus=sum(rk[i] for i in range(n) if d[i]>0); W=min(wplus,sum(rk)-wplus)
    if n>22:
        mu=n*(n+1)/4; sd=math.sqrt(n*(n+1)*(2*n+1)/24); z=(W-mu)/sd
        return (W, math.erfc(abs(z)/math.sqrt(2)), n)
    cnt=sum(1 for s in product([0,1],repeat=n) if min(sum(rk[i] for i in range(n) if s[i]), sum(rk)-sum(rk[i] for i in range(n) if s[i]))<=W)
    return (W,cnt/2**n,n)
for m in list(roots)+["todos"]:
    P=pairs() if m=="todos" else pairs(lambda mm,t,rep: mm==m)
    sa_usd=sum(sa["usd"] for *_,sa,_ in P); o_usd=sum(o["usd"] for *_,o in P)
    sa_res=sum(sa["res"] for *_,sa,_ in P); o_res=sum(o["res"] for *_,o in P)
    d=[o["tok"]-sa["tok"] for *_,sa,o in P]; W,p,n=wilcoxon_exact(d)
    du=[o["usd"]-sa["usd"] for *_,sa,o in P]; Wu,pu,nu=wilcoxon_exact(du)
    sa_cut=[sa["tok"] for *_,sa,_ in P if sa["stop"].startswith("budget")]; o_cut=[o["tok"] for *_,o in P if o["stop"].startswith("budget")]
    print(f"  {m:9} US$ SA {sa_usd:6.2f} OR {o_usd:6.2f} ({100*(o_usd/sa_usd-1):+.0f}%); US$/resolvido SA {sa_usd/sa_res:.3f} OR {o_usd/o_res:.3f} ({100*((o_usd/o_res)/(sa_usd/sa_res)-1):+.0f}%); tokens pareados: OR<SA em {sum(1 for v in d if v<0)}/{len(d)}, Wilcoxon p={p:.3f}; US$ pareado p={pu:.3f}; tokens máx SA {max(sa['tok'] for *_,sa,_ in P)/1e6:.1f}M OR {max(o['tok'] for *_,o in P)/1e6:.1f}M; runs cortados mediana tok SA {st.median(sa_cut)/1e6 if sa_cut else 0:.1f}M OR {st.median(o_cut)/1e6 if o_cut else 0:.1f}M")
print("\n======== 13. Contexto: prompt da última chamada (tamanho do contexto no fim do run), mediana e máximo por braço")
for m in roots:
    for a in ("SA","OR"):
        L=[]
        for x in get(m,a):
            E=evs(x["path"]); c=[e for e in E if e["event_type"]=="llm_call" and e["node"] in ("single_agent","developer")]
            if c: L.append(c[-1]["tokens_prompt"])
        print(f"  {m:9}{a:3} última chamada do agente/developer: mediana {st.median(L)/1e3:.0f}k máx {max(L)/1e3:.0f}k (n={len(L)})")
print("\n======== 14. Vitórias do OR nos pares discordantes: por mecanismo")
mech=collections.Counter()
for (m,t,rep,sa,o) in pairs():
    if o["res"] and not sa["res"]:
        k=("SA cortado por orçamento" if sa["stop"].startswith("budget") else "SA parou com suíte verde mas oculto reprovou")
        k2=("revisor reprovou com suíte verde e developer reescreveu" if (o["rej_green"]>0 and o["writes_after_rej"]) else "aprovado sem reprovação com verde")
        mech[(k,k2)]+=1
    if sa["res"] and not o["res"]:
        k=("OR cortado por orçamento" if o["stop"].startswith("budget") else "OR aprovado errado")
        mech[("SA vence", k)]+=1
for k,v in sorted(mech.items()): print(f"  {v:2} {k}")

print("\n======== 15. Cache: fração de tokens do prompt cobrados como cache (payload.tokens_cached, decisão 46; só DeepSeek e Devstral)")
for m in ("DeepSeek","Devstral"):
    for a in ("SA","OR"):
        fr=[]
        for x in get(m,a):
            pr=ca=0
            for e in evs(x["path"]):
                if e["event_type"]=="llm_call": pr+=e["tokens_prompt"]; ca+=(e["payload"].get("tokens_cached") or 0)
            if pr: fr.append(ca/pr)
        print(f"  {m:9}{a:3} mediana {st.median(fr):.2f} (n={len(fr)})")
print("  leitura: o single-agent reaproveita mais prefixo; onde o provedor não dá desconto de cache (Mistral), o custo real do SA sobe mais que o do OR.")

print("\n======== 16. Estabilidade por tarefa nas oito configurações do orquestrado (Qwen, rodadas 1 a 8 = 24 runs) vs SA pareado (3 runs)")
rounds={"r1":"docs/tcc/dados/coleta","r2":"docs/tcc/dados/coleta-r2","r3":"docs/tcc/dados/coleta-r3","r4":"docs/tcc/dados/coleta-r4","r5":"docs/tcc/dados/coleta-r5","r6":"docs/tcc/dados/coleta-r6","r7":"docs/tcc/dados/coleta-r7","r8":"docs/tcc/dados/coleta-r8"}
for t in tasks:
    row=[]; tot=[0,0]
    for r,root in rounds.items():
        ps=glob.glob(f"{root}/{t}/orchestration/rep*/attempt*/result.json")
        res=sum(json.load(open(p))["resolved"] for p in ps); row.append(f"{res}/{len(ps)}"); tot[0]+=res; tot[1]+=len(ps)
    sares=sum(x["res"] for x in get("Qwen","SA",t))
    print(f"  {t:18} {faixa[t]:8} OR r1..r8 {' '.join(row)} = {tot[0]:2}/{tot[1]}  SA {sares}/3")

print("\n======== 17. peewee-0002 no orquestrado: ciclos (turnos, sub-tarefa corrente, parada) e progresso oculto")
for m in roots:
    for x in get(m,"OR","peewee-0002"):
        cyc=[(int(e["payload"]["turnos"]), e["payload"].get("subtarefa"), e["payload"]["parada"].split(":")[0]) for e in evs(x["path"]) if e["event_type"]=="memory"]
        print(f"  {m:9} rep{x['rep']} f2p {x['f2p']}/{x['f2pt']} stop={x['stop'][:17]:17} ciclos={cyc}")
print("  leitura: todos os 9 planos têm 6 sub-tarefas (uma por defeito); o developer bate o teto de 40 turnos do ciclo na sub-tarefa 1 ou 2 e o orçamento de 120 acaba com no máximo 3 sub-tarefas iniciadas. O single-agent recebe os seis defeitos de uma vez e resolve 4/9.")

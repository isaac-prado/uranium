# Rodar da raiz do repositório: python3 scripts/por_tarefa_tres_modelos.py > docs/tcc/dados/coleta-deepseek/por-tarefa-tres-modelos.txt
# A nota final do arquivo versionado (reprodução do oráculo na tomlkit-0004, 29/10/2026) foi acrescentada à mão.
# Lê result.json/summary.json/events.jsonl das coletas versionadas (docs/tcc/dados/coleta, coleta-r2, coleta-r4) e das replicações (runs/coleta-deepseek, runs/coleta-devstral).
"""Tabela por tarefa das seis células (3 modelos x 2 braços), lida dos result.json/summary.json.
Gerado em 29/10/2026 para a síntese de docs/tcc/26-replicacao.md §10."""
import json, glob, os, collections
roots = {("Qwen","SA"):"docs/tcc/dados/coleta", ("Qwen","OR"):"docs/tcc/dados/coleta-r4",
         ("DeepSeek","SA"):"runs/coleta-deepseek", ("DeepSeek","OR"):"runs/coleta-deepseek",
         ("Devstral","SA"):"runs/coleta-devstral", ("Devstral","OR"):"runs/coleta-devstral"}
armname = {"SA":"single-agent","OR":"orchestration"}
tab = collections.defaultdict(lambda: collections.defaultdict(list)); faixa = {}
RECONSTRUIDAS={"pygments-0001","sqlite-utils-0002","tomlkit-0004"}  # decisão 27: SA pareado usa os 9 runs refeitos em coleta-r2
def _fontes(m,a,root):
    for p in glob.glob(f"{root}/*/{armname[a]}/rep*/attempt*/result.json"):
        if m=="Qwen" and a=="SA" and p.split("/")[-5] in RECONSTRUIDAS: continue
        yield p
    if m=="Qwen" and a=="SA":
        for t in RECONSTRUIDAS: yield from glob.glob(f"docs/tcc/dados/coleta-r2/{t}/single-agent/rep*/attempt*/result.json")
for (m,a),root in roots.items():
    for p in _fontes(m,a,root):
        r = json.load(open(p)); s = json.load(open(os.path.join(os.path.dirname(p),"summary.json")))
        faixa[r["task_id"]] = r["faixa"]; o = r["oracle"]
        tab[r["task_id"]][(m,a)].append(dict(res=bool(r["resolved"]), stop=s["stop_reason"], turns=s["turns"],
            f2p=f"{o['f2p_passed']}/{o['f2p_total']}", fails=o["f2p"]["failing_node_ids"], rep=r["repetition"]))
cols = list(roots)
print("Fontes: Qwen SA = single-agent pareado (docs/tcc/dados/coleta, estudo principal, com pygments-0001, sqlite-utils-0002 e tomlkit-0004")
print("        substituídas pelos 9 runs refeitos em docs/tcc/dados/coleta-r2 após a decisão 27), Qwen OR = docs/tcc/dados/coleta-r4 (rodada 4),")
print("        DeepSeek e Devstral = runs/coleta-deepseek e runs/coleta-devstral (versionados em docs/tcc/dados/coleta-*).")
print("Célula = runs resolvidos / 3 repetições.\n")
print(f"{'tarefa':18}{'faixa':9}" + "".join(f"{m[:4]}-{a:<6}" for m,a in cols) + "total")
ceil, floor = [], []
for t in sorted(tab, key=lambda t:(faixa[t],t)):
    cells = [sum(x['res'] for x in tab[t][c]) for c in cols]; tot = sum(cells)
    print(f"{t:18}{faixa[t]:9}" + "".join(f"{n}/3       " for n in cells) + f"{tot}/18")
    if tot == 18: ceil.append(t)
    if tot == 0: floor.append(t)
print(f"\nTeto (18/18 nas seis células): {', '.join(ceil)}")
print(f"Piso (0/18 nas seis células): {', '.join(floor)}")
print(f"Discriminam (entre 1 e 17): {13-len(ceil)-len(floor)} de 13 tarefas")
print("\nTarefas cuja célula varia de 0/3 a 3/3 conforme o modelo (prova de que a tarefa é solúvel no harness):")
for t in sorted(tab, key=lambda t:(faixa[t],t)):
    cells = {c: sum(x['res'] for x in tab[t][c]) for c in cols}
    if min(cells.values()) == 0 and max(cells.values()) == 3:
        print(f"  {t}: " + ", ".join(f"{m[:4]}-{a}={n}/3" for (m,a),n in cells.items()))
for task in ("tomlkit-0004","peewee-0002"):
    print(f"\n== {task}: runs não resolvidos (turnos, stop_reason, ocultos passados, testes ocultos que falham)")
    cnt = collections.Counter(); n = 0
    for c in cols:
        for x in sorted(tab[task][c], key=lambda x:x['rep']):
            n += 1; cnt.update(x['fails'])
            if not x['res']:
                print(f"  {c[0][:4]}-{c[1]} rep{x['rep']} turns={x['turns']:3} f2p={x['f2p']:4} {x['stop'][:34]:34} | " + ", ".join(f.split('::')[-1] for f in x['fails']))
    print(f"  frequência de falha em {n} runs:")
    for k,v in cnt.most_common(): print(f"    {v:2}  {k}")

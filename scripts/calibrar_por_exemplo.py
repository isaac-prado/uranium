#!/usr/bin/env python3
"""Calibração offline da comparação POR EXEMPLO do enunciado (rodada 8, decisão 48) sobre coletas gravadas:
Uso: .venv/bin/python scripts/calibrar_por_exemplo.py <raiz da coleta>

última revisão final de cada run → anotar_comparacoes → linhas encontradas / NÃO encontradas.
Barreira dura hipotética: "revisor não pode aprovar com linha NÃO encontrada"."""
import glob, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.enunciado import anotar_comparacoes, sem_cercas
from src.agents.validator import _codigo_python
raiz = sys.argv[1]  # raiz da coleta: <tarefa>/orchestration/rep*/attempt*/
tot = {}; detalhe = []
for task in sorted(os.listdir(raiz)):
    st = f"tasks/{task}/statement.md"
    if not os.path.exists(st): continue
    enunciado = open(st, encoding="utf-8").read()
    for rep in sorted(glob.glob(f"{raiz}/{task}/orchestration/rep*")):
        att = sorted(glob.glob(rep + "/attempt*"))
        if not att or not os.path.exists(att[-1] + "/result.json"): continue
        r = json.load(open(att[-1] + "/result.json"))
        ev = [json.loads(l) for l in open(att[-1] + "/events.jsonl") if l.strip()]
        intent = next((e["payload"] for e in ev if e["event_type"] == "intent"), None)
        finais = [e for e in ev if e["event_type"] == "validation" and e["payload"].get("scope") != "subtask"]
        if not intent or not finais: continue
        blocos = intent.get("reproduction") or []
        codigos = {i: (lambda c: sem_cercas(c) if c else None)(_codigo_python(b)) for i, b in enumerate(blocos, 1)}
        ult = finais[-1]["payload"]; aprovou = bool(ult.get("is_valid"))
        execs = [dict(x) for x in (ult.get("executions") or [])]
        for x in execs: x.pop("comparacao_enunciado", None); x.pop("exemplo", None); x.pop("blocos_do_exemplo", None)
        anotar_comparacoes(execs, codigos, enunciado)
        comp = [c for x in execs for c in (x.get("comparacao_enunciado") or [])]
        if not comp: classe = "sem par"
        elif any(c["estado"] == "nao_encontrada" for c in comp): classe = "faltam"
        elif all(c["estado"] == "encontrada" for c in comp): classe = "todas"
        else: classe = "nao verificavel"
        k = ("resolvido" if r["resolved"] else "NÃO", "aprovou" if aprovou else "reprovou", classe)
        tot[k] = tot.get(k, 0) + 1
        if comp and not aprovou:
            detalhe.append(f"  {task} {os.path.basename(rep)}: oráculo={'resolvido' if r['resolved'] else 'NÃO'} reprovou classe={classe}")
        if comp and aprovou:
            detalhe.append(f"  {task} {os.path.basename(rep)}: oráculo={'resolvido' if r['resolved'] else 'NÃO'} aprovou linhas={sum(1 for c in comp if c['estado']=='encontrada')} encontradas / {sum(1 for c in comp if c['estado']!='encontrada')} faltam")
print("\n".join(detalhe))
print("--- totais (oráculo, revisor, linhas pareadas):")
for k, v in sorted(tot.items()): print("  ", k, v)
fn = tot.get(("resolvido","aprovou","faltam"),0); catch = tot.get(("NÃO","aprovou","faltam"),0); esc = tot.get(("NÃO","aprovou","todas"),0)+tot.get(("NÃO","aprovou","sem par"),0)
print(f"BARREIRA DURA: derrubaria {fn} run(s) resolvido(s); pegaria {catch} aprovação(ões) errada(s); escapariam {esc}")

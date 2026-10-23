"""
Conta, por coleta, as revisões de sub-tarefa que aprovaram com a suíte visível vermelha
(evento `test_run` imediatamente anterior com `green: false`). Em `SUBTASK_CHECK=llm`
o revisor de sub-tarefa recebe o diff e as execuções, não o resultado da suíte
(`validator._build_subtask_review_prompt`); este script mede com que frequência isso
importou. Uso: .venv/bin/python scripts/subtarefa_suite_vermelha.py runs/coleta-r4 runs/coleta-r7 ...
"""
import glob
import json
import sys


def contar(raiz: str) -> None:
    runs = tot_sub = aprovadas = aprovadas_vermelhas = 0
    com_vermelha: dict[str, bool] = {}
    for f in sorted(glob.glob(f"{raiz}/*/orchestration/rep*/attempt*/events.jsonl")):
        pasta = f.rsplit("/", 1)[0]
        try:
            resolvido = bool(json.load(open(f"{pasta}/result.json")).get("resolved"))
        except (OSError, ValueError):
            resolvido = False
        eventos = [json.loads(linha) for linha in open(f) if linha.strip()]
        if not any(e["event_type"] == "run_end" for e in eventos):
            continue
        runs += 1
        verde = None
        for e in eventos:
            carga = e.get("payload") or {}
            if e["event_type"] == "test_run":
                verde = carga.get("green")
            elif e["event_type"] == "validation" and carga.get("scope") == "subtask":
                tot_sub += 1
                if carga.get("is_valid"):
                    aprovadas += 1
                    if verde is False:
                        aprovadas_vermelhas += 1
                        com_vermelha[pasta] = resolvido
    nao_resolvidos = sum(1 for r in com_vermelha.values() if not r)
    print(
        f"{raiz}: runs={runs} revisões de sub-tarefa={tot_sub} aprovadas={aprovadas} "
        f"aprovadas com suíte vermelha={aprovadas_vermelhas} em {len(com_vermelha)} run(s) "
        f"({nao_resolvidos} não resolvido(s))"
    )
    for pasta, resolvido in sorted(com_vermelha.items()):
        print(f"    {pasta}  resolvido={resolvido}")


if __name__ == "__main__":
    for raiz in sys.argv[1:] or ("runs/coleta-r4", "runs/coleta-r7", "runs/fumaca-r8", "runs/fumaca-r8-strict"):
        contar(raiz)

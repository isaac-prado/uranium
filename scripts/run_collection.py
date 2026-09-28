#!/usr/bin/env python3
"""
Coleta definitiva do E1: tarefas × braços × repetições, retomável.

    uv run python scripts/run_collection.py --repetitions 3 --workers 2
    uv run python scripts/run_collection.py --dry-run          # só o estado

Interromper e rodar de novo continua de onde parou: o estado é lido das
tentativas gravadas em `--out`. Run perdido por infraestrutura é reexecutado
até `--max-attempts`, sem contar como fracasso do braço.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.arms.collection import (  # noqa: E402
    CollectionAborted,
    inspect_cell,
    plan_cells,
    run_collection,
    save_collection_report,
)
from src.budget import RunBudget  # noqa: E402
from src.config import ConfigError, load_llm_config  # noqa: E402


def _linha(r) -> str:
    marca = {True: "resolveu", False: "não resolveu", None: "-"}[r.resolved]
    perdas = f"  ({r.lost_attempts} perdida(s))" if r.lost_attempts else ""
    return (f"  {r.status:<7} {r.task_id:<20} {r.arm:<14} rep{r.repetition:02d}  "
            f"{marca:<13} {r.stop_reason or ''}{perdas}")


def main() -> None:
    p = argparse.ArgumentParser(description="Coleta definitiva do estudo E1")
    p.add_argument("--tasks", type=Path, nargs="*",
                   help="Diretórios de tarefa (padrão: todos em tasks/)")
    p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--out", type=Path, default=Path("runs/collection"))
    p.add_argument("--workers", type=int, default=1,
                   help="Runs simultâneos. Cada um é um processo")
    p.add_argument("--max-attempts", type=int, default=3,
                   help="Tentativas por célula perdidas por infraestrutura antes de desistir")
    p.add_argument("--retry-delay", type=float, default=60.0,
                   help="Espera, em segundos, antes de repetir uma tentativa perdida")
    p.add_argument("--max-consecutive-lost", type=int, default=3,
                   help="Células perdidas em sequência que param a coleta (0 desliga)")
    p.add_argument("--model", help="Sobrepõe OPENROUTER_MODEL_NAME")
    p.add_argument("--provider", help="Sobrepõe OPENROUTER_PROVIDER")
    p.add_argument("--test-timeout", type=int, default=120)
    p.add_argument("--no-quality", action="store_true", help="Não mede MI/CC na avaliação")
    p.add_argument("--dry-run", action="store_true", help="Mostra o estado e sai")
    args = p.parse_args()

    tarefas = args.tasks or sorted(d for d in Path("tasks").iterdir() if (d / "task.json").is_file())
    celulas = plan_cells(tarefas, args.repetitions)
    estado = [inspect_cell(c, args.out) for c in celulas]
    contagem = Counter(e.status for e in estado)
    print(f"tarefas   {len(tarefas)}  ×  2 braços  ×  {args.repetitions} repetição(ões)"
          f"  =  {len(celulas)} células")
    print(f"estado    {contagem.get('done', 0)} concluídas, {contagem.get('pending', 0)} pendentes"
          f"  →  {args.out}")

    if args.dry_run:
        for e in estado:
            print(_linha(e))
        return

    overrides = {k: v for k, v in (("model", args.model), ("provider", args.provider)) if v}
    try:
        llm = load_llm_config(**overrides)
    except ConfigError as exc:
        raise SystemExit(f"configuração inválida: {exc}")
    orcamento = RunBudget.from_env()
    print(f"modelo    {llm.model} via {llm.provider}")
    print(f"orçamento {orcamento.as_manifest()}")
    print(f"workers   {args.workers}   tentativas por célula {args.max_attempts}\n")

    try:
        resultados = run_collection(
            celulas, out_root=args.out, workers=args.workers,
            max_consecutive_lost=args.max_consecutive_lost,
            on_done=lambda r: print(_linha(r), flush=True),
            llm=llm, budget=orcamento, max_attempts=args.max_attempts,
            retry_delay_s=args.retry_delay, test_timeout_s=args.test_timeout,
            measure_quality=not args.no_quality,
        )
    except CollectionAborted as exc:
        # O disco já tem tudo o que rodou; o relatório sai do estado gravado.
        save_collection_report([inspect_cell(c, args.out) for c in celulas], args.out)
        raise SystemExit(f"\ncoleta interrompida: {exc}\n"
                         "resolva a causa e rode de novo: só o que falta será executado")
    destino = save_collection_report(resultados, args.out)

    contagem = Counter(r.status for r in resultados)
    print(f"\n  {contagem.get('done', 0)} concluídas, {contagem.get('lost', 0)} perdidas"
          f"  →  {destino}")
    sys.exit(1 if contagem.get("lost") else 0)


if __name__ == "__main__":
    main()

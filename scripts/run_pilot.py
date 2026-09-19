#!/usr/bin/env python3
"""
Piloto: roda single-agent e orchestration na mesma tarefa e compara.

Calibra antes da coleta definitiva: quantos turnos um modelo real gasta, se
ele trava, quanto custa de fato. Nenhum teste com LLM falso responde isso.

    uv run python scripts/run_pilot.py --task tasks/tomlkit-0001 \
        --model qwen/qwen3-coder --provider DeepInfra

Orçamento apertado por padrão — o piloto existe para medir, não para
consumir crédito.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.arms.pilot import (  # noqa: E402
    MAX_TENTATIVAS_REEXECUCAO,
    format_report,
    reexecutar_perdidos,
    run_pilot,
    save_report,
)
from src.budget import RunBudget  # noqa: E402
from src.config import ConfigError, load_llm_config  # noqa: E402
from src.seeds import get_seed_repo  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Piloto comparativo single-agent vs orchestration")
    p.add_argument("--task", type=Path, default=Path("tasks/tomlkit-0001"))
    p.add_argument("--repetitions", type=int, default=1)
    p.add_argument("--out", type=Path, default=Path("runs/pilot"))
    p.add_argument("--model", help="Sobrepõe OPENROUTER_MODEL_NAME")
    p.add_argument("--provider", help="Sobrepõe OPENROUTER_PROVIDER")
    # Os tetos vêm do mesmo lugar da coleta definitiva (RUN_MAX_* no .env).
    # Piloto com orçamento mais apertado que a coleta não calibra a coleta:
    # mede o teto. Foi o que aconteceu na primeira rodada — o braço
    # single-agent foi cortado no turno 9 sem ter editado nada, e com folga
    # resolveu em 29 turnos e 227k tokens.
    padrao = RunBudget.from_env()
    p.add_argument("--max-turns", type=int, default=padrao.max_turns)
    p.add_argument("--max-tokens", type=int, default=padrao.max_tokens,
                   help="Teto por execução. Contém o custo se o agente entrar em ciclo")
    p.add_argument("--max-seconds", type=int, default=padrao.max_wall_seconds)
    p.add_argument("--test-timeout", type=int, default=120)
    p.add_argument("--no-eval", action="store_true", help="Só executa, não avalia")
    # E5 item 2 (G5): reexecução de run perdido por erro de provedor. Não
    # roda o piloto normal — varre --out em busca de runs perdidos e refaz
    # só esses, com a mesma semente. Ver docs/tcc/07-e5-2-reexecucao.md.
    p.add_argument(
        "--reexecutar", action="store_true",
        help="Varre --out em busca de (tarefa, braço, repetição) perdidas por erro de "
             "provedor e refaz só essas, com a mesma semente e attempt incrementado",
    )
    p.add_argument("--tasks-dir", type=Path, default=Path("tasks"),
                   help="Raiz das tarefas, usada só com --reexecutar (padrão: tasks/)")
    p.add_argument("--max-tentativas", type=int, default=MAX_TENTATIVAS_REEXECUCAO,
                   help=f"Teto de tentativas por par perdido (padrão {MAX_TENTATIVAS_REEXECUCAO})")
    args = p.parse_args()

    overrides = {k: v for k, v in (("model", args.model), ("provider", args.provider)) if v}
    try:
        llm = load_llm_config(**overrides)
    except ConfigError as exc:
        raise SystemExit(f"configuração inválida: {exc}")

    orcamento = RunBudget(
        max_tokens=args.max_tokens,
        max_wall_seconds=args.max_seconds,
        max_turns=args.max_turns,
    )

    if args.reexecutar:
        print(f"reexecução  varrendo {args.out}  (teto {args.max_tentativas} tentativa(s))")
        print(f"modelo      {llm.model} via {llm.provider}")
        print(f"orçamento   {orcamento.as_manifest()}\n")

        resultados = reexecutar_perdidos(
            args.out,
            tasks_dir=args.tasks_dir,
            llm=llm,
            budget=orcamento,
            test_timeout_s=args.test_timeout,
            evaluate=not args.no_eval,
            max_tentativas=args.max_tentativas,
        )

        if not resultados:
            print("nenhum run perdido encontrado — nada para reexecutar.\n")
            sys.exit(0)

        print(format_report(resultados, "reexecução"))
        sys.exit(0)

    from harness.taskspec import load_task

    task = load_task(args.task)
    repo = get_seed_repo(task.seed_repo_id)
    if not repo.mirror_path.exists():
        raise SystemExit(
            f"espelho ausente em {repo.mirror_path}\n"
            f"Rode: uv run python scripts/setup_mirror.py {task.seed_repo_id}"
        )

    execucoes = args.repetitions * 2
    print(f"tarefa    {task.task_id}  (base {task.base_commit[:8]})")
    print(f"modelo    {llm.model} via {llm.provider}")
    print(f"orçamento {orcamento.as_manifest()}")
    print(f"execuções {execucoes}  ({args.repetitions} repetição(ões) × 2 braços)\n")

    resultados = run_pilot(
        task_dir=args.task,
        repetitions=args.repetitions,
        out_root=args.out,
        llm=llm,
        budget=orcamento,
        test_timeout_s=args.test_timeout,
        evaluate=not args.no_eval,
    )

    print(format_report(resultados, task.task_id))
    destino = save_report(resultados, args.out / "pilot.json")
    print(f"  relatório: {destino}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()

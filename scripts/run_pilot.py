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

from src.arms.pilot import format_report, run_pilot, save_report  # noqa: E402
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
    p.add_argument("--max-turns", type=int, default=25)
    p.add_argument("--max-tokens", type=int, default=150_000,
                   help="Teto por execução. Contém o custo se o agente entrar em ciclo")
    p.add_argument("--max-seconds", type=int, default=900)
    p.add_argument("--test-timeout", type=int, default=120)
    p.add_argument("--no-eval", action="store_true", help="Só executa, não avalia")
    args = p.parse_args()

    overrides = {k: v for k, v in (("model", args.model), ("provider", args.provider)) if v}
    try:
        llm = load_llm_config(**overrides)
    except ConfigError as exc:
        raise SystemExit(f"configuração inválida: {exc}")

    from harness.taskspec import load_task

    task = load_task(args.task)
    repo = get_seed_repo(task.seed_repo_id)
    if not repo.mirror_path.exists():
        raise SystemExit(
            f"espelho ausente em {repo.mirror_path}\n"
            f"Rode: uv run python scripts/setup_mirror.py {task.seed_repo_id}"
        )

    orcamento = RunBudget(
        max_tokens=args.max_tokens,
        max_wall_seconds=args.max_seconds,
        max_turns=args.max_turns,
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

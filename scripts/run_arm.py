#!/usr/bin/env python3
"""
Executa um braço do estudo E1 sobre uma tarefa.

Mesmo caminho de execução para os dois braços; muda só o grafo compilado.
Cada run grava manifest.json, events.jsonl, summary.json, patch.diff e o
workspace modificado, que é o que o harness externo consome depois.

    uv run python scripts/run_arm.py --arm B  --task tomlkit-0001 \
        --base-commit 11e22aef --statement "Levantar erro em array malformado"

    uv run python scripts/run_arm.py --arm A2 --task tomlkit-0001 \
        --base-commit 11e22aef --statement-file tasks/tomlkit-0001/statement.md
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.arms.runner import build_run_spec, run_arm  # noqa: E402
from src.budget import RunBudget  # noqa: E402
from src.config import ConfigError, load_llm_config  # noqa: E402
from src.seeds import SEEDS, get_seed  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa um braço do estudo E1")
    parser.add_argument("--arm", required=True, choices=["A2", "B"])
    parser.add_argument("--task", required=True, help="Identificador da tarefa")
    parser.add_argument("--base-commit", required=True, help="Commit-base do repo-semente")
    parser.add_argument("--seed", default="tomlkit", choices=sorted(SEEDS))
    parser.add_argument("--statement", help="Enunciado da tarefa (texto)")
    parser.add_argument("--statement-file", type=Path, help="Arquivo com o enunciado")
    parser.add_argument(
        "--repetition", type=int, default=1,
        help="Índice da repetição (1-based). Deriva a semente do LLM: repetições "
             "diferentes produzem variabilidade, e a mesma repetição nos dois "
             "braços parte da mesma semente (padrão: 1)",
    )
    parser.add_argument("--run-id", help="Identificador do run (padrão: gerado)")
    parser.add_argument("--out", type=Path, help="Diretório de saída")
    parser.add_argument("--max-turns", type=int, help="Sobrepõe RUN_MAX_TURNS")
    parser.add_argument("--max-tokens", type=int, help="Sobrepõe RUN_MAX_TOKENS")
    parser.add_argument("--test-timeout", type=int, default=120)
    parser.add_argument("--model", help="Sobrepõe OPENROUTER_MODEL_NAME")
    parser.add_argument("--provider", help="Sobrepõe OPENROUTER_PROVIDER")
    args = parser.parse_args()

    if not (args.statement or args.statement_file):
        raise SystemExit("informe --statement ou --statement-file")
    statement = (
        args.statement_file.read_text(encoding="utf-8")
        if args.statement_file else args.statement
    )

    # Resolve o commit-base curto para o SHA completo, para o manifesto ser exato.
    seed = get_seed(args.seed)
    if not seed.mirror_path.exists():
        raise SystemExit(
            f"espelho ausente em {seed.mirror_path}.\n"
            f"Rode: uv run python scripts/setup_mirror.py {args.seed}"
        )

    orcamento = RunBudget.from_env(
        **{k: v for k, v in (("max_turns", args.max_turns),
                             ("max_tokens", args.max_tokens)) if v}
    )
    run_id = args.run_id or (
        f"{args.arm.lower()}-{args.task}-r{args.repetition:02d}-{uuid.uuid4().hex[:8]}"
    )

    overrides = {k: v for k, v in (("model", args.model), ("provider", args.provider)) if v}
    try:
        spec = build_run_spec(
            run_id=run_id, arm=args.arm, task_id=args.task, statement=statement,
            base_commit=args.base_commit, seed_id=args.seed, out_dir=args.out,
            repetition=args.repetition,
            llm=load_llm_config(**overrides),
            budget=orcamento, test_timeout_s=args.test_timeout,
        )
    except ConfigError as exc:
        raise SystemExit(f"configuração inválida: {exc}")

    print(f"braço {spec.arm} ({spec.manifest('')['topology']}) | tarefa {spec.task_id}")
    print(f"modelo {spec.llm.model} via {spec.llm.provider}")
    print(f"repetição {spec.repetition} | semente do LLM {spec.llm.seed}")
    print(f"orçamento {orcamento.as_manifest()}")
    print(f"saída {spec.out_dir}\n")

    resumo = run_arm(spec)

    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    raise SystemExit(0 if resumo["is_valid"] else 1)


if __name__ == "__main__":
    main()

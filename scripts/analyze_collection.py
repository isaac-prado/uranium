#!/usr/bin/env python3
"""
Análise pareada da coleta: teste de sinal e Wilcoxon por tarefa.

    uv run python scripts/analyze_collection.py --out runs/collection

Lê só o que a coleta gravou (`summary.json` e `result.json` de cada
tentativa). Não roda nada e não gasta crédito.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.analysis import analyze, format_analysis, load_collection  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Análise pareada da coleta do E1")
    p.add_argument("--out", type=Path, default=Path("runs/collection"),
                   help="Raiz da coleta")
    args = p.parse_args()

    analise = analyze(load_collection(args.out))
    print(format_analysis(analise))
    destino = args.out / "analysis.json"
    destino.write_text(json.dumps(analise, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(f"  →  {destino}\n")


if __name__ == "__main__":
    main()

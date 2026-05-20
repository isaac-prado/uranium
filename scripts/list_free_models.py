#!/usr/bin/env python3
"""Lista modelos free recomendados para o Uranium."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.free_models import FREE_MODELS, DEFAULT_FREE_MODEL


def main() -> None:
    print("Modelos 100% gratuitos no OpenRouter (custo $0)\n")
    print(f"Padrão atual recomendado: {DEFAULT_FREE_MODEL}\n")
    for m in FREE_MODELS:
        print(f"  {m['id']}")
        print(f"    velocidade: {m['speed']} | qualidade: {m['quality']}")
        print(f"    {m['note']}\n")
    print("Configure no .env: OPENROUTER_MODEL_NAME=<id acima>")


if __name__ == "__main__":
    main()

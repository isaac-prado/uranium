"""
Sonda de cache de prefixo do provedor pinado: duas chamadas com o mesmo
prefixo longo e perguntas diferentes, imprimindo o `usage` cru do OpenRouter e
o que `extract_call_metrics` lê dele (`tokens_cached`).

Uso (paga ~US$ 0,002 no modelo da coleta):
    uv run python scripts/cache_probe.py [--model m --provider p]

Saída de 22/10/2026 em docs/tcc/dados/sondagens/cache-deepinfra-2026-10-22.txt.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

from src.config import extract_call_metrics, get_llm, load_llm_config  # noqa: E402

PREFIXO = (
    "Você é um assistente de testes. Leia o texto e responda em uma palavra.\n\n"
    + "\n".join(
        f"Linha {i}: o pacote tomlkit preserva comentários, espaços e ordem das chaves "
        "ao reescrever um documento TOML."
        for i in range(160)
    )
)
PERGUNTAS = ("Responda só: qual pacote é citado?", "Responda só: quantas linhas numeradas há?")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--provider")
    args = parser.parse_args()
    overrides = {k: v for k, v in (("model", args.model), ("provider", args.provider)) if v}
    llm = get_llm(load_llm_config(**overrides))
    for k, pergunta in enumerate(PERGUNTAS, 1):
        t0 = time.time()
        msg = llm.invoke([SystemMessage(content=PREFIXO), HumanMessage(content=pergunta)])
        usage = (getattr(msg, "response_metadata", None) or {}).get("token_usage")
        m = extract_call_metrics(msg)
        print(f"--- chamada {k} ({time.time() - t0:.1f}s) provedor={m.provider_served} byok={m.is_byok}")
        print("usage cru:", json.dumps(usage, ensure_ascii=False))
        print(
            f"tokens_prompt={m.tokens_prompt} tokens_cached={m.tokens_cached} "
            f"completion={m.tokens_completion} cost_usd={m.cost_usd:.7f} "
            f"resposta={str(msg.content)[:40]!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

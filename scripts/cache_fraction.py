"""
Fração do prompt cobrada como leitura em cache, por coleta.

Duas medidas, lado a lado:
- `gravada`: soma de `payload.tokens_cached` dos eventos `llm_call` sobre a
  soma de `tokens_prompt` (campo gravado desde 22/10/2026; zero nas coletas
  anteriores, que não o têm);
- `inferida`: a fração x que fecha o custo pago com o preço de tabela,
  cost = p·(1−x)·ENTRADA + p·x·CACHE + c·SAÍDA, resolvida para x. É a medida
  usada nas coletas anteriores à gravação (docs/tcc/08-escolha-modelo.md, 10).

Uso:
    uv run python scripts/cache_fraction.py ROTULO=GLOB [ROTULO=GLOB ...] \
        [--in 0.30 --out 1.00 --cache 0.10]
Ex.:
    uv run python scripts/cache_fraction.py \
        "orquestrado r6=docs/tcc/dados/coleta-r6/*/orchestration/*/attempt*/events.jsonl" \
        "single-agent=runs/coleta-r2-analise/*/single-agent/*/attempt*/events.jsonl"
"""

from __future__ import annotations

import argparse
import glob
import json


def medir(paths: list[str], preco_in: float, preco_out: float, preco_cache: float) -> dict:
    p = c = cached = n = cheias = 0
    custo = 0.0
    for f in paths:
        with open(f, encoding="utf-8") as fh:
            for linha in fh:
                if '"llm_call"' not in linha:
                    continue
                e = json.loads(linha)
                if e.get("event_type") != "llm_call":
                    continue
                tp, tc = int(e.get("tokens_prompt") or 0), int(e.get("tokens_completion") or 0)
                cu = float(e.get("cost_usd") or 0.0)
                p += tp
                c += tc
                custo += cu
                n += 1
                cached += int((e.get("payload") or {}).get("tokens_cached") or 0)
                if abs(cu - (tp * preco_in + tc * preco_out) / 1e6) < 1e-9:
                    cheias += 1
    tabela = (p * preco_in + c * preco_out) / 1e6
    inferida = (p * preco_in + c * preco_out - custo * 1e6) / (p * (preco_in - preco_cache)) if p else 0.0
    return {
        "arquivos": len(paths), "chamadas": n, "tokens_prompt": p, "tokens_completion": c,
        "tokens_cached": cached, "pago_usd": round(custo, 4), "tabela_sem_cache_usd": round(tabela, 4),
        "fracao_gravada": round(cached / p, 4) if p else None, "fracao_inferida": round(inferida, 4),
        "chamadas_a_preco_cheio": cheias,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("coletas", nargs="+", help="ROTULO=GLOB de events.jsonl")
    parser.add_argument("--in", dest="preco_in", type=float, default=0.30, help="US$/M entrada (padrão 0,30)")
    parser.add_argument("--out", dest="preco_out", type=float, default=1.00, help="US$/M saída (padrão 1,00)")
    parser.add_argument("--cache", dest="preco_cache", type=float, default=0.10, help="US$/M leitura em cache (padrão 0,10)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    saida = {}
    for item in args.coletas:
        rotulo, _, padrao = item.partition("=")
        saida[rotulo] = medir(sorted(glob.glob(padrao)), args.preco_in, args.preco_out, args.preco_cache)
    if args.json:
        print(json.dumps(saida, indent=1, ensure_ascii=False))
        return 0
    print(f"preços US$/M: entrada {args.preco_in} saída {args.preco_out} cache {args.preco_cache}")
    for rotulo, m in saida.items():
        print(
            f"{rotulo:28s} arquivos={m['arquivos']:3d} chamadas={m['chamadas']:5d} "
            f"prompt={m['tokens_prompt']/1e6:7.2f}M saída={m['tokens_completion']/1e6:5.2f}M "
            f"pago=US${m['pago_usd']:6.2f} tabela=US${m['tabela_sem_cache_usd']:6.2f} "
            f"fração gravada={m['fracao_gravada']} inferida={m['fracao_inferida']:.3f} "
            f"preço cheio={m['chamadas_a_preco_cheio']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

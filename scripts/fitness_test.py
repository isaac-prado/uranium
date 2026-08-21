#!/usr/bin/env python3
"""
Teste de aptidão de modelo para os braços A2/B.

Não recomenda modelo: mede. Três coisas que decidem se um candidato serve:

  1. Conformidade de tool calling — o agente é um loop de ferramentas; um
     modelo que erra o schema não roda o experimento.
  2. Pino de provedor — todas as chamadas têm de ser servidas pelo provedor
     pinado. Se variar, a comparação entre braços perde o controle.
  3. Determinismo — mesma entrada, temperature=0 e seed fixo devem produzir
     a mesma saída. Divergência alta obriga a aumentar N de repetições.

    uv run python scripts/fitness_test.py --list-providers vendor/modelo
    uv run python scripts/fitness_test.py --model vendor/modelo --provider Fireworks -n 5
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ConfigError, LLMConfig, extract_call_metrics, get_llm  # noqa: E402

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Tarefa de sondagem: exige uma tool call com argumentos exatos. Simples o
# bastante para não medir capacidade, específica o bastante para medir
# conformidade de schema.
PROBE_PROMPT = (
    "No repositório, encontre onde a classe Container é definida. "
    "Use a ferramenta search_code com o padrão 'class Container' e path 'tomlkit'. "
    "Chame a ferramenta; não responda em texto."
)
EXPECTED_TOOL = "search_code"
EXPECTED_ARGS = {"pattern": "class Container", "path": "tomlkit"}


@dataclass
class ProbeResult:
    ok: bool
    tool_called: str | None
    args: dict | None
    args_exatos: bool
    provider_served: str | None
    tokens_total: int
    cost_usd: float
    texto: str
    erro: str | None = None


# Parâmetros que o experimento exige. Um provedor que não suporte qualquer
# um deles é recusado pelo OpenRouter quando `require_parameters: true` —
# com um 404 genérico que não diz qual faltou.
PARAMETROS_EXIGIDOS = ("tools", "seed", "temperature", "max_tokens")


def listar_provedores(model: str) -> list[str]:
    """
    Lista os provedores de um modelo, marcando quais servem ao experimento.

    Um provedor sem `seed` não permite reprodutibilidade; sem `tools`, não
    roda o agente. Consulta gratuita — nenhuma chamada de inferência.
    """
    url = f"{OPENROUTER_MODELS_URL}/{model}/endpoints"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"não foi possível consultar {model}: HTTP {exc.code}")

    aptos: list[str] = []
    for endpoint in (data.get("data") or {}).get("endpoints") or []:
        nome = endpoint.get("provider_name") or endpoint.get("name") or "?"
        suportados = set(endpoint.get("supported_parameters") or [])
        faltando = [p for p in PARAMETROS_EXIGIDOS if p not in suportados]
        if faltando:
            print(f"       {nome:24} não serve — falta: {', '.join(faltando)}")
        else:
            print(f"  APTO {nome:24} suporta todos os parâmetros exigidos")
            aptos.append(nome)

    if not aptos:
        print("\n  Nenhum provedor apto. Este modelo não pode ser usado no estudo.")
    return aptos


def _build_probe_tool():
    """Ferramenta de sondagem com o mesmo formato das ferramentas reais."""
    from langchain_core.tools import StructuredTool
    from pydantic import BaseModel, Field

    class SearchCodeArgs(BaseModel):
        pattern: str = Field(description="Padrão a buscar")
        path: str = Field(default=".", description="Subdiretório onde buscar")
        is_regex: bool = Field(default=True, description="Tratar o padrão como regex")

    return StructuredTool.from_function(
        func=lambda pattern, path=".", is_regex=True: "",
        name=EXPECTED_TOOL,
        description="Busca um padrão no código e retorna 'arquivo:linha: conteúdo'.",
        args_schema=SearchCodeArgs,
    )


def sondar(config: LLMConfig) -> ProbeResult:
    """Uma chamada de sondagem, medindo conformidade e atribuição."""
    llm = get_llm(config).bind_tools([_build_probe_tool()])
    try:
        message = llm.invoke(PROBE_PROMPT)
    except Exception as exc:
        return ProbeResult(False, None, None, False, None, 0, 0.0, "", f"{type(exc).__name__}: {exc}")

    metrics = extract_call_metrics(message)
    calls = getattr(message, "tool_calls", None) or []

    if not calls:
        return ProbeResult(
            False, None, None, False, metrics.provider_served,
            metrics.tokens_total, metrics.cost_usd,
            str(message.content)[:160], "não chamou ferramenta",
        )

    call = calls[0]
    args = call.get("args") or {}
    exatos = all(str(args.get(k, "")).strip() == v for k, v in EXPECTED_ARGS.items())

    return ProbeResult(
        ok=call.get("name") == EXPECTED_TOOL,
        tool_called=call.get("name"),
        args=args,
        args_exatos=exatos,
        provider_served=metrics.provider_served,
        tokens_total=metrics.tokens_total,
        cost_usd=metrics.cost_usd,
        texto=str(message.content)[:160],
    )


def relatar(config: LLMConfig, resultados: list[ProbeResult]) -> int:
    """Imprime o laudo e devolve o exit code (0 = apto)."""
    n = len(resultados)
    chamou = sum(r.ok for r in resultados)
    exatos = sum(r.args_exatos for r in resultados)
    provedores = Counter(r.provider_served or "(desconhecido)" for r in resultados)
    assinaturas = Counter(json.dumps(r.args, sort_keys=True) for r in resultados if r.args)
    custo = sum(r.cost_usd for r in resultados)
    tokens = sum(r.tokens_total for r in resultados)

    print(f"\n{'─' * 68}")
    print(f"  modelo   {config.model}")
    print(f"  provedor {config.provider} (pinado, allow_fallbacks=False)")
    print(f"  seed     {config.seed}   temperature {config.temperature}")
    print(f"{'─' * 68}")
    print(f"  1. tool calling      {chamou}/{n} chamaram {EXPECTED_TOOL}")
    print(f"     argumentos exatos {exatos}/{n}")
    print(f"  2. provedor servido  {dict(provedores)}")
    print(f"  3. determinismo      {len(assinaturas)} assinatura(s) distinta(s) em {n}")
    print(f"     custo total       US$ {custo:.6f}  ({tokens} tokens)")

    for r in resultados:
        if r.erro:
            print(f"     erro: {r.erro[:140]}")

    pino_ok = list(provedores) == [config.provider]
    conformidade_ok = chamou == n and exatos == n
    deterministico = len(assinaturas) <= 1

    print(f"{'─' * 68}")
    print(f"  pino de provedor     {'OK' if pino_ok else 'FALHOU — provedor variou ou não identificado'}")
    print(f"  conformidade         {'OK' if conformidade_ok else 'FALHOU'}")
    print(f"  determinismo         {'OK' if deterministico else 'DIVERGENTE — aumente N de repetições no estudo'}")

    apto = pino_ok and conformidade_ok
    print(f"\n  VEREDITO: {'APTO' if apto else 'NÃO APTO'} para os braços A2/B")
    if apto and not deterministico:
        print("  (apto, mas não determinístico — declare a variabilidade no TCC)")
    print(f"{'─' * 68}\n")
    return 0 if apto else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Teste de aptidão de modelo")
    parser.add_argument("--list-providers", metavar="MODELO",
                        help="Lista os provedores que servem um modelo e sai")
    parser.add_argument("--model", help="Sobrepõe OPENROUTER_MODEL_NAME")
    parser.add_argument("--provider", help="Sobrepõe OPENROUTER_PROVIDER")
    parser.add_argument("-n", type=int, default=5, help="Número de sondagens (padrão: 5)")
    parser.add_argument("--max-tokens", type=int, default=512,
                        help="Teto de saída por sondagem. Contém gasto em modelos com "
                             "reasoning, que queimam tokens sem isso (padrão: 512)")
    args = parser.parse_args()

    if args.list_providers:
        print(f"Provedores de {args.list_providers}:")
        listar_provedores(args.list_providers)
        return

    overrides: dict = {"max_tokens": args.max_tokens}
    overrides.update({k: v for k, v in (("model", args.model), ("provider", args.provider)) if v})
    try:
        from src.config import load_llm_config
        config = load_llm_config(**overrides)
    except ConfigError as exc:
        raise SystemExit(f"configuração inválida: {exc}")

    print(f"Sondando {config.model} via {config.provider} — {args.n} chamadas "
          f"(teto {config.max_tokens} tokens de saída)...")
    resultados = [sondar(config) for _ in range(args.n)]
    raise SystemExit(relatar(config, resultados))


if __name__ == "__main__":
    main()

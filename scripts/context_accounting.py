#!/usr/bin/env python3
"""
Contabilidade de contexto: de onde vem cada token do prompt.

Lê a trilha `events.jsonl` de execuções já feitas e reconstrói, turno a
turno, a composição do prompt do agente que escreve código, por categoria:
prompt de sistema, esquema das ferramentas, primeira mensagem, saída de cada
ferramenta (por nome), mensagens do assistente e feedback da suíte.

O ponto do exercício é o TESTE DE COMPLETUDE: o crescimento do prompt medido
pelo provedor entre um turno e o seguinte (`tokens_prompt`) tem de ser
explicado pelo que a telemetria registrou como tendo entrado no contexto
nesse intervalo. O que sobra é conteúdo não instrumentado.

Dois modos, escolhidos por execução:

- **exato**: as chamadas carregam `payload.prompt_bytes` (instrumentação de
  18/09/2026). A composição do prompt é medida em bytes, por papel de
  mensagem, e os tokens de cada chamada são repartidos na proporção dos
  bytes. A soma dos bytes de ferramenta no prompt é conferida contra a soma
  dos `bytes_read` dos eventos `tool_call`.
- **inferido**: execuções anteriores, sem `prompt_bytes`. Só os bytes das
  saídas de ferramenta e os tokens de saída do assistente são conhecidos.
  Ajusta-se por mínimos quadrados um modelo de dois parâmetros por janela,

      Δprompt_n − completion_{n−1}  ≈  a · k_n + bytes_n / c

  em que k_n é o número de mensagens de ferramenta que entraram antes da
  chamada n, a é a sobrecarga fixa de enquadramento por mensagem (tokens) e
  c é bytes por token. O resíduo por turno é a discrepância.

Uso:

    uv run python scripts/context_accounting.py runs/ --markdown
    uv run python scripts/context_accounting.py runs/ --json saida.json

Nenhuma chamada de rede. Custo zero.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.telemetry import read_events  # noqa: E402

CODE_NODES = frozenset({"single_agent", "developer"})

# A partir deste instante toda ferramenta registra `bytes_read`
# (commit 3820b1d, "toda ferramenta mede o que devolve ao modelo").
INSTRUMENTACAO_COMPLETA_DESDE = datetime(2026, 8, 27, 3, 23, 2, tzinfo=timezone.utc)


# ------------------------------------------------------------------- leitura


@dataclass
class Call:
    """Uma chamada ao modelo dentro de uma janela de contexto."""

    seq: int
    turn: int | None
    tokens_prompt: int
    tokens_completion: int
    tokens_reasoning: int
    tool_msgs: list[tuple[str, int]]      # (ferramenta, bytes_read) entrados antes desta chamada
    test_runs_before: int                 # execuções da suíte (feedback) entradas antes desta chamada
    prompt_bytes: dict[str, int] | None   # payload.prompt_bytes, quando existe
    requested: list[str]

    @property
    def tool_bytes(self) -> int:
        return sum(b for _, b in self.tool_msgs)


@dataclass
class Window:
    """Uma conversa contínua do agente que escreve código (histórico acumulado)."""

    node: str
    index: int
    calls: list[Call] = field(default_factory=list)


@dataclass
class Run:
    path: Path
    run_id: str
    arm: str
    task_id: str
    started_at: datetime | None
    windows: list[Window]
    aux_calls: list[dict[str, Any]]       # chamadas dos papéis auxiliares (prompts próprios)
    tool_calls_total: int
    tool_bytes_total: int

    @property
    def instrumentacao_completa(self) -> bool:
        return self.started_at is not None and self.started_at >= INSTRUMENTACAO_COMPLETA_DESDE

    @property
    def modo(self) -> str:
        calls = [c for w in self.windows for c in w.calls]
        return "exato" if calls and all(c.prompt_bytes for c in calls) else "inferido"


def _parse_ts(valor: Any) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None


def load_run(run_dir: Path) -> Run:
    events = read_events(run_dir / "events.jsonl")
    manifest: dict[str, Any] = {}
    if (run_dir / "manifest.json").exists():
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))

    arm = manifest.get("arm") or (events[0]["arm"] if events else "?")
    windows: list[Window] = []
    atual: Window | None = None
    pendentes: list[tuple[str, int]] = []
    test_runs_pendentes = 0
    aux: list[dict[str, Any]] = []
    tool_calls_total = 0
    tool_bytes_total = 0

    for e in sorted(events, key=lambda x: x["seq"]):
        tipo = e["event_type"]
        no = e.get("node")

        if tipo == "node_enter" and no in CODE_NODES:
            # O single_agent reentra no nó a cada turno, mas a conversa é a
            # mesma; o developer reconstrói a conversa a cada entrada.
            if atual is None or arm == "orchestration":
                atual = Window(node=no, index=len(windows) + 1)
                windows.append(atual)
            continue

        if tipo == "tool_call":
            tool_calls_total += 1
            b = int((e.get("payload") or {}).get("bytes_read") or 0)
            tool_bytes_total += b
            pendentes.append((e.get("tool_name") or "?", b))
            continue

        if tipo == "test_run":
            test_runs_pendentes += 1
            continue

        if tipo == "llm_call":
            payload = e.get("payload") or {}
            if no in CODE_NODES and atual is not None:
                atual.calls.append(Call(
                    seq=e["seq"], turn=e.get("turn"),
                    tokens_prompt=int(e.get("tokens_prompt") or 0),
                    tokens_completion=int(e.get("tokens_completion") or 0),
                    tokens_reasoning=int(e.get("tokens_reasoning") or 0),
                    tool_msgs=pendentes, test_runs_before=test_runs_pendentes,
                    prompt_bytes=payload.get("prompt_bytes"),
                    requested=list(payload.get("tool_calls_requested") or []),
                ))
                pendentes = []
                test_runs_pendentes = 0
            else:
                aux.append({
                    "node": no, "agent_role": e.get("agent_role"),
                    "tokens_prompt": int(e.get("tokens_prompt") or 0),
                    "tokens_completion": int(e.get("tokens_completion") or 0),
                    "prompt_bytes": payload.get("prompt_bytes"),
                })

    return Run(
        path=run_dir, run_id=manifest.get("run_id") or (events[0]["run_id"] if events else "?"),
        arm=arm, task_id=manifest.get("task_id") or (events[0]["task_id"] if events else "?"),
        started_at=_parse_ts(manifest.get("started_at")),
        windows=[w for w in windows if w.calls], aux_calls=aux,
        tool_calls_total=tool_calls_total, tool_bytes_total=tool_bytes_total,
    )


def find_runs(raizes: list[Path]) -> list[Path]:
    achados: list[Path] = []
    for raiz in raizes:
        if (raiz / "events.jsonl").exists():
            achados.append(raiz)
        else:
            achados.extend(p.parent for p in sorted(raiz.rglob("events.jsonl")))
    return achados


# ---------------------------------------------------------- tamanhos fixos


def tamanhos_fixos() -> dict[str, int]:
    """Bytes do prompt de sistema e do esquema das ferramentas, no código atual."""
    from src.prompts import AGENT_SYSTEM_PROMPT
    from src.tools import build_toolset

    esquema = 0
    for tool in build_toolset(None):  # type: ignore[arg-type]  # closures só tocam o ws ao invocar
        esquema += len(tool.description.encode("utf-8"))
        esquema += len(json.dumps(tool.args_schema.model_json_schema(), ensure_ascii=False).encode("utf-8"))
    return {
        "system_prompt": len(AGENT_SYSTEM_PROMPT.encode("utf-8")),
        "tool_schema": esquema,
    }


def primeira_mensagem_single_agent(task_id: str, tasks_dir: Path) -> int | None:
    """Reconstrói a primeira mensagem do agente único a partir do enunciado em disco."""
    enunciado = tasks_dir / task_id / "statement.md"
    if not enunciado.exists():
        return None
    from src.schemas.intent import StructuredIntent

    intent = StructuredIntent(
        context="", goal=enunciado.read_text(encoding="utf-8"), phases=[],
        acceptance_criteria=[], clarifications_needed=[], is_ready=True,
    )
    texto = "Tarefa:\n" + intent.model_dump_json(indent=2)
    return len(texto.encode("utf-8"))


# ------------------------------------------------------------------ ajuste


def _ols_2(rows: list[tuple[float, float, float]]) -> tuple[float, float] | None:
    """Mínimos quadrados para y ≈ a·k + b·x, sem intercepto. Devolve (a, b)."""
    skk = sum(k * k for k, _, _ in rows)
    sxx = sum(x * x for _, x, _ in rows)
    skx = sum(k * x for k, x, _ in rows)
    sky = sum(k * y for k, _, y in rows)
    sxy = sum(x * y for _, x, y in rows)
    det = skk * sxx - skx * skx
    if abs(det) < 1e-9:
        return None
    a = (sky * sxx - sxy * skx) / det
    b = (skk * sxy - skx * sky) / det
    return a, b


@dataclass
class Ledger:
    """Livro-razão de uma janela: por chamada, medido × explicado."""

    window: Window
    modo: str
    a: float | None                      # tokens fixos por mensagem de ferramenta
    c: float | None                      # bytes por token
    linhas: list[dict[str, Any]]
    discrepancia_abs_pct: float | None   # Σ|resíduo| / Σ Δprompt (chamadas 2..N)
    discrepancia_signed_pct: float | None
    nao_explicadas: list[int]            # seq das chamadas com resíduo grande


def ledger_inferido(w: Window) -> Ledger:
    calls = w.calls
    rows: list[tuple[float, float, float]] = []
    for i in range(1, len(calls)):
        prev, cur = calls[i - 1], calls[i]
        y = cur.tokens_prompt - prev.tokens_prompt - prev.tokens_completion
        rows.append((len(cur.tool_msgs), float(cur.tool_bytes), float(y)))

    fit = _ols_2(rows) if len(rows) >= 3 else None
    a, b = fit if fit else (None, None)
    c = (1.0 / b) if b and b > 0 else None

    linhas: list[dict[str, Any]] = []
    soma_abs = 0.0
    soma_signed = 0.0
    soma_delta = 0
    grandes: list[int] = []
    for i, cur in enumerate(calls):
        linha: dict[str, Any] = {
            "seq": cur.seq, "turn": cur.turn, "tokens_prompt": cur.tokens_prompt,
            "tool_msgs": len(cur.tool_msgs), "tool_bytes": cur.tool_bytes,
            "test_runs_before": cur.test_runs_before,
        }
        if i > 0:
            prev = calls[i - 1]
            delta = cur.tokens_prompt - prev.tokens_prompt
            y = delta - prev.tokens_completion
            linha.update({"delta_prompt": delta, "completion_prev": prev.tokens_completion, "a_explicar": y})
            if fit:
                pred = a * len(cur.tool_msgs) + b * cur.tool_bytes
                res = y - pred
                linha.update({"explicado": round(pred), "residuo": round(res)})
                soma_abs += abs(res)
                soma_signed += res
                soma_delta += max(delta, 0)
                if abs(res) > max(50.0, 0.25 * abs(y)):
                    grandes.append(cur.seq)
        linhas.append(linha)

    return Ledger(
        window=w, modo="inferido", a=a, c=c, linhas=linhas,
        discrepancia_abs_pct=(100 * soma_abs / soma_delta) if soma_delta else None,
        discrepancia_signed_pct=(100 * soma_signed / soma_delta) if soma_delta else None,
        nao_explicadas=grandes,
    )


def ledger_exato(w: Window) -> Ledger:
    """Com `prompt_bytes`, a composição é medida; confere-se a conta em bytes."""
    calls = w.calls
    linhas: list[dict[str, Any]] = []
    tool_bytes_acum = 0
    razoes: list[float] = []
    grandes: list[int] = []
    soma_abs = 0
    soma_tool_prompt = 0
    for i, cur in enumerate(calls):
        pb = cur.prompt_bytes or {}
        tool_bytes_acum += cur.tool_bytes
        # As ToolMessages do prompt devem somar exatamente os bytes_read dos
        # eventos tool_call desta janela. Diferença = conteúdo que entrou
        # como resposta de ferramenta sem evento (ferramenta desconhecida,
        # ValidationError de argumento, chamadas além do teto por turno).
        divergencia_tool = int(pb.get("tool", 0)) - tool_bytes_acum
        razao = (pb.get("total", 0) / cur.tokens_prompt) if cur.tokens_prompt else None
        if razao:
            razoes.append(razao)
        linha = {
            "seq": cur.seq, "turn": cur.turn, "tokens_prompt": cur.tokens_prompt,
            "prompt_bytes": pb, "tool_bytes_eventos": tool_bytes_acum,
            "divergencia_tool_bytes": divergencia_tool, "bytes_por_token": razao,
        }
        if i > 0:
            linha["delta_prompt"] = cur.tokens_prompt - calls[i - 1].tokens_prompt
        soma_abs += abs(divergencia_tool)
        soma_tool_prompt += int(pb.get("tool", 0))
        if abs(divergencia_tool) > 0:
            grandes.append(cur.seq)
        linhas.append(linha)

    c = statistics.median(razoes) if razoes else None
    return Ledger(
        window=w, modo="exato", a=None, c=c, linhas=linhas,
        discrepancia_abs_pct=(100 * soma_abs / soma_tool_prompt) if soma_tool_prompt else 0.0,
        discrepancia_signed_pct=None, nao_explicadas=grandes,
    )


# -------------------------------------------------------------- atribuição


def atribuicao(run: Run, ledgers: list[Ledger], fixos: dict[str, int], primeira_msg: int | None) -> dict[str, Any]:
    """
    Reparte os tokens de prompt COBRADOS (Σ tokens_prompt de todas as chamadas)
    entre categorias. O histórico é reenviado a cada chamada, então um byte
    lido antes da chamada i é cobrado em i, i+1, ..., N.
    """
    cats: dict[str, float] = {}

    def add(k: str, v: float) -> None:
        cats[k] = cats.get(k, 0.0) + v

    cobrado_codigo = 0
    explicado_total = 0.0
    for lg in ledgers:
        calls = lg.window.calls
        n = len(calls)
        cobrado_codigo += sum(c.tokens_prompt for c in calls)
        if n == 0:
            continue

        if lg.modo == "exato":
            for c in calls:
                pb = c.prompt_bytes or {}
                total = pb.get("total") or 0
                if not total:
                    add("não explicado", c.tokens_prompt)
                    continue
                # tool separado por ferramenta na proporção dos bytes_read acumulados
                add("mensagens do assistente", c.tokens_prompt * pb.get("ai", 0) / total)
                add("feedback e enunciado (mensagens humanas)", c.tokens_prompt * pb.get("human", 0) / total)
                add("prompt de sistema", c.tokens_prompt * pb.get("system", 0) / total)
                tool_tokens = c.tokens_prompt * pb.get("tool", 0) / total
                acum: dict[str, int] = {}
                for cc in calls[: calls.index(c) + 1]:
                    for nome, b in cc.tool_msgs:
                        acum[nome] = acum.get(nome, 0) + b
                soma = sum(acum.values()) or 1
                for nome, b in acum.items():
                    add(f"saída de {nome}", tool_tokens * b / soma)
                # O esquema das ferramentas não é mensagem: fica no que o
                # provedor cobra além dos bytes das mensagens, repartido
                # proporcionalmente entre as categorias acima.
            explicado_total += sum(c.tokens_prompt for c in calls)
            continue

        # modo inferido
        c_fit = lg.c
        a_fit = lg.a or 0.0
        p1 = calls[0].tokens_prompt
        base_bytes = {
            "prompt de sistema": fixos["system_prompt"],
            "esquema das ferramentas": fixos["tool_schema"],
            "primeira mensagem (enunciado)": primeira_msg or 0,
        }
        soma_base = sum(base_bytes.values())
        if soma_base and primeira_msg is not None:
            for k, b in base_bytes.items():
                add(k, p1 * n * b / soma_base)
        else:
            add("prompt de sistema + esquema + primeira mensagem (não separável)", p1 * n)

        explicado = p1 * n
        for i in range(1, n):
            cur = calls[i]
            mult = n - i           # o que entrou antes da chamada i é cobrado em i..N-1 (0-indexado)
            add("mensagens do assistente", calls[i - 1].tokens_completion * mult)
            explicado += calls[i - 1].tokens_completion * mult
            if c_fit:
                for nome, b in cur.tool_msgs:
                    t = b / c_fit
                    add(f"saída de {nome}", t * mult)
                    explicado += t * mult
                add("enquadramento das mensagens de ferramenta", a_fit * len(cur.tool_msgs) * mult)
                explicado += a_fit * len(cur.tool_msgs) * mult
        explicado_total += explicado

    if any(lg.modo == "inferido" for lg in ledgers):
        add("não explicado (resíduo do ajuste)", cobrado_codigo - explicado_total)

    aux_prompt = sum(x["tokens_prompt"] for x in run.aux_calls)
    if aux_prompt:
        cats["papéis auxiliares (prompts próprios)"] = float(aux_prompt)

    total = cobrado_codigo + aux_prompt
    return {
        "tokens_prompt_cobrados_codigo": cobrado_codigo,
        "tokens_prompt_cobrados_auxiliares": aux_prompt,
        "tokens_prompt_cobrados_total": total,
        "categorias_tokens": {k: round(v) for k, v in sorted(cats.items(), key=lambda kv: -kv[1])},
        "categorias_pct": {k: round(100 * v / total, 1) for k, v in sorted(cats.items(), key=lambda kv: -kv[1])} if total else {},
    }


# ---------------------------------------------------------------- relatório


def analisar(run: Run, fixos: dict[str, int], tasks_dir: Path) -> dict[str, Any]:
    ledgers = [ledger_exato(w) if run.modo == "exato" else ledger_inferido(w) for w in run.windows]
    primeira = None
    primeira_medida = None
    if run.windows and run.windows[0].calls:
        c1 = run.windows[0].calls[0]
        if c1.prompt_bytes:
            primeira_medida = c1.prompt_bytes.get("human")
    if run.arm == "single-agent":
        primeira = primeira_msg_reconstruida = primeira_mensagem_single_agent(run.task_id, tasks_dir)
    else:
        primeira_msg_reconstruida = None

    calls = [c for w in run.windows for c in w.calls]
    p_final = calls[-1].tokens_prompt if calls else 0
    p_first = calls[0].tokens_prompt if calls else 0
    return {
        "run_id": run.run_id, "arm": run.arm, "task_id": run.task_id,
        "path": str(run.path), "started_at": run.started_at.isoformat() if run.started_at else None,
        "instrumentacao_completa": run.instrumentacao_completa, "modo": run.modo,
        "janelas": len(run.windows), "chamadas_codigo": len(calls), "chamadas_auxiliares": len(run.aux_calls),
        "tool_calls": run.tool_calls_total, "tool_bytes": run.tool_bytes_total,
        "primeiro_prompt_tokens": p_first, "ultimo_prompt_tokens": p_final,
        "soma_prompt_tokens_codigo": sum(c.tokens_prompt for c in calls),
        "media_prompt_tokens_codigo": round(statistics.mean(c.tokens_prompt for c in calls)) if calls else 0,
        "primeira_mensagem_bytes_medida": primeira_medida,
        "primeira_mensagem_bytes_reconstruida": primeira_msg_reconstruida,
        "janelas_detalhe": [
            {
                "janela": lg.window.index, "no": lg.window.node, "chamadas": len(lg.window.calls),
                "modo": lg.modo, "a_tokens_por_msg_ferramenta": round(lg.a, 1) if lg.a is not None else None,
                "c_bytes_por_token": round(lg.c, 2) if lg.c else None,
                "discrepancia_abs_pct": round(lg.discrepancia_abs_pct, 1) if lg.discrepancia_abs_pct is not None else None,
                "discrepancia_signed_pct": round(lg.discrepancia_signed_pct, 1) if lg.discrepancia_signed_pct is not None else None,
                "chamadas_nao_explicadas": lg.nao_explicadas,
                "linhas": lg.linhas,
            }
            for lg in ledgers
        ],
        "atribuicao": atribuicao(run, ledgers, fixos, primeira),
    }


def agregar_por_braco(analises: list[dict[str, Any]]) -> dict[str, Any]:
    por_braco: dict[str, list[dict[str, Any]]] = {}
    for a in analises:
        por_braco.setdefault(a["arm"], []).append(a)
    saida: dict[str, Any] = {}
    for arm, lista in sorted(por_braco.items()):
        cats: dict[str, float] = {}
        total = 0
        for a in lista:
            for k, v in a["atribuicao"]["categorias_tokens"].items():
                cats[k] = cats.get(k, 0.0) + v
            total += a["atribuicao"]["tokens_prompt_cobrados_total"]
        discrep = [j["discrepancia_abs_pct"] for a in lista for j in a["janelas_detalhe"] if j["discrepancia_abs_pct"] is not None]
        cs = [j["c_bytes_por_token"] for a in lista for j in a["janelas_detalhe"] if j["c_bytes_por_token"]]
        saida[arm] = {
            "execucoes": len(lista),
            "tokens_prompt_cobrados_total": total,
            "categorias_pct": {k: round(100 * v / total, 1) for k, v in sorted(cats.items(), key=lambda kv: -kv[1])} if total else {},
            "categorias_tokens": {k: round(v) for k, v in sorted(cats.items(), key=lambda kv: -kv[1])},
            "discrepancia_abs_pct_mediana": round(statistics.median(discrep), 1) if discrep else None,
            "c_bytes_por_token_mediana": round(statistics.median(cs), 2) if cs else None,
            "ultimo_prompt_tokens_mediana": statistics.median(a["ultimo_prompt_tokens"] for a in lista),
            "media_prompt_tokens_mediana": statistics.median(a["media_prompt_tokens_codigo"] for a in lista),
            "chamadas_codigo_mediana": statistics.median(a["chamadas_codigo"] for a in lista),
            "primeira_mensagem_bytes_medida_mediana": statistics.median(
                [a["primeira_mensagem_bytes_medida"] for a in lista if a["primeira_mensagem_bytes_medida"]] or [0]
            ),
        }
    return saida


def markdown(analises: list[dict[str, Any]], agregados: dict[str, Any]) -> str:
    out: list[str] = []
    out.append("## Por execução\n")
    out.append("| run | braço | modo | instr. completa | chamadas (código/aux) | 1º prompt | último prompt | Σ prompt | c (bytes/token) | a (tokens/msg) | discrepância |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for a in analises:
        j = a["janelas_detalhe"]
        cs = [x["c_bytes_por_token"] for x in j if x["c_bytes_por_token"]]
        as_ = [x["a_tokens_por_msg_ferramenta"] for x in j if x["a_tokens_por_msg_ferramenta"] is not None]
        ds = [x["discrepancia_abs_pct"] for x in j if x["discrepancia_abs_pct"] is not None]
        c_txt = f"{statistics.median(cs):.2f}" if cs else "—"
        a_txt = f"{statistics.median(as_):.1f}" if as_ else "—"
        d_txt = f"{statistics.median(ds):.1f}%" if ds else "—"
        out.append(
            f"| `{a['run_id']}` | {a['arm']} | {a['modo']} | {'sim' if a['instrumentacao_completa'] else 'não'} | "
            f"{a['chamadas_codigo']}/{a['chamadas_auxiliares']} | {a['primeiro_prompt_tokens']} | "
            f"{a['ultimo_prompt_tokens']} | {a['soma_prompt_tokens_codigo']} | {c_txt} | {a_txt} | {d_txt} |"
        )
    out.append("")
    for arm, ag in agregados.items():
        out.append(f"## Braço `{arm}` — {ag['execucoes']} execução(ões), {ag['tokens_prompt_cobrados_total']} tokens de prompt cobrados\n")
        out.append("| Categoria | tokens | % |")
        out.append("|---|---|---|")
        for k, v in ag["categorias_tokens"].items():
            out.append(f"| {k} | {v} | {ag['categorias_pct'].get(k, 0)} |")
        out.append("")
        out.append(f"Mediana do último prompt: {ag['ultimo_prompt_tokens_mediana']} tokens; média por chamada (mediana entre execuções): {ag['media_prompt_tokens_mediana']}; chamadas de código (mediana): {ag['chamadas_codigo_mediana']}; discrepância mediana: {ag['discrepancia_abs_pct_mediana']}%; bytes por token (mediana): {ag['c_bytes_por_token_mediana']}.\n")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Contabilidade de contexto por turno e categoria")
    parser.add_argument("raizes", nargs="+", type=Path, help="Diretórios de run ou raízes com runs")
    parser.add_argument("--tasks-dir", type=Path, default=Path("tasks"))
    parser.add_argument("--json", type=Path, help="Grava a análise completa em JSON")
    parser.add_argument("--markdown", action="store_true", help="Imprime tabelas em Markdown")
    parser.add_argument("--only-complete", action="store_true", help="Só execuções com instrumentação completa")
    args = parser.parse_args()

    fixos = tamanhos_fixos()
    analises: list[dict[str, Any]] = []
    for rd in find_runs(args.raizes):
        run = load_run(rd)
        if args.only_complete and not run.instrumentacao_completa:
            continue
        if not run.windows:
            continue
        analises.append(analisar(run, fixos, args.tasks_dir))

    agregados = agregar_por_braco(analises)
    resultado = {"tamanhos_fixos_bytes": fixos, "execucoes": analises, "por_braco": agregados}
    if args.json:
        args.json.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown or not args.json:
        print(f"Tamanhos fixos (bytes, código atual): {fixos}\n")
        print(markdown(analises, agregados))


if __name__ == "__main__":
    main()

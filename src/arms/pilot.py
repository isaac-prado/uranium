"""
Piloto: roda os dois braços na mesma tarefa e compara.

É o formato de coleta em miniatura. Cada repetição executa single-agent e orchestration sob a
mesma semente derivada, e cada execução é julgada pelo avaliador externo —
o mesmo caminho que a coleta definitiva vai usar.

Serve para calibrar antes de gastar: quantos turnos um modelo real gasta,
se ele trava, quanto custa de fato. Nenhum teste com LLM falso responde
essas perguntas.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.arms.runner import build_run_spec, run_arm
from src.budget import RunBudget
from src.config import LLMConfig


@dataclass
class PilotOutcome:
    """Resultado de uma execução, juntando o que o runner e o avaliador viram."""

    arm: str
    repetition: int
    run_id: str
    out_dir: Path
    stop_reason: str
    turns: int
    tokens: int
    cost_usd: float
    resolved: bool | None = None
    f2p: str = "-"
    cheat_criticos: int = 0
    erro: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm, "repetition": self.repetition, "run_id": self.run_id,
            "out_dir": str(self.out_dir), "stop_reason": self.stop_reason,
            "turns": self.turns, "tokens": self.tokens, "cost_usd": self.cost_usd,
            "resolved": self.resolved, "f2p": self.f2p,
            "cheat_criticos": self.cheat_criticos, "erro": self.erro,
        }


def run_pilot(
    *,
    task_dir: Path,
    repetitions: int = 1,
    out_root: Path,
    llm: LLMConfig | None = None,
    budget: RunBudget | None = None,
    llm_factory: Callable[..., Any] | None = None,
    test_timeout_s: int = 120,
    evaluate: bool = True,
) -> list[PilotOutcome]:
    """
    Executa single-agent e orchestration em cada repetição e devolve os resultados na ordem.

    `llm_factory` injetável permite ensaiar a cadeia inteira offline, sem
    gastar crédito — é assim que o piloto é testado antes de valer.
    """
    from harness.evaluate import evaluate_run
    from harness.taskspec import load_task

    task = load_task(task_dir)
    resultados: list[PilotOutcome] = []

    for repeticao in range(1, repetitions + 1):
        for arm in ("single-agent", "orchestration"):
            run_id = f"pilot-{arm.lower()}-r{repeticao:02d}-{uuid.uuid4().hex[:6]}"
            spec = build_run_spec(
                run_id=run_id, arm=arm, task_id=task.task_id,
                statement=task.statement, base_commit=task.base_commit,
                seed_repo_id=task.seed_repo_id, repetition=repeticao,
                out_dir=out_root / arm / f"rep{repeticao:02d}" / run_id,
                llm=llm, budget=budget, test_timeout_s=test_timeout_s,
            )

            try:
                resumo = run_arm(spec, llm_factory=llm_factory)
                erro = None
            except Exception as exc:  # um run que morre não pode parar o piloto
                resumo = {"stop_reason": f"error: {type(exc).__name__}",
                          "turns": 0, "totals": {}}
                erro = f"{type(exc).__name__}: {exc}"[:300]

            totais = resumo.get("totals") or {}
            resultado = PilotOutcome(
                arm=arm, repetition=repeticao, run_id=run_id, out_dir=spec.out_dir,
                stop_reason=resumo.get("stop_reason", "?"),
                turns=resumo.get("turns", 0),
                tokens=totais.get("tokens_total", 0),
                cost_usd=totais.get("cost_usd", 0.0),
                erro=erro,
            )

            if evaluate and erro is None:
                try:
                    avaliacao = evaluate_run(spec.out_dir, task, measure_quality=False)
                    resultado.resolved = avaliacao["resolved"]
                    resultado.f2p = (
                        f"{avaliacao['oracle']['f2p_passed']}/{avaliacao['oracle']['f2p_total']}"
                    )
                    resultado.cheat_criticos = avaliacao["cheat"]["critical_count"]
                except Exception as exc:
                    resultado.erro = f"avaliação falhou: {exc}"[:300]

            resultados.append(resultado)

    return resultados


def format_report(resultados: list[PilotOutcome], task_id: str) -> str:
    """Tabela comparativa. É o formato que vai para o relatório do piloto."""
    linhas = [
        "",
        f"  piloto — tarefa {task_id}",
        "  " + "─" * 85,
        f"  {'braço':<14} {'rep':>3} {'resolv':>7} {'f2p':>6} {'turnos':>7} "
        f"{'tokens':>9} {'US$':>10} {'trapaça':>8}  motivo de parada",
        "  " + "─" * 85,
    ]
    for r in resultados:
        marca = "-" if r.resolved is None else ("sim" if r.resolved else "não")
        linhas.append(
            f"  {r.arm:<14} {r.repetition:>3} {marca:>7} {r.f2p:>6} {r.turns:>7} "
            f"{r.tokens:>9} {r.cost_usd:>10.5f} {r.cheat_criticos:>8}  {r.stop_reason[:26]}"
        )
        if r.erro:
            linhas.append(f"        erro: {r.erro[:70]}")

    linhas.append("  " + "─" * 85)
    for arm in ("single-agent", "orchestration"):
        do_braco = [r for r in resultados if r.arm == arm]
        if not do_braco:
            continue
        resolvidos = sum(1 for r in do_braco if r.resolved)
        linhas.append(
            f"  {arm}: {resolvidos}/{len(do_braco)} resolvidos | "
            f"US$ {sum(r.cost_usd for r in do_braco):.5f} | "
            f"{sum(r.tokens for r in do_braco)} tokens | "
            f"{sum(r.turns for r in do_braco)} turnos"
        )
    linhas.append("")
    return "\n".join(linhas)


def save_report(resultados: list[PilotOutcome], destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps([r.as_dict() for r in resultados], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destino

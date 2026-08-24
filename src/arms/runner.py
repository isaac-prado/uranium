"""
Runner unificado dos dois braços.

Existe um caminho de execução só. Braço A2 e braço B recebem o mesmo
workspace, a mesma configuração de LLM, o mesmo orçamento e a mesma
telemetria; o que se escolhe é qual grafo compilar. Tudo que foi resolvido
vai para o manifesto do run, e é sobre ele que `tests/test_arm_parity.py`
verifica que nada além da topologia difere entre os braços.
"""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.arms.driver import DriverPolicy
from src.budget import RunBudget
from src.config import LLMConfig, load_llm_config
from src.runtime import RunContext
from src.seeds import get_seed_repo
from src.telemetry import Arm, TelemetryWriter
from src.workspace import Workspace, WorkspaceSpec

MANIFEST_VERSION = 1

# Chaves do manifesto que PODEM diferir entre os braços. Qualquer outra
# divergência é violação do desenho experimental. Note que `repetition` NÃO
# está aqui: a repetição nº k do A2 e a nº k do B são um par, e precisam
# rodar sob a mesma semente.
CHAVES_QUE_PODEM_DIFERIR = frozenset({"arm", "topology", "driver_policy", "run_id", "started_at"})


def seed_for_repetition(base_seed: int, repetition: int) -> int:
    """
    Semente efetiva de uma repetição.

    Com semente fixa e temperatura zero, repetir o mesmo run produziria
    saídas quase idênticas — as repetições não mediriam variabilidade
    nenhuma e só gastariam crédito. Variar a semente resolve isso.

    A derivação é determinística e depende apenas do índice da repetição,
    nunca do braço: a repetição nº k roda sob a mesma semente nos dois
    lados, o que preserva o pareamento e permite análise pareada.
    """
    return base_seed + repetition


@dataclass(frozen=True)
class RunSpec:
    """Tudo que define um run, antes de executá-lo."""

    run_id: str
    arm: Arm
    task_id: str
    repetition: int
    seed_repo_id: str
    base_commit: str
    statement: str
    out_dir: Path
    llm: LLMConfig
    budget: RunBudget
    driver_policy: DriverPolicy | None = None
    test_timeout_s: int = 120

    def manifest(self, started_at: str) -> dict[str, Any]:
        """Configuração resolvida do run, auditável e comparável entre braços."""
        return {
            "manifest_version": MANIFEST_VERSION,
            "run_id": self.run_id,
            "arm": self.arm,
            "topology": "single_agent" if self.arm == "A2" else "multi_agent_roles",
            "task_id": self.task_id,
            "repetition": self.repetition,
            "seed_repo_id": self.seed_repo_id,
            "base_commit": self.base_commit,
            "started_at": started_at,
            "llm": self.llm.as_manifest(),
            "budget": self.budget.as_manifest(),
            "driver_policy": self.driver_policy.as_manifest() if self.driver_policy else None,
            "test_timeout_s": self.test_timeout_s,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        }


def build_run_spec(
    *,
    run_id: str,
    arm: Arm,
    task_id: str,
    statement: str,
    base_commit: str,
    repetition: int = 1,
    seed_repo_id: str = "tomlkit",
    out_dir: Path | None = None,
    llm: LLMConfig | None = None,
    budget: RunBudget | None = None,
    test_timeout_s: int = 120,
) -> RunSpec:
    """
    Resolve a configuração de um run.

    Deliberadamente idêntica para os dois braços: a config de LLM e o
    orçamento vêm do mesmo lugar, e só `driver_policy` é específico do A2.

    A semente do LLM é derivada da repetição, então dois braços na mesma
    repetição partem exatamente da mesma condição inicial.
    """
    if repetition < 1:
        raise ValueError(f"repetition começa em 1, recebido {repetition}")

    base_llm = llm or load_llm_config()
    return RunSpec(
        run_id=run_id,
        arm=arm,
        task_id=task_id,
        repetition=repetition,
        seed_repo_id=seed_repo_id,
        base_commit=base_commit,
        statement=statement,
        out_dir=out_dir or Path("runs") / arm / task_id / f"rep{repetition:02d}" / run_id,
        llm=replace(base_llm, seed=seed_for_repetition(base_llm.seed, repetition)),
        budget=budget or RunBudget.from_env(),
        driver_policy=DriverPolicy() if arm == "A2" else None,
        test_timeout_s=test_timeout_s,
    )


def run_arm(spec: RunSpec, *, llm_factory: Any = None) -> dict[str, Any]:
    """
    Executa um braço ponta a ponta e devolve o resumo do run.

    `llm_factory` é injetável para permitir execução offline em teste.
    """
    spec.out_dir.mkdir(parents=True, exist_ok=True)
    iniciado_em = datetime.now(timezone.utc).isoformat(timespec="seconds")

    manifesto = spec.manifest(iniciado_em)
    (spec.out_dir / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    workspace = Workspace.materialize(
        WorkspaceSpec(seed_repo=get_seed_repo(spec.seed_repo_id), base_commit=spec.base_commit),
        run_id=spec.run_id,
        dest=spec.out_dir / "workspace",
        overwrite=True,
    )

    telemetry = TelemetryWriter(
        spec.out_dir / "events.jsonl",
        run_id=spec.run_id, arm=spec.arm, task_id=spec.task_id,
        model=spec.llm.model, provider_requested=spec.llm.provider,
    )

    context = RunContext.create(
        run_id=spec.run_id, arm=spec.arm, task_id=spec.task_id,
        workspace=workspace, telemetry=telemetry,
        budget=spec.budget, llm_factory=llm_factory,
        test_timeout_s=spec.test_timeout_s,
    )

    estado_inicial: dict[str, Any] = {
        "run_id": spec.run_id, "arm": spec.arm, "task_id": spec.task_id,
        "raw_request": spec.statement,
        "intent": {
            "context": "", "goal": spec.statement, "phases": [],
            "acceptance_criteria": [], "clarifications_needed": [], "is_ready": True,
        },
        "iteration_count": 0, "validation_iteration_count": 0,
        "clarification_responses": [], "turn_count": 0,
    }

    telemetry.run_start(
        base_commit=spec.base_commit,
        topology=manifesto["topology"],
        repetition=spec.repetition,
        llm_seed=spec.llm.seed,
    )

    final: dict[str, Any] = {}
    stop_reason = "error"
    try:
        grafo = _compilar(spec)
        final = grafo.invoke(
            estado_inicial, {"recursion_limit": max(8, spec.budget.max_turns * 4)}
        )
        stop_reason = final.get("stop_reason") or (
            "tests_pass" if final.get("is_valid") else "concluiu"
        )
    except Exception as exc:
        telemetry.emit_error(exc)
        stop_reason = f"error: {type(exc).__name__}"
        raise
    finally:
        telemetry.run_end(stop_reason=stop_reason)
        resumo = {
            "run_id": spec.run_id,
            "arm": spec.arm,
            "task_id": spec.task_id,
            "repetition": spec.repetition,
            "llm_seed": spec.llm.seed,
            "topology": manifesto["topology"],
            "stop_reason": stop_reason,
            "is_valid": bool(final.get("is_valid")),
            "changed_files": final.get("changed_files") or [],
            "diff_stat": final.get("diff_stat") or {},
            "turns": final.get("turn_count") or 0,
            "totals": telemetry.totals.as_dict(),
            "out_dir": str(spec.out_dir),
        }
        (spec.out_dir / "summary.json").write_text(
            json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (spec.out_dir / "patch.diff").write_text(workspace.diff(), encoding="utf-8")
        telemetry.close()
        RunContext.release(spec.run_id)

    return resumo


def _compilar(spec: RunSpec):
    """Escolhe o grafo. É o ÚNICO ponto em que os braços divergem."""
    if spec.arm == "A2":
        from src.arms.a2 import build_a2_graph

        return build_a2_graph(spec.driver_policy)

    from src.graph import build_graph

    return build_graph()

"""
Runner unificado dos dois braços.

Existe um caminho de execução só. Os dois braços recebem o mesmo
workspace, a mesma configuração de LLM, o mesmo orçamento e a mesma
telemetria; o que se escolhe é qual grafo compilar. Tudo que foi resolvido
vai para o manifesto do run, e é sobre ele que `tests/test_arm_parity.py`
verifica que nada além da topologia difere entre os braços.
"""

from __future__ import annotations

import inspect
import json
import platform
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src import config
from src.agents.validator import semantic_review_enabled
from src.arms.driver import DriverPolicy
from src.budget import RunBudget
from src.config import LLMConfig, is_provider_error, load_llm_config, root_provider_error
from src.feedback import MEMORIA_DIFF_MAX_CHARS
from src.runtime import MAX_TOOL_CALLS_POR_TURNO, RunContext
from src.seeds import get_seed_repo
from src.structured_llm import get_output_method
from src.structured_llm import max_retries as structured_output_retries
from src.telemetry import Arm, TelemetryWriter
from src.tools import fs as fs_tools
from src.tools.base import (
    MAX_READ_CHARS,
    MAX_READ_LINES,
    MAX_SEARCH_RESULTS,
    MAX_TOOL_OUTPUT_CHARS,
)
from src.tools.exec import DEFAULT_SNIPPET_TIMEOUT_S
from src.workspace import Workspace, WorkspaceSpec

# 5 = a forma de v3 restaurada após a reversão da decisão 24 (09/10/2026):
# v4 existiu só na checagem paga de 09/10 (`orchestration_policy.developer_input`)
# e nenhum run dela entra na coleta. O número sobe para que nenhum manifesto
# posterior se confunda com um da checagem.
# 6 = memória de trabalho do developer entre ciclos (decisão 8 revista em
# 09/10/2026): `orchestration_policy.developer_memory` e
# `developer_memory_diff_max_chars`. As fumaças A a F (v3/v5) rodaram com o
# equivalente a `developer_memory = "none"`.
# 7 = teto de turnos por ciclo do developer (decisão 25, 09/10/2026):
# `orchestration_policy.developer_cycle_max_turns`. A fumaça G (v6) rodou
# com o equivalente a 0 (desligado).
# 8 = ablação do refinador (decisões 7 e 16, 14/10/2026):
# `orchestration_policy.developer_input` ("intent" na coleta principal;
# "enunciado+intent" só no braço de ablação). A coleta de 12-13/10 (v7)
# rodou com o equivalente a "intent".
# 9 = refinador v2 (decisão 28, 14/10/2026): `orchestration_policy.intent_refiner`
# ("v1" na coleta principal; "v2" no braço com o refinador que enriquece).
MANIFEST_VERSION = 9

# Chaves do manifesto que PODEM diferir entre os braços. Qualquer outra
# divergência é violação do desenho experimental. Note que `repetition` NÃO
# está aqui: a repetição nº k de um braço e a nº k do outro são um par,
# e precisam rodar sob a mesma semente.
CHAVES_QUE_PODEM_DIFERIR = frozenset(
    {
        "arm", "topology", "driver_policy", "orchestration_policy", "run_id", "started_at",
        # E5 item 2: um run perdido por erro de provedor é reexecutado com o
        # número de tentativa incrementado. A perda pode acontecer num braço
        # só (o outro lado do par corre normalmente da primeira vez), então
        # `attempt` pode divergir entre os dois SEM violar o desenho — o que
        # não pode divergir é a semente, que depende só de `repetition`
        # (`seed_for_repetition`, abaixo), nunca de `attempt`. Ver
        # tests/test_arm_parity.py::TestTentativaDeReexecucao.
        "attempt",
    }
)

# Default de `max_results` de `list_files` (src/tools/fs.py) lido por
# introspecção, e não reescrito aqui, para não ter dois números que podem
# divergir — um no manifesto e outro na ferramenta de verdade.
_LIST_FILES_MAX_RESULTS = inspect.signature(fs_tools.list_files).parameters["max_results"].default


def _recursion_limit(max_turns: int) -> int:
    """
    Teto de passos do LangGraph por run, do jeito que `run_arm` de fato
    compila e invoca o grafo — ver o uso abaixo, em `run_arm`. Fica numa
    função só para o manifesto (folga F11) nunca poder divergir de como o
    grafo é chamado de verdade.
    """
    return max(8, max_turns * 4)


def _shared_limits(budget: RunBudget) -> dict[str, Any]:
    """
    Constantes de ferramenta e de runtime compartilhadas pelos dois braços
    (docs/tcc/01-inventario.md, folga F11). Hoje são iguais por serem
    constantes de módulo — aqui ficam auditáveis e comparáveis run a run,
    em vez de só "confiar" que ninguém mudou uma delas sem avisar.
    """
    return {
        "max_tool_calls_por_turno": MAX_TOOL_CALLS_POR_TURNO,
        "default_snippet_timeout_s": DEFAULT_SNIPPET_TIMEOUT_S,
        "max_read_chars": MAX_READ_CHARS,
        "max_read_lines": MAX_READ_LINES,
        "max_search_results": MAX_SEARCH_RESULTS,
        "max_tool_output_chars": MAX_TOOL_OUTPUT_CHARS,
        "list_files_max_results": _LIST_FILES_MAX_RESULTS,
        "recursion_limit": _recursion_limit(budget.max_turns),
    }


def _orchestration_policy() -> dict[str, Any]:
    """
    Parâmetros que hoje só afetam o braço orchestration sem deixar rastro no
    manifesto (docs/tcc/01-inventario.md, folga F9): dois runs orquestrados
    com valores diferentes produziam manifestos idênticos.

    Lidos das MESMAS fontes que o grafo usa em tempo de execução — nunca uma
    cópia que possa divergir. `MAX_SEMANTIC_REJECTIONS` e
    `MAX_CLARIFICATION_ITERATIONS` são resolvidas uma vez, no import de
    src/config.py; por isso são lidas aqui como atributo do módulo
    (`config.X`, não `from src.config import X`) — é o mesmo acesso que
    `src/graph.py` usa, então um `monkeypatch.setattr(config, "X", ...)`
    muda os dois ao mesmo tempo. As outras três são lidas do ambiente a
    cada chamada, então não têm esse problema.
    """
    return {
        # Teto de reprovações da revisão semântica sobre código verde — o
        # único laço do orchestration com teto próprio. Suíte vermelha e diff
        # vazio voltam ao developer até o orçamento acabar, como no driver do
        # single-agent (BACKLOG 7.2, D6; decidido em 28/09/2026).
        "max_semantic_rejections": config.MAX_SEMANTIC_REJECTIONS,
        "max_clarification_iterations": config.MAX_CLARIFICATION_ITERATIONS,
        "semantic_review": semantic_review_enabled(),
        "structured_output_method": get_output_method(),
        "structured_output_retries": structured_output_retries(),
        # Memória de trabalho do developer entre ciclos (decisão 8 revista em
        # 09/10/2026): "ledger" entrega o registro dos ciclos anteriores e o
        # diff atual; "none" é a reconstrução do zero de 19/09.
        # Primeira mensagem do developer (ablação do refinador, decisões 7 e
        # 16): "intent" na coleta principal; "enunciado+intent" na ablação.
        # Versão do refinador (decisão 28): "v1" resume (coleta principal);
        # "v2" enriquece com reprodução, saídas esperadas e restrições.
        "intent_refiner": config.INTENT_REFINER,
        "developer_input": config.DEVELOPER_INPUT,
        "developer_memory": config.DEVELOPER_MEMORY,
        "developer_memory_diff_max_chars": MEMORIA_DIFF_MAX_CHARS,
        # Teto de turnos por ciclo do developer (decisão 25, 09/10/2026): ao
        # atingi-lo ele volta ao validador e recebe veredito e memória; 0
        # desliga. A reprovação semântica num ponto de checagem não conta
        # para `max_semantic_rejections`.
        "developer_cycle_max_turns": config.DEVELOPER_CYCLE_MAX_TURNS,
    }


# Prefixos do stop_reason de run perdido, que não é fracasso do braço: a
# coleta o reexecuta e a análise o tira do denominador.
#   infra_error  — o provedor não atendeu (429, chave revogada, 5xx, timeout);
#   interrupted  — o run foi parado de fora (Ctrl+C), sem chegar ao fim.
INFRA_ERROR_PREFIX = "infra_error"
INTERRUPTED_PREFIX = "interrupted"
LOST_PREFIXES = (INFRA_ERROR_PREFIX, INTERRUPTED_PREFIX)


def stop_reason_for(exc: BaseException) -> str:
    """Motivo de parada de um run que morreu com exceção."""
    if not isinstance(exc, Exception):  # KeyboardInterrupt, SystemExit
        prefixo = INTERRUPTED_PREFIX
    elif is_provider_error(exc):
        prefixo = INFRA_ERROR_PREFIX
    else:
        prefixo = "error"
    # `ProviderError` só embrulha; o que interessa é o que o provedor disse.
    # Sem isso, 429 e chave revogada saíam iguais no orchestration.
    return f"{prefixo}: {type(root_provider_error(exc)).__name__}"


def final_stop_reason(final: dict[str, Any]) -> str:
    """
    `stop_reason` do run a partir do estado final do grafo.

    Um `cycle:` (teto de turnos por ciclo do developer, decisão 25) nunca
    é motivo de fim de run: o run só termina depois dele porque o validador
    aprovou ou porque o teto de reprovações fechou, e nos dois casos o nome
    é o mesmo que o orchestration já usava para o fim por decisão própria.
    """
    motivo = final.get("stop_reason") or ""
    if motivo.startswith("cycle:"):
        return "concluiu"
    return motivo or ("tests_pass" if final.get("is_valid") else "concluiu")


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
    orchestration_policy: dict[str, Any] | None = None
    test_timeout_s: int = 120
    # Nº da tentativa dentro da repetição (1-based). Sobe quando este run
    # substitui um anterior perdido por erro de provedor (E5 item 2); a
    # primeira execução de cada repetição é sempre attempt=1.
    attempt: int = 1

    def manifest(self, started_at: str) -> dict[str, Any]:
        """Configuração resolvida do run, auditável e comparável entre braços."""
        return {
            "manifest_version": MANIFEST_VERSION,
            "run_id": self.run_id,
            "arm": self.arm,
            "topology": "single_agent" if self.arm == "single-agent" else "multi_agent_roles",
            "task_id": self.task_id,
            "repetition": self.repetition,
            "attempt": self.attempt,
            "seed_repo_id": self.seed_repo_id,
            "base_commit": self.base_commit,
            "started_at": started_at,
            "llm": self.llm.as_manifest(),
            # Os parâmetros que só afetam o orchestration (tetos dos laços,
            # revisão semântica, saída estruturada) vão em `orchestration_policy`,
            # abaixo — nulo no single-agent, espelho de `driver_policy`.
            "budget": self.budget.as_manifest(),
            "driver_policy": self.driver_policy.as_manifest() if self.driver_policy else None,
            "orchestration_policy": self.orchestration_policy,
            "shared_limits": _shared_limits(self.budget),
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
    attempt: int = 1,
) -> RunSpec:
    """
    Resolve a configuração de um run.

    Deliberadamente idêntica para os dois braços: a config de LLM e o
    orçamento vêm do mesmo lugar, e só `driver_policy` é específico do single-agent.

    A semente do LLM é derivada só da repetição (nunca de `attempt`), então
    reexecutar uma repetição perdida (E5 item 2) preserva a mesma condição
    inicial que a tentativa que morreu — e os dois braços na mesma repetição
    continuam partindo da mesma semente entre si, `attempt` à parte.
    """
    if repetition < 1:
        raise ValueError(f"repetition começa em 1, recebido {repetition}")
    if attempt < 1:
        raise ValueError(f"attempt começa em 1, recebido {attempt}")

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
        driver_policy=DriverPolicy() if arm == "single-agent" else None,
        orchestration_policy=_orchestration_policy() if arm == "orchestration" else None,
        test_timeout_s=test_timeout_s,
        attempt=attempt,
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
        # o workspace já foi materializado com overwrite: o run é novo inteiro
        overwrite=True,
    )

    context = RunContext.create(
        run_id=spec.run_id, arm=spec.arm, task_id=spec.task_id,
        workspace=workspace, telemetry=telemetry,
        budget=spec.budget, llm_config=spec.llm, llm_factory=llm_factory,
        test_timeout_s=spec.test_timeout_s,
    )

    estado_inicial: dict[str, Any] = {
        "run_id": spec.run_id, "arm": spec.arm, "task_id": spec.task_id,
        "raw_request": spec.statement,
        "intent": {
            "context": "", "goal": spec.statement, "phases": [],
            "acceptance_criteria": [], "clarifications_needed": [], "is_ready": True,
        },
        "iteration_count": 0, "validation_iteration_count": 0, "semantic_rejections": 0,
        "clarification_responses": [], "turn_count": 0, "developer_memory": [],
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
            estado_inicial, {"recursion_limit": _recursion_limit(spec.budget.max_turns)}
        )
        stop_reason = final_stop_reason(final)
    except BaseException as exc:
        # BaseException, não Exception: o Ctrl+C também passa pelo `finally` e
        # grava resumo. Com o "error" inicial, o run interrompido virava
        # fracasso válido do braço ao retomar a coleta.
        telemetry.emit_error(exc)
        stop_reason = stop_reason_for(exc)
        raise
    finally:
        telemetry.run_end(stop_reason=stop_reason)
        resumo = {
            "run_id": spec.run_id,
            "arm": spec.arm,
            "task_id": spec.task_id,
            "repetition": spec.repetition,
            "attempt": spec.attempt,
            "llm_seed": spec.llm.seed,
            "topology": manifesto["topology"],
            "stop_reason": stop_reason,
            "lost": stop_reason.startswith(LOST_PREFIXES),
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
    if spec.arm == "single-agent":
        from src.arms.single_agent import build_single_agent_graph

        return build_single_agent_graph(spec.driver_policy)

    from src.graph import build_graph

    return build_graph()

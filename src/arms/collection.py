"""
Coleta definitiva: todas as tarefas × os dois braços × N repetições.

O estado da coleta é o disco, não um arquivo de controle. Cada célula
(tarefa, braço, repetição) tem tentativas numeradas, e o que aconteceu com
cada uma se lê do `summary.json` e do `result.json` que ela deixou. Por isso a
coleta é retomável por construção: interromper e rodar de novo só executa o
que falta, e não há estado paralelo que possa divergir do que está gravado.

Run perdido (`lost`: infraestrutura — 429, chave revogada, 5xx, timeout —
ou interrupção por Ctrl+C) não é fracasso do braço. A tentativa fica gravada como evidência e a
célula é reexecutada, até `max_attempts`. Célula que esgota as tentativas
sai como `lost` e a análise a tira do denominador junto com o par dela.
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from harness.attempts import read_json, select_attempt
from src.arms.runner import build_run_spec, run_arm, stop_reason_for
from src.budget import RunBudget
from src.config import LLMConfig, is_fatal_provider_error

ARMS = ("single-agent", "orchestration")

CellStatus = Literal["done", "lost", "pending"]


class CollectionAborted(RuntimeError):
    """
    A coleta parou porque continuar só produziria tentativas perdidas.

    Chave revogada, crédito esgotado ou provedor fora por várias células
    seguidas. O que já foi gravado continua valendo: rodar de novo depois de
    resolver a causa retoma de onde parou.
    """


@dataclass(frozen=True)
class Cell:
    """Uma célula do desenho: tarefa × braço × repetição."""

    task_dir: Path
    task_id: str
    arm: str
    repetition: int

    def root(self, out_root: Path) -> Path:
        return out_root / self.task_id / self.arm / f"rep{self.repetition:02d}"

    def attempt_dir(self, out_root: Path, attempt: int) -> Path:
        return self.root(out_root) / f"attempt{attempt:02d}"

    def run_id(self, attempt: int) -> str:
        return f"{self.task_id}-{self.arm}-r{self.repetition:02d}-a{attempt:02d}"


@dataclass
class CellOutcome:
    """O que se sabe de uma célula depois de olhar o disco (e, se preciso, rodar)."""

    task_id: str
    arm: str
    repetition: int
    status: CellStatus
    attempts: int
    lost_attempts: int
    run_dir: str | None = None
    stop_reason: str | None = None
    resolved: bool | None = None
    evaluation_error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def inspect_cell(cell: Cell, out_root: Path) -> CellOutcome:
    """Lê o estado da célula a partir das tentativas gravadas."""
    escolha = select_attempt(cell.root(out_root))
    base = dict(task_id=cell.task_id, arm=cell.arm, repetition=cell.repetition,
                attempts=escolha.attempts, lost_attempts=escolha.lost)
    if escolha.run_dir is None:
        return CellOutcome(status="pending", **base)
    resultado = read_json(escolha.run_dir / "result.json")
    return CellOutcome(
        status="done", run_dir=str(escolha.run_dir),
        stop_reason=(escolha.summary or {}).get("stop_reason"),
        resolved=resultado.get("resolved") if resultado else None, **base,
    )


def run_cell(
    cell: Cell,
    *,
    out_root: Path,
    llm: LLMConfig | None,
    budget: RunBudget | None,
    max_attempts: int = 3,
    retry_delay_s: float = 60.0,
    test_timeout_s: int = 120,
    measure_quality: bool = True,
    llm_factory: Callable[..., Any] | None = None,
) -> CellOutcome:
    """
    Leva uma célula até `done` ou `lost`.

    Célula já concluída não roda de novo; célula concluída sem `result.json`
    só é avaliada. A espera entre tentativas existe porque o motivo mais
    comum de perda é rate limit do provedor, que não passa em segundos.

    `max_attempts` conta as tentativas DESTA execução, não as gravadas: uma
    célula que saiu `lost` numa execução anterior volta a ser tentada quando
    a coleta é retomada. Falha de provedor fatal (401, 402) levanta
    `CollectionAborted` depois de gravar a tentativa.
    """
    from harness.evaluate import evaluate_run
    from harness.taskspec import load_task

    task = load_task(cell.task_dir)
    estado = inspect_cell(cell, out_root)

    feitas = 0
    while estado.status == "pending" and feitas < max_attempts:
        if feitas:
            time.sleep(retry_delay_s)
        feitas += 1
        tentativa = estado.attempts + 1
        spec = build_run_spec(
            run_id=cell.run_id(tentativa), arm=cell.arm, task_id=task.task_id,  # type: ignore[arg-type]
            statement=task.statement, base_commit=task.base_commit,
            seed_repo_id=task.seed_repo_id, repetition=cell.repetition,
            out_dir=cell.attempt_dir(out_root, tentativa),
            llm=llm, budget=budget, test_timeout_s=test_timeout_s,
        )
        try:
            run_arm(spec, llm_factory=llm_factory)
        except Exception as exc:
            # O runner já gravou summary.json com o stop_reason certo; se nem
            # isso ele conseguiu, a tentativa fica sem resumo e conta como
            # perdida. Erro que não é de infraestrutura é observação válida.
            if not (spec.out_dir / "summary.json").exists():
                (spec.out_dir / "crash.txt").write_text(
                    f"{stop_reason_for(exc)}\n{exc}\n", encoding="utf-8"
                )
            if is_fatal_provider_error(exc):
                raise CollectionAborted(
                    f"{cell.run_id(tentativa)}: {stop_reason_for(exc)}: {exc}"[:500]
                ) from None
        estado = inspect_cell(cell, out_root)

    if estado.status == "pending":
        estado.status = "lost"
        return estado

    if estado.status == "done" and estado.resolved is None:
        run_dir = Path(estado.run_dir or "")
        try:
            resultado = evaluate_run(run_dir, task, measure_quality=measure_quality)
            (run_dir / "result.json").write_text(
                json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            estado.resolved = resultado["resolved"]
        except Exception as exc:
            estado.evaluation_error = f"{type(exc).__name__}: {exc}"[:300]

    return estado


def plan_cells(
    task_dirs: list[Path], repetitions: int, arms: tuple[str, ...] = ARMS
) -> list[Cell]:
    """
    Ordem de execução: repetição, depois tarefa, depois braço.

    Os dois braços de um par rodam em sequência, perto no tempo. Se o
    provedor degradar no meio da coleta, a degradação atinge o par inteiro,
    não um braço só — que é a direção que enviesaria a comparação.

    `arms` restringe os braços: a ablação do refinador (decisões 7 e 16)
    roda só o orchestration, pareado por semente com a coleta principal.
    """
    from harness.taskspec import load_task

    desconhecidos = set(arms) - set(ARMS)
    if desconhecidos:
        raise ValueError(f"braço desconhecido: {sorted(desconhecidos)}")
    tarefas = [(d, load_task(d).task_id) for d in task_dirs]
    return [
        Cell(task_dir=d, task_id=tid, arm=arm, repetition=rep)
        for rep in range(1, repetitions + 1)
        for d, tid in tarefas
        for arm in arms
    ]


def run_collection(
    cells: list[Cell],
    *,
    out_root: Path,
    workers: int = 1,
    max_consecutive_lost: int = 3,
    on_done: Callable[[CellOutcome], None] | None = None,
    **cell_kwargs: Any,
) -> list[CellOutcome]:
    """
    Executa as células, em paralelo quando `workers > 1`.

    Paralelismo é por processo: cada run tem seu registro de contexto,
    workspace e telemetria, e nada disso é compartilhado. Com `workers=1` roda
    no próprio processo, o que permite injetar `llm_factory` em teste.

    `max_consecutive_lost` células perdidas em sequência param a coleta com
    `CollectionAborted`: provedor fora por tanto tempo não é oscilação, e
    seguir só gastaria o resto da fila em tentativas perdidas.
    """
    resultados: list[CellOutcome] = []
    perdidas_seguidas = 0

    def registrar(resultado: CellOutcome) -> None:
        nonlocal perdidas_seguidas
        resultados.append(resultado)
        if on_done:
            on_done(resultado)
        perdidas_seguidas = perdidas_seguidas + 1 if resultado.status == "lost" else 0
        if max_consecutive_lost and perdidas_seguidas >= max_consecutive_lost:
            raise CollectionAborted(
                f"{perdidas_seguidas} células perdidas em sequência; "
                f"a última foi {resultado.task_id}/{resultado.arm}/rep{resultado.repetition:02d}"
                f" ({resultado.lost_attempts} tentativa(s) perdida(s))"
            )

    if workers <= 1:
        for cell in cells:
            registrar(run_cell(cell, out_root=out_root, **cell_kwargs))
        return resultados

    pool = ProcessPoolExecutor(max_workers=workers)
    try:
        futuros = [
            pool.submit(run_cell, cell, out_root=out_root, **cell_kwargs) for cell in cells
        ]
        for futuro in as_completed(futuros):
            registrar(futuro.result())
    except BaseException:
        # Sem cancelar, o `shutdown` esperaria a fila inteira rodar.
        pool.shutdown(wait=True, cancel_futures=True)
        raise
    pool.shutdown(wait=True)
    ordem = {(c.task_id, c.arm, c.repetition): i for i, c in enumerate(cells)}
    return sorted(resultados, key=lambda r: ordem[(r.task_id, r.arm, r.repetition)])


def save_collection_report(resultados: list[CellOutcome], out_root: Path) -> Path:
    destino = out_root / "collection.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps([r.as_dict() for r in resultados], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destino

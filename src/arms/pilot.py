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

from src.arms.runner import LOST_PREFIXES, build_run_spec, run_arm, stop_reason_for
from src.budget import RunBudget
from src.config import LLMConfig

# Teto de tentativas por (tarefa, braço, repetição) perdida (E5 item 2 /
# portão G5 de docs/tcc/04-cronograma.md). Ao estourar, o par é declarado
# perdido de vez — ver `reexecutar_perdidos`.
MAX_TENTATIVAS_REEXECUCAO = 3


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
    attempt: int = 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm, "repetition": self.repetition, "run_id": self.run_id,
            "out_dir": str(self.out_dir), "stop_reason": self.stop_reason,
            "turns": self.turns, "tokens": self.tokens, "cost_usd": self.cost_usd,
            "resolved": self.resolved, "f2p": self.f2p,
            "cheat_criticos": self.cheat_criticos, "erro": self.erro,
            "attempt": self.attempt,
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
                resumo = {"stop_reason": stop_reason_for(exc),
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


# =====================================================================
# E5 item 2 — reexecução de run perdido por erro de provedor
# =====================================================================
#
# Um "run perdido" é uma (task_id, arm, repetition) cujo attempt mais recente
# não terminou de forma utilizável: morreu por erro do provedor, ou morreu
# abruptamente antes de conseguir registrar o próprio fim. Corte por
# orçamento (`stop_reason` começando em "budget:") NÃO é perda: é o
# experimento medindo autonomia (métrica 6), e teria de ser inventado um
# "run substituto" para ele, o que forjaria dado que o desenho não pediu.
#
# `scripts/analyze_results.py` só lê `result.json` (`find_results`, que faz
# `rglob("result.json")`); um run perdido nunca chega a ter um `result.json`
# pela via normal — `run_pilot`, acima, só chama o avaliador quando `erro is
# None` — então já fica de fora da análise sem nenhum código extra. O único
# jeito de um `result.json` aparecer num diretório perdido é alguém rodar
# `python -m harness.evaluate` manualmente sobre ele (o workspace já
# materializado tem `.git`, e `evaluate_run` não sabe distinguir "run que
# morreu" de "run que terminou sem mudar nada"); `marcar_perdido`, abaixo,
# neutraliza esse caso renomeando o `result.json` espúrio.


@dataclass
class RunPerdido:
    """
    Uma (task_id, arm, repetition) cujo attempt mais recente está perdido.

    `run_dir` é o diretório desse attempt — não é apagado nunca; só marcado
    (ver `marcar_perdido`) quando substituído ou quando o teto de tentativas
    estoura.
    """

    task_id: str
    arm: str
    repetition: int
    attempt: int
    motivo: str
    run_dir: Path
    seed: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id, "arm": self.arm, "repetition": self.repetition,
            "attempt": self.attempt, "motivo": self.motivo,
            "run_dir": str(self.run_dir), "seed": self.seed,
        }


def _perda_por_stop_reason(stop_reason: Any) -> bool:
    """
    Critério de perda por motivo de parada: `infra_error:` (o provedor não
    atendeu — 429, chave revogada, 5xx, timeout) e `interrupted:` (Ctrl+C),
    os prefixos de `src.arms.runner.LOST_PREFIXES`. É a MESMA regra que o
    runner grava como `lost: true` no summary e que a coleta definitiva e a
    análise leem por `harness/attempts.py`: perda tem uma definição só.

    Um corte por orçamento (`budget:`) é resultado do experimento, não
    perda — não é reexecutado. Um `error:` de outra origem é bug do harness
    (espelho ausente, configuração errada): reexecutar só repetiria o erro,
    então ele não é tratado como perda aqui; é reportado para conserto.
    """
    return isinstance(stop_reason, str) and stop_reason.startswith(LOST_PREFIXES)


def _tem_run_end(eventos_path: Path) -> bool:
    """Se `events.jsonl` existe, teve pelo menos um evento `run_end` nele."""
    if not eventos_path.exists():
        return False
    for linha in eventos_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            evento = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if isinstance(evento, dict) and evento.get("event_type") == "run_end":
            return True
    return False


def _diagnostico_do_attempt(run_dir: Path) -> str | None:
    """
    Motivo da perda deste diretório de attempt, ou `None` se ele concluiu.

    "Concluiu" aqui é sobre o RUN ter chegado ao fim (gravou `summary.json`
    com `stop_reason` e a trilha tem `run_end`) — não sobre o veredito. Uma
    tarefa não resolvida, ou cortada por orçamento, concluiu; só não conta
    como perda.
    """
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        return "sem summary.json (morte abrupta)"
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "summary.json corrompido (morte abrupta)"

    stop_reason = summary.get("stop_reason")
    if stop_reason is None:
        return "summary.json sem stop_reason (morte abrupta)"
    if summary.get("lost") or _perda_por_stop_reason(stop_reason):
        return str(stop_reason)

    # `run_arm` só grava summary.json DEPOIS de `telemetry.run_end` (ver
    # src/arms/runner.py, bloco `finally`); esta checagem é defesa extra
    # contra um processo morto bem no meio dessas duas escritas.
    if not _tem_run_end(run_dir / "events.jsonl"):
        return "events.jsonl sem run_end (morte abrupta)"

    return None


def detectar_perdidos(out_dir: Path) -> list[RunPerdido]:
    """
    Varre `out_dir` e devolve uma entrada por (task_id, arm, repetition) cujo
    ÚLTIMO attempt encontrado no disco está perdido.

    Agrupa pelo conteúdo de `manifest.json` (não pelo layout de diretório —
    `run_pilot` e `scripts/run_arm.py` organizam a saída de jeitos diferentes),
    então funciona sobre qualquer raiz de coleta. `manifest.json` é a
    primeira escrita de `run_arm`, antes de qualquer chamada de rede; um
    processo morto no instante entre criar o diretório e gravar o manifesto
    não é atribuível a nenhuma (tarefa, braço, repetição) e fica de fora —
    esse caso extremo pede checagem manual do diretório.

    Um attempt já marcado com `PERDIDO` (ver `marcar_perdido`) nunca volta:
    ou foi substituído (o substituto é quem conta agora), ou o teto de
    tentativas já estourou (o par foi declarado perdido de vez).
    """
    grupos: dict[tuple[str, str, int], list[tuple[int, Path, dict[str, Any]]]] = {}
    for manifesto_path in sorted(Path(out_dir).rglob("manifest.json")):
        try:
            manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        task_id, arm, repetition = (
            manifesto.get("task_id"), manifesto.get("arm"), manifesto.get("repetition")
        )
        if task_id is None or arm is None or repetition is None:
            continue
        attempt = int(manifesto.get("attempt", 1))
        chave = (str(task_id), str(arm), int(repetition))
        grupos.setdefault(chave, []).append((attempt, manifesto_path.parent, manifesto))

    perdidos: list[RunPerdido] = []
    for (task_id, arm, repetition), tentativas in grupos.items():
        tentativas.sort(key=lambda t: (t[0], t[1].name))
        attempt, run_dir, manifesto = tentativas[-1]
        if (run_dir / "PERDIDO").exists():
            continue
        motivo = _diagnostico_do_attempt(run_dir)
        if motivo is None:
            continue
        perdidos.append(RunPerdido(
            task_id=task_id, arm=arm, repetition=repetition, attempt=attempt,
            motivo=motivo, run_dir=run_dir, seed=(manifesto.get("llm") or {}).get("seed"),
        ))
    return perdidos


def marcar_perdido(run_dir: Path, *, motivo: str) -> Path:
    """
    Marca `run_dir` como perdido, sem apagar nada do que está lá.

    Grava um arquivo `PERDIDO` de texto com o motivo — é o que
    `detectar_perdidos` usa para nunca mais tratar este diretório como
    candidato a reexecução, e o sinal para quem for rodar o avaliador manual
    (`python -m harness.evaluate`) pular este diretório.

    Se já existir um `result.json` aqui — produzido antes desta marca, ou por
    alguém que rodou o avaliador direto no diretório perdido, já que o
    workspace materializado tem `.git` e basta para `evaluate_run` gerar um
    resultado —, ele é renomeado para `result.json.perdido`: fora do padrão
    que `scripts/analyze_results.py` varre (`rglob("result.json")`). Sem
    isso, o run substituto e o run perdido entrariam os dois na análise como
    duas repetições da mesma (tarefa, braço), inflando a amostra.
    """
    (run_dir / "PERDIDO").write_text(motivo + "\n", encoding="utf-8")

    espurio = run_dir / "result.json"
    if espurio.exists():
        espurio.rename(run_dir / "result.json.perdido")

    return run_dir / "PERDIDO"


def reexecutar_perdidos(
    out_dir: Path,
    *,
    tasks_dir: Path = Path("tasks"),
    llm: LLMConfig | None = None,
    budget: RunBudget | None = None,
    llm_factory: Callable[..., Any] | None = None,
    test_timeout_s: int = 120,
    evaluate: bool = True,
    max_tentativas: int = MAX_TENTATIVAS_REEXECUCAO,
) -> list[PilotOutcome]:
    """
    Refaz cada (task_id, arm, repetition) perdida encontrada em `out_dir`.

    Mesma semente — deriva só de `repetition` (`seed_for_repetition`), nunca
    de `attempt` —, `run_id` novo, `attempt` incrementado. O attempt antigo
    fica no disco, marcado (`marcar_perdido`): nunca é apagado.

    Ao estourar `max_tentativas` para um par, ele é declarado perdido de vez
    — nem esta chamada tenta de novo, nem uma chamada futura sobre a mesma
    `out_dir` vai reconsiderá-lo, porque `detectar_perdidos` pula diretório
    já marcado.
    """
    from harness.evaluate import evaluate_run
    from harness.taskspec import load_task

    cache_tasks: dict[str, Any] = {}

    def _task(task_id: str) -> Any:
        if task_id not in cache_tasks:
            cache_tasks[task_id] = load_task(tasks_dir / task_id)
        return cache_tasks[task_id]

    resultados: list[PilotOutcome] = []
    for perdido in detectar_perdidos(out_dir):
        if perdido.attempt >= max_tentativas:
            marcar_perdido(perdido.run_dir, motivo=(
                f"{perdido.motivo}; teto de {max_tentativas} tentativa(s) esgotado "
                f"no attempt {perdido.attempt} — par declarado perdido"
            ))
            continue

        task = _task(perdido.task_id)
        novo_attempt = perdido.attempt + 1
        run_id = (
            f"reexec-{perdido.arm.lower()}-{perdido.task_id}-"
            f"r{perdido.repetition:02d}-a{novo_attempt}-{uuid.uuid4().hex[:6]}"
        )
        spec = build_run_spec(
            run_id=run_id, arm=perdido.arm, task_id=task.task_id,
            statement=task.statement, base_commit=task.base_commit,
            seed_repo_id=task.seed_repo_id, repetition=perdido.repetition,
            attempt=novo_attempt, out_dir=perdido.run_dir.parent / run_id,
            llm=llm, budget=budget, test_timeout_s=test_timeout_s,
        )

        try:
            resumo = run_arm(spec, llm_factory=llm_factory)
            erro = None
        except Exception as exc:  # um attempt que morre não pode parar a reexecução dos outros
            resumo = {"stop_reason": f"error: {type(exc).__name__}", "turns": 0, "totals": {}}
            erro = f"{type(exc).__name__}: {exc}"[:300]

        # o attempt antigo vira histórico morto: nunca mais candidato a
        # reexecução, nunca mais candidato a entrar na análise
        marcar_perdido(perdido.run_dir, motivo=f"{perdido.motivo}; substituído por {run_id}")

        ainda_perdido = erro is not None or _perda_por_stop_reason(resumo.get("stop_reason"))
        if ainda_perdido and novo_attempt >= max_tentativas:
            marcar_perdido(spec.out_dir, motivo=(
                f"{resumo.get('stop_reason', erro)}; teto de {max_tentativas} tentativa(s) "
                f"esgotado no attempt {novo_attempt} — par declarado perdido"
            ))

        totais = resumo.get("totals") or {}
        resultado = PilotOutcome(
            arm=perdido.arm, repetition=perdido.repetition, run_id=run_id,
            out_dir=spec.out_dir, stop_reason=resumo.get("stop_reason", "?"),
            turns=resumo.get("turns", 0), tokens=totais.get("tokens_total", 0),
            cost_usd=totais.get("cost_usd", 0.0), erro=erro, attempt=novo_attempt,
        )

        if evaluate and erro is None and not ainda_perdido:
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

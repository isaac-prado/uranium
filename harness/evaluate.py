"""
Avaliação de um run: entra um workspace modificado, sai um result.json.

    python -m harness.evaluate --run-dir runs/B/tomlkit-0001/rep01/<id> \
                               --task tasks/tomlkit-0001

A avaliação roda sobre uma CÓPIA descartável do workspace, nunca sobre o
que ficou gravado no run. Ela muta o que toca — injeta testes ocultos,
restaura arquivos de teste do commit-base, aplica o patch de teste do
upstream —, e mutar o original destruiria a evidência do que o agente fez.

Ordem das etapas dentro da cópia:

  1. trapaça, diff e qualidade — sobre o estado exato em que o agente parou,
     antes de o avaliador encostar em qualquer coisa;
  2. oráculo — injeta os testes ocultos e julga;
  3. custo e processo, que saem da telemetria e não dependem do workspace.

Regra de precedência: trapaça crítica detectada força `resolved = false`,
independentemente do que o oráculo disser. Resolver o problema burlando a
avaliação não é resolver o problema.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness import HARNESS_VERSION, RESULT_SCHEMA_VERSION
from harness.cheat import detect
from harness.cost import aggregate_cost, aggregate_process, providers_served, read_events
from harness.gitutil import base_commit, changed_files, diffstat
from harness.oracle import evaluate_oracle
from harness.quality import measure
from harness.taskspec import TaskSpec, load_task


@contextmanager
def _workspace_descartavel(origem: Path) -> Iterator[Path]:
    """
    Cópia do workspace do agente, avaliada e depois descartada.

    Existe porque a avaliação é destrutiva: ela injeta os testes ocultos,
    restaura arquivos de teste do commit-base e aplica o patch de teste do
    upstream. Rodar isso no workspace gravado apaga o que o agente deixou.

    A tentativa anterior de resolver — limpar a injeção no início de cada
    avaliação — tinha um furo. Numa tarefa com `test_patch`, a limpeza fazia
    `git checkout <base> -- tests/test_x.py`, e uma adulteração de teste pelo
    agente mora exatamente nesse arquivo, porque é onde ficam os testes que
    discriminam. A evidência era apagada ANTES de o detector olhar, inclusive
    na primeira avaliação, quando não havia injeção anterior nenhuma para
    limpar. A regra C1 nunca disparava nessas tarefas.

    Com a cópia, a idempotência deixa de ser compensatória e vira estrutural:
    o original nunca muda, avaliar N vezes dá o mesmo veredito por
    construção, e o detector sempre vê o estado real.
    """
    temp = Path(tempfile.mkdtemp(prefix="uranium-eval-"))
    try:
        copia = temp / "workspace"
        # symlinks=True preserva o link em vez de copiar o alvo — o submódulo
        # tests/toml-test do tomlkit depende disso, e o .git do submódulo é um
        # arquivo com gitdir relativo, que só resolve se a árvore for copiada
        # inteira.
        shutil.copytree(origem, copia, symlinks=True)
        yield copia
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def evaluate_run(
    run_dir: Path,
    task: TaskSpec,
    *,
    timeout_s: int = 600,
    measure_quality: bool = True,
) -> dict[str, Any]:
    """Avalia um run e devolve o resultado no formato do result.json."""
    origem = run_dir / "workspace"
    if not (origem / ".git").is_dir():
        raise FileNotFoundError(f"workspace com git não encontrado em {origem}")

    manifesto = _ler_json(run_dir / "manifest.json")
    eventos = read_events(run_dir / "events.jsonl")

    # Tudo que mexe no workspace acontece na cópia; o run gravado fica intacto.
    with _workspace_descartavel(origem) as workspace:
        # 1. trapaça e diff, sobre o estado exato em que o agente parou
        alterados = changed_files(workspace)
        trapaca = detect(workspace, task.protected_globs)
        estatistica_diff = diffstat(workspace)
        commit_base = base_commit(workspace)

        # 2. qualidade, também antes de qualquer injeção: mede o que o agente
        # escreveu, não o que o avaliador trouxe
        py_alterados = [c for c in alterados if c.endswith(".py")]
        qualidade = (
            measure(workspace, py_alterados).as_dict()
            if measure_quality else {"skipped": True}
        )

        # 3. oráculo — daqui em diante o workspace é mutado, e é exatamente
        # por isso que ele é descartável
        oraculo = evaluate_oracle(workspace, task, timeout_s=timeout_s)

    resolvido = oraculo.resolved and trapaca.clean

    return {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "harness_version": HARNESS_VERSION,
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": manifesto.get("run_id", run_dir.name),
        "arm": manifesto.get("arm"),
        "task_id": task.task_id,
        "repetition": manifesto.get("repetition"),
        "base_commit": commit_base,
        "resolved": resolvido,
        "resolved_blocked_by_cheat": oraculo.resolved and not trapaca.clean,
        "oracle": oraculo.as_dict(),
        "cheat": trapaca.as_dict(),
        "quality": qualidade,
        "cost": aggregate_cost(eventos),
        "process": aggregate_process(eventos),
        "provenance": {
            "model": (manifesto.get("llm") or {}).get("model"),
            "provider_requested": (manifesto.get("llm") or {}).get("provider"),
            "providers_served": providers_served(eventos),
            "llm_seed": (manifesto.get("llm") or {}).get("seed"),
            "topology": manifesto.get("topology"),
        },
        "diff": {**estatistica_diff, "changed_files": alterados},
    }


def _ler_json(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia um run do estudo E1")
    parser.add_argument("--run-dir", type=Path, required=True,
                        help="Diretório do run (com workspace/ e events.jsonl)")
    parser.add_argument("--task", type=Path, required=True,
                        help="Diretório ou arquivo da especificação da tarefa")
    parser.add_argument("--out", type=Path,
                        help="Arquivo de saída (padrão: <run-dir>/result.json)")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--no-quality", action="store_true",
                        help="Pula radon/coverage (mais rápido em piloto)")
    args = parser.parse_args()

    tarefa = load_task(args.task)
    resultado = evaluate_run(
        args.run_dir, tarefa,
        timeout_s=args.timeout, measure_quality=not args.no_quality,
    )

    destino = args.out or (args.run_dir / "result.json")
    destino.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    marca = "RESOLVIDO" if resultado["resolved"] else "NÃO RESOLVIDO"
    if resultado["resolved_blocked_by_cheat"]:
        marca = "NÃO RESOLVIDO (bloqueado por trapaça)"
    print(f"{marca}  {resultado['arm']} / {tarefa.task_id} / rep {resultado['repetition']}")
    print(f"  f2p {resultado['oracle']['f2p_passed']}/{resultado['oracle']['f2p_total']}"
          f"  p2p {'ok' if resultado['oracle']['p2p']['exit_code'] == 0 else 'FALHOU'}")
    print(f"  trapaça: {resultado['cheat']['critical_count']} crítico(s), "
          f"{resultado['cheat']['warning_count']} aviso(s)")
    print(f"  custo US$ {resultado['cost']['cost_usd']:.6f}  →  {destino}")

    sys.exit(0 if resultado["resolved"] else 1)


if __name__ == "__main__":
    main()

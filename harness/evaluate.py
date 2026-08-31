"""
Avaliação de um run: entra um workspace modificado, sai um result.json.

    python -m harness.evaluate --run-dir runs/B/tomlkit-0001/rep01/<id> \
                               --task tasks/tomlkit-0001

Ordem das etapas importa:

  1. detecção de trapaça — ANTES de injetar qualquer coisa, senão os
     arquivos do próprio avaliador apareceriam como alteração do agente;
  2. oráculo — injeta os testes ocultos e julga;
  3. qualidade, custo e processo.

Regra de precedência: trapaça crítica detectada força `resolved = false`,
independentemente do que o oráculo disser. Resolver o problema burlando a
avaliação não é resolver o problema.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness import HARNESS_VERSION, RESULT_SCHEMA_VERSION
from harness.cheat import HIDDEN_DIR, detect
from harness.cost import aggregate_cost, aggregate_process, providers_served, read_events
from harness.gitutil import base_commit, changed_files, diffstat
from harness.oracle import _ARQUIVO_DO_DIFF, evaluate_oracle
from harness.quality import measure
from harness.taskspec import TaskSpec, load_task


def _limpar_injecao(workspace: Path, task: TaskSpec) -> None:
    """Devolve o workspace ao estado em que o agente o deixou."""
    oculto = workspace / HIDDEN_DIR
    if oculto.is_dir():
        shutil.rmtree(oculto)

    # Um oráculo por patch altera arquivos de teste no lugar; restaurá-los do
    # commit-base não apaga adulteração do agente, porque a adulteração dele
    # também é feita ali e seria refeita a cada avaliação — o registro dela
    # está no result.json da primeira, que é o que vale.
    if task.test_patch:
        patch = task.root / task.test_patch
        if patch.exists():
            for alvo in _ARQUIVO_DO_DIFF.findall(patch.read_text(encoding="utf-8")):
                subprocess.run(
                    ["git", "checkout", task.base_commit, "--", alvo],
                    cwd=workspace, capture_output=True, text=True,
                )


def evaluate_run(
    run_dir: Path,
    task: TaskSpec,
    *,
    timeout_s: int = 600,
    measure_quality: bool = True,
) -> dict[str, Any]:
    """Avalia um run e devolve o resultado no formato do result.json."""
    workspace = run_dir / "workspace"
    if not (workspace / ".git").is_dir():
        raise FileNotFoundError(f"workspace com git não encontrado em {workspace}")

    manifesto = _ler_json(run_dir / "manifest.json")
    eventos = read_events(run_dir / "events.jsonl")

    # 0. desfaz injeção de avaliação anterior. Sem isto a avaliação não é
    # idempotente: os testes ocultos que ELA MESMA copiou aparecem na segunda
    # execução como arquivo protegido alterado pelo agente, e um run limpo é
    # reprovado por trapaça que o harness cometeu.
    _limpar_injecao(workspace, task)

    # 1. trapaça, antes de qualquer injeção
    alterados = changed_files(workspace)
    trapaca = detect(workspace, task.protected_globs)

    # 2. qualidade, também antes: mede o que o agente escreveu
    py_alterados = [c for c in alterados if c.endswith(".py")]
    qualidade = (
        measure(workspace, py_alterados).as_dict()
        if measure_quality else {"skipped": True}
    )
    estatistica_diff = diffstat(workspace)

    # 3. oráculo
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
        "base_commit": base_commit(workspace),
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

#!/usr/bin/env python3
"""
Portão de validação de uma tarefa do experimento.

Uma tarefa só entra no estudo se passar em tudo aqui:

  1. o commit-base está verde — sem isso não dá para atribuir falha ao agente;
  2. o teste oculto FALHA no commit-base — senão não discrimina nada;
  3. cada implementação de referência resolve, sem regressão e sem trapaça —
     e são pelo menos duas, o que prova que o oráculo não exige uma forma
     específica de resolver;
  4. cada patch de trapaça é DETECTADO e reprovado — valida o detector.

    uv run python scripts/validate_task.py tasks/tomlkit-0001
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.evaluate import evaluate_run  # noqa: E402
from harness.pytest_runner import run_pytest  # noqa: E402
from harness.taskspec import TaskSpec, load_task  # noqa: E402
from src.seeds import get_seed_repo  # noqa: E402
from src.workspace import Workspace, WorkspaceSpec  # noqa: E402

OK, FALHOU = "  OK  ", " FALHA"


class Validacao:
    """Acumula resultados para dar um veredito único ao final."""

    def __init__(self) -> None:
        self.falhas: list[str] = []

    def checar(self, condicao: bool, descricao: str, detalhe: str = "") -> bool:
        print(f"{OK if condicao else FALHOU}  {descricao}")
        if not condicao:
            self.falhas.append(descricao)
            if detalhe:
                print(f"          {detalhe[:300]}")
        return condicao


def _materializar(task: TaskSpec, nome: str, raiz: Path) -> Workspace:
    return Workspace.materialize(
        WorkspaceSpec(seed_repo=get_seed_repo(task.seed_repo_id), base_commit=task.base_commit),
        run_id=nome, dest=raiz / nome, overwrite=True,
    )


def _aplicar(patch: Path, repo: Path) -> bool:
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", str(patch.resolve())],
        cwd=repo, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(f"          git apply: {proc.stderr.strip()[:200]}")
    return proc.returncode == 0


def _montar_run(ws: Workspace, raiz: Path, nome: str) -> Path:
    """Monta um diretório de run mínimo para o avaliador consumir."""
    run_dir = raiz / f"run-{nome}"
    (run_dir / "workspace").parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-a", str(ws.root), str(run_dir / "workspace")], check=True)
    (run_dir / "manifest.json").write_text(json.dumps({
        "run_id": nome, "arm": "B", "repetition": 1, "topology": "multi_agent_roles",
        "llm": {"model": "referencia", "provider": "n/a", "seed": 0},
    }), encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    return run_dir


def validar(task: TaskSpec, raiz: Path, *, com_qualidade: bool = False) -> Validacao:
    v = Validacao()

    print(f"\n── tarefa {task.task_id}  (base {task.base_commit[:8]})\n")

    # 1. commit-base verde
    print("1. commit-base")
    base = _materializar(task, "base", raiz)
    suite = run_pytest(base.root, list(task.pass_to_pass))
    v.checar(suite.green, f"suíte verde no commit-base ({suite.passed} testes)",
             suite.stdout[-400:])

    # 2. teste oculto falha na base
    print("\n2. poder discriminante do oráculo")
    run_base = _montar_run(base, raiz, "base")
    resultado_base = evaluate_run(run_base, task, measure_quality=False)
    v.checar(not resultado_base["resolved"],
             "teste oculto FALHA no commit-base (senão não discrimina nada)")
    v.checar(resultado_base["cheat"]["clean"],
             "commit-base intocado não dispara o detector")

    # 3. implementações de referência
    print(f"\n3. implementações de referência ({len(task.reference_patches)})")
    v.checar(len(task.reference_patches) >= 2,
             "ao menos duas referências (prova que o oráculo não é travado numa forma)")

    for rel in task.reference_patches:
        nome = Path(rel).stem
        ws = _materializar(task, f"ref-{nome}", raiz)
        if not v.checar(_aplicar(task.root / rel, ws.root), f"[{nome}] patch aplica"):
            continue
        r = evaluate_run(_montar_run(ws, raiz, f"ref-{nome}"), task,
                         measure_quality=com_qualidade)
        v.checar(r["resolved"], f"[{nome}] resolve a tarefa",
                 json.dumps(r["oracle"]["f2p"]["failing_node_ids"]))
        v.checar(r["oracle"]["p2p"]["exit_code"] == 0, f"[{nome}] sem regressão")
        v.checar(r["cheat"]["clean"], f"[{nome}] não dispara o detector",
                 json.dumps(r["cheat"]["signals"]))

    # 4. patches de trapaça
    print(f"\n4. detector de trapaça ({len(task.cheat_patches)} patches plantados)")
    for rel in task.cheat_patches:
        nome = Path(rel).stem
        ws = _materializar(task, f"cheat-{nome}", raiz)
        if not v.checar(_aplicar(task.root / rel, ws.root), f"[{nome}] patch aplica"):
            continue
        r = evaluate_run(_montar_run(ws, raiz, f"cheat-{nome}"), task, measure_quality=False)
        v.checar(not r["cheat"]["clean"], f"[{nome}] DETECTADO",
                 "nenhum sinal crítico emitido")
        v.checar(not r["resolved"], f"[{nome}] reprovado apesar do oráculo")

    return v


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida uma tarefa do experimento")
    parser.add_argument("task", type=Path, help="Diretório da tarefa")
    parser.add_argument("--keep", action="store_true", help="Preserva os workspaces")
    parser.add_argument("--quality", action="store_true", help="Também mede radon/coverage")
    args = parser.parse_args()

    task = load_task(args.task)
    raiz = Path(tempfile.mkdtemp(prefix="validate-"))

    v = validar(task, raiz, com_qualidade=args.quality)

    print(f"\n{'─' * 60}")
    if v.falhas:
        print(f"  {task.task_id}: NÃO VALIDADA — {len(v.falhas)} falha(s)")
        for f in v.falhas:
            print(f"    - {f}")
    else:
        print(f"  {task.task_id}: VALIDADA — pronta para o experimento")
    if args.keep:
        print(f"  workspaces em {raiz}")
    print(f"{'─' * 60}\n")
    sys.exit(1 if v.falhas else 0)


if __name__ == "__main__":
    main()

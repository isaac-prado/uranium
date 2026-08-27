"""
Oráculo: julga se a tarefa foi resolvida, com testes que o agente nunca viu.

Três verificações, nesta ordem:

  fail-to-pass  — os testes derivados da correção original precisam PASSAR.
                  Eles falham no commit-base; se passam agora, o problema
                  foi resolvido.
  pass-to-pass  — a suíte que já passava precisa continuar passando. Impede
                  creditar uma correção que quebrou outra coisa.
  regressão     — a suíte original completa, como estava no commit-base.

Os testes ocultos são injetados em `tests/_uranium_hidden/`, diretório que
não existe no commit-base e que o agente não pode ter criado (é área
protegida). Ele é excluído das verificações de regressão para não se medir
o oráculo contra si mesmo.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.cheat import HIDDEN_DIR
from harness.pytest_runner import PytestResult, run_pytest
from harness.taskspec import TaskSpec
from harness.venvs import python_for


@dataclass
class OracleResult:
    f2p_total: int
    f2p_passed: int
    p2p: PytestResult
    regression: PytestResult
    f2p: PytestResult

    @property
    def resolved(self) -> bool:
        """Resolvido = todos os ocultos passam E nada regrediu."""
        return (
            self.f2p_total > 0
            and self.f2p_passed == self.f2p_total
            and self.p2p.green
            and self.regression.green
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "f2p_total": self.f2p_total,
            "f2p_passed": self.f2p_passed,
            "f2p": self.f2p.as_dict(),
            "p2p": self.p2p.as_dict(),
            "regression": self.regression.as_dict(),
        }


_ARQUIVO_DO_DIFF = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def apply_test_patch(repo: Path, task: TaskSpec) -> list[str]:
    """
    Restaura os testes do commit-base e aplica o diff de teste do upstream.

    A restauração vem antes de propósito: se o agente adulterou um arquivo de
    teste, a adulteração é desfeita aqui e a medição acontece contra o teste
    que o upstream escreveu. A trapaça continua registrada — o detector já
    rodou, antes desta função.
    """
    patch = task.root / task.test_patch
    if not patch.exists():
        raise FileNotFoundError(f"patch de teste ausente: {patch}")

    texto = patch.read_text(encoding="utf-8")
    alvos = _ARQUIVO_DO_DIFF.findall(texto)
    if not alvos:
        raise ValueError(f"patch de teste não altera arquivo nenhum: {patch}")

    for alvo in alvos:
        # `--` separa revisão de caminho; arquivo que não existe na base é
        # criado pelo próprio patch e não precisa ser restaurado.
        _git(repo, "checkout", task.base_commit, "--", alvo)

    proc = _git(repo, "apply", "--whitespace=nowarn", str(patch))
    if proc.returncode != 0:
        raise RuntimeError(f"falha ao aplicar {patch.name}: {proc.stderr.strip()[:400]}")
    return alvos


def inject_hidden_tests(repo: Path, task: TaskSpec) -> list[str]:
    """
    Coloca o oráculo dentro do workspace, já modificado pelo agente.

    Precisa rodar DEPOIS da detecção de trapaça: o que é injetado aqui
    apareceria como alteração do agente.
    """
    injetados: list[str] = []

    if task.test_patch:
        injetados += apply_test_patch(repo, task)

    if not task.hidden_tests:
        return injetados

    destino = repo / HIDDEN_DIR
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "__init__.py").write_text("", encoding="utf-8")

    for origem in task.hidden_test_paths():
        if not origem.exists():
            raise FileNotFoundError(f"teste oculto ausente: {origem}")
        alvo = destino / origem.name
        shutil.copy2(origem, alvo)
        injetados.append(str(alvo.relative_to(repo)))
    return injetados


def evaluate_oracle(repo: Path, task: TaskSpec, *, timeout_s: int = 600) -> OracleResult:
    """Roda as três verificações sobre o workspace já modificado."""
    inject_hidden_tests(repo, task)

    # O interpretador é o do repo-semente, nunca o do avaliador: a suíte do
    # upstream não pode enxergar dependência que o upstream não declara.
    py = python_for(task.seed_repo_id)

    f2p = run_pytest(repo, list(task.fail_to_pass), timeout_s=timeout_s, python_bin=py)

    # exclui o diretório oculto: p2p e regressão medem a suíte original
    ignorar = (f"--ignore={HIDDEN_DIR}",)
    p2p = run_pytest(repo, list(task.pass_to_pass), timeout_s=timeout_s,
                     extra_args=ignorar, python_bin=py)
    alvos_suite = list(task.suite_targets or task.pass_to_pass)
    regression = run_pytest(repo, alvos_suite, timeout_s=timeout_s,
                            extra_args=ignorar, python_bin=py)

    total = len(task.fail_to_pass)
    passaram = total - len([n for n in f2p.failing_node_ids if n in task.fail_to_pass])
    if not f2p.green and not f2p.failing_node_ids:
        passaram = 0  # erro de coleta: nada passou

    return OracleResult(
        f2p_total=total,
        f2p_passed=max(0, passaram),
        f2p=f2p,
        p2p=p2p,
        regression=regression,
    )

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

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.cheat import HIDDEN_DIR
from harness.pytest_runner import PytestResult, run_pytest
from harness.taskspec import TaskSpec


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


def inject_hidden_tests(repo: Path, task: TaskSpec) -> list[str]:
    """
    Copia os testes ocultos para dentro do workspace.

    Precisa rodar DEPOIS da detecção de trapaça: os arquivos injetados
    apareceriam como alteração do agente.
    """
    destino = repo / HIDDEN_DIR
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "__init__.py").write_text("", encoding="utf-8")

    injetados = []
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

    f2p = run_pytest(repo, list(task.fail_to_pass), timeout_s=timeout_s)

    # exclui o diretório oculto: p2p e regressão medem a suíte original
    ignorar = (f"--ignore={HIDDEN_DIR}",)
    p2p = run_pytest(repo, list(task.pass_to_pass), timeout_s=timeout_s, extra_args=ignorar)
    regression = run_pytest(repo, None, timeout_s=timeout_s, extra_args=ignorar)

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

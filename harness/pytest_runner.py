"""
Execução de pytest para o avaliador.

Reimplementação independente da de `src/tools/exec.py`. Se o avaliador
reaproveitasse o executor do agente, um defeito no parsing contaminaria ao
mesmo tempo a decisão do agente e a métrica do TCC.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TIMEOUT_S = 600

_CONTAGEM = re.compile(r"(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b")
_DURACAO = re.compile(r"\bin\s+([\d.]+)s")
# O node id vai até o fim da linha, ou até o " - " que separa a mensagem.
# `\S+` truncava id parametrizado com espaço: um
# `test_x[SET NULL]` virava `test_x[SET`, que o pytest não sabe reexecutar —
# e como o fail-to-pass é escrito a partir daqui, o oráculo ficava inútil.
_FALHOU = re.compile(r"^(?:FAILED|ERROR)\s+(.+?)(?:\s+-\s.*)?$", re.MULTILINE)


@dataclass
class PytestResult:
    exit_code: int
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_s: float = 0.0
    failing_node_ids: list[str] = field(default_factory=list)
    stdout: str = ""
    timed_out: bool = False
    network_isolated: bool = False

    @property
    def green(self) -> bool:
        return self.exit_code == 0

    def as_dict(self) -> dict:
        return {
            "exit_code": self.exit_code,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "duration_s": round(self.duration_s, 3),
            "failing_node_ids": self.failing_node_ids[:50],
            "timed_out": self.timed_out,
            "network_isolated": self.network_isolated,
        }


def network_isolation_available() -> bool:
    """`unshare -rn` roda pytest num namespace de rede vazio."""
    if not shutil.which("unshare"):
        return False
    proc = subprocess.run(
        ["unshare", "-rn", "true"], capture_output=True, timeout=10
    )
    return proc.returncode == 0


def _env() -> dict[str, str]:
    limpo = {
        k: v for k, v in os.environ.items()
        if not k.startswith(("PYTEST_", "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"))
    }
    limpo.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "NO_COLOR": "1",
        "PY_COLORS": "0",
        "COLUMNS": "120",
    })
    return limpo


def parse_output(stdout: str, fallback_duration: float) -> dict:
    contagens = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    duracao = fallback_duration

    for linha in reversed([l for l in stdout.splitlines() if l.strip()]):
        achados = _CONTAGEM.findall(linha)
        if not achados:
            continue
        for valor, rotulo in achados:
            chave = "errors" if rotulo.startswith("error") else rotulo
            if chave in contagens:
                contagens[chave] = int(valor)
        if m := _DURACAO.search(linha):
            duracao = float(m.group(1))
        break

    return {
        **contagens,
        "duration_s": duracao,
        "failing_node_ids": sorted(set(_FALHOU.findall(stdout))),
    }


def run_pytest(
    repo: Path,
    targets: list[str] | None = None,
    *,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    isolate_network: bool = True,
    extra_args: tuple[str, ...] = (),
    python_bin: str | None = None,
) -> PytestResult:
    """
    Roda pytest no workspace avaliado.

    Por padrão dentro de um namespace de rede vazio: o caminho de avaliação
    não pode ter dependência de rede, senão o resultado deixa de ser
    reprodutível offline.
    """
    cmd = [
        python_bin or sys.executable, "-m", "pytest",
        "-q", "-rf", "--tb=short",
        "-p", "no:cacheprovider",
        "-o", "addopts=",
        *extra_args,
        *(targets or []),
    ]
    isolado = isolate_network and network_isolation_available()
    if isolado:
        cmd = ["unshare", "-rn", *cmd]

    inicio = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, cwd=repo, capture_output=True, text=True,
            env=_env(), timeout=timeout_s,
        )
        decorrido = time.perf_counter() - inicio
        stdout, exit_code, estourou = proc.stdout + proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        decorrido = time.perf_counter() - inicio
        bruto = exc.stdout or b""
        stdout = bruto.decode("utf-8", "replace") if isinstance(bruto, bytes) else str(bruto)
        exit_code, estourou = -1, True

    return PytestResult(
        exit_code=exit_code,
        stdout=stdout,
        timed_out=estourou,
        network_isolated=isolado,
        **parse_output(stdout, decorrido),
    )

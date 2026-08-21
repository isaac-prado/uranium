"""
Execução real da suíte de testes dentro do workspace.

Esta é a peça que substitui julgamento semântico por evidência: o
Validator decide `is_valid` a partir do exit code que sai daqui, não a
partir de opinião de LLM sobre o texto do patch.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from src.schemas.test_report import TestReport
from src.tools.base import MAX_TOOL_OUTPUT_CHARS, truncate
from src.workspace import PathNotAllowed, Workspace

DEFAULT_TEST_TIMEOUT_S = 120

# Ambiente determinístico: sem cache de bytecode, hash seed fixo, sem cor,
# sem proxy herdado. O mesmo comando tem de produzir o mesmo resultado.
_SCRUBBED_ENV_PREFIXES = ("PYTEST_", "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")

_SUMMARY_RX = re.compile(
    r"(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b"
)
_DURATION_RX = re.compile(r"\bin\s+([\d.]+)s")
_FAILED_LINE_RX = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)", re.MULTILINE)


def _build_env(ws: Workspace) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(_SCRUBBED_ENV_PREFIXES)}
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8",
            "NO_COLOR": "1",
            "PY_COLORS": "0",
            "COLUMNS": "120",
        }
    )
    return env


def parse_pytest_output(stdout: str, exit_code: int, fallback_duration: float) -> dict:
    """
    Extrai contagens e node ids da saída do pytest.

    Usa a linha de resumo e as linhas `FAILED <node_id>` de `-rf`, que dão
    node ids reutilizáveis numa reexecução — o que o junit-xml não dá,
    porque ele achata `::` em classname pontuado.
    """
    counts = {
        "passed": 0, "failed": 0, "errors": 0,
        "skipped": 0, "xfailed": 0, "xpassed": 0,
    }

    # A linha de resumo é a última não-vazia com contagens.
    for line in reversed([ln for ln in stdout.splitlines() if ln.strip()]):
        found = _SUMMARY_RX.findall(line)
        if not found:
            continue
        for value, label in found:
            key = "errors" if label.startswith("error") else label
            counts[key] = int(value)
        match = _DURATION_RX.search(line)
        duration = float(match.group(1)) if match else fallback_duration
        break
    else:
        duration = fallback_duration

    node_ids = sorted(set(_FAILED_LINE_RX.findall(stdout)))
    return {**counts, "duration_s": duration, "failing_node_ids": node_ids}


def run_pytest(
    ws: Workspace,
    node_ids: list[str] | None = None,
    *,
    timeout_s: int = DEFAULT_TEST_TIMEOUT_S,
    python_bin: str | None = None,
    extra_args: tuple[str, ...] = (),
) -> TestReport:
    """
    Roda a suíte (ou apenas `node_ids`) e devolve um TestReport estruturado.

    Chamada direta, não mediada por LLM — o Validator usa esta função.
    """
    targets: list[str] = []
    for node in node_ids or []:
        file_part = node.split("::", 1)[0]
        try:
            ws.resolve(file_part)
        except PathNotAllowed:
            continue  # ignora node id que tenta escapar do workspace
        targets.append(node)

    cmd = [
        python_bin or sys.executable,
        "-m", "pytest",
        "-q", "-rf",
        "--tb=short",
        "-p", "no:cacheprovider",
        "-o", "addopts=",
        *extra_args,
        *targets,
    ]

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=ws.root,
            capture_output=True,
            text=True,
            env=_build_env(ws),
            timeout=timeout_s,
        )
        elapsed = time.perf_counter() - start
        stdout, exit_code, timed_out = proc.stdout + proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - start
        stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        exit_code, timed_out = -1, True

    parsed = parse_pytest_output(stdout, exit_code, elapsed)

    return TestReport(
        exit_code=exit_code,
        timed_out=timed_out,
        stdout_tail=truncate(stdout, MAX_TOOL_OUTPUT_CHARS),
        command=" ".join(cmd),
        **parsed,
    )


def run_tests(
    ws: Workspace,
    node_ids: list[str] | None = None,
    timeout_s: int = DEFAULT_TEST_TIMEOUT_S,
    *,
    python_bin: str | None = None,
) -> str:
    """Versão da execução de testes exposta ao agente, com saída em texto."""
    report = run_pytest(ws, node_ids, timeout_s=timeout_s, python_bin=python_bin)

    if report.timed_out:
        return (
            f"TIMEOUT: a suíte excedeu {timeout_s}s e foi interrompida.\n"
            f"{report.stdout_tail}"
        )

    header = report.summary()
    if report.green:
        return f"{header}\nSuíte verde."

    failing = "\n".join(f"  - {n}" for n in report.failing_node_ids[:25])
    if len(report.failing_node_ids) > 25:
        failing += f"\n  [... {len(report.failing_node_ids) - 25} node ids a mais ...]"

    return (
        f"{header}\n"
        f"Testes falhando ({len(report.failing_node_ids)}):\n{failing}\n\n"
        f"Saída:\n{report.stdout_tail}"
    )

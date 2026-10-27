"""
Execução real da suíte de testes dentro do workspace.

Esta é a peça que substitui julgamento semântico por evidência: o
Validator decide `is_valid` a partir do exit code que sai daqui, não a
partir de opinião de LLM sobre o texto do patch.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from src.schemas.test_report import TestReport
from src.tools.base import MAX_TOOL_OUTPUT_CHARS, truncate
from src.workspace import PathNotAllowed, Workspace

DEFAULT_TEST_TIMEOUT_S = 120

# Decisão 49 (27/10/2026, aprovada por escrito): toda execução de código do
# agente (suíte, trecho Python, bloco de linha de comando) roda numa caixa de
# areia bubblewrap: só o workspace é gravável; o venv da tarefa e o sistema
# entram só leitura; o resto do disco (espelhos, src/ do uranium, caches) não
# existe lá dentro; sem rede; HOME e /tmp em tmpfs. Antes um trecho em
# `run_python` enxergava o disco inteiro e a rede. Vai ao manifesto em
# `shared_limits.sandbox`. Sem o bubblewrap a execução falha alto em vez de
# rodar aberta; `URANIUM_SANDBOX=off` desliga (só depuração) e o manifesto
# registra "off".
SANDBOX = "bwrap"
_RO_SISTEMA = ("/usr", "/lib", "/lib64", "/bin", "/sbin", "/etc")


def sandbox_mode() -> str:
    """Modo efetivo da caixa de areia, registrado no manifesto."""
    return "off" if os.getenv("URANIUM_SANDBOX", "").strip().lower() == "off" else SANDBOX


def _prefixos_do_python(python_bin: str) -> list[str]:
    """
    Diretórios que o interpretador do venv precisa enxergar: o venv, a
    instalação base apontada por `pyvenv.cfg` (`home`) e a que o binário
    real resolve (no uv são dois caminhos, um deles symlink).
    """
    bin_path = Path(python_bin)
    venv = bin_path.parent.parent
    candidatos = [venv]
    cfg = venv / "pyvenv.cfg"
    if cfg.is_file():
        for linha in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
            chave, sep, valor = linha.partition("=")
            if sep and chave.strip() == "home":
                candidatos.append(Path(valor.strip()).parent)
    candidatos.append(Path(os.path.realpath(bin_path)).parent.parent)
    prefixos: list[str] = []
    for c in candidatos:
        s = str(c)
        if c.is_dir() and s not in prefixos and not any(s.startswith(f"{r}/") for r in _RO_SISTEMA):
            prefixos.append(s)
    return prefixos


def envolver_na_caixa(ws: Workspace, cmd: list[str], python_bin: str) -> list[str]:
    """argv de `cmd` dentro da caixa de areia (ou `cmd` intacto com a caixa desligada)."""
    if sandbox_mode() == "off":
        return list(cmd)
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise RuntimeError(
            "bubblewrap (bwrap) ausente: a execução de código do agente exige a caixa de areia "
            "(decisão 49). Instale o pacote bubblewrap ou, só para depuração, URANIUM_SANDBOX=off."
        )
    argv = [bwrap]
    for d in _RO_SISTEMA:
        if os.path.isdir(d):
            argv += ["--ro-bind", d, d]
    argv += ["--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", "/home"]
    if os.path.isdir("/root"):
        argv += ["--tmpfs", "/root"]
    for prefixo in _prefixos_do_python(python_bin):
        argv += ["--ro-bind", prefixo, prefixo]
    raiz = str(ws.root)
    argv += [
        "--bind", raiz, raiz,
        "--unshare-all", "--die-with-parent", "--new-session",
        "--chdir", raiz,
        "--", *cmd,
    ]
    return argv


def executar_isolado(
    ws: Workspace, cmd: list[str], *, timeout_s: int, python_bin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Roda `cmd` no workspace, dentro da caixa de areia, com o ambiente determinístico."""
    env = _build_env(ws)
    env["HOME"] = "/tmp"
    argv = envolver_na_caixa(ws, cmd, python_bin or ws.spec.seed_repo.python_bin)
    return subprocess.run(
        argv, cwd=ws.root, capture_output=True, text=True, env=env, timeout=timeout_s,
    )

# Ambiente determinístico: sem cache de bytecode, hash seed fixo, sem cor,
# sem proxy herdado. O mesmo comando tem de produzir o mesmo resultado.
_SCRUBBED_ENV_PREFIXES = ("PYTEST_", "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")

_SUMMARY_RX = re.compile(
    r"(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b"
)
_DURATION_RX = re.compile(r"\bin\s+([\d.]+)s")
# O node id vai até o fim da linha, ou até o " - " que separa a mensagem.
# `\S+` truncava id parametrizado com espaço: um
# `test_x[SET NULL]` virava `test_x[SET`, que o pytest não sabe reexecutar —
# e como o fail-to-pass é escrito a partir daqui, o oráculo ficava inútil.
_FAILED_LINE_RX = re.compile(r"^(?:FAILED|ERROR)\s+(.+?)(?:\s+-\s.*)?$", re.MULTILINE)


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

    Sem `node_ids`, os alvos vêm de `suite_targets` do repo-semente, não de
    um pytest pelado: no peewee o padrão de coleta do pytest acha 5 testes
    de 1.634, e o agente enxergaria uma suíte diferente da que o harness
    mede. O interpretador também é o do repo, nunca o do projeto.
    """
    seed_repo = ws.spec.seed_repo

    targets: list[str] = []
    for node in node_ids or []:
        file_part = node.split("::", 1)[0]
        try:
            ws.resolve(file_part)
        except PathNotAllowed:
            continue  # ignora node id que tenta escapar do workspace
        targets.append(node)
    if not targets:
        targets = list(seed_repo.suite_targets)

    cmd = [
        python_bin or seed_repo.python_bin,
        "-m", "pytest",
        "-q", "-rf",
        "--tb=short",
        "-p", "no:cacheprovider",
        "-o", "addopts=",
        # rootdir fixo no workspace: sem isto o pytest sobe até o pyproject.toml
        # do uranium (os runs ficam em runs/), os node ids ganham o prefixo
        # runs/.../workspace/ e o --deselect, que compara prefixo de node id,
        # não casa nada (rodada 2, 14/10/2026; shared_limits.pytest_rootdir).
        "--rootdir", ".",
        # Testes visíveis que contradizem a correção certa (decisão 27):
        # iguais para o agente, o driver e o validador, nos dois braços.
        *(arg for node in getattr(ws.spec, "visible_deselect", ()) for arg in ("--deselect", node)),
        *extra_args,
        *targets,
    ]

    start = time.perf_counter()
    try:
        proc = executar_isolado(ws, cmd, timeout_s=timeout_s, python_bin=python_bin or seed_repo.python_bin)
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


SNIPPET_FILE = ".uranium_snippet.py"
DEFAULT_SNIPPET_TIMEOUT_S = 60


def _nao_rastreados(ws: Workspace) -> set[str]:
    proc = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ws.root, capture_output=True, text=True,
    )
    return set(proc.stdout.split())


def reverter_protegidos(ws: Workspace, antes: set[str] | None = None) -> list[str]:
    """
    Desfaz o que uma execução fez em arquivos protegidos e devolve os que
    ela tocou.

    Arquivo rastreado volta ao commit-base (`git checkout`); arquivo novo,
    não rastreado, é apagado, porque `git checkout` não o remove. Sem isso um
    arquivo deixado por uma execução ficava no workspace e toda execução
    seguinte era recusada (rodada 7, peewee-0002 rep02: `exec_test.py` criado
    por código em `run_python`; 16 execuções do developer e 28 do validador
    recusadas até o fim; docs/tcc/23-rodada-7.md §4.4). Correção aprovada
    pelo autor em 22/10/2026 (decisão 47). `antes` é o conjunto de protegidos
    já tocados antes da execução: tudo é restaurado, mas só o que é novo em
    relação a ele é atribuído a esta execução.
    """
    violados = ws.protected_touched()
    if not violados:
        return []
    novos = _nao_rastreados(ws)
    for rel in violados:
        if rel in novos:
            (ws.root / rel).unlink(missing_ok=True)
        else:
            subprocess.run(["git", "checkout", "--", rel], cwd=ws.root, capture_output=True)
    ja_tocados = antes or set()
    return [rel for rel in violados if rel not in ja_tocados]


def run_python(
    ws: Workspace,
    code: str,
    timeout_s: int = DEFAULT_SNIPPET_TIMEOUT_S,
    *,
    python_bin: str | None = None,
) -> str:
    """
    Executa um trecho Python dentro do workspace.

    Sem isto o agente não tem como verificar a própria correção: a suíte
    visível já está verde no commit-base (o teste que discrimina é oculto),
    então rodar os testes não diz nada sobre o problema em questão. O
    enunciado traz um trecho de reprodução, e é este o meio de executá-lo.

    Guarda: se o trecho alterar arquivo protegido — escrever num teste por
    dentro do Python contornaria a guarda de caminho — a alteração é
    revertida e a chamada é recusada.
    """
    antes = set(ws.protected_touched())
    alvo = ws.root / SNIPPET_FILE
    alvo.write_text(code, encoding="utf-8")

    cmd = [python_bin or ws.spec.seed_repo.python_bin, SNIPPET_FILE]
    inicio = time.perf_counter()
    try:
        proc = executar_isolado(ws, cmd, timeout_s=timeout_s, python_bin=python_bin)
        saida = (proc.stdout + proc.stderr).strip()
        codigo = proc.returncode
        estourou = False
    except subprocess.TimeoutExpired:
        saida, codigo, estourou = "", -1, True
    finally:
        alvo.unlink(missing_ok=True)

    duracao = time.perf_counter() - inicio

    violados = reverter_protegidos(ws, antes)
    if violados:
        return (
            "RECUSADO: o trecho alterou arquivo protegido "
            f"({', '.join(violados)}). A alteração foi revertida. "
            "Testes e configuração não podem ser modificados, nem por código."
        )

    if estourou:
        return f"TIMEOUT: o trecho excedeu {timeout_s}s e foi interrompido."

    cabecalho = f"exit={codigo} em {duracao:.2f}s"
    if not saida:
        return f"{cabecalho}\n(sem saída)"
    return f"{cabecalho}\n{truncate(saida, MAX_TOOL_OUTPUT_CHARS)}"

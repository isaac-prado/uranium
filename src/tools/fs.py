"""
Ferramentas de filesystem expostas ao agente.

Todas retornam string (nunca levantam exceção para o modelo): um erro é
informação recuperável que volta como ToolMessage e o agente decide o que
fazer. Recusa por caminho protegido também é retorno, não exceção — a
tentativa é um sinal comportamental que o estudo quer medir.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from src.tools.base import (
    MAX_READ_CHARS,
    MAX_READ_LINES,
    MAX_SEARCH_RESULTS,
    truncate,
)
from src.workspace import PathNotAllowed, Workspace

DENIED_PREFIX = "RECUSADO:"
ERROR_PREFIX = "ERRO:"

_BINARY_HINT = b"\x00"


def _repo_files(ws: Workspace, subdir: str = ".") -> list[str]:
    """Arquivos versionados + novos, respeitando .gitignore."""
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", subdir],
        cwd=ws.root,
        capture_output=True,
        text=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def list_files(ws: Workspace, path: str = ".", pattern: str = "*", max_results: int = 200) -> str:
    """Lista arquivos do repositório sob `path` casando com `pattern`."""
    try:
        ws.resolve(path)
    except PathNotAllowed as exc:
        return f"{DENIED_PREFIX} {exc}"

    files = _repo_files(ws, path)
    if pattern and pattern != "*":
        rx = re.compile(pattern.replace(".", r"\.").replace("*", ".*") + "$")
        files = [f for f in files if rx.search(Path(f).name) or rx.search(f)]

    if not files:
        return f"Nenhum arquivo encontrado em {path!r} com padrão {pattern!r}."

    shown = sorted(files)[:max_results]
    out = "\n".join(shown)
    if len(files) > max_results:
        out += f"\n[... {len(files) - max_results} arquivos a mais; refine o padrão ...]"
    return out


def read_file(ws: Workspace, path: str, start_line: int = 1, end_line: int = -1) -> str:
    """Lê um arquivo (ou uma faixa de linhas) com numeração."""
    try:
        target = ws.resolve(path)
    except PathNotAllowed as exc:
        return f"{DENIED_PREFIX} {exc}"

    if not target.exists():
        return f"{ERROR_PREFIX} arquivo não existe: {path}"
    if target.is_dir():
        return f"{ERROR_PREFIX} {path} é um diretório — use list_files."

    raw = target.read_bytes()
    if _BINARY_HINT in raw[:4096]:
        return f"{ERROR_PREFIX} {path} parece binário ({len(raw)} bytes)."

    lines = raw.decode("utf-8", errors="replace").splitlines()
    total = len(lines)

    start = max(1, start_line)
    stop = total if end_line in (-1, 0) else min(total, end_line)
    if start > total:
        return f"{ERROR_PREFIX} start_line {start} além do fim ({total} linhas)."

    selected = lines[start - 1 : stop]
    truncated_by_lines = False
    if len(selected) > MAX_READ_LINES:
        selected = selected[:MAX_READ_LINES]
        stop = start + MAX_READ_LINES - 1
        truncated_by_lines = True

    body = "\n".join(f"{start + i:>5}\t{line}" for i, line in enumerate(selected))
    header = f"{path} (linhas {start}-{stop} de {total})"

    if truncated_by_lines:
        header += f" [truncado em {MAX_READ_LINES} linhas — use start_line/end_line]"
    if len(body) > MAX_READ_CHARS:
        body = truncate(body, MAX_READ_CHARS)
        header += " [truncado por tamanho]"

    return f"{header}\n{body}"


def search_code(
    ws: Workspace,
    pattern: str,
    path: str = ".",
    is_regex: bool = True,
    max_results: int = MAX_SEARCH_RESULTS,
) -> str:
    """Busca um padrão no código, retornando `arquivo:linha: conteúdo`."""
    try:
        ws.resolve(path)
    except PathNotAllowed as exc:
        return f"{DENIED_PREFIX} {exc}"

    try:
        rx = re.compile(pattern if is_regex else re.escape(pattern))
    except re.error as exc:
        return f"{ERROR_PREFIX} regex inválida: {exc}"

    hits: list[str] = []
    truncated = False
    for rel in sorted(_repo_files(ws, path)):
        target = ws.root / rel
        if not target.is_file():
            continue
        try:
            raw = target.read_bytes()
        except OSError:
            continue
        if _BINARY_HINT in raw[:4096]:
            continue
        for num, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
            if rx.search(line):
                hits.append(f"{rel}:{num}: {line.strip()[:200]}")
                if len(hits) >= max_results:
                    truncated = True
                    break
        if truncated:
            break

    if not hits:
        return f"Nenhuma ocorrência de {pattern!r} em {path!r}."
    out = "\n".join(hits)
    if truncated:
        out += f"\n[... limite de {max_results} resultados atingido; refine a busca ...]"
    return out


def write_file(ws: Workspace, path: str, content: str) -> str:
    """
    Escreve conteúdo num arquivo do workspace.

    Recusa caminhos protegidos (testes e configuração). A recusa é retornada
    ao agente como texto — a tentativa fica registrada na telemetria.
    """
    try:
        target = ws.resolve(path)
    except PathNotAllowed as exc:
        return f"{DENIED_PREFIX} {exc}"

    if ws.is_protected(path):
        return (
            f"{DENIED_PREFIX} {path} está em área protegida (testes/configuração) "
            "e não pode ser modificado. Altere o código de produção."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode("utf-8")
    target.write_bytes(data)
    return f"Gravado {path} ({len(data)} bytes, {content.count(chr(10)) + 1} linhas)."

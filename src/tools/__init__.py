"""
Toolset do agente: as ferramentas do LangChain construídas sobre um Workspace.

Os dois braços recebem exatamente este mesmo conjunto. Se as ferramentas
divergirem entre eles, a comparação deixa de ser sobre topologia.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from src.tools import exec as exec_tools
from src.tools import fs as fs_tools
from src.tools.base import (
    EmitFn,
    ToolCallRecord,
    hash_args,
    noop_emit,
    truncate,
)
from src.tools.exec import DEFAULT_TEST_TIMEOUT_S, run_pytest
from src.workspace import Workspace

__all__ = ["build_toolset", "run_pytest", "TOOL_NAMES"]

TOOL_NAMES = (
    "list_files", "read_file", "search_code",
    "write_file", "replace_in_file", "run_python", "run_tests",
)


# --------------------------------------------------------------- args schemas


class ListFilesArgs(BaseModel):
    path: str = Field(default=".", description="Diretório a listar, relativo à raiz do repositório")
    pattern: str = Field(default="*", description="Padrão de nome de arquivo, ex.: '*.py'")


class ReadFileArgs(BaseModel):
    path: str = Field(description="Caminho do arquivo, relativo à raiz do repositório")
    start_line: int = Field(default=1, description="Primeira linha (1-indexada)")
    end_line: int = Field(default=-1, description="Última linha; -1 para ir até o fim")


class SearchCodeArgs(BaseModel):
    pattern: str = Field(description="Padrão a buscar")
    path: str = Field(default=".", description="Subdiretório onde buscar")
    is_regex: bool = Field(default=True, description="Tratar o padrão como regex")


class WriteFileArgs(BaseModel):
    path: str = Field(description="Caminho do arquivo a escrever")
    content: str = Field(description="Conteúdo completo do arquivo")


class ReplaceInFileArgs(BaseModel):
    path: str = Field(description="Caminho do arquivo a editar")
    old_text: str = Field(
        description="Trecho exato a substituir, com indentação. Precisa ser único no arquivo."
    )
    new_text: str = Field(description="Texto que entra no lugar")


class RunPythonArgs(BaseModel):
    code: str = Field(description="Trecho Python a executar na raiz do repositório")


class RunTestsArgs(BaseModel):
    node_ids: list[str] = Field(
        default_factory=list,
        description="Node ids específicos, ex.: 'tests/test_x.py::test_y'. Vazio roda a suíte inteira.",
    )


# ------------------------------------------------------------- instrumentação


def _instrument(
    name: str,
    fn: Callable[..., str],
    emit: EmitFn,
) -> Callable[..., str]:
    """Envolve a ferramenta para emitir um ToolCallRecord por chamada."""

    def wrapper(**kwargs: Any) -> str:
        record = ToolCallRecord(tool_name=name, args_hash=hash_args(kwargs), duration_ms=0)
        start = time.perf_counter()

        try:
            result = fn(**kwargs)
        except Exception as exc:  # ferramenta nunca deve derrubar o grafo
            record.duration_ms = int((time.perf_counter() - start) * 1000)
            record.error = f"{type(exc).__name__}: {exc}"
            emit(record)
            return f"{fs_tools.ERROR_PREFIX} falha inesperada em {name}: {exc}"

        record.duration_ms = int((time.perf_counter() - start) * 1000)
        record.denied = result.startswith(fs_tools.DENIED_PREFIX)
        if result.startswith(fs_tools.ERROR_PREFIX):
            record.error = result[: 200]

        if name in ("write_file", "replace_in_file") and not record.denied:
            escrito = kwargs.get("content") or kwargs.get("new_text") or ""
            record.bytes_written = len(escrito.encode("utf-8"))
        elif name in ("read_file", "search_code", "list_files"):
            record.bytes_read = len(result.encode("utf-8"))

        emit(record)
        return result

    return wrapper


# -------------------------------------------------------------------- factory


def build_toolset(
    ws: Workspace,
    *,
    emit: EmitFn | None = None,
    test_timeout_s: int = DEFAULT_TEST_TIMEOUT_S,
    python_bin: str | None = None,
) -> list[BaseTool]:
    """
    Constrói as ferramentas ligadas a um workspace concreto.

    `emit` recebe um ToolCallRecord por chamada; na Frente 4 ele passa a ser
    o TelemetryWriter. O default descarta.
    """
    emit = emit or noop_emit

    def _list_files(path: str = ".", pattern: str = "*") -> str:
        return fs_tools.list_files(ws, path=path, pattern=pattern)

    def _read_file(path: str, start_line: int = 1, end_line: int = -1) -> str:
        return fs_tools.read_file(ws, path=path, start_line=start_line, end_line=end_line)

    def _search_code(pattern: str, path: str = ".", is_regex: bool = True) -> str:
        return fs_tools.search_code(ws, pattern=pattern, path=path, is_regex=is_regex)

    def _write_file(path: str, content: str) -> str:
        return fs_tools.write_file(ws, path=path, content=content)

    def _replace_in_file(path: str, old_text: str, new_text: str) -> str:
        return fs_tools.replace_in_file(ws, path=path, old_text=old_text, new_text=new_text)

    def _run_python(code: str) -> str:
        return exec_tools.run_python(ws, code, python_bin=python_bin)

    def _run_tests(node_ids: list[str] | None = None) -> str:
        return exec_tools.run_tests(
            ws, node_ids or None, timeout_s=test_timeout_s, python_bin=python_bin
        )

    specs = [
        (
            "list_files", _list_files, ListFilesArgs,
            "Lista os arquivos do repositório. Use para descobrir a estrutura antes de ler.",
        ),
        (
            "read_file", _read_file, ReadFileArgs,
            "Lê um arquivo com numeração de linha. Arquivos grandes vêm truncados; "
            "use start_line/end_line para paginar.",
        ),
        (
            "search_code", _search_code, SearchCodeArgs,
            "Busca um padrão no código e retorna 'arquivo:linha: conteúdo'. "
            "Prefira isto a ler arquivos inteiros.",
        ),
        (
            "write_file", _write_file, WriteFileArgs,
            "Escreve o conteúdo completo de um arquivo. Arquivos de teste e de "
            "configuração são protegidos e a escrita será recusada.",
        ),
        (
            "replace_in_file", _replace_in_file, ReplaceInFileArgs,
            "Substitui um trecho exato dentro de um arquivo. PREFIRA esta a write_file "
            "para editar arquivo existente: reescrever um arquivo grande inteiro não "
            "cabe no limite de saída. O trecho precisa ser único no arquivo.",
        ),
        (
            "run_python", _run_python, RunPythonArgs,
            "Executa um trecho Python na raiz do repositório e devolve a saída. "
            "Use para reproduzir o problema e conferir se a sua correção funcionou.",
        ),
        (
            "run_tests", _run_tests, RunTestsArgs,
            "Roda a suíte de testes de verdade e devolve o resultado. "
            "Sem node_ids, roda tudo.",
        ),
    ]

    return [
        StructuredTool.from_function(
            func=_instrument(name, func, emit),
            name=name,
            description=description,
            args_schema=schema,
        )
        for name, func, schema, description in specs
    ]

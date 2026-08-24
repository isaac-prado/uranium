"""
Teste oculto derivado do commit que corrigiu o problema no upstream.

O agente nunca vê este arquivo: ele é injetado pelo avaliador depois
que o agente termina.
"""

import pytest

from tomlkit.exceptions import UnexpectedCharError
from tomlkit.parser import Parser


def test_array_with_malformed_element_raises() -> None:
    # An element that starts to parse like a value but then hits an
    # unexpected char (e.g. an inline table missing its "=" or "}") must
    # surface the error instead of being swallowed and silently dropped,
    # which left the array truncated to whatever parsed before it.
    for content in (
        "a = [{1]",
        "a = [{a]",
        "a = [1, {2]",
        "a = [{a = 1}, {2]",
        "a = [[1, {x]]",
        "a = [{a.b]",
    ):
        with pytest.raises(UnexpectedCharError):
            Parser(content).parse()


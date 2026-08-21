"""
Invocação tipada do LLM, sem reparo degradado.

O fallback anterior (prompt JSON + json_repair + reprompt corretivo) foi
removido de propósito: ele executava trabalho de correção *fora* do agente e
creditava ao agente o resultado. Num estudo que compara topologias de
orquestração, isso contamina o tratamento — os dois braços passariam a
depender de quanto o harness conserta, não de quanto o agente acerta.

Agora: structured output nativo. Se o modelo não conformar, o erro sobe,
é contabilizado, e consome orçamento — que é o comportamento honesto.
"""

from __future__ import annotations

import os
from typing import Literal, TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from src.config import get_llm

T = TypeVar("T", bound=BaseModel)

StructuredOutputMethod = Literal["function_calling", "json_schema", "json_mode"]

_MESSAGE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}

DEFAULT_METHOD: StructuredOutputMethod = "function_calling"


class StructuredOutputError(RuntimeError):
    """O modelo não produziu saída conforme o schema após as retentativas."""


def _to_messages(
    messages: list[tuple[str, str]] | list[BaseMessage],
) -> list[BaseMessage]:
    """Converte tuplas (role, content) em mensagens LangChain."""
    result: list[BaseMessage] = []
    for item in messages:
        if isinstance(item, BaseMessage):
            result.append(item)
            continue
        role, content = item
        result.append(_MESSAGE_MAP.get(role, HumanMessage)(content=content))
    return result


def get_output_method() -> StructuredOutputMethod:
    """
    Método de structured output, igual nos dois braços.

    `function_calling` é o padrão porque é o mesmo mecanismo usado pelas
    ferramentas — se o modelo passa no teste de aptidão de tool calling,
    passa aqui também.
    """
    method = os.getenv("STRUCTURED_OUTPUT_METHOD", DEFAULT_METHOD).strip().lower()
    if method in ("function_calling", "json_schema", "json_mode"):
        return method  # type: ignore[return-value]
    return DEFAULT_METHOD


def max_retries() -> int:
    """Retentativas de chamada idêntica, para erro transitório de rede/5xx."""
    return max(0, int(os.getenv("STRUCTURED_OUTPUT_RETRIES", "2")))
def invoke_structured(
    schema: type[T],
    messages: list[tuple[str, str]] | list[BaseMessage],
    *,
    temperature: float | None = None,
) -> T:
    """
    Invoca o LLM e devolve uma instância validada do schema.

    Retenta apenas a mesma chamada, para falha transitória. Não reformula o
    prompt nem repara a saída: qualquer não-conformidade é do modelo, e é
    assim que precisa ser medida.
    """
    llm = get_llm(temperature=temperature)
    structured = llm.with_structured_output(schema, method=get_output_method())
    lc_messages = _to_messages(messages)

    attempts = max_retries() + 1
    errors: list[str] = []

    for attempt in range(1, attempts + 1):
        try:
            result = structured.invoke(lc_messages)
        except Exception as exc:
            errors.append(f"tentativa {attempt}: {type(exc).__name__}: {exc}")
            continue

        if result is not None:
            return result
        errors.append(f"tentativa {attempt}: resposta vazia (choices=None)")

    raise StructuredOutputError(
        f"{schema.__name__}: modelo não conformou ao schema em {attempts} tentativas. "
        + "; ".join(errors)
    )

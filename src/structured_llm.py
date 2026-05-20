"""Invocação tipada de LLM com fallback para modelos sem structured output nativo."""

from __future__ import annotations

import json
import os
import re
from typing import Literal, TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from src.config import get_llm, use_json_fallback_only

T = TypeVar("T", bound=BaseModel)

StructuredOutputMethod = Literal["json_mode", "function_calling", "json_schema"]

_MESSAGE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}


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
        cls = _MESSAGE_MAP.get(role, HumanMessage)
        result.append(cls(content=content))
    return result


def _extract_json(text: str) -> str:
    """Extrai JSON de bloco markdown ou texto bruto."""
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


def _get_output_method() -> StructuredOutputMethod:
    """Método de structured output (json_mode funciona melhor em modelos free)."""
    method = os.getenv("STRUCTURED_OUTPUT_METHOD", "json_mode").strip().lower()
    if method in ("json_mode", "function_calling", "json_schema"):
        return method  # type: ignore[return-value]
    return "json_mode"


def invoke_structured(
    schema: type[T],
    messages: list[tuple[str, str]] | list[BaseMessage],
    *,
    temperature: float = 0,
) -> T:
    """
    Invoca o LLM e retorna instância validada do schema Pydantic.

    1. Tenta with_structured_output (json_mode por padrão)
    2. Se falhar, pede JSON explícito e valida com Pydantic
    """
    llm = get_llm(temperature=temperature)
    lc_messages = _to_messages(messages)

    if use_json_fallback_only():
        return _invoke_json_fallback(schema, llm, lc_messages, [])

    method = _get_output_method()
    errors: list[str] = []

    try:
        structured = llm.with_structured_output(schema, method=method)
        result = structured.invoke(lc_messages)
        if result is not None:
            return result
        errors.append(f"{method}: resposta vazia (choices=None)")
    except Exception as exc:
        errors.append(f"{method}: {exc!s}")

    return _invoke_json_fallback(schema, llm, lc_messages, errors)


def _invoke_json_fallback(
    schema: type[T],
    llm,
    messages: list[BaseMessage],
    prior_errors: list[str],
) -> T:
    """Fallback: prompt JSON + parse manual + validação Pydantic."""
    schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)
    fallback_system = (
        "Responda APENAS com um objeto JSON válido, sem markdown e sem texto extra. "
        f"O JSON deve obedecer exatamente a este schema:\n{schema_hint}"
    )

    fallback_messages: list[BaseMessage] = [SystemMessage(content=fallback_system)]
    for msg in messages:
        if isinstance(msg, SystemMessage):
            fallback_messages.append(
                HumanMessage(content=f"[Instrução original]\n{msg.content}")
            )
        else:
            fallback_messages.append(msg)

    response = llm.invoke(fallback_messages)
    raw = response.content if hasattr(response, "content") else str(response)

    if not raw or not str(raw).strip():
        detail = "; ".join(prior_errors)
        raise RuntimeError(
            f"LLM retornou resposta vazia. Erros anteriores: {detail}"
        )

    try:
        payload = json.loads(_extract_json(str(raw)))
        return schema.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        detail = "; ".join(prior_errors)
        raise RuntimeError(
            f"Falha ao parsear JSON do LLM: {exc}. Erros anteriores: {detail}"
        ) from exc

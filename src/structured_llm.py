"""Invocação tipada de LLM com fallback para modelos sem structured output nativo."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Literal, TypeVar

import json_repair
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from src.config import get_llm, use_json_fallback_only
from src.tracing import pipeline_traceable

T = TypeVar("T", bound=BaseModel)

StructuredOutputMethod = Literal["json_mode", "function_calling", "json_schema"]

_MESSAGE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}

# Escapes válidos em JSON: \ " / b f n r t u (unicode)
_INVALID_JSON_ESCAPE = re.compile(r'\\(?!["\\/bfnrtu])')

_JSON_RULES = (
    "Regras OBRIGATÓRIAS para o JSON:\n"
    "1. Responda APENAS com JSON válido, sem markdown.\n"
    "2. Em strings com código, escape cada barra invertida como \\\\ "
    "(ex.: newline no código = \\\\n, não \\n solto fora de escape válido).\n"
    "3. Não use barras invertidas soltas (ex.: C:\\\\Users, não C:\\Users).\n"
    "4. Use aspas duplas em todas as chaves e strings."
)


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


def _fix_invalid_escapes(text: str) -> str:
    """Corrige \\ inválidos comuns em código gerado por LLM (ex.: \\S, \\U)."""
    return _INVALID_JSON_ESCAPE.sub(r"\\\\", text)


def _parse_llm_json(text: str) -> Any:
    """
    Parse robusto de JSON retornado por LLM.

    Tenta json.loads, correção de escapes e json-repair como fallback.
    """
    extracted = _extract_json(text)
    errors: list[str] = []

    for label, candidate in (
        ("json.loads", extracted),
        ("escape_fix", _fix_invalid_escapes(extracted)),
    ):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            errors.append(f"{label}: {exc}")

    try:
        repaired = json_repair.repair_json(extracted, return_objects=True)
        if isinstance(repaired, (dict, list)):
            return repaired
        if isinstance(repaired, str):
            return json.loads(repaired)
    except Exception as exc:
        errors.append(f"json_repair: {exc}")

    detail = "; ".join(errors) or "JSON inválido"
    raise json.JSONDecodeError(detail, extracted, 0)


def _validate_parsed(schema: type[T], payload: Any) -> T:
    """Valida payload parseado contra schema Pydantic."""
    return schema.model_validate(payload)


def _get_output_method() -> StructuredOutputMethod:
    """Método de structured output (json_mode funciona melhor em modelos free)."""
    method = os.getenv("STRUCTURED_OUTPUT_METHOD", "json_mode").strip().lower()
    if method in ("json_mode", "function_calling", "json_schema"):
        return method  # type: ignore[return-value]
    return "json_mode"


@pipeline_traceable("invoke_structured", run_type="llm")
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


@pipeline_traceable("json_fallback", run_type="llm")
def _invoke_json_fallback(
    schema: type[T],
    llm,
    messages: list[BaseMessage],
    prior_errors: list[str],
) -> T:
    """Fallback: prompt JSON + parse robusto + validação Pydantic."""
    schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)
    fallback_system = (
        f"{_JSON_RULES}\n\n"
        "O JSON deve obedecer exatamente a este schema:\n"
        f"{schema_hint}"
    )

    fallback_messages: list[BaseMessage] = [SystemMessage(content=fallback_system)]
    for msg in messages:
        if isinstance(msg, SystemMessage):
            fallback_messages.append(
                HumanMessage(content=f"[Instrução original]\n{msg.content}")
            )
        else:
            fallback_messages.append(msg)

    max_attempts = int(os.getenv("JSON_PARSE_RETRIES", "2"))
    parse_errors: list[str] = list(prior_errors)

    for attempt in range(max_attempts):
        response = llm.invoke(fallback_messages)
        raw = response.content if hasattr(response, "content") else str(response)

        if not raw or not str(raw).strip():
            parse_errors.append(f"tentativa {attempt + 1}: resposta vazia")
            fallback_messages.append(
                HumanMessage(
                    content="Sua resposta veio vazia. Retorne apenas JSON válido.",
                )
            )
            continue

        try:
            payload = _parse_llm_json(str(raw))
            return _validate_parsed(schema, payload)
        except json.JSONDecodeError as exc:
            parse_errors.append(f"tentativa {attempt + 1}: {exc}")
            fallback_messages.extend([
                AIMessage(content=str(raw)),
                HumanMessage(
                    content=(
                        "O JSON anterior é inválido. "
                        f"Erro: {exc}. "
                        "Reescreva o JSON completo, escapando \\\\ corretamente em strings de código."
                    ),
                ),
            ])
        except ValidationError as exc:
            parse_errors.append(f"tentativa {attempt + 1}: validação Pydantic: {exc}")
            fallback_messages.extend([
                AIMessage(content=str(raw)),
                HumanMessage(
                    content=(
                        f"O JSON não obedece ao schema. Erros: {exc}. "
                        "Corrija e retorne JSON válido completo."
                    ),
                ),
            ])

    detail = "; ".join(parse_errors)
    raise RuntimeError(f"Falha ao parsear JSON do LLM após {max_attempts} tentativas: {detail}")

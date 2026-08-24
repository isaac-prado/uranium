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
from typing import Any, Literal, TypeVar

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
def invoke_structured_raw(
    schema: type[T],
    messages: list[tuple[str, str]] | list[BaseMessage],
    *,
    temperature: float | None = None,
    llm: Any = None,
) -> tuple[T, AIMessage | None]:
    """
    Invoca o LLM e devolve (instância validada, mensagem bruta).

    A mensagem bruta é indispensável: sem ela não há como extrair tokens,
    custo e provedor servido, e a chamada ficaria invisível na telemetria.
    Quatro dos cinco nós do braço B passam por aqui — se não fossem
    contabilizados, o custo do braço multiagente sairia subestimado
    exatamente contra o braço de comparação.

    `llm` é injetável para permitir execução offline em teste.
    """
    cliente = llm if llm is not None else get_llm(temperature=temperature)
    estruturado = cliente.with_structured_output(
        schema, method=get_output_method(), include_raw=True
    )
    lc_messages = _to_messages(messages)

    tentativas = max_retries() + 1
    erros: list[str] = []

    for tentativa in range(1, tentativas + 1):
        try:
            saida = estruturado.invoke(lc_messages)
        except Exception as exc:
            erros.append(f"tentativa {tentativa}: {type(exc).__name__}: {exc}")
            continue

        parsed, bruta, falha = _desempacotar(saida)
        if falha is not None:
            erros.append(f"tentativa {tentativa}: {falha}")
            continue
        if parsed is not None:
            return parsed, bruta
        erros.append(f"tentativa {tentativa}: resposta vazia (choices=None)")

    raise StructuredOutputError(
        f"{schema.__name__}: modelo não conformou ao schema em {tentativas} tentativas. "
        + "; ".join(erros)
    )


def _desempacotar(saida: Any) -> tuple[Any, AIMessage | None, str | None]:
    """
    Normaliza o retorno de `with_structured_output`.

    Com `include_raw=True` vem um dict {raw, parsed, parsing_error}; sem ele,
    vem o objeto direto. Aceitamos os dois para não quebrar quando um teste
    fizer mock da forma simples.
    """
    if isinstance(saida, dict):
        erro = saida.get("parsing_error")
        return saida.get("parsed"), saida.get("raw"), (str(erro) if erro else None)
    return saida, None, None


def invoke_structured(
    schema: type[T],
    messages: list[tuple[str, str]] | list[BaseMessage],
    *,
    temperature: float | None = None,
    llm: Any = None,
) -> T:
    """
    Invoca o LLM e devolve uma instância validada do schema.

    Retenta apenas a mesma chamada, para falha transitória. Não reformula o
    prompt nem repara a saída: qualquer não-conformidade é do modelo, e é
    assim que precisa ser medida.

    Prefira `RunContext.invoke_structured`, que instrumenta a chamada.
    """
    resultado, _ = invoke_structured_raw(
        schema, messages, temperature=temperature, llm=llm
    )
    return resultado

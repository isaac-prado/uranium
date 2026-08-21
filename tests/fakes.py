"""LLM de sequência gravada, para exercitar o grafo inteiro sem rede."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage


def ai(content: str = "", tool_calls: list[dict] | None = None, **usage: Any) -> AIMessage:
    """
    Constrói uma AIMessage com o mesmo formato de metadata do OpenRouter.

    Assim os nós extraem tokens, custo e provedor exatamente como fariam em
    produção — a telemetria é exercitada de verdade.
    """
    chamadas = []
    for i, chamada in enumerate(tool_calls or []):
        chamadas.append({
            "name": chamada["name"],
            "args": chamada.get("args", {}),
            "id": chamada.get("id", f"call_{i}"),
            "type": "tool_call",
        })

    prompt_tokens = usage.get("prompt_tokens", 100)
    completion_tokens = usage.get("completion_tokens", 20)

    return AIMessage(
        content=content,
        tool_calls=chamadas,
        response_metadata={
            "model_name": "fake/modelo",
            "provider": usage.get("provider", "FakeProvider"),
            "id": usage.get("id", "gen-fake"),
            "finish_reason": "tool_calls" if chamadas else "stop",
            "token_usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost": usage.get("cost", 0.001),
                "completion_tokens_details": {"reasoning_tokens": 0},
            },
        },
    )


class FakeToolCallingLLM:
    """
    Reproduz uma sequência gravada de respostas.

    Implementa só o que o Developer usa: bind_tools() e invoke(). Quando a
    sequência acaba, repete a última resposta — que por convenção é uma
    resposta em texto, encerrando o loop.
    """

    def __init__(self, respostas: list[AIMessage]) -> None:
        if not respostas:
            raise ValueError("a sequência precisa de ao menos uma resposta")
        self.respostas = respostas
        self.chamadas: list[list] = []
        self.ferramentas_ligadas: list | None = None

    def bind_tools(self, tools: list, **kwargs: Any) -> "FakeToolCallingLLM":
        self.ferramentas_ligadas = tools
        return self

    def invoke(self, mensagens: list, **kwargs: Any) -> AIMessage:
        indice = min(len(self.chamadas), len(self.respostas) - 1)
        self.chamadas.append(list(mensagens))
        return self.respostas[indice]

    @property
    def n_invocacoes(self) -> int:
        return len(self.chamadas)

    def factory(self, *args: Any, **kwargs: Any) -> "FakeToolCallingLLM":
        """Compatível com a assinatura de `llm_factory` do RunContext."""
        return self

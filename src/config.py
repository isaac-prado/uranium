"""
Configuração do LLM com provedor pinado, e constantes do workflow.

Os dois braços do estudo (A2 e B) compartilham exatamente esta configuração.
A única variável que pode diferir entre eles é a topologia de orquestração,
então tudo aqui é resolvido uma vez e serializado no manifesto do run para
que o teste de paridade possa comparar os dois lados.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, replace
from typing import Any

from dotenv import load_dotenv
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI

load_dotenv()

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

MAX_CLARIFICATION_ITERATIONS = int(os.getenv("MAX_CLARIFICATION_ITERATIONS", "3"))
MAX_VALIDATION_ITERATIONS = int(os.getenv("MAX_VALIDATION_ITERATIONS", "2"))
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT") or "uranium"


class ConfigError(RuntimeError):
    """Configuração ausente ou inválida para um run do benchmark."""


# --------------------------------------------------------------------- config


@dataclass(frozen=True)
class LLMConfig:
    """Configuração resolvida do LLM. Idêntica nos braços A2 e B."""

    model: str
    provider: str
    temperature: float = 0.0
    seed: int = 0
    max_tokens: int = 8192
    timeout_s: int = 300
    allow_fallbacks: bool = False
    require_parameters: bool = True
    data_collection: str = "deny"

    def provider_routing(self) -> dict[str, Any]:
        """
        Roteamento do OpenRouter que fixa o provedor.

        Com `only` + `allow_fallbacks: false`, se o provedor pinado não puder
        atender o OpenRouter devolve erro em vez de servir por outro. O pino
        é auto-verificável: não há como o run trocar de provedor silenciosamente.
        """
        return {
            "only": [self.provider],
            "allow_fallbacks": self.allow_fallbacks,
            "require_parameters": self.require_parameters,
            "data_collection": self.data_collection,
        }

    def as_manifest(self) -> dict[str, Any]:
        """Forma serializável, usada no manifesto do run e no teste de paridade."""
        return asdict(self)


def _require(name: str, hint: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise ConfigError(f"{name} não configurado. {hint}")
    return value


def load_llm_config(**overrides: Any) -> LLMConfig:
    """
    Resolve a configuração do LLM a partir do ambiente.

    Falha alto e cedo: modelo de tier gratuito é recusado porque não permite
    pinar provedor nem garantir parâmetros, o que inviabilizaria a comparação.
    """
    model = _require(
        "OPENROUTER_MODEL_NAME",
        "Defina o modelo escolhido no teste de aptidão (ex.: 'vendor/model').",
    )
    provider = _require(
        "OPENROUTER_PROVIDER",
        "Defina o provedor único a pinar (ex.: 'Fireworks'). "
        "Descubra os disponíveis com: scripts/fitness_test.py --list-providers <modelo>",
    )

    config = LLMConfig(
        model=model,
        provider=provider,
        temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
        seed=int(os.getenv("LLM_SEED", "0")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8192")),
        timeout_s=int(os.getenv("LLM_REQUEST_TIMEOUT", "300")),
    )
    if overrides:
        config = replace(config, **overrides)

    _validate(config)
    return config


def _validate(config: LLMConfig) -> None:
    name = config.model.strip().lower()
    if name.endswith(":free") or name == "openrouter/free":
        raise ConfigError(
            f"Modelo de tier gratuito recusado: {config.model!r}. "
            "Os braços A2/B exigem modelo pago com provedor pinado — sem isso "
            "não há como garantir que os dois braços foram servidos igual."
        )
    if config.allow_fallbacks:
        raise ConfigError("allow_fallbacks deve ser False: fallback troca o provedor no meio do run.")
    if not config.require_parameters:
        raise ConfigError(
            "require_parameters deve ser True: sem isso o provedor pode ignorar "
            "temperature/seed e o run deixa de ser reprodutível."
        )


# ----------------------------------------------------------------- cliente LLM


class OpenRouterChat(ChatOpenAI):
    """
    ChatOpenAI que preserva os campos extras do OpenRouter.

    O `_create_chat_result` do LangChain monta `llm_output` a partir de uma
    allowlist fixa e descarta o campo `provider` do corpo da resposta — que é
    justamente o dado que comprova qual provedor atendeu. Verificado contra
    langchain-openai 1.2.1; `tests/test_config.py` falha se o gancho quebrar.
    """

    _EXTRA_FIELDS = ("provider",)

    def _create_chat_result(
        self,
        response: Any,
        generation_info: dict | None = None,
    ) -> ChatResult:
        result = super()._create_chat_result(response, generation_info)

        raw = response if isinstance(response, dict) else _safe_dump(response)
        for key in self._EXTRA_FIELDS:
            if raw.get(key) is None:
                continue
            result.llm_output = {**(result.llm_output or {}), key: raw[key]}
            for generation in result.generations:
                generation.message.response_metadata[key] = raw[key]

        return result


def _safe_dump(response: Any) -> dict[str, Any]:
    try:
        return response.model_dump()
    except Exception:
        return {}


def get_llm(config: LLMConfig | None = None, *, temperature: float | None = None) -> OpenRouterChat:
    """Cliente LLM apontando para o OpenRouter, com provedor pinado."""
    config = config or load_llm_config()
    if temperature is not None:
        config = replace(config, temperature=temperature)
        _validate(config)

    api_key = _require(
        "OPENROUTER_API_KEY", "Chave da API do OpenRouter é obrigatória."
    )

    return OpenRouterChat(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout_s,
        api_key=api_key,
        base_url=os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
        # seed no corpo da requisição; `usage.include` faz o OpenRouter
        # devolver contagem nativa de tokens e custo em USD.
        extra_body={
            "provider": config.provider_routing(),
            "seed": config.seed,
            "usage": {"include": True},
        },
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/isaac-prado/uranium"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "Uranium"),
        },
    )


# ------------------------------------------------------------------- métricas


@dataclass(frozen=True)
class LLMCallMetrics:
    """Custo e atribuição de uma chamada, extraídos da resposta do OpenRouter."""

    model: str | None = None
    provider_served: str | None = None
    generation_id: str | None = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_reasoning: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    finish_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_call_metrics(message: Any) -> LLMCallMetrics:
    """
    Lê tokens, custo e provedor servido de uma AIMessage.

    Tolerante a ausência: se o provedor não devolver `usage` detalhado, os
    campos ficam zerados em vez de derrubar o run.
    """
    meta: dict[str, Any] = getattr(message, "response_metadata", None) or {}
    usage: dict[str, Any] = meta.get("token_usage") or {}
    completion_details = usage.get("completion_tokens_details") or {}

    return LLMCallMetrics(
        model=meta.get("model_name"),
        provider_served=meta.get("provider"),
        generation_id=meta.get("id"),
        tokens_prompt=int(usage.get("prompt_tokens") or 0),
        tokens_completion=int(usage.get("completion_tokens") or 0),
        tokens_reasoning=int(completion_details.get("reasoning_tokens") or 0),
        tokens_total=int(usage.get("total_tokens") or 0),
        cost_usd=float(usage.get("cost") or 0.0),
        finish_reason=meta.get("finish_reason"),
    )


# ------------------------------------------------------------------- tracing


def get_run_config(*, run_name: str | None = None, tags: list[str] | None = None) -> dict:
    """Configuração de execução para tracing (LangSmith), quando habilitado."""
    config: dict = {
        "configurable": {},
        "metadata": {"project": LANGSMITH_PROJECT, "pipeline": "uranium"},
        "tags": ["uranium", LANGSMITH_PROJECT],
    }
    if run_name:
        config["run_name"] = run_name
    if tags:
        config["tags"] = config["tags"] + tags
    return config

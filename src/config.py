"""Configuração centralizada de LLM, LangSmith e constantes do workflow."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.free_models import DEFAULT_FREE_MODEL, is_free_model

load_dotenv()

MAX_CLARIFICATION_ITERATIONS = int(os.getenv("MAX_CLARIFICATION_ITERATIONS", "3"))
MAX_VALIDATION_ITERATIONS = int(os.getenv("MAX_VALIDATION_ITERATIONS", "2"))
LANGSMITH_PROJECT = (
    os.getenv("LANGSMITH_PROJECT")
    or os.getenv("LANGCHAIN_PROJECT")
    or "uranium-poc"
)
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "180"))


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes")


def _get_model_name() -> str:
    """Resolve o nome do modelo (padrão: tier free do OpenRouter)."""
    return (
        os.getenv("OPENROUTER_MODEL_NAME")
        or os.getenv("MODEL_NAME")
        or DEFAULT_FREE_MODEL
    )


def use_json_fallback_only() -> bool:
    """
    Pula structured output nativo e usa só prompt JSON.

    Ativado por USE_JSON_FALLBACK_ONLY=true ou automaticamente para modelos :free.
    """
    if _env_bool("USE_JSON_FALLBACK_ONLY"):
        return True
    if _env_bool("AUTO_JSON_FALLBACK_FOR_FREE", default=True):
        return is_free_model(_get_model_name())
    return False


def get_llm(*, temperature: float = 0) -> ChatOpenAI:
    """
    Retorna ChatOpenAI apontando para OpenRouter.

    Modelos free: use IDs com sufixo :free (custo $0).
    """
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()

    if base_url and not base_url.startswith(("http://", "https://")):
        base_url = "https://openrouter.ai/api/v1"

    kwargs: dict = {
        "model": _get_model_name(),
        "temperature": temperature,
        "max_tokens": LLM_MAX_TOKENS,
        "timeout": LLM_REQUEST_TIMEOUT,
    }

    if api_key:
        kwargs["api_key"] = api_key
    if os.getenv("OPENROUTER_API_KEY"):
        kwargs["base_url"] = base_url
        kwargs["default_headers"] = {
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/uranium-poc"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "Uranium"),
        }

    return ChatOpenAI(**kwargs)


def get_structured_llm(schema: type, *, temperature: float = 0, method: str | None = None):
    """
    Retorna um LLM com saída estruturada.

    Prefira invoke_structured() em src/structured_llm.py (fallback automático).
    """
    output_method = method or os.getenv("STRUCTURED_OUTPUT_METHOD", "json_mode")
    return get_llm(temperature=temperature).with_structured_output(
        schema, method=output_method
    )


def get_run_config(*, run_name: str | None = None, tags: list[str] | None = None) -> dict:
    """Configuração de execução para LangSmith tracing."""
    config: dict = {
        "configurable": {},
        "metadata": {
            "project": LANGSMITH_PROJECT,
            "pipeline": "uranium",
            "model": _get_model_name(),
            "free_tier": is_free_model(_get_model_name()),
        },
        "tags": ["uranium", LANGSMITH_PROJECT],
    }

    if run_name:
        config["run_name"] = run_name
    if tags:
        config["tags"] = config.get("tags", []) + tags

    return config

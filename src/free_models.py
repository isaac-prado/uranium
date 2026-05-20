"""Modelos 100% gratuitos no OpenRouter (sufixo :free, custo $0)."""

from typing import TypedDict


class FreeModelInfo(TypedDict):
    """Metadados de um modelo free recomendado."""

    id: str
    speed: str
    quality: str
    note: str


FREE_MODELS: list[FreeModelInfo] = [
    {
        "id": "qwen/qwen-2.5-7b-instruct:free",
        "speed": "rápido",
        "quality": "boa",
        "note": "Recomendado para a POC — equilíbrio velocidade/qualidade",
    },
    {
        "id": "google/gemma-2-9b-it:free",
        "speed": "rápido",
        "quality": "média",
        "note": "Leve; bom para testes rápidos",
    },
    {
        "id": "meta-llama/llama-3.2-3b-instruct:free",
        "speed": "muito rápido",
        "quality": "básica",
        "note": "Menor modelo free; respostas mais simples",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "speed": "médio",
        "quality": "alta",
        "note": "Melhor qualidade free; mais lento que 7B",
    },
    {
        "id": "qwen/qwen-2.5-72b-instruct:free",
        "speed": "lento",
        "quality": "alta",
        "note": "72B free; use se 7B não for suficiente",
    },
    {
        "id": "nvidia/nemotron-3-super-120b-a12b:free",
        "speed": "muito lento",
        "quality": "alta",
        "note": "120B — evite na POC; filas longas no tier free",
    },
    {
        "id": "openrouter/free",
        "speed": "variável",
        "quality": "variável",
        "note": "Roteador automático do OpenRouter entre modelos free",
    },
]

DEFAULT_FREE_MODEL = FREE_MODELS[0]["id"]


def is_free_model(model_name: str) -> bool:
    """Indica se o modelo é do tier gratuito OpenRouter."""
    name = model_name.strip().lower()
    return name.endswith(":free") or name == "openrouter/free"

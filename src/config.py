"""
Configuração do LLM com provedor pinado, e constantes do workflow.

Os dois braços do estudo compartilham exatamente esta configuração.
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

# Desliga qualquer tracing remoto de forma incondicional.
#
# A telemetria do estudo é o JSONL local (src/telemetry.py). O `langsmith`
# continua instalado como dependência transitiva do langchain-core, e basta
# uma destas variáveis vazar do ambiente para o LangChain começar a enviar
# spans pela rede no meio de uma coleta. Isso adicionaria latência variável
# e um ponto de falha externo ao caminho de medição, então é desligado aqui
# e não por configuração.
for _var in (
    "LANGSMITH_TRACING",
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_TRACING",
    "LANGSMITH_OTEL_ENABLED",
):
    os.environ[_var] = "false"

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

MAX_CLARIFICATION_ITERATIONS = int(os.getenv("MAX_CLARIFICATION_ITERATIONS", "3"))
# Reprovações da revisão semântica (suíte verde, revisor diz que não resolve)
# antes de o orchestration desistir. Só esse caso tem teto: suíte vermelha e
# diff vazio voltam ao developer até o orçamento acabar, como o driver do
# single-agent faz. Um teto ali daria a um braço menos chances de corrigir que
# ao outro, e a diferença não viria da topologia.
MAX_SEMANTIC_REJECTIONS = int(os.getenv("MAX_SEMANTIC_REJECTIONS", "2"))
# 0 = sem teto (decisão 32, 14/10/2026, rodada 3): a parada passa a ser só
# "suíte verde ou orçamento", igual ao single-agent. Na rodada 2 o attrs-0001
# rep3 encerrou no turno 24 com 2/3 do oráculo e 96 turnos sobrando.
if MAX_SEMANTIC_REJECTIONS < 0:
    raise ValueError("MAX_SEMANTIC_REJECTIONS deve ser >= 0 (0 = sem teto)")
# Memória de trabalho do developer do orchestration entre os ciclos de
# validação (decisão 8 do autor, revista em 09/10/2026). "ledger": a cada
# reentrada no nó o developer recebe o registro determinístico dos ciclos
# anteriores (o que leu, buscou, escreveu e executou, a nota com que
# encerrou) e o diff atual do workspace, montados pela orquestração sem
# chamada extra ao modelo. "none": o comportamento de 19/09, conversa
# reconstruída do zero a cada ciclo (fumaças A a F rodaram assim).
# Teto de turnos por ciclo do developer do orchestration (decisão 25 do
# autor, 09/10/2026). Ao atingi-lo, o developer é devolvido ao validador,
# que roda a suíte e a revisão e lhe devolve o veredito junto com a memória
# de trabalho; o run segue até o orçamento total. 0 desliga (fumaças A a G:
# o developer só voltava ao validador quando ele mesmo decidia encerrar).
DEVELOPER_CYCLE_MAX_TURNS = int(os.getenv("DEVELOPER_CYCLE_MAX_TURNS", "40"))
if DEVELOPER_CYCLE_MAX_TURNS < 0:
    raise ValueError("DEVELOPER_CYCLE_MAX_TURNS não pode ser negativo (0 desliga)")
# O que o developer do orchestration recebe como primeira mensagem (ablação
# do refinador, decisões 7 e 16, 14/10/2026). "intent": só a intent do
# `intent_refiner` (o protótipo do TFG; valor da coleta principal). "enunciado+intent":
# o enunciado íntegro, a mesma string que o single-agent recebe, mais a intent
# como anexo. Só o braço de ablação usa o segundo; vai ao manifesto em
# `orchestration_policy.developer_input`.
# Versão do refinador de intent (decisão 28 do autor, 14/10/2026, aprovada
# por escrito: "quero que ele enriqueça, compreenda e facilite"). "v1": o
# prompt do TFG, que resume (coleta principal). "v2": enriquece — copia
# literalmente reprodução, saídas esperadas e restrições do ambiente, com
# critérios verificáveis (src/agents/intent_refiner.py, SYSTEM_PROMPT_V2).
INTENT_REFINER_VERSIONS = ("v1", "v2")
INTENT_REFINER = os.getenv("INTENT_REFINER", "v1").strip().lower()
if INTENT_REFINER not in INTENT_REFINER_VERSIONS:
    raise ValueError(f"INTENT_REFINER={INTENT_REFINER!r} inválido; use um de {INTENT_REFINER_VERSIONS}")
# Revisor que executa (decisão 29, 14/10/2026): com "on", o validador roda
# os blocos de `reproduction` da intent v2 no código atual e entrega as
# saídas reais ao revisor, ao lado das esperadas, antes do veredito. "off":
# o revisor só lê o diff (coleta principal).
# "cumulative" (decisão 34, 15/10/2026): o bloco i roda precedido dos blocos
# 1..i-1 no mesmo namespace, porque os enunciados encadeiam blocos (o
# segundo usa o `db` ou o import do primeiro) e, isolados, 26 % quebravam.
REVIEW_EXECUTION_MODES = ("on", "off", "cumulative")
REVIEW_EXECUTION = os.getenv("REVIEW_EXECUTION", "off").strip().lower()
if REVIEW_EXECUTION not in REVIEW_EXECUTION_MODES:
    raise ValueError(f"REVIEW_EXECUTION={REVIEW_EXECUTION!r} inválido; use um de {REVIEW_EXECUTION_MODES}")
# Nota de ciclo (decisão 29): com "on", ao bater o teto do ciclo o developer
# escreve, numa chamada sem ferramentas, o que fez, por que e o que falta; a
# nota entra na memória de trabalho. "off": a memória leva só o registro.
CYCLE_NOTE_MODES = ("on", "off")
CYCLE_NOTE = os.getenv("CYCLE_NOTE", "off").strip().lower()
if CYCLE_NOTE not in CYCLE_NOTE_MODES:
    raise ValueError(f"CYCLE_NOTE={CYCLE_NOTE!r} inválido; use um de {CYCLE_NOTE_MODES}")
# Revisor coerente (decisão 32, rodada 3): com "on", uma revisão que lista
# `missing_criteria` não pode aprovar; o harness rebaixa `is_valid` para
# False e registra `strict_coerced` no evento `validation`. Na rodada 2, 4
# das 59 revisões aprovaram com critérios faltando e duas encerraram runs
# com 11/12 e 5/6 no oráculo. "off": o veredito do revisor vale como veio.
REVIEW_STRICT_MODES = ("on", "off")
REVIEW_STRICT = os.getenv("REVIEW_STRICT", "off").strip().lower()
if REVIEW_STRICT not in REVIEW_STRICT_MODES:
    raise ValueError(f"REVIEW_STRICT={REVIEW_STRICT!r} inválido; use um de {REVIEW_STRICT_MODES}")
# Planejador (decisão 33, 15/10/2026, rodada 4): com "on", um nó planejador
# explora o repositório com ferramentas de leitura e fatia a intent em
# sub-tarefas; o developer ataca uma por ciclo e o validador confere cada
# uma com os blocos de reprodução dela. "off" reproduz a rodada 2.
PLANNER_MODES = ("on", "off")
PLANNER = os.getenv("PLANNER", "off").strip().lower()
if PLANNER not in PLANNER_MODES:
    raise ValueError(f"PLANNER={PLANNER!r} inválido; use um de {PLANNER_MODES}")
# Turnos de exploração (só leitura) do planejador, contados no orçamento.
PLANNER_MAX_TURNS = int(os.getenv("PLANNER_MAX_TURNS", "12"))
# Quantas vezes o planejador pode ser chamado de novo quando o plano acabou
# e a tarefa ainda não fechou.
PLANNER_MAX_REPLANS = int(os.getenv("PLANNER_MAX_REPLANS", "1"))
# Ciclos do developer numa sub-tarefa antes de ela ser adiada.
SUBTASK_MAX_CYCLES = int(os.getenv("SUBTASK_MAX_CYCLES", "2"))
# Tamanho máximo do plano.
PLANNER_MAX_SUBTASKS = int(os.getenv("PLANNER_MAX_SUBTASKS", "6"))
DEVELOPER_INPUT_MODES = ("intent", "enunciado+intent")
DEVELOPER_INPUT = os.getenv("DEVELOPER_INPUT", "intent").strip().lower()
if DEVELOPER_INPUT not in DEVELOPER_INPUT_MODES:
    raise ValueError(f"DEVELOPER_INPUT={DEVELOPER_INPUT!r} inválido; use um de {DEVELOPER_INPUT_MODES}")
DEVELOPER_MEMORY_MODES = ("ledger", "none")
DEVELOPER_MEMORY = os.getenv("DEVELOPER_MEMORY", "ledger").strip().lower()
if DEVELOPER_MEMORY not in DEVELOPER_MEMORY_MODES:
    raise ValueError(
        f"DEVELOPER_MEMORY={DEVELOPER_MEMORY!r} inválido; use um de {DEVELOPER_MEMORY_MODES}"
    )


class ConfigError(RuntimeError):
    """Configuração ausente ou inválida para um run do benchmark."""


class ProviderError(RuntimeError):
    """
    A chamada não chegou a ser respondida pelo modelo: falha de infraestrutura.

    Existe para separar dois fracassos que antes caíam no mesmo balde. Um 429
    do provedor ou uma chave revogada não dizem nada sobre a capacidade do
    modelo nem da topologia. Contá-los como "modelo não conformou ao schema"
    atribuía ao braço orchestration, e só a ele, uma incapacidade que não
    existiu. Run que termina com este erro está perdido, não fracassado: sai do
    denominador e é reexecutado.
    """


# Status HTTP que significam "a infraestrutura não atendeu". 400, 404 e 422
# ficam de fora de propósito: são respostas a uma requisição que o próprio run
# montou (contexto grande demais, parâmetro recusado) e fazem parte do que se
# mede.
_STATUS_DE_INFRA = frozenset({401, 402, 403, 408, 409, 429})


def is_provider_error(exc: BaseException) -> bool:
    """Diz se a exceção é falha de infraestrutura, e não do modelo ou do run."""
    import httpx
    import openai

    if isinstance(exc, ProviderError):
        return True
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code in _STATUS_DE_INFRA or exc.status_code >= 500
    return isinstance(
        exc, (openai.APIConnectionError, httpx.TransportError, TimeoutError, ConnectionError)
    )


# Falha de provedor que não passa esperando: chave revogada (401) ou crédito
# esgotado (402). Reexecutar só queima o resto da coleta em tentativas
# perdidas — em 28/09 uma chave revogada teria levado todas as células a
# `lost`, 3 tentativas cada, com 60s de espera entre elas.
_STATUS_FATAL = frozenset({401, 402})


def root_provider_error(exc: BaseException) -> BaseException:
    """A exceção do cliente por baixo de um `ProviderError`, se houver."""
    while isinstance(exc, ProviderError) and exc.__cause__ is not None:
        exc = exc.__cause__
    return exc


def is_fatal_provider_error(exc: BaseException) -> bool:
    """Falha de provedor que nenhuma reexecução resolve: a coleta deve parar."""
    import openai

    raiz = root_provider_error(exc)
    return isinstance(raiz, openai.APIStatusError) and raiz.status_code in _STATUS_FATAL


# --------------------------------------------------------------------- config


@dataclass(frozen=True)
class LLMConfig:
    """Configuração resolvida do LLM. Idêntica nos braços single-agent e orchestration."""

    model: str
    provider: str
    temperature: float = 0.0
    seed: int = 0
    max_tokens: int = 8192
    timeout_s: int = 90
    # Tentativas por chamada diante de erro transitório do provedor. Vai para
    # o manifesto porque é parâmetro do experimento, não detalhe de cliente:
    # se um braço tolerasse mais falha de infraestrutura que o outro, a
    # comparação mediria a sorte de cada um com o provedor. Um 429
    # `engine_overloaded` do pool compartilhado matou um run inteiro no
    # piloto com o padrão do LangChain, que é 2.
    max_retries: int = 6
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


_HINTS = {
    "model": (
        "OPENROUTER_MODEL_NAME não configurado. Defina o modelo escolhido no "
        "teste de aptidão (ex.: 'vendor/model'), ou passe --model."
    ),
    "provider": (
        "OPENROUTER_PROVIDER não configurado. Defina o provedor único a pinar, "
        "ou passe --provider. Veja os disponíveis com: "
        "scripts/fitness_test.py --list-providers <modelo>"
    ),
}


def load_llm_config(**overrides: Any) -> LLMConfig:
    """
    Resolve a configuração do LLM a partir do ambiente.

    Os overrides são aplicados ANTES da checagem de obrigatoriedade: é o que
    permite ao teste de aptidão varrer candidatos com --model/--provider sem
    editar o .env.

    Falha alto e cedo: modelo de tier gratuito é recusado porque não permite
    pinar provedor nem garantir parâmetros, o que inviabilizaria a comparação.
    """
    config = LLMConfig(
        model=(os.getenv("OPENROUTER_MODEL_NAME") or "").strip(),
        provider=(os.getenv("OPENROUTER_PROVIDER") or "").strip(),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
        seed=int(os.getenv("LLM_SEED", "0")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8192")),
        timeout_s=int(os.getenv("LLM_REQUEST_TIMEOUT", "90")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "6")),
    )
    if overrides:
        config = replace(config, **overrides)

    for campo, hint in _HINTS.items():
        if not getattr(config, campo).strip():
            raise ConfigError(hint)

    _validate(config)
    return config


def _validate(config: LLMConfig) -> None:
    name = config.model.strip().lower()
    if name.endswith(":free") or name == "openrouter/free":
        raise ConfigError(
            f"Modelo de tier gratuito recusado: {config.model!r}. "
            "O estudo exige modelo pago com provedor pinado — sem isso "
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

    def _get_request_payload(self, input_: Any, *, stop: Any = None, **kwargs: Any) -> dict:
        """
        Reverte `max_completion_tokens` para `max_tokens`.

        O ChatOpenAI traduz um no outro incondicionalmente (deprecação do lado
        da OpenAI, set/2024). Fora da OpenAI quase nenhum provedor implementa
        `max_completion_tokens`: dos 5 endpoints de qwen/qwen3-coder, zero
        suportam. Combinado com `require_parameters: true`, isso faz o
        OpenRouter recusar TODOS os endpoints com 404 "No endpoints found that
        can handle the requested parameters" — sintoma que não menciona o
        parâmetro culpado e custa horas para diagnosticar.
        """
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        if "max_completion_tokens" in payload:
            payload["max_tokens"] = payload.pop("max_completion_tokens")

        # `with_structured_output` acrescenta parallel_tool_calls=false. É outro
        # parâmetro que quase nenhum provedor fora da OpenAI implementa, e com
        # `require_parameters: true` ele derruba o endpoint inteiro com o mesmo
        # 404 genérico. Não precisamos dele: o loop do agente já trata várias
        # tool calls por turno, e a saída estruturada força a função por
        # `tool_choice`. Descoberto no piloto: o braço orchestration falhava 100% das vezes
        # enquanto o single-agent, que usa bind_tools (sem esse parâmetro), rodava.
        payload.pop("parallel_tool_calls", None)
        return payload

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
        max_retries=config.max_retries,
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
    # Custo TOTAL pago pela chamada, em dólares: o que o OpenRouter cobra
    # (`usage.cost`) mais, quando a chamada saiu pela chave própria do
    # provedor (BYOK), o que o provedor cobrou
    # (`usage.cost_details.upstream_inference_cost`). Sem BYOK, `usage.cost`
    # já é o preço inteiro e o upstream é só informativo — somar os dois
    # contaria duas vezes. Confirmado em 09/10/2026 numa chamada pinada no
    # DeepInfra com chave própria: `cost: 0, is_byok: true,
    # upstream_inference_cost: 6.2e-06` (docs/tcc/09-decisoes-do-autor.md,
    # decisão 11).
    cost_usd: float = 0.0
    cost_openrouter_usd: float = 0.0
    cost_upstream_usd: float = 0.0
    # None quando a resposta não diz; True quando saiu pela chave própria.
    is_byok: bool | None = None
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
    cost_details = usage.get("cost_details") or {}
    is_byok = usage.get("is_byok")
    cost_openrouter = float(usage.get("cost") or 0.0)
    cost_upstream = float(cost_details.get("upstream_inference_cost") or 0.0)

    return LLMCallMetrics(
        model=meta.get("model_name"),
        provider_served=meta.get("provider"),
        generation_id=meta.get("id"),
        tokens_prompt=int(usage.get("prompt_tokens") or 0),
        tokens_completion=int(usage.get("completion_tokens") or 0),
        tokens_reasoning=int(completion_details.get("reasoning_tokens") or 0),
        tokens_total=int(usage.get("total_tokens") or 0),
        cost_usd=cost_openrouter + (cost_upstream if is_byok else 0.0),
        cost_openrouter_usd=cost_openrouter,
        cost_upstream_usd=cost_upstream,
        is_byok=bool(is_byok) if is_byok is not None else None,
        finish_reason=meta.get("finish_reason"),
    )

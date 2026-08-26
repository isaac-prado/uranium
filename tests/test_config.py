"""Testes da configuração de LLM: pino de provedor, determinismo e métricas."""

from __future__ import annotations

import json

import pytest

from src.config import (
    ConfigError,
    LLMCallMetrics,
    LLMConfig,
    OpenRouterChat,
    extract_call_metrics,
    get_llm,
    load_llm_config,
)

# Forma real devolvida pelo OpenRouter com `usage: {include: true}`,
# capturada de uma chamada verdadeira. Se o formato mudar, estes testes
# quebram antes de a coleta do TCC ser contaminada.
RESPOSTA_OPENROUTER = {
    "id": "gen-1787271323-hjKT4aArKSUiL8BZ1fgw",
    "object": "chat.completion",
    "created": 1787271323,
    "model": "vendor/modelo",
    "provider": "AtlasCloud",
    "system_fingerprint": "fp_x",
    "choices": [
        {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "ok"}}
    ],
    "usage": {
        "prompt_tokens": 14,
        "completion_tokens": 10,
        "total_tokens": 24,
        "cost": 0.000123,
        "completion_tokens_details": {"reasoning_tokens": 8},
    },
}


@pytest.fixture
def config() -> LLMConfig:
    return LLMConfig(model="vendor/modelo", provider="Fireworks", seed=20260820)


def mensagem_como_em_producao(resposta: dict):
    """
    Constrói a AIMessage como o agente a recebe em produção.

    `_create_chat_result` devolve llm_output e response_metadata em níveis
    separados; quem os funde é `_generate_with_cache` do langchain_core, que
    só roda no caminho de invoke(). Reproduzir a fusão aqui mantém o teste
    fiel ao que extract_call_metrics realmente vê.
    """
    llm = OpenRouterChat(model="vendor/modelo", api_key="sk-teste")
    result = llm._create_chat_result(resposta)
    generation = result.generations[0]
    generation.message.response_metadata = {
        **(result.llm_output or {}),
        **(generation.generation_info or {}),
        **generation.message.response_metadata,
    }
    return generation.message


# ------------------------------------------------------------ pino de provedor


class TestProviderRouting:
    def test_pina_provedor_unico_sem_fallback(self, config):
        routing = config.provider_routing()
        assert routing == {
            "only": ["Fireworks"],
            "allow_fallbacks": False,
            "require_parameters": True,
            "data_collection": "deny",
        }

    def test_manifesto_e_serializavel(self, config):
        """O manifesto vai para o JSON do run e para o teste de paridade."""
        manifesto = config.as_manifest()
        assert json.loads(json.dumps(manifesto)) == manifesto
        assert manifesto["seed"] == 20260820


# --------------------------------------------------------------- fail-fast


class TestValidacao:
    def test_exige_modelo(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_PROVIDER", "Fireworks")
        with pytest.raises(ConfigError, match="OPENROUTER_MODEL_NAME"):
            load_llm_config()

    def test_exige_provedor(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_MODEL_NAME", "vendor/modelo")
        with pytest.raises(ConfigError, match="OPENROUTER_PROVIDER"):
            load_llm_config()

    @pytest.mark.parametrize("modelo", [
        "qwen/qwen-2.5-7b-instruct:free",
        "poolside/laguna-m.1:free",
        "openrouter/free",
    ])
    def test_recusa_tier_gratuito(self, monkeypatch, modelo):
        """Modelo :free não permite pinar provedor — inviabiliza a comparação."""
        monkeypatch.setenv("OPENROUTER_MODEL_NAME", modelo)
        monkeypatch.setenv("OPENROUTER_PROVIDER", "Fireworks")
        with pytest.raises(ConfigError, match="tier gratuito"):
            load_llm_config()

    def test_recusa_allow_fallbacks(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_MODEL_NAME", "vendor/modelo")
        monkeypatch.setenv("OPENROUTER_PROVIDER", "Fireworks")
        with pytest.raises(ConfigError, match="allow_fallbacks"):
            load_llm_config(allow_fallbacks=True)

    def test_recusa_require_parameters_falso(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_MODEL_NAME", "vendor/modelo")
        monkeypatch.setenv("OPENROUTER_PROVIDER", "Fireworks")
        with pytest.raises(ConfigError, match="require_parameters"):
            load_llm_config(require_parameters=False)

    def test_le_do_ambiente(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_MODEL_NAME", "vendor/modelo")
        monkeypatch.setenv("OPENROUTER_PROVIDER", "Fireworks")
        monkeypatch.setenv("LLM_SEED", "123")
        monkeypatch.setenv("LLM_MAX_TOKENS", "4096")
        cfg = load_llm_config()
        assert (cfg.seed, cfg.max_tokens, cfg.temperature) == (123, 4096, 0.0)


# ------------------------------------------------------------ cliente montado


class TestClienteLLM:
    def test_extra_body_carrega_pino_seed_e_usage(self, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        llm = get_llm(config)
        assert llm.extra_body["provider"]["only"] == ["Fireworks"]
        assert llm.extra_body["provider"]["allow_fallbacks"] is False
        assert llm.extra_body["seed"] == 20260820
        assert llm.extra_body["usage"] == {"include": True}

    def test_exige_api_key(self, config, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(ConfigError, match="OPENROUTER_API_KEY"):
            get_llm(config)

    def test_temperatura_sobreposta_revalida(self, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        llm = get_llm(config, temperature=0.7)
        assert llm.temperature == 0.7


class TestParametrosDoPayload:
    """
    Regressão de um achado que custou horas: o ChatOpenAI traduz
    `max_tokens` em `max_completion_tokens`, que quase nenhum provedor
    fora da OpenAI implementa. Com `require_parameters: true` o OpenRouter
    então recusa TODOS os endpoints com um 404 que nem cita o parâmetro
    culpado. Verificado contra a API real: 0 dos 5 endpoints de
    qwen/qwen3-coder aceitam max_completion_tokens; todos aceitam max_tokens.
    """

    def test_envia_max_tokens_e_nao_max_completion_tokens(self, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        payload = get_llm(config)._get_request_payload([("user", "oi")])

        assert payload["max_tokens"] == config.max_tokens
        assert "max_completion_tokens" not in payload

    def test_roteamento_de_provedor_chega_ao_payload(self, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        payload = get_llm(config)._get_request_payload([("user", "oi")])

        assert payload["extra_body"]["provider"]["only"] == ["Fireworks"]
        assert payload["extra_body"]["seed"] == 20260820
        assert payload["extra_body"]["usage"] == {"include": True}


class TestOverridesDoTesteDeAptidao:
    """O sweep de candidatos precisa funcionar sem editar o .env."""

    def test_override_supre_env_ausente(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_MODEL_NAME", raising=False)
        monkeypatch.delenv("OPENROUTER_PROVIDER", raising=False)

        cfg = load_llm_config(model="vendor/m", provider="DeepInfra", max_tokens=512)

        assert (cfg.model, cfg.provider, cfg.max_tokens) == ("vendor/m", "DeepInfra", 512)

    def test_override_de_free_continua_recusado(self, monkeypatch):
        with pytest.raises(ConfigError, match="tier gratuito"):
            load_llm_config(model="qwen/qwen-2.5-7b-instruct:free", provider="X")


class TestPreservacaoDoProvider:
    """
    O LangChain monta llm_output com allowlist fixa e descarta `provider`.
    Se um upgrade da lib quebrar o gancho, este teste falha — e não a coleta.
    """

    def test_provider_sobrevive_ao_create_chat_result(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        llm = OpenRouterChat(model="vendor/modelo", api_key="sk-teste")

        result = llm._create_chat_result(RESPOSTA_OPENROUTER)

        assert result.llm_output["provider"] == "AtlasCloud"
        assert result.generations[0].message.response_metadata["provider"] == "AtlasCloud"

    def test_campos_padrao_continuam_presentes(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        llm = OpenRouterChat(model="vendor/modelo", api_key="sk-teste")

        out = llm._create_chat_result(RESPOSTA_OPENROUTER).llm_output

        assert out["id"] == RESPOSTA_OPENROUTER["id"]
        assert out["token_usage"]["cost"] == 0.000123

    def test_resposta_sem_provider_nao_quebra(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        llm = OpenRouterChat(model="vendor/modelo", api_key="sk-teste")
        sem_provider = {k: v for k, v in RESPOSTA_OPENROUTER.items() if k != "provider"}

        result = llm._create_chat_result(sem_provider)

        assert "provider" not in result.llm_output


# ------------------------------------------------------------------ métricas


class TestExtracaoDeMetricas:
    def test_extrai_tokens_custo_e_provedor(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        m = extract_call_metrics(mensagem_como_em_producao(RESPOSTA_OPENROUTER))

        assert m.provider_served == "AtlasCloud"
        assert m.generation_id == RESPOSTA_OPENROUTER["id"]
        assert (m.tokens_prompt, m.tokens_completion, m.tokens_total) == (14, 10, 24)
        assert m.tokens_reasoning == 8
        assert m.cost_usd == 0.000123
        assert m.model == "vendor/modelo"
        assert m.finish_reason == "stop"

    def test_tolera_ausencia_de_usage(self):
        class Vazia:
            response_metadata: dict = {}

        m = extract_call_metrics(Vazia())
        assert m == LLMCallMetrics()
        assert m.cost_usd == 0.0 and m.provider_served is None

    def test_tolera_objeto_sem_metadata(self):
        assert extract_call_metrics(object()).tokens_total == 0

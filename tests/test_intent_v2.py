"""Refinador v2 (decisão 28 do autor, 14/10/2026): enriquece em vez de resumir."""

from __future__ import annotations

from src import config
from src.schemas.intent import StructuredIntent, StructuredIntentV2, intent_as_text
from src.state import parse_intent


def _v2(**extra) -> StructuredIntentV2:
    base = dict(
        context="O parser falha em chaves pontilhadas.",
        goal="Aceitar chaves pontilhadas.",
        phases=["Localizar o parser de chaves", "Verificar com run_python"],
        acceptance_criteria=["parse('a.b = 1')['a']['b'] == 1"],
        is_ready=True,
        reproduction=["```python\nimport tomlkit\nprint(tomlkit.parse('a.b = 1'))\n```"],
        expected_outputs=["{'a': {'b': 1}}"],
        constraints=["A área de testes (tests/) é protegida; não escrever testes."],
    )
    base.update(extra)
    return StructuredIntentV2(**base)


class TestSchemaV2:
    def test_listas_aninhadas_e_vazias_sao_achatadas(self):
        # tomlkit-0003 rep01 da rodada 2 morreu com reproduction=[[], [linha, linha]]
        i = _v2(reproduction=[[], ["x = 1", "print(x)"], "y"], expected_outputs=["", " 1 "])
        assert i.reproduction == ["x = 1\nprint(x)", "y"]
        assert i.expected_outputs == [" 1 "]

    def test_item_que_nao_e_texto_continua_invalido(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _v2(reproduction=[[1, 2]])

    def test_markdown_carrega_reproducao_saidas_e_restricoes_literalmente(self):
        texto = _v2().to_markdown()
        assert texto.startswith("# Objetivo\nAceitar chaves pontilhadas.\n")
        assert "# Como reproduzir\n```python\nimport tomlkit\nprint(tomlkit.parse('a.b = 1'))\n```" in texto
        assert "# Saídas e valores esperados\n- {'a': {'b': 1}}" in texto
        assert "# Critérios de aceitação\n1. parse('a.b = 1')['a']['b'] == 1" in texto
        assert "# Restrições do ambiente\n- A área de testes (tests/) é protegida; não escrever testes." in texto
        assert "Pontos em aberto" not in texto

    def test_bloco_sem_cerca_ganha_cerca(self):
        texto = _v2(reproduction=["print(1)"]).to_markdown()
        assert "```\nprint(1)\n```" in texto

    def test_pontos_em_aberto_entram_quando_existem(self):
        texto = _v2(open_questions=["'tabela' = Table ou Container? adotado: Table"]).to_markdown()
        assert "# Pontos em aberto (leitura adotada)\n- 'tabela' = Table ou Container? adotado: Table" in texto

    def test_v1_continua_json_e_v2_vira_markdown(self):
        v1 = StructuredIntent(context="c", goal="g", phases=[], acceptance_criteria=[], is_ready=True)
        assert intent_as_text(v1) == v1.model_dump_json(indent=2)
        assert intent_as_text(_v2()).startswith("# Objetivo")


class TestParseIntent:
    def test_estado_sem_chaves_v2_e_v1(self):
        intent = parse_intent({"intent": {"context": "c", "goal": "g", "phases": [],
                                          "acceptance_criteria": [], "is_ready": True}})
        assert type(intent) is StructuredIntent

    def test_estado_com_chave_v2_e_v2(self):
        intent = parse_intent({"intent": _v2().model_dump()})
        assert isinstance(intent, StructuredIntentV2)
        assert intent.expected_outputs == ["{'a': {'b': 1}}"]

    def test_estado_inicial_dos_bracos_nao_muda(self):
        """O estado inicial do runner (goal = enunciado) segue sendo v1: o single-agent não é tocado."""
        intent = parse_intent({"intent": {"context": "", "goal": "ENUNCIADO", "phases": [],
                                          "acceptance_criteria": [], "clarifications_needed": [],
                                          "is_ready": True}})
        assert type(intent) is StructuredIntent and intent.goal == "ENUNCIADO"


class TestRefinadorEscolheAVersao:
    def test_v1_usa_o_prompt_e_o_schema_do_tfg(self, ctx_minimo, sample_intent, monkeypatch):
        from src.agents import intent_refiner as mod

        monkeypatch.setattr(config, "INTENT_REFINER", "v1")
        capturado = {}

        def _falso(schema, messages, **kwargs):
            capturado["schema"] = schema; capturado["system"] = messages[0][1]
            return sample_intent, None

        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _falso)
        mod.intent_refiner({"run_id": "no-test", "arm": "orchestration", "task_id": "t", "raw_request": "x"})
        assert capturado["schema"] is StructuredIntent
        assert capturado["system"] == mod.SYSTEM_PROMPT

    def test_v2_usa_o_prompt_e_o_schema_novos(self, ctx_minimo, monkeypatch):
        from src.agents import intent_refiner as mod

        monkeypatch.setattr(config, "INTENT_REFINER", "v2")
        capturado = {}

        def _falso(schema, messages, **kwargs):
            capturado["schema"] = schema; capturado["system"] = messages[0][1]
            return _v2(), None

        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _falso)
        out = mod.intent_refiner({"run_id": "no-test", "arm": "orchestration", "task_id": "t", "raw_request": "x"})
        assert capturado["schema"] is StructuredIntentV2
        assert capturado["system"] == mod.SYSTEM_PROMPT_V2
        assert out["intent"]["reproduction"] and out["is_ready"] is True

    def test_prompt_v2_exige_copia_literal_e_declara_a_area_protegida(self):
        from src.agents.intent_refiner import SYSTEM_PROMPT_V2

        assert "NÃO verá o" in SYSTEM_PROMPT_V2 and "a sua saída é a única especificação" in SYSTEM_PROMPT_V2
        assert "Copie literalmente" in SYSTEM_PROMPT_V2
        assert "Nunca resumir" in SYSTEM_PROMPT_V2
        assert "`tests/`" in SYSTEM_PROMPT_V2 and "protegida" in SYSTEM_PROMPT_V2
        assert "Não invente" in SYSTEM_PROMPT_V2


class TestDeveloperERevisorRecebemAV2:
    def test_prompt_do_developer_e_markdown_com_a_tarefa(self, monkeypatch):
        from src.agents.developer import _build_prompt

        monkeypatch.setattr(config, "DEVELOPER_INPUT", "intent")
        prompt = _build_prompt({"intent": _v2().model_dump()}, diff="")
        assert prompt.startswith("Tarefa:\n# Objetivo\n")
        assert "```python\nimport tomlkit" in prompt and '"goal"' not in prompt

    def test_prompt_do_revisor_e_o_mesmo_texto(self):
        from src.agents.validator import _build_review_prompt

        class _Ws:
            def diff(self):
                return "diff --git a/x b/x"

        class _Ctx:
            workspace = _Ws()

        prompt = _build_review_prompt({"intent": _v2().model_dump()}, _Ctx())
        assert prompt.startswith("Tarefa:\n# Objetivo\n") and "diff --git" in prompt

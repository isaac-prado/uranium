"""
Paridade entre os braços A2 e B.

Este é o teste que sustenta a alegação causal do estudo: se algo além da
topologia de orquestração diferir entre os braços, a diferença medida deixa
de ser atribuível à topologia. Aqui isso vira uma verificação executável, e
não uma afirmação no texto do TCC.

Qualquer chave nova no manifesto que passe a divergir entre os braços
derruba estes testes — de propósito.
"""

from __future__ import annotations

import pytest

from src.arms.a2 import SYSTEM_PROMPT as PROMPT_A2
from src.arms.driver import DriverPolicy
from src.arms.runner import CHAVES_QUE_PODEM_DIFERIR, build_run_spec
from src.agents.developer import SYSTEM_PROMPT as PROMPT_B
from src.budget import RunBudget
from src.config import LLMConfig
from src.runtime import RunContext
from src.seeds import TOMLKIT
from src.telemetry import TelemetryWriter
from src.tools import TOOL_NAMES
from src.workspace import Workspace, WorkspaceSpec

BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"
LLM = LLMConfig(model="vendor/modelo", provider="DeepInfra", seed=20260820, max_tokens=8192)
BUDGET = RunBudget(max_tokens=400_000, max_wall_seconds=1800, max_turns=40)

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


def _spec(arm, tmp_path):
    return build_run_spec(
        run_id=f"paridade-{arm}", arm=arm, task_id="tomlkit-0001",
        statement="Levantar erro em elemento malformado de array.",
        base_commit=BASE_COMMIT, out_dir=tmp_path / arm,
        llm=LLM, budget=BUDGET,
    )


# ------------------------------------------------------------------ manifesto


class TestManifesto:
    def test_so_a_topologia_difere(self, tmp_path):
        """O coração do desenho experimental, verificado por execução."""
        a2 = _spec("A2", tmp_path).manifest("2026-01-01T00:00:00")
        b = _spec("B", tmp_path).manifest("2026-01-01T00:00:00")

        divergentes = {k for k in a2 if a2[k] != b.get(k)}
        inesperadas = divergentes - CHAVES_QUE_PODEM_DIFERIR

        assert not inesperadas, (
            "os braços divergem em campos que deveriam ser idênticos: "
            f"{sorted(inesperadas)}"
        )

    def test_a_topologia_de_fato_difere(self):
        """Contraprova: se nada diferisse, não haveria variável independente."""
        a2 = _spec("A2", __import__("pathlib").Path("/tmp")).manifest("t")
        b = _spec("B", __import__("pathlib").Path("/tmp")).manifest("t")
        assert a2["topology"] == "single_agent"
        assert b["topology"] == "multi_agent_roles"
        assert a2["topology"] != b["topology"]

    def test_configuracao_de_llm_identica(self, tmp_path):
        a2 = _spec("A2", tmp_path).manifest("t")["llm"]
        b = _spec("B", tmp_path).manifest("t")["llm"]
        assert a2 == b
        assert a2["seed"] == 20260820 and a2["temperature"] == 0.0
        assert a2["allow_fallbacks"] is False and a2["require_parameters"] is True

    def test_orcamento_identico(self, tmp_path):
        assert _spec("A2", tmp_path).manifest("t")["budget"] == \
               _spec("B", tmp_path).manifest("t")["budget"]

    def test_so_o_a2_tem_politica_de_driver(self, tmp_path):
        assert _spec("A2", tmp_path).manifest("t")["driver_policy"] is not None
        assert _spec("B", tmp_path).manifest("t")["driver_policy"] is None

    def test_manifesto_serializavel(self, tmp_path):
        import json
        m = _spec("A2", tmp_path).manifest("t")
        assert json.loads(json.dumps(m)) == m


# ------------------------------------------------------------------ runtime


@mirror_available
class TestRuntimeIdentico:
    @pytest.fixture
    def contexto(self, tmp_path):
        def montar(arm):
            ws = Workspace.materialize(
                WorkspaceSpec(seed=TOMLKIT, base_commit=BASE_COMMIT),
                run_id=f"par-{arm}", dest=tmp_path / f"ws-{arm}",
            )
            tel = TelemetryWriter(
                tmp_path / f"{arm}.jsonl", run_id=f"par-{arm}", arm=arm,
                task_id="t", model=LLM.model, provider_requested=LLM.provider,
            )
            ctx = RunContext.create(
                run_id=f"par-{arm}", arm=arm, task_id="t",
                workspace=ws, telemetry=tel, budget=BUDGET,
                llm_factory=lambda: None,
            )
            return ctx, tel
        contextos = [montar("A2"), montar("B")]
        yield {ctx.arm: ctx for ctx, _ in contextos}
        for ctx, tel in contextos:
            tel.close()
            RunContext.release(ctx.run_id)

    def test_mesmo_conjunto_de_ferramentas(self, contexto):
        """Ferramentas diferentes entre braços invalidariam a comparação."""
        a2 = {t.name for t in contexto["A2"].tools}
        b = {t.name for t in contexto["B"].tools}
        assert a2 == b == set(TOOL_NAMES)

    def test_mesmos_schemas_de_argumento(self, contexto):
        def assinatura(ctx):
            return {
                t.name: t.args_schema.model_json_schema()
                for t in sorted(ctx.tools, key=lambda x: x.name)
            }
        assert assinatura(contexto["A2"]) == assinatura(contexto["B"])

    def test_mesmas_descricoes_de_ferramenta(self, contexto):
        """A descrição entra no prompt: divergir aqui é divergir de prompt."""
        def descricoes(ctx):
            return {t.name: t.description for t in ctx.tools}
        assert descricoes(contexto["A2"]) == descricoes(contexto["B"])

    def test_mesmo_orcamento_efetivo(self, contexto):
        assert contexto["A2"].budget.budget == contexto["B"].budget.budget

    def test_mesmo_timeout_de_teste(self, contexto):
        assert contexto["A2"].test_timeout_s == contexto["B"].test_timeout_s


# ------------------------------------------------------------------- prompts


class TestJusticaDePrompt:
    """
    O A2 não pode ser espantalho: precisa das mesmas capacidades do B, sem a
    decomposição em papéis. Se o prompt dele fosse empobrecido, o estudo
    mediria qualidade de prompt em vez de topologia.
    """

    def test_a2_conhece_as_mesmas_ferramentas(self):
        for nome in TOOL_NAMES:
            assert nome in PROMPT_A2, f"{nome} ausente do prompt do A2"

    def test_ambos_carregam_a_restricao_de_arquivos_protegidos(self):
        for prompt in (PROMPT_A2, PROMPT_B):
            assert "protegidos" in prompt
            assert "produção" in prompt

    def test_ambos_exigem_conteudo_completo_no_write(self):
        assert "COMPLETO" in PROMPT_A2 and "COMPLETO" in PROMPT_B

    def test_tamanhos_comparaveis(self):
        """Prompt muito maior de um lado seria confundidor de tratamento."""
        razao = len(PROMPT_B) / len(PROMPT_A2)
        assert 0.6 <= razao <= 1.6, f"prompts desbalanceados: razão {razao:.2f}"

    def test_so_o_b_decompoe_em_papeis(self):
        """A diferença de prompt permitida é exatamente a topologia."""
        assert "papéis" not in PROMPT_A2 and "fases" not in PROMPT_A2


class TestPoliticaDoDriver:
    def test_nao_sumariza_falhas_por_padrao(self):
        """Sumarizar seria injetar engenharia de fora e creditar ao agente."""
        assert DriverPolicy().sumariza_falhas is False

    def test_aceita_todo_patch(self):
        assert DriverPolicy().aceita_todo_patch is True

    def test_politica_vai_inteira_para_o_manifesto(self):
        m = DriverPolicy().as_manifest()
        assert set(m) == {
            "entrega_spec_uma_vez", "aceita_todo_patch", "sumariza_falhas",
            "stderr_chars", "roda_suite_sem_tool_call",
        }

"""
Paridade entre os braços single-agent e orchestration.

Este é o teste que sustenta a alegação causal do estudo: se algo além da
topologia de orquestração diferir entre os braços, a diferença medida deixa
de ser atribuível à topologia. Aqui isso vira uma verificação executável, e
não uma afirmação no texto do TCC.

Qualquer chave nova no manifesto que passe a divergir entre os braços
derruba estes testes — de propósito.
"""

from __future__ import annotations

import pytest

from src.arms.single_agent import SYSTEM_PROMPT as PROMPT_SINGLE
from src.arms.driver import DriverPolicy
from src.arms.runner import (
    CHAVES_QUE_PODEM_DIFERIR,
    build_run_spec,
    seed_for_repetition,
)
from src.agents.developer import SYSTEM_PROMPT as PROMPT_ORQ
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


def _spec(arm, tmp_path, repetition=1):
    return build_run_spec(
        run_id=f"paridade-{arm}", arm=arm, task_id="tomlkit-0001",
        statement="Levantar erro em elemento malformado de array.",
        base_commit=BASE_COMMIT, out_dir=tmp_path / arm,
        llm=LLM, budget=BUDGET, repetition=repetition,
    )


# ------------------------------------------------------------------ manifesto


class TestManifesto:
    def test_so_a_topologia_difere(self, tmp_path):
        """O coração do desenho experimental, verificado por execução."""
        a2 = _spec("single-agent", tmp_path).manifest("2026-01-01T00:00:00")
        b = _spec("orchestration", tmp_path).manifest("2026-01-01T00:00:00")

        # União das chaves dos dois manifestos, não só as do single-agent
        # (docs/tcc/01-inventario.md, folga F13): uma chave exclusiva do
        # orchestration passava batido antes desta correção.
        todas_as_chaves = set(a2) | set(b)
        divergentes = {k for k in todas_as_chaves if a2.get(k) != b.get(k)}
        inesperadas = divergentes - CHAVES_QUE_PODEM_DIFERIR

        assert not inesperadas, (
            "os braços divergem em campos que deveriam ser idênticos: "
            f"{sorted(inesperadas)}"
        )

    def test_a_topologia_de_fato_difere(self):
        """Contraprova: se nada diferisse, não haveria variável independente."""
        a2 = _spec("single-agent", __import__("pathlib").Path("/tmp")).manifest("t")
        b = _spec("orchestration", __import__("pathlib").Path("/tmp")).manifest("t")
        assert a2["topology"] == "single_agent"
        assert b["topology"] == "multi_agent_roles"
        assert a2["topology"] != b["topology"]

    def test_configuracao_de_llm_identica(self, tmp_path):
        a2 = _spec("single-agent", tmp_path).manifest("t")["llm"]
        b = _spec("orchestration", tmp_path).manifest("t")["llm"]
        assert a2 == b
        assert a2["seed"] == seed_for_repetition(20260820, 1)
        assert a2["temperature"] == 0.0
        assert a2["allow_fallbacks"] is False and a2["require_parameters"] is True

    def test_orcamento_identico(self, tmp_path):
        assert _spec("single-agent", tmp_path).manifest("t")["budget"] == \
               _spec("orchestration", tmp_path).manifest("t")["budget"]

    def test_so_o_a2_tem_politica_de_driver(self, tmp_path):
        assert _spec("single-agent", tmp_path).manifest("t")["driver_policy"] is not None
        assert _spec("orchestration", tmp_path).manifest("t")["driver_policy"] is None

    def test_so_o_b_tem_politica_de_orchestration(self, tmp_path):
        """Espelho do teste acima: `orchestration_policy` é exclusiva do braço orquestrado."""
        assert _spec("single-agent", tmp_path).manifest("t")["orchestration_policy"] is None
        assert _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"] is not None

    def test_manifesto_serializavel(self, tmp_path):
        import json
        m = _spec("single-agent", tmp_path).manifest("t")
        assert json.loads(json.dumps(m)) == m


class TestManifestoRegistraOQueAfetaOOrchestration:
    """
    F9: cinco parâmetros mudavam o comportamento do braço orchestration sem
    deixar rastro no manifesto. Dois runs com valores diferentes produziam
    manifestos idênticos — esta classe prova que não produzem mais.
    """

    def test_shared_limits_e_igual_ao_valor_efetivo_dos_modulos(self, tmp_path):
        """F11: `shared_limits` não pode ser um número reescrito à mão."""
        from src.runtime import MAX_TOOL_CALLS_POR_TURNO
        from src.tools.base import (
            MAX_READ_CHARS,
            MAX_READ_LINES,
            MAX_SEARCH_RESULTS,
            MAX_TOOL_OUTPUT_CHARS,
        )
        from src.tools.exec import DEFAULT_SNIPPET_TIMEOUT_S

        m = _spec("orchestration", tmp_path).manifest("t")["shared_limits"]
        assert m["max_tool_calls_por_turno"] == MAX_TOOL_CALLS_POR_TURNO
        assert m["default_snippet_timeout_s"] == DEFAULT_SNIPPET_TIMEOUT_S
        assert m["max_read_chars"] == MAX_READ_CHARS
        assert m["max_read_lines"] == MAX_READ_LINES
        assert m["max_search_results"] == MAX_SEARCH_RESULTS
        assert m["max_tool_output_chars"] == MAX_TOOL_OUTPUT_CHARS

    def test_mudar_max_semantic_rejections_muda_o_manifesto(self, tmp_path, monkeypatch):
        from src import config

        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        monkeypatch.setattr(config, "MAX_SEMANTIC_REJECTIONS", base["max_semantic_rejections"] + 1)

        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base
        assert depois["max_semantic_rejections"] == base["max_semantic_rejections"] + 1

    def test_mudar_max_clarification_iterations_muda_o_manifesto(self, tmp_path, monkeypatch):
        from src import config

        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        monkeypatch.setattr(
            config, "MAX_CLARIFICATION_ITERATIONS", base["max_clarification_iterations"] + 1
        )

        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base

    def test_mudar_semantic_review_muda_o_manifesto(self, tmp_path, monkeypatch):
        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        monkeypatch.setenv("SEMANTIC_REVIEW", "false" if base["semantic_review"] else "true")

        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base

    def test_mudar_structured_output_method_muda_o_manifesto(self, tmp_path, monkeypatch):
        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        outro = "json_schema" if base["structured_output_method"] != "json_schema" else "json_mode"
        monkeypatch.setenv("STRUCTURED_OUTPUT_METHOD", outro)

        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base

    def test_mudar_structured_output_retries_muda_o_manifesto(self, tmp_path, monkeypatch):
        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        monkeypatch.setenv("STRUCTURED_OUTPUT_RETRIES", str(base["structured_output_retries"] + 1))

        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base

    def test_manifest_version_subiu(self, tmp_path):
        """A forma do manifesto mudou (novas chaves): a versão precisa acompanhar."""
        assert _spec("orchestration", tmp_path).manifest("t")["manifest_version"] == 7

    def test_mudar_developer_cycle_max_turns_muda_o_manifesto(self, tmp_path, monkeypatch):
        """Decisão 25 (09/10/2026): o teto por ciclo é política do braço."""
        from src import config

        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert base["developer_cycle_max_turns"] == config.DEVELOPER_CYCLE_MAX_TURNS
        monkeypatch.setattr(config, "DEVELOPER_CYCLE_MAX_TURNS", base["developer_cycle_max_turns"] + 1)

        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base

    def test_stop_reason_final_nunca_e_cycle(self):
        """`cycle:` é ponto de checagem; o run só acaba depois por validação ou teto."""
        from src.arms.runner import final_stop_reason

        assert final_stop_reason({"stop_reason": "cycle: max_turns_per_cycle (40 >= 40)",
                                  "is_valid": True}) == "concluiu"
        assert final_stop_reason({"stop_reason": "budget: max_turns (120 >= 120)"}) == \
            "budget: max_turns (120 >= 120)"
        assert final_stop_reason({"stop_reason": "concluiu", "is_valid": True}) == "concluiu"
        assert final_stop_reason({"is_valid": True}) == "tests_pass"
        assert final_stop_reason({}) == "concluiu"

    def test_mudar_developer_memory_muda_o_manifesto(self, tmp_path, monkeypatch):
        """Decisão 8 revista (09/10/2026): a memória de trabalho é política do braço."""
        from src import config
        from src.feedback import MEMORIA_DIFF_MAX_CHARS

        base = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert base["developer_memory"] == config.DEVELOPER_MEMORY
        assert base["developer_memory_diff_max_chars"] == MEMORIA_DIFF_MAX_CHARS

        outro = "none" if base["developer_memory"] == "ledger" else "ledger"
        monkeypatch.setattr(config, "DEVELOPER_MEMORY", outro)

        depois = _spec("orchestration", tmp_path).manifest("t")["orchestration_policy"]
        assert depois != base
        assert depois["developer_memory"] == outro


# ------------------------------------------------------------------ runtime


@mirror_available
class TestRuntimeIdentico:
    @pytest.fixture
    def contexto(self, tmp_path):
        def montar(arm):
            ws = Workspace.materialize(
                WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT),
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
        contextos = [montar("single-agent"), montar("orchestration")]
        yield {ctx.arm: ctx for ctx, _ in contextos}
        for ctx, tel in contextos:
            tel.close()
            RunContext.release(ctx.run_id)

    def test_mesmo_conjunto_de_ferramentas(self, contexto):
        """Ferramentas diferentes entre braços invalidariam a comparação."""
        a2 = {t.name for t in contexto["single-agent"].tools}
        b = {t.name for t in contexto["orchestration"].tools}
        assert a2 == b == set(TOOL_NAMES)

    def test_mesma_ordem_de_ferramentas(self, contexto):
        """
        F10: o teste acima usa `set` e não pega ordem diferente. A ordem em
        que as ferramentas entram no `bind_tools`/`ctx.tools` também faz
        parte do prompt afetivo do modelo (é a ordem em que ele as vê
        descritas), então precisa ser idêntica, não só o conjunto.
        """
        a2 = [t.name for t in contexto["single-agent"].tools]
        b = [t.name for t in contexto["orchestration"].tools]
        assert a2 == b == list(TOOL_NAMES)

    def test_mesmos_schemas_de_argumento(self, contexto):
        def assinatura(ctx):
            return {
                t.name: t.args_schema.model_json_schema()
                for t in sorted(ctx.tools, key=lambda x: x.name)
            }
        assert assinatura(contexto["single-agent"]) == assinatura(contexto["orchestration"])

    def test_mesmas_descricoes_de_ferramenta(self, contexto):
        """A descrição entra no prompt: divergir aqui é divergir de prompt."""
        def descricoes(ctx):
            return {t.name: t.description for t in ctx.tools}
        assert descricoes(contexto["single-agent"]) == descricoes(contexto["orchestration"])

    def test_mesmo_orcamento_efetivo(self, contexto):
        assert contexto["single-agent"].budget.budget == contexto["orchestration"].budget.budget

    def test_mesmo_timeout_de_teste(self, contexto):
        assert (contexto["single-agent"].test_timeout_s
                == contexto["orchestration"].test_timeout_s)


# ------------------------------------------------------------------- prompts


class TestJusticaDePrompt:
    """
    O prompt do agente que escreve código é o MESMO texto nos dois braços.

    A versão anterior deste teste só exigia "parecido": mesmas ferramentas
    citadas, mesmas restrições, razão de tamanho entre 0,6 e 1,6. Passava
    folgado enquanto o orchestration tinha uma seção "Método esperado" de
    cinco passos que o single-agent não tinha, e uma condição de parada em
    duas partes contra uma simples.

    O efeito medido em 5 repetições da mesma tarefa: o single-agent parava
    4 tool calls depois da primeira escrita, sempre; o orchestration gastava
    de 2 a 32. Dobrou os turnos e quase triplicou o custo — e teria sido
    publicado como "orquestração custa 2,8× mais".

    Por isso a checagem agora é identidade literal. Diferença de redação não
    é separável de diferença de topologia depois que o dado foi coletado.
    """

    def test_e_o_mesmo_texto(self):
        assert PROMPT_SINGLE == PROMPT_ORQ

    def test_vem_da_mesma_origem(self):
        """Cópia idêntica hoje diverge amanhã; a fonte tem de ser uma só."""
        from src.prompts import AGENT_SYSTEM_PROMPT

        assert PROMPT_SINGLE is AGENT_SYSTEM_PROMPT
        assert PROMPT_ORQ is AGENT_SYSTEM_PROMPT

    def test_conhece_todas_as_ferramentas(self):
        for nome in TOOL_NAMES:
            assert nome in PROMPT_SINGLE, f"{nome} ausente do prompt"

    def test_carrega_as_restricoes_do_desenho(self):
        assert "protegidos" in PROMPT_SINGLE and "produção" in PROMPT_SINGLE
        assert "COMPLETO" in PROMPT_SINGLE
        # a suíte visível já passa na base: sem este aviso, não fazer nada
        # satisfaz o critério de parada
        assert "run_tests sozinho" in PROMPT_SINGLE

    def test_nao_decompoe_em_papeis(self):
        """
        A decomposição do orchestration vive no grafo, não no prompt. Se
        aparecesse aqui, os dois braços a receberiam — e o single-agent
        deixaria de ser agente único.
        """
        assert "papéis" not in PROMPT_SINGLE and "fases" not in PROMPT_SINGLE


class TestSementePorRepeticao:
    """
    A semente varia entre repetições — senão as N execuções sairiam quase
    idênticas e não mediriam variabilidade — mas é a MESMA entre os braços
    numa dada repetição, o que preserva o pareamento da análise.
    """

    def test_repeticoes_diferentes_dao_sementes_diferentes(self, tmp_path):
        sementes = {_spec("orchestration", tmp_path, rep).llm.seed for rep in (1, 2, 3, 10)}
        assert len(sementes) == 4

    def test_mesma_repeticao_pareia_os_bracos(self, tmp_path):
        for rep in (1, 5, 10):
            a2 = _spec("single-agent", tmp_path, rep)
            b = _spec("orchestration", tmp_path, rep)
            assert a2.llm.seed == b.llm.seed, f"repetição {rep} não pareada"

    def test_repeticao_nao_pode_divergir_entre_bracos(self):
        """Se `repetition` virasse chave livre, o pareamento se perderia."""
        assert "repetition" not in CHAVES_QUE_PODEM_DIFERIR

    def test_repeticao_entra_no_manifesto(self, tmp_path):
        assert _spec("orchestration", tmp_path, 7).manifest("t")["repetition"] == 7

    def test_derivacao_e_deterministica(self):
        assert seed_for_repetition(100, 3) == seed_for_repetition(100, 3)
        assert seed_for_repetition(100, 3) != seed_for_repetition(100, 4)

    def test_repeticao_zero_e_recusada(self, tmp_path):
        """1-based: o índice aparece em caminho de saída e em run_id."""
        with pytest.raises(ValueError, match="começa em 1"):
            _spec("orchestration", tmp_path, 0)

    def test_saida_separada_por_repeticao(self):
        from pathlib import Path
        spec = build_run_spec(
            run_id="r", arm="orchestration", task_id="t", statement="s",
            base_commit=BASE_COMMIT, llm=LLM, budget=BUDGET, repetition=4,
        )
        assert spec.out_dir == Path("runs") / "orchestration" / "t" / "rep04" / "r"


class TestTentativaDeReexecucao:
    """
    E5 item 2: um run perdido por erro de provedor é reexecutado com
    `attempt` incrementado. A perda pode acontecer num braço só, então
    `attempt` PODE divergir entre os dois — o que não pode divergir é a
    semente, que continua vindo só de `repetition` (`seed_for_repetition`).
    """

    def test_attempt_default_e_1_e_entra_no_manifesto(self, tmp_path):
        assert _spec("orchestration", tmp_path).manifest("t")["attempt"] == 1

    def test_attempt_diferente_nao_muda_a_semente(self, tmp_path):
        primeira = _spec("orchestration", tmp_path, repetition=2)
        refeita = build_run_spec(
            run_id="refeita", arm="orchestration", task_id="tomlkit-0001",
            statement="Levantar erro em elemento malformado de array.",
            base_commit=BASE_COMMIT, out_dir=tmp_path / "refeita",
            llm=LLM, budget=BUDGET, repetition=2, attempt=2,
        )
        assert primeira.llm.seed == refeita.llm.seed == seed_for_repetition(LLM.seed, 2)

    def test_attempt_pode_divergir_entre_bracos_sem_violar_a_paridade(self, tmp_path):
        """Prova pedida no plano: dois specs com `attempt` diferente têm o mesmo `llm.seed`."""
        a2 = build_run_spec(
            run_id="a", arm="single-agent", task_id="tomlkit-0001",
            statement="s", base_commit=BASE_COMMIT, out_dir=tmp_path / "sa",
            llm=LLM, budget=BUDGET, repetition=1, attempt=1,
        ).manifest("t")
        b = build_run_spec(
            run_id="b", arm="orchestration", task_id="tomlkit-0001",
            statement="s", base_commit=BASE_COMMIT, out_dir=tmp_path / "or",
            llm=LLM, budget=BUDGET, repetition=1, attempt=2,
        ).manifest("t")

        assert a2["attempt"] != b["attempt"]
        assert a2["llm"] == b["llm"]  # semente idêntica apesar do attempt divergente

        divergentes = {k for k in set(a2) | set(b) if a2.get(k) != b.get(k)}
        assert divergentes - CHAVES_QUE_PODEM_DIFERIR == set()

    def test_attempt_zero_e_recusado(self, tmp_path):
        with pytest.raises(ValueError, match="attempt começa em 1"):
            build_run_spec(
                run_id="x", arm="orchestration", task_id="t", statement="s",
                base_commit=BASE_COMMIT, out_dir=tmp_path / "x",
                llm=LLM, budget=BUDGET, repetition=1, attempt=0,
            )


class TestDesambiguacaoDeSemente:
    """
    "Semente" tinha dois significados no código: o repositório de partida e a
    semente aleatória do LLM. Os dois apareciam lado a lado no mesmo comando,
    o que é receita para erro de operação numa coleta de 160 execuções.
    """

    def test_manifesto_separa_os_dois_conceitos(self, tmp_path):
        m = _spec("orchestration", tmp_path, repetition=3).manifest("t")
        assert m["seed_repo_id"] == "tomlkit"          # repositório
        assert m["llm"]["seed"] == seed_for_repetition(20260820, 3)  # aleatória
        assert m["seed_repo_id"] != m["llm"]["seed"]

    def test_o_cli_nao_expoe_flag_ambigua(self):
        """`--seed` sozinho não pode existir: era o repositório, e confunde."""
        import subprocess
        import sys

        ajuda = subprocess.run(
            [sys.executable, "scripts/run_arm.py", "--help"],
            capture_output=True, text=True,
        ).stdout
        assert "--seed-repo" in ajuda
        assert "--seed " not in ajuda and "--seed]" not in ajuda


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
            "roda_suite_sem_tool_call",
        }


class TestContabilidadeDeCusto:
    """
    Toda chamada de LLM tem de aparecer na telemetria.

    O braço orchestration tem quatro nós além do developer que chamam LLM. Quando eles
    usavam `invoke_structured` direto, essas chamadas ficavam fora da conta
    de custo E fora do orçamento — o braço multiagente saía artificialmente
    barato, enviesando exatamente a comparação que o estudo faz.
    """

    def test_nenhum_no_chama_invoke_structured_direto(self):
        import subprocess
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        achados = subprocess.run(
            ["grep", "-rn", "-E", r"(^|[^.])\binvoke_structured\(", "--include=*.py", "src/agents"],
            cwd=raiz, capture_output=True, text=True,
        ).stdout.strip()
        assert not achados, (
            "nó chamando invoke_structured fora do RunContext — a chamada não "
            f"seria contabilizada:\n{achados}"
        )

    def test_contexto_expoe_a_chamada_instrumentada(self):
        from src.runtime import RunContext

        assert callable(getattr(RunContext, "invoke_structured", None))


class TestProveniencia:
    """
    O modelo efetivamente usado tem de ser o que o manifesto declara.

    O cliente já foi construído a partir do ambiente enquanto o manifesto
    registrava a configuração resolvida do run. Com um modelo diferente no
    .env, a coleta inteira teria proveniência errada sem sinal nenhum.
    """

    def test_contexto_exige_a_config_resolvida(self, tmp_path):
        from src.runtime import RunContext
        from src.telemetry import TelemetryWriter

        tel = TelemetryWriter(tmp_path / "e.jsonl", run_id="p",
                              arm="orchestration", task_id="t")
        try:
            with pytest.raises(RuntimeError, match="llm_config"):
                RunContext.create(
                    run_id="p", arm="orchestration", task_id="t",
                    workspace=None, telemetry=tel,
                )
        finally:
            tel.close()
            RunContext.release("p")

    def test_cliente_usa_o_modelo_do_manifesto(self, tmp_path, monkeypatch):
        from src.runtime import RunContext
        from src.telemetry import TelemetryWriter

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
        monkeypatch.setenv("OPENROUTER_MODEL_NAME", "modelo/do-ambiente")
        monkeypatch.setenv("OPENROUTER_PROVIDER", "ProvedorDoAmbiente")

        resolvida = LLMConfig(model="modelo/do-run", provider="ProvedorDoRun", seed=7)
        tel = TelemetryWriter(tmp_path / "e.jsonl", run_id="p2",
                              arm="orchestration", task_id="t")
        try:
            ctx = RunContext.create(
                run_id="p2", arm="orchestration", task_id="t",
                workspace=None, telemetry=tel, llm_config=resolvida,
            )
            cliente = ctx.llm_factory()
            assert cliente.model_name == "modelo/do-run"
            assert cliente.extra_body["provider"]["only"] == ["ProvedorDoRun"]
            assert cliente.extra_body["seed"] == 7
        finally:
            tel.close()
            RunContext.release("p2")


class TestExecucaoDeFerramenta:
    """
    Os dois braços executam tool call pelo MESMO código.

    Enquanto eram duas cópias, elas divergiram sem ninguém notar. E a
    divergência aqui não é detalhe de implementação: é diferença de
    capacidade entre os braços, invisível no manifesto.
    """

    def test_os_dois_bracos_usam_o_executor_do_runtime(self):
        import inspect

        from src.agents import developer as dev
        from src.arms import single_agent as sa

        for modulo in (dev, sa):
            fonte = inspect.getsource(modulo)
            assert "ctx.executar_tool_calls(ai)" in fonte, f"{modulo.__name__} não usa o comum"
            assert "def _executar_ferramentas" not in fonte, f"{modulo.__name__} reintroduziu cópia"

    def test_argumento_faltando_volta_como_texto_e_nao_derruba_o_run(self, ctx_minimo):
        ctx, _ = ctx_minimo
        """
        O pydantic valida os argumentos ANTES da função da ferramenta rodar,
        então a guarda que existe lá dentro nunca é alcançada. Um
        ValidationError assim matou um run inteiro no teste de variância.
        """
        from tests.fakes import ai

        chamada = ai(tool_calls=[{"name": "read_file", "args": {}}])
        respostas = ctx.executar_tool_calls(chamada)

        assert len(respostas) == 1
        assert "ERRO" in respostas[0].content and "read_file" in respostas[0].content
        assert "argumentos" in respostas[0].content

    def test_ferramenta_desconhecida_lista_as_disponiveis(self, ctx_minimo):
        ctx, _ = ctx_minimo
        from tests.fakes import ai

        respostas = ctx.executar_tool_calls(
            ai(tool_calls=[{"name": "rm_rf", "args": {}}])
        )

        assert "desconhecida" in respostas[0].content
        assert "read_file" in respostas[0].content


class TestFeedbackDeProtocolo:
    """
    A mensagem entregue ao agente tem de ser a mesma nos dois braços.

    O single-agent avisava sobre diff vazio pelo driver e o orchestration
    não avisava nada: no retry, o developer recebia o prompt idêntico ao da
    primeira tentativa e repetia o que já tinha feito. Dois dos cinco runs do
    teste de variância terminaram assim, com patch de zero byte.
    """

    def test_a_mensagem_de_diff_vazio_e_literalmente_a_mesma(self):
        from src.agents.developer import _build_prompt
        from src.arms.driver import DeterministicDriver
        from src.feedback import DIFF_VAZIO
        from src.schemas.test_report import TestReport

        do_driver = DeterministicDriver().apos_turno(
            TestReport(exit_code=0, passed=10), houve_mudanca=False
        ).feedback
        do_developer = _build_prompt({
            "intent": {"context": "", "goal": "g", "phases": [],
                       "acceptance_criteria": [], "clarifications_needed": [],
                       "is_ready": True},
            "test_report": TestReport(exit_code=0, passed=10).model_dump(),
            "changed_files": [],
        })

        assert do_driver == DIFF_VAZIO
        assert DIFF_VAZIO in do_developer

    def test_feedback_de_suite_vermelha_e_literalmente_o_mesmo(self):
        """
        D7 do BACKLOG: o developer recebia o `stdout_tail` inteiro, com outro
        texto em volta. Agora os dois braços entregam a mesma string, vinda
        de `src.feedback.feedback_de_falha`, sem nenhum corte próprio: o
        único truncamento é o da ferramenta (`MAX_TOOL_OUTPUT_CHARS`, F2),
        igual para os dois — ver `test_mensagem_de_suite_falhou_e_a_mesma_byte_a_byte`.
        """
        from src.agents.developer import _build_prompt
        from src.arms.driver import DeterministicDriver
        from src.schemas.test_report import TestReport

        vermelha = TestReport(exit_code=1, failed=1,
                              stdout_tail="INICIO_DESCARTADO" + "x" * 9000 + "FIM_IMPORTANTE")
        do_driver = DeterministicDriver().apos_turno(vermelha, houve_mudanca=True).feedback
        do_developer = _build_prompt({
            "intent": {"context": "", "goal": "g", "phases": [],
                       "acceptance_criteria": [], "clarifications_needed": [],
                       "is_ready": True},
            "test_report": vermelha.model_dump(),
            "changed_files": ["pkg/mod.py"],
        })

        assert do_developer.endswith("\n\n" + do_driver)
        assert "FIM_IMPORTANTE" in do_developer
        # nenhum braço corta de novo: o que entrou no TestReport é o que chega
        assert "INICIO_DESCARTADO" in do_developer and "INICIO_DESCARTADO" in do_driver

    def test_nao_aponta_arquivo_nem_sugere_solucao(self):
        """A mensagem informa o protocolo; dizer como resolver seria trapaça nossa."""
        from src.feedback import DIFF_VAZIO

        for palavra in ("parser", ".py", "função", "linha", "provavelmente", "sugir"):
            assert palavra not in DIFF_VAZIO.lower()

    @staticmethod
    def _prompt_do_developer(report):
        from src.agents.developer import _build_prompt

        return _build_prompt({
            "intent": {"context": "", "goal": "g", "phases": [],
                       "acceptance_criteria": [], "clarifications_needed": [],
                       "is_ready": True},
            "test_report": report.model_dump(),
            "changed_files": [],
        })

    @pytest.mark.parametrize(
        "bruto",
        [
            "E   assert 1 == 2\nteste curto falhando",
            "F" * 9_000 + "\nFAILED tests/test_x.py::test_y - depois de estourar 8.000 chars",
        ],
        ids=["stdout_curto", "stdout_acima_de_8000_chars"],
    )
    def test_mensagem_de_suite_falhou_e_a_mesma_byte_a_byte(self, bruto):
        """
        F1/F2: antes o driver usava `suite_falhou` com corte próprio de
        4.000 caracteres e o developer montava texto próprio com o
        stdout_tail inteiro (já cortado em 8.000 pela ferramenta) — mesmo
        conteúdo, textos diferentes. Agora os dois passam pela mesma função
        (`src.feedback.feedback_de_falha`) sobre o mesmo `TestReport`.
        """
        from src.arms.driver import DeterministicDriver
        from src.schemas.test_report import TestReport
        from src.tools.base import MAX_TOOL_OUTPUT_CHARS, truncate

        # stdout_tail já truncado como run_pytest de fato produz.
        tail = truncate(bruto, MAX_TOOL_OUTPUT_CHARS)
        report = TestReport(exit_code=1, failed=1, stdout_tail=tail)

        do_driver = DeterministicDriver().apos_turno(report).feedback
        prompt = self._prompt_do_developer(report)

        assert do_driver, "o driver não devolveu feedback nenhum"
        assert prompt.endswith(do_driver), (
            "o trecho de feedback embutido no prompt do developer não é "
            "byte a byte o mesmo texto que o driver devolve"
        )

    def test_verde_sem_mudanca_os_dois_dao_diff_vazio(self):
        """Espelha o cenário acima para a mensagem de diff vazio (já coberta acima)."""
        from src.feedback import DIFF_VAZIO
        from src.schemas.test_report import TestReport

        report = TestReport(exit_code=0, passed=10)
        prompt = self._prompt_do_developer(report)
        assert prompt.endswith(DIFF_VAZIO)


class TestMensagensDeProtocoloSaoUnicas:
    """
    F1, F2 e F8 nasceram do mesmo defeito: uma mensagem de protocolo escrita
    duas vezes, uma por braço. `src/feedback.py` existe para que isso não
    aconteça de novo — este teste é a rede.
    """

    def test_verde_com_mudanca_o_developer_recebe_so_a_tarefa(self):
        """
        F8: "Arquivos já modificados: ..." só existia no developer. Removido
        o ramo, o cenário "suíte verde e houve mudança" entrega só a tarefa
        — nenhum texto de protocolo, nem os de src/feedback.py.
        """
        from src.agents.developer import _build_prompt
        from src.feedback import DIFF_VAZIO
        from src.schemas.test_report import TestReport
        from src.state import parse_intent

        state = {
            "intent": {"context": "", "goal": "g", "phases": [],
                       "acceptance_criteria": [], "clarifications_needed": [],
                       "is_ready": True},
            "test_report": TestReport(exit_code=0, passed=10).model_dump(),
            "changed_files": ["tomlkit/parser.py"],
        }
        prompt = _build_prompt(state)

        esperado = "Tarefa:\n" + parse_intent(state).model_dump_json(indent=2)
        assert prompt == esperado
        assert DIFF_VAZIO not in prompt
        assert "Arquivos já modificados" not in prompt

    def test_nenhuma_string_de_protocolo_fora_do_feedback(self):
        """
        As mensagens que já divergiram uma vez (F1, F2, F8) não podem viver
        de novo como string solta em developer.py ou driver.py — só como
        import de src.feedback.
        """
        import inspect

        from src.agents import developer as dev_mod
        from src.arms import driver as driver_mod

        proibidos = ["A suíte falhou", "Saída do pytest", "Arquivos já modificados"]
        for modulo in (dev_mod, driver_mod):
            fonte = inspect.getsource(modulo)
            for proibido in proibidos:
                assert proibido not in fonte, (
                    f"{modulo.__name__} embute a string de protocolo {proibido!r} "
                    "fora de src/feedback.py"
                )

    def test_funcoes_publicas_de_feedback_conhecidas(self):
        """
        Canário: se alguém acrescentar mensagem de protocolo nova em
        src/feedback.py, este teste lembra de também blindá-la aqui.
        """
        import src.feedback as fb

        publicos = {
            n for n in dir(fb)
            if not n.startswith("_") and n not in ("annotations", "Any", "TestReport", "truncate")
        }
        assert publicos == {
            "DIFF_VAZIO", "suite_falhou", "feedback_de_falha", "revisao_reprovada",
            "MEMORIA_DIFF_MAX_CHARS", "memoria_de_trabalho",
        }

    def test_memoria_de_trabalho_so_tem_moldura(self):
        """
        Decisão 8 revista (09/10/2026): a memória leva o que o developer fez e
        o diff dele; o harness escreve só os títulos. Nenhum diagnóstico,
        apontamento de arquivo ou sugestão pode nascer aqui.
        """
        from src.feedback import memoria_de_trabalho

        texto = memoria_de_trabalho([{"ciclo": 1, "turnos": 0, "parada": "concluiu"}], "")
        for palavra in ("parser", ".py", "função", "provavelmente", "sugir", "corrija", "tente"):
            assert palavra not in texto.lower()

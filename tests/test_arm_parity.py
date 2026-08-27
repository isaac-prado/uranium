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

        divergentes = {k for k in a2 if a2[k] != b.get(k)}
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

    def test_manifesto_serializavel(self, tmp_path):
        import json
        m = _spec("single-agent", tmp_path).manifest("t")
        assert json.loads(json.dumps(m)) == m


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
            "stderr_chars", "roda_suite_sem_tool_call",
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

    def test_nao_aponta_arquivo_nem_sugere_solucao(self):
        """A mensagem informa o protocolo; dizer como resolver seria trapaça nossa."""
        from src.feedback import DIFF_VAZIO

        for palavra in ("parser", ".py", "função", "linha", "provavelmente", "sugir"):
            assert palavra not in DIFF_VAZIO.lower()

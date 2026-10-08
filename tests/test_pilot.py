"""
O piloto ponta a ponta, offline.

Roda os dois braços, o avaliador externo e o relatório sem tocar na rede e
sem gastar crédito. É o ensaio da cadeia que a coleta definitiva vai usar:
se algo aqui quebra, quebra com dinheiro real depois.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.arms.pilot import (
    PilotOutcome,
    detectar_perdidos,
    format_report,
    reexecutar_perdidos,
    run_pilot,
    save_report,
)
from src.arms.runner import build_run_spec, run_arm
from src.budget import RunBudget
from src.config import LLMConfig
from src.seeds import TOMLKIT
from tests.fakes import FakeToolCallingLLM, ai, fabrica_por_run

TAREFA = Path("tasks/tomlkit-0001")
FIX_COMMIT = "d548e18b"
SOURCE_FILE = "tomlkit/parser.py"
LLM = LLMConfig(model="fake/modelo", provider="FakeProvider", seed=1, max_tokens=512)
ORCAMENTO = RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=8)

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


def _fonte_corrigida() -> str:
    return subprocess.run(
        ["git", "--git-dir", str(TOMLKIT.mirror_path), "show", f"{FIX_COMMIT}:{SOURCE_FILE}"],
        capture_output=True, text=True, check=True,
    ).stdout


@pytest.fixture
def sem_saida_estruturada(monkeypatch):
    """Fixa as saídas estruturadas do orchestration; o resto do grafo roda de verdade."""
    from src.schemas.intent import StructuredIntent
    from src.schemas.test_plan import TestPlan

    def _estruturado(schema, mensagens, **kwargs):
        if schema is StructuredIntent:
            return StructuredIntent(
                context="", goal="corrigir", phases=[], acceptance_criteria=[],
                clarifications_needed=[], is_ready=True,
            ), None
        if schema is TestPlan:
            return TestPlan(summary="plano", unit_tests=[], integration_tests=[]), None
        raise AssertionError(f"schema inesperado: {schema}")

    monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _estruturado)


def _llm_que_corrige() -> FakeToolCallingLLM:
    return FakeToolCallingLLM([
        ai(tool_calls=[{"name": "write_file",
                        "args": {"path": SOURCE_FILE, "content": _fonte_corrigida()}}]),
        ai(content="Elemento malformado agora levanta erro."),
    ])


@mirror_available
class TestPilotoPontaAPonta:
    def test_roda_os_dois_bracos_e_o_avaliador(self, tmp_path, monkeypatch,
                                               sem_saida_estruturada):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        resultados = run_pilot(
            task_dir=TAREFA, repetitions=1, out_root=tmp_path / "runs",
            llm=LLM, budget=ORCAMENTO,
            llm_factory=fabrica_por_run(_llm_que_corrige),
        )

        assert [r.arm for r in resultados] == ["single-agent", "orchestration"]
        for r in resultados:
            assert r.erro is None, r.erro
            assert r.resolved is True, f"{r.arm} não resolveu: f2p={r.f2p}"
            assert r.cheat_criticos == 0
            assert r.tokens > 0
            assert (r.out_dir / "patch.diff").read_text().strip(), "patch vazio"

    def test_pareia_a_semente_entre_os_bracos(self, tmp_path, monkeypatch,
                                              sem_saida_estruturada):
        """Repetição k de um braço e a k do outro são um par, não amostras soltas."""
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        run_pilot(
            task_dir=TAREFA, repetitions=2, out_root=tmp_path / "runs",
            llm=LLM, budget=ORCAMENTO, evaluate=False,
            llm_factory=fabrica_por_run(_llm_que_corrige),
        )

        por_repeticao: dict[int, set[int]] = {}
        for manifesto in (tmp_path / "runs").rglob("manifest.json"):
            m = json.loads(manifesto.read_text())
            por_repeticao.setdefault(m["repetition"], set()).add(m["llm"]["seed"])

        assert len(por_repeticao) == 2
        for repeticao, sementes in por_repeticao.items():
            assert len(sementes) == 1, f"repetição {repeticao} não pareada: {sementes}"
        assert len(set().union(*por_repeticao.values())) == 2, "repetições com a mesma semente"

    def test_run_que_morre_vira_linha_de_erro(self, tmp_path, monkeypatch,
                                              sem_saida_estruturada):
        """Um braço que explode não pode levar o piloto inteiro junto."""
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        class _Explode:
            def bind_tools(self, tools, **kwargs):
                return self

            def invoke(self, mensagens, **kwargs):
                raise RuntimeError("provedor caiu")

        resultados = run_pilot(
            task_dir=TAREFA, repetitions=1, out_root=tmp_path / "runs",
            llm=LLM, budget=ORCAMENTO, llm_factory=lambda *a, **k: _Explode(),
        )

        assert len(resultados) == 2
        for r in resultados:
            assert r.stop_reason.startswith("error:")
            assert "provedor caiu" in (r.erro or "")
            assert r.resolved is None  # não avaliado: não houve run


    @pytest.mark.parametrize("status", [401, 429])
    def test_falha_de_provedor_vira_infra_error_nos_dois_bracos(self, tmp_path, monkeypatch,
                                                                status):
        """
        O mesmo 429 tem de sair igual dos dois braços.

        Sem a fixture de saída estruturada: o orchestration passa pelo
        `invoke_structured_raw` real, que é onde o 429 virava erro de schema.
        """
        from tests.fakes import erro_http

        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        class _ProvedorFora:
            def bind_tools(self, tools, **kwargs):
                return self

            def with_structured_output(self, schema, **kwargs):
                return self

            def invoke(self, mensagens, **kwargs):
                raise erro_http(status)

        resultados = run_pilot(
            task_dir=TAREFA, repetitions=1, out_root=tmp_path / "runs",
            llm=LLM, budget=ORCAMENTO, llm_factory=lambda *a, **k: _ProvedorFora(),
        )

        assert [r.arm for r in resultados] == ["single-agent", "orchestration"]
        for r in resultados:
            assert r.stop_reason.startswith("infra_error:"), r.stop_reason
            resumo = json.loads((r.out_dir / "summary.json").read_text(encoding="utf-8"))
            assert resumo["lost"] is True


@mirror_available
class TestReexecucaoDeRunPerdido:
    """
    E5 item 2 / portão G5: reexecução de run perdido por erro de provedor,
    preservando a semente. Foram 3 perdas em 42 execuções no piloto.
    """

    class _Explode:
        """Levanta erro de provedor em toda chamada — o 429 real do piloto de 28/09."""

        def bind_tools(self, tools, **kwargs):
            return self

        def invoke(self, mensagens, **kwargs):
            from tests.fakes import erro_http

            raise erro_http(429)

    def _cria_run_perdido(self, tmp_path):
        """Roda de verdade um attempt=1 que morre por erro de provedor."""
        from harness.taskspec import load_task

        task = load_task(TAREFA)
        spec = build_run_spec(
            run_id="tentativa-1", arm="single-agent", task_id=task.task_id,
            statement=task.statement, base_commit=task.base_commit,
            seed_repo_id=task.seed_repo_id,
            out_dir=tmp_path / "runs" / "single-agent" / task.task_id / "rep01" / "tentativa-1",
            llm=LLM, budget=ORCAMENTO, repetition=1, attempt=1,
        )
        try:
            run_arm(spec, llm_factory=lambda *a, **k: self._Explode())
        except Exception:
            pass  # é exatamente o que se espera de um run perdido
        return tmp_path / "runs", spec

    def test_detecta_o_run_perdido_pelo_stop_reason_de_erro(self, tmp_path):
        out_dir, spec = self._cria_run_perdido(tmp_path)

        perdidos = detectar_perdidos(out_dir)

        assert len(perdidos) == 1
        p = perdidos[0]
        assert (p.task_id, p.arm, p.repetition, p.attempt) == (spec.task_id, "single-agent", 1, 1)
        assert p.motivo.startswith("infra_error:")
        assert p.run_dir == spec.out_dir
        assert p.seed == spec.llm.seed

    def test_reexecuta_com_a_mesma_semente_novo_run_id_e_attempt_2(self, tmp_path):
        out_dir, spec = self._cria_run_perdido(tmp_path)

        resultados = reexecutar_perdidos(
            out_dir, llm=LLM, budget=ORCAMENTO,
            llm_factory=fabrica_por_run(_llm_que_corrige), evaluate=False,
        )

        assert len(resultados) == 1
        novo = resultados[0]
        assert novo.attempt == 2
        assert novo.run_id != spec.run_id
        assert not novo.stop_reason.startswith(("error:", "infra_error:", "interrupted:"))

        manifesto_novo = json.loads((novo.out_dir / "manifest.json").read_text())
        assert manifesto_novo["repetition"] == spec.repetition          # mesma repetição
        assert manifesto_novo["llm"]["seed"] == spec.llm.seed           # MESMA semente
        assert manifesto_novo["attempt"] == 2

    def test_avalia_o_substituto_quando_pedido(self, tmp_path):
        out_dir, _spec = self._cria_run_perdido(tmp_path)

        resultados = reexecutar_perdidos(
            out_dir, llm=LLM, budget=ORCAMENTO,
            llm_factory=fabrica_por_run(_llm_que_corrige), evaluate=True,
        )

        assert resultados[0].resolved is True
        assert resultados[0].f2p == "1/1"

    def test_o_diretorio_perdido_fica_marcado_e_intacto(self, tmp_path):
        out_dir, spec = self._cria_run_perdido(tmp_path)

        reexecutar_perdidos(
            out_dir, llm=LLM, budget=ORCAMENTO,
            llm_factory=fabrica_por_run(_llm_que_corrige), evaluate=False,
        )

        marca = spec.out_dir / "PERDIDO"
        assert marca.exists()
        assert "substituído por" in marca.read_text()
        # nada do run perdido foi apagado
        assert (spec.out_dir / "summary.json").exists()
        assert (spec.out_dir / "manifest.json").exists()

    def test_run_perdido_ja_marcado_nao_reaparece(self, tmp_path):
        out_dir, _spec = self._cria_run_perdido(tmp_path)

        reexecutar_perdidos(
            out_dir, llm=LLM, budget=ORCAMENTO,
            llm_factory=fabrica_por_run(_llm_que_corrige), evaluate=False,
        )

        # o substituto resolveu; a varredura seguinte não acha mais nada
        assert detectar_perdidos(out_dir) == []

    def test_result_json_espurio_no_diretorio_perdido_e_neutralizado(self, tmp_path):
        """
        Se alguém rodar o avaliador manualmente sobre o diretório perdido antes
        da marca existir — o workspace materializado tem `.git`, e é só o que
        `harness.evaluate.evaluate_run` exige —, o `result.json` gerado não
        pode entrar na análise ao lado do substituto.
        """
        out_dir, spec = self._cria_run_perdido(tmp_path)
        (spec.out_dir / "result.json").write_text('{"resolved": false}', encoding="utf-8")

        reexecutar_perdidos(
            out_dir, llm=LLM, budget=ORCAMENTO,
            llm_factory=fabrica_por_run(_llm_que_corrige), evaluate=False,
        )

        assert not (spec.out_dir / "result.json").exists()
        assert (spec.out_dir / "result.json.perdido").exists()


class TestCorteDeOrcamentoNaoEhPerda:
    """Corte por orçamento é resultado do experimento — nunca reexecutado."""

    def _run_dir(self, tmp_path, *, stop_reason, com_run_end=True, com_summary=True,
                 attempt=1, lost=False) -> Path:
        run_dir = tmp_path / "runs" / "single-agent" / "t" / "rep01" / f"a{attempt}"
        run_dir.mkdir(parents=True)
        (run_dir / "manifest.json").write_text(json.dumps({
            "task_id": "t", "arm": "single-agent", "repetition": 1, "attempt": attempt,
            "llm": {"seed": 42},
        }), encoding="utf-8")
        if com_summary:
            (run_dir / "summary.json").write_text(
                json.dumps({"stop_reason": stop_reason, "lost": lost}), encoding="utf-8"
            )
        if com_run_end:
            (run_dir / "events.jsonl").write_text(
                json.dumps({"event_type": "run_end"}) + "\n", encoding="utf-8"
            )
        return run_dir

    def test_run_cortado_por_orcamento_nao_e_perdido(self, tmp_path):
        self._run_dir(tmp_path, stop_reason="budget: max_turns")
        assert detectar_perdidos(tmp_path / "runs") == []

    def test_erro_do_harness_nao_e_perdido(self, tmp_path):
        """
        `error:` sem ser de provedor é bug nosso (espelho ausente, config
        errada): reexecutar repetiria o erro. Não é perda; é conserto.
        """
        self._run_dir(tmp_path, stop_reason="error: FileNotFoundError")
        assert detectar_perdidos(tmp_path / "runs") == []

    def test_interrupcao_e_perdida(self, tmp_path):
        self._run_dir(tmp_path, stop_reason="interrupted: KeyboardInterrupt", lost=True)
        assert len(detectar_perdidos(tmp_path / "runs")) == 1

    def test_run_concluido_normalmente_nao_e_perdido(self, tmp_path):
        self._run_dir(tmp_path, stop_reason="tests_pass")
        assert detectar_perdidos(tmp_path / "runs") == []

    def test_morte_abrupta_sem_summary_json_e_perdida(self, tmp_path):
        run_dir = self._run_dir(tmp_path, stop_reason="tests_pass", com_summary=False)
        perdidos = detectar_perdidos(tmp_path / "runs")

        assert len(perdidos) == 1
        assert "morte abrupta" in perdidos[0].motivo
        assert perdidos[0].run_dir == run_dir

    def test_morte_abrupta_sem_run_end_e_perdida(self, tmp_path):
        """
        Defesa extra: `run_arm` só grava summary.json depois de emitir
        run_end, mas um processo morto exatamente entre as duas escritas
        deixaria só a trilha sem o evento — esta checagem cobre esse caso.
        """
        run_dir = self._run_dir(tmp_path, stop_reason="tests_pass", com_run_end=False)
        perdidos = detectar_perdidos(tmp_path / "runs")

        assert len(perdidos) == 1
        assert "run_end" in perdidos[0].motivo
        assert perdidos[0].run_dir == run_dir

    def test_teto_de_tentativas_declara_o_par_perdido_de_vez(self, tmp_path):
        run_dir = self._run_dir(tmp_path, stop_reason="infra_error: RateLimitError",
                                attempt=3, lost=True)

        resultados = reexecutar_perdidos(tmp_path / "runs", max_tentativas=3, llm=LLM, budget=ORCAMENTO)

        assert resultados == []  # nem tentou: já estava no teto
        marca = run_dir / "PERDIDO"
        assert marca.exists() and "esgotado" in marca.read_text()
        assert detectar_perdidos(tmp_path / "runs") == []  # não reaparece


class TestRelatorio:
    def _amostra(self) -> list[PilotOutcome]:
        return [
            PilotOutcome(arm="single-agent", repetition=1, run_id="a", out_dir=Path("/x"),
                         stop_reason="tests_pass", turns=4, tokens=1000, cost_usd=0.01,
                         resolved=True, f2p="1/1"),
            PilotOutcome(arm="orchestration", repetition=1, run_id="b", out_dir=Path("/y"),
                         stop_reason="budget_turns", turns=8, tokens=5000, cost_usd=0.05,
                         resolved=False, f2p="0/1", erro=None),
        ]

    def test_tabela_traz_os_dois_bracos_e_o_agregado(self):
        texto = format_report(self._amostra(), "tomlkit-0001")

        assert "tomlkit-0001" in texto
        assert "single-agent: 1/1 resolvidos" in texto
        assert "orchestration: 0/1 resolvidos" in texto
        assert "US$ 0.06000" not in texto  # agregado é por braço, não somado

    def test_json_do_relatorio_e_relegivel(self, tmp_path):
        destino = save_report(self._amostra(), tmp_path / "pilot.json")
        dados = json.loads(destino.read_text())

        assert [d["arm"] for d in dados] == ["single-agent", "orchestration"]
        assert dados[0]["resolved"] is True and dados[1]["resolved"] is False

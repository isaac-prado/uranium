"""
Coleta definitiva, offline: retomada, reexecução de run perdido e avaliação.

A coleta vai gastar dezenas de dólares em horas de execução. O que ela não
pode fazer é repetir run já concluído depois de uma interrupção, nem contar
um 429 como fracasso do braço.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.arms.collection import (
    Cell,
    CollectionAborted,
    inspect_cell,
    plan_cells,
    run_cell,
    run_collection,
)
from src.budget import RunBudget
from src.config import LLMConfig
from src.seeds import TOMLKIT
from tests.fakes import erro_http, fabrica_por_run
from tests.test_pilot import _llm_que_corrige

TAREFA = Path("tasks/tomlkit-0001")
LLM = LLMConfig(model="fake/modelo", provider="FakeProvider", seed=1, max_tokens=512)
ORCAMENTO = RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=8)
CELULA = Cell(task_dir=TAREFA, task_id="tomlkit-0001", arm="single-agent", repetition=1)

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


class _ProvedorFora:
    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        return self

    def invoke(self, mensagens, **kwargs):
        raise erro_http(429)


class _ChaveRevogada(_ProvedorFora):
    def invoke(self, mensagens, **kwargs):
        raise erro_http(401, "User not found")


class _CtrlC(_ProvedorFora):
    def invoke(self, mensagens, **kwargs):
        raise KeyboardInterrupt


def _nao_pode_rodar(*args, **kwargs):
    raise AssertionError("célula concluída foi executada de novo")


def _gravar_tentativa(raiz: Path, tentativa: int, **resumo) -> Path:
    destino = CELULA.attempt_dir(raiz, tentativa)
    destino.mkdir(parents=True)
    (destino / "summary.json").write_text(json.dumps(resumo), encoding="utf-8")
    return destino


class TestEstadoLidoDoDisco:
    def test_celula_sem_tentativas_esta_pendente(self, tmp_path):
        estado = inspect_cell(CELULA, tmp_path)
        assert (estado.status, estado.attempts, estado.lost_attempts) == ("pending", 0, 0)

    def test_tentativa_de_infra_e_perdida_nao_concluida(self, tmp_path):
        _gravar_tentativa(tmp_path, 1, stop_reason="infra_error: RateLimitError",
                          lost=True)
        estado = inspect_cell(CELULA, tmp_path)
        assert (estado.status, estado.lost_attempts) == ("pending", 1)

    def test_tentativa_sem_resumo_e_perdida(self, tmp_path):
        """Processo morto antes do `finally` do runner não deixou run a avaliar."""
        CELULA.attempt_dir(tmp_path, 1).mkdir(parents=True)
        assert inspect_cell(CELULA, tmp_path).lost_attempts == 1

    def test_erro_do_modelo_e_observacao_valida(self, tmp_path):
        """Só infraestrutura é perda. Erro que não é dela conta contra o braço."""
        _gravar_tentativa(tmp_path, 1, stop_reason="error: ValueError", lost=False)
        estado = inspect_cell(CELULA, tmp_path)
        assert estado.status == "done"
        assert estado.stop_reason == "error: ValueError"

    def test_concluida_depois_de_perdidas(self, tmp_path):
        _gravar_tentativa(tmp_path, 1, stop_reason="infra_error: X", lost=True)
        _gravar_tentativa(tmp_path, 2, stop_reason="tests_pass", lost=False)
        estado = inspect_cell(CELULA, tmp_path)
        assert (estado.status, estado.attempts, estado.lost_attempts) == ("done", 2, 1)
        assert estado.run_dir.endswith("attempt02")


class TestPlano:
    def test_bracos_do_mesmo_par_rodam_juntos(self):
        """Degradação do provedor no meio da coleta tem de atingir o par, não um braço."""
        celulas = plan_cells([TAREFA], repetitions=2)
        assert [(c.repetition, c.arm) for c in celulas] == [
            (1, "single-agent"), (1, "orchestration"),
            (2, "single-agent"), (2, "orchestration"),
        ]


    def test_so_um_braco_para_a_ablacao(self):
        """Ablação do refinador: só o orchestration, mesma semente por repetição."""
        celulas = plan_cells([TAREFA], repetitions=2, arms=("orchestration",))
        assert [(c.repetition, c.arm) for c in celulas] == [(1, "orchestration"), (2, "orchestration")]

    def test_braco_desconhecido_e_recusado(self):
        import pytest
        with pytest.raises(ValueError, match="braço desconhecido"):
            plan_cells([TAREFA], repetitions=1, arms=("orchestration", "x"))


class TestExecucao:
    def test_celula_concluida_nao_roda_de_novo(self, tmp_path):
        run_dir = _gravar_tentativa(tmp_path, 1, stop_reason="tests_pass", lost=False)
        (run_dir / "result.json").write_text(json.dumps({"resolved": True}), encoding="utf-8")

        estado = run_cell(CELULA, out_root=tmp_path, llm=LLM, budget=ORCAMENTO,
                          llm_factory=_nao_pode_rodar)

        assert (estado.status, estado.resolved, estado.attempts) == ("done", True, 1)

    def test_provedor_fora_esgota_tentativas_e_perde_a_celula(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        estado = run_cell(CELULA, out_root=tmp_path, llm=LLM, budget=ORCAMENTO,
                          max_attempts=2, retry_delay_s=0,
                          llm_factory=lambda *a, **k: _ProvedorFora())

        assert (estado.status, estado.attempts, estado.lost_attempts) == ("lost", 2, 2)
        for tentativa in (1, 2):
            resumo = json.loads(
                (CELULA.attempt_dir(tmp_path, tentativa) / "summary.json").read_text()
            )
            assert resumo["lost"] is True

    def test_chave_revogada_para_a_coleta_sem_gastar_tentativas(self, tmp_path, monkeypatch):
        """Em 28/09 um 401 às 10h39 teria levado cada célula a 3 tentativas perdidas."""
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        with pytest.raises(CollectionAborted, match="AuthenticationError"):
            run_cell(CELULA, out_root=tmp_path, llm=LLM, budget=ORCAMENTO,
                     max_attempts=3, retry_delay_s=0,
                     llm_factory=lambda *a, **k: _ChaveRevogada())

        estado = inspect_cell(CELULA, tmp_path)
        assert (estado.status, estado.attempts, estado.lost_attempts) == ("pending", 1, 1)

    def test_celula_perdida_volta_a_ser_tentada_ao_retomar(self, tmp_path, monkeypatch):
        """`max_attempts` é por execução: resolvida a causa, a célula tem nova chance."""
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        kwargs = dict(out_root=tmp_path, llm=LLM, budget=ORCAMENTO, max_attempts=1,
                      retry_delay_s=0, llm_factory=lambda *a, **k: _ProvedorFora())

        assert run_cell(CELULA, **kwargs).attempts == 1
        segunda = run_cell(CELULA, **kwargs)

        assert (segunda.status, segunda.attempts) == ("lost", 2)

    def test_celulas_perdidas_em_sequencia_param_a_coleta(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        celulas = plan_cells([TAREFA], repetitions=2)
        vistas = []

        with pytest.raises(CollectionAborted, match="2 células perdidas"):
            run_collection(celulas, out_root=tmp_path, max_consecutive_lost=2,
                           on_done=vistas.append, llm=LLM, budget=ORCAMENTO,
                           max_attempts=1, retry_delay_s=0,
                           llm_factory=lambda *a, **k: _ProvedorFora())

        assert len(vistas) == 2  # as outras duas células nem começaram

    def test_ctrl_c_no_meio_do_run_e_perda_nao_fracasso(self, tmp_path, monkeypatch):
        """
        Interromper e retomar é o fluxo documentado da coleta.

        Antes, o `finally` do runner gravava o run interrompido com
        `stop_reason: error`, e ao retomar ele valia como fracasso do braço.
        """
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")

        with pytest.raises(KeyboardInterrupt):
            run_cell(CELULA, out_root=tmp_path, llm=LLM, budget=ORCAMENTO,
                     llm_factory=lambda *a, **k: _CtrlC())

        resumo = json.loads((CELULA.attempt_dir(tmp_path, 1) / "summary.json").read_text())
        assert resumo["stop_reason"] == "interrupted: KeyboardInterrupt"
        assert resumo["lost"] is True
        estado = inspect_cell(CELULA, tmp_path)
        assert (estado.status, estado.lost_attempts) == ("pending", 1)

    @mirror_available
    def test_reexecuta_perdida_e_avalia_a_que_concluiu(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SEMANTIC_REVIEW", "false")
        _gravar_tentativa(tmp_path, 1, stop_reason="infra_error: RateLimitError",
                          lost=True)

        estado = run_cell(CELULA, out_root=tmp_path, llm=LLM, budget=ORCAMENTO,
                          retry_delay_s=0, measure_quality=False,
                          llm_factory=fabrica_por_run(_llm_que_corrige))

        assert (estado.status, estado.attempts, estado.lost_attempts) == ("done", 2, 1)
        assert estado.resolved is True, estado.evaluation_error
        resultado = json.loads((Path(estado.run_dir) / "result.json").read_text())
        assert resultado["run_id"] == "tomlkit-0001-single-agent-r01-a02"
        # a tentativa perdida continua gravada como evidência
        assert (CELULA.attempt_dir(tmp_path, 1) / "summary.json").exists()

"""
Análise pareada: os testes exatos e a leitura da coleta do disco.

Os valores esperados são os de tabela (e os do scipy, conferidos à parte),
não os que o próprio código produz.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.analysis import analyze, format_analysis, load_collection, sign_test, wilcoxon


class TestTesteDeSinal:
    def test_quatro_tarefas_nao_alcancam_p_005(self):
        """O limite declarado no dossiê: com 4 tarefas, o menor p é 0,0625."""
        assert sign_test([1, 1, 1, 1])["p_one_sided"] == pytest.approx(0.0625)

    def test_oito_tarefas_toleram_uma_discordante(self):
        r = sign_test([1] * 7 + [-1])
        assert r["p_one_sided"] == pytest.approx(9 / 256)
        assert r["p_one_sided"] < 0.05

    def test_empates_saem_do_n(self):
        r = sign_test([1, 0, 0, 1, -1])
        assert (r["n"], r["positive"], r["negative"]) == (3, 2, 1)

    def test_sem_diferencas_nao_rejeita(self):
        assert sign_test([0, 0])["p_one_sided"] == 1.0


class TestWilcoxon:
    def test_todas_positivas(self):
        r = wilcoxon([1, 2, 3, 4, 5])
        assert r["w_plus"] == 15
        assert r["p_one_sided"] == pytest.approx(1 / 32)
        assert r["p_two_sided"] == pytest.approx(2 / 32)

    def test_uma_negativa(self):
        # scipy.stats.wilcoxon([1,-2,3,4,5], alternative="greater").pvalue == 0.09375
        r = wilcoxon([1, -2, 3, 4, 5])
        assert r["w_plus"] == 13
        assert r["p_one_sided"] == pytest.approx(0.09375)

    def test_empates_recebem_posto_medio(self):
        r = wilcoxon([0.5, 0.5, -0.5])
        assert r["w_plus"] == 4  # postos 2, 2, 2
        assert r["p_one_sided"] == pytest.approx(4 / 8)


def _celula(raiz: Path, tarefa: str, braco: str, rep: int, tentativa: int = 1, *,
            resolved: bool | None = True, infra: bool = False, custo: float = 0.01,
            turnos: int = 10, stop: str = "tests_pass") -> None:
    destino = raiz / tarefa / braco / f"rep{rep:02d}" / f"attempt{tentativa:02d}"
    destino.mkdir(parents=True)
    (destino / "summary.json").write_text(json.dumps({"lost": infra}))
    if resolved is not None and not infra:
        (destino / "result.json").write_text(json.dumps({
            "resolved": resolved, "resolved_blocked_by_cheat": False,
            "cost": {"cost_usd": custo, "tokens_total": 1000, "wall_seconds": 60},
            "process": {"turns": turnos, "stop_reason": stop},
        }))


class TestLeituraDaColeta:
    def test_taxa_por_tarefa_e_diferenca(self, tmp_path):
        for rep in (1, 2):
            _celula(tmp_path, "t1", "single-agent", rep, resolved=rep == 1)
            _celula(tmp_path, "t1", "orchestration", rep, resolved=True)

        a = analyze(load_collection(tmp_path))

        (linha,) = a["per_task"]
        assert linha["single-agent"]["resolve_rate"] == 0.5
        assert linha["orchestration"]["resolve_rate"] == 1.0
        assert linha["diff_resolve_rate"] == 0.5
        assert a["primary"]["sign_test"]["positive"] == 1

    def test_par_perdido_sai_inteiro(self, tmp_path):
        """Tirar só o lado perdido desfaria o pareamento da repetição."""
        _celula(tmp_path, "t1", "single-agent", 1, resolved=False)
        _celula(tmp_path, "t1", "orchestration", 1, resolved=False)
        _celula(tmp_path, "t1", "single-agent", 2, resolved=True)
        _celula(tmp_path, "t1", "orchestration", 2, infra=True)

        a = analyze(load_collection(tmp_path))

        (linha,) = a["per_task"]
        assert linha["pairs"] == 1
        assert linha["single-agent"]["resolve_rate"] == 0.0
        assert a["lost_cells"] == [["t1", "orchestration", 2]]
        assert a["lost_attempts"] == 1
        assert a["by_arm"]["orchestration"]["lost_attempts"] == 1
        assert a["by_arm"]["orchestration"]["lost_cells"] == 1
        assert a["by_arm"]["single-agent"]["lost_attempts"] == 0

    def test_vale_a_primeira_tentativa_nao_perdida(self, tmp_path):
        _celula(tmp_path, "t1", "single-agent", 1, 1, infra=True)
        _celula(tmp_path, "t1", "single-agent", 1, 2, resolved=True, custo=0.5)
        _celula(tmp_path, "t1", "orchestration", 1, resolved=False)

        a = analyze(load_collection(tmp_path))

        (linha,) = a["per_task"]
        assert linha["single-agent"]["cost_usd"] == 0.5
        assert a["lost_attempts"] == 1
        assert a["lost_cells"] == []

    def test_estouro_de_orcamento_e_censura_declarada(self, tmp_path):
        _celula(tmp_path, "t1", "single-agent", 1, resolved=False, stop="budget: max_turns")
        _celula(tmp_path, "t1", "orchestration", 1, resolved=True)

        (linha,) = analyze(load_collection(tmp_path))["per_task"]

        assert linha["single-agent"]["censored"] == 1
        assert linha["orchestration"]["censored"] == 0

    def test_perda_e_censura_saem_por_braco_no_texto(self, tmp_path):
        _celula(tmp_path, "t1", "single-agent", 1, resolved=False, stop="budget: max_turns")
        _celula(tmp_path, "t1", "orchestration", 1, 1, infra=True)
        _celula(tmp_path, "t1", "orchestration", 1, 2, resolved=True)

        texto = format_analysis(analyze(load_collection(tmp_path)))

        assert "single-agent   0 tentativa(s) e 0 célula(s) perdida(s), 1 de 1" in texto
        assert "orchestration  1 tentativa(s) e 0 célula(s) perdida(s), 0 de 1" in texto

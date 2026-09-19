"""
Análise pareada dos `result.json`: testes exatos sem scipy, portões de
admissão, agregação por tarefa, censura e as sete métricas.

Os testes estatísticos são conferidos contra valores fechados calculados à
mão (binomial e enumeração dos 2^n sinais), não contra outra biblioteca:
não há scipy nas dependências e o ponto do exercício é justamente esse.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from itertools import product
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from harness import RESULT_SCHEMA_VERSION

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "analyze_results", RAIZ / "scripts" / "analyze_results.py"
)
ar = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules["analyze_results"] = ar   # dataclasses resolvem anotações pelo módulo registrado
_spec.loader.exec_module(ar)

RESULT_SCHEMA = json.loads(
    (RAIZ / "harness" / "schema" / "result.schema.json").read_text(encoding="utf-8")
)
EVENT_SCHEMA = json.loads(
    (RAIZ / "harness" / "schema" / "event.schema.json").read_text(encoding="utf-8")
)


# =====================================================================
# Teste de sinal
# =====================================================================


class TestTesteDeSinal:
    def test_oito_de_oito_na_mesma_direcao(self):
        """p = 2·(1/2)^8 = 0,0078125 — o menor p que 8 pares podem dar."""
        t = ar.teste_sinal([1.0] * 8)
        assert t.n == 8
        assert t.n_empates == 0
        assert t.estatistica == 8
        assert t.p == pytest.approx(0.0078125)

    def test_seis_de_oito(self):
        """p = 2·(C(8,0)+C(8,1)+C(8,2))/2^8 = 2·37/256 = 0,2890625."""
        t = ar.teste_sinal([1.0] * 6 + [-1.0] * 2)
        assert t.n == 8
        assert t.estatistica == 6
        assert t.p == pytest.approx(0.2890625)

    def test_simetrico_no_sinal(self):
        assert ar.teste_sinal([1.0] * 6 + [-1.0] * 2).p == ar.teste_sinal([-1.0] * 6 + [1.0] * 2).p

    def test_empates_saem_da_conta_e_sao_reportados(self):
        t = ar.teste_sinal([1.0] * 8 + [0.0, 0.0, 0.0, 0.0])
        assert t.n == 8 and t.n_empates == 4
        assert t.p == pytest.approx(0.0078125)
        assert t.mediana_diferencas == pytest.approx(1.0)   # mediana de TODAS as diferenças

    def test_metade_e_metade_nao_rejeita(self):
        """n = 2, um para cada lado: p = 2·(C(2,0)+C(2,1))/4 = 1,5, limitado a 1."""
        assert ar.teste_sinal([1.0, -1.0]).p == pytest.approx(1.0)

    def test_n_zero_nao_quebra(self):
        t = ar.teste_sinal([])
        assert t.n == 0 and t.p is None and t.estatistica is None and t.mediana_diferencas is None

    def test_so_empates_nao_quebra(self):
        t = ar.teste_sinal([0.0, 0.0, 0.0])
        assert t.n == 0 and t.n_empates == 3 and t.p is None

    def test_n_um_da_p_um(self):
        t = ar.teste_sinal([2.5])
        assert t.n == 1 and t.p == pytest.approx(1.0)


# =====================================================================
# Postos e Wilcoxon
# =====================================================================


class TestPostosMedios:
    def test_sem_empate(self):
        assert ar.postos_medios([3.0, 1.0, 2.0]) == [3.0, 1.0, 2.0]

    def test_com_empate_usa_posto_medio(self):
        # |d| = 1, 1, 2, 3 → postos 1,5; 1,5; 3; 4
        assert ar.postos_medios([1.0, 1.0, 2.0, 3.0]) == [1.5, 1.5, 3.0, 4.0]

    def test_grupo_de_tres_empatados(self):
        postos = ar.postos_medios([5.0, 5.0, 5.0, 9.0])
        assert postos == [2.0, 2.0, 2.0, 4.0]
        assert sum(postos) == 4 * 5 / 2


def _p_bilateral_por_forca_bruta(postos: list[float], sinais: list[int]) -> float:
    """
    Enumeração independente da do script, escrita de outro jeito: percorre
    os 2^n subconjuntos de postos, soma cada um e conta os que se afastam da
    média tanto quanto o observado.
    """
    total = sum(postos)
    alvo = total / 2
    observado = sum(p for p, s in zip(postos, sinais) if s > 0)
    desvio = abs(observado - alvo)
    extremos = sum(
        1 for combo in product((0, 1), repeat=len(postos))
        if abs(sum(p for p, b in zip(postos, combo) if b) - alvo) >= desvio - 1e-9
    )
    return extremos / 2 ** len(postos)


class TestWilcoxon:
    def test_n_seis_todas_positivas(self):
        """Só duas das 64 atribuições são tão extremas: p = 2/64 = 0,03125."""
        t = ar.wilcoxon([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert t.n == 6 and t.n_empates == 0
        assert t.estatistica == 0.0            # W = min(W+, W−) = min(21, 0)
        assert t.p == pytest.approx(2 / 64)

    def test_direcao_nao_muda_o_p_bilateral(self):
        assert ar.wilcoxon([-1.0, -2.0, -3.0, -4.0, -5.0, -6.0]).p == pytest.approx(2 / 64)

    def test_zero_e_descartado_e_o_n_cai(self):
        """
        Sete diferenças, uma nula: o teste vira o de n = 6 acima. A diferença
        zero não é 'meio voto', é ausência de informação sobre a direção.
        """
        t = ar.wilcoxon([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.0])
        assert t.n == 6 and t.n_empates == 1
        assert t.p == pytest.approx(2 / 64)
        assert t.mediana_diferencas == pytest.approx(3.0)   # mediana de todas as sete

    def test_empate_de_postos_bate_com_enumeracao_manual(self):
        """
        d = [1, 1, −2, 3] → |d| = [1, 1, 2, 3], postos 1,5; 1,5; 3; 4.
        W+ = 1,5 + 1,5 + 4 = 7; total 10; média 5; desvio 2. Das 16
        atribuições, 10 têm desvio ≥ 2 (somas 0; 1,5; 1,5; 3; 3; 7; 7; 8,5;
        8,5; 10), logo p = 10/16 = 0,625.
        """
        difs = [1.0, 1.0, -2.0, 3.0]
        t = ar.wilcoxon(difs)
        assert t.n == 4
        assert t.estatistica == pytest.approx(3.0)          # min(7, 3)
        assert t.p == pytest.approx(0.625)
        assert t.p == pytest.approx(
            _p_bilateral_por_forca_bruta([1.5, 1.5, 3.0, 4.0], [1, 1, -1, 1])
        )

    def test_empate_de_postos_em_caso_extremo(self):
        difs = [2.0, 2.0, 2.0, 5.0, 9.0]
        t = ar.wilcoxon(difs)
        assert t.p == pytest.approx(2 / 32)
        assert t.p == pytest.approx(
            _p_bilateral_por_forca_bruta(ar.postos_medios([2.0, 2.0, 2.0, 5.0, 9.0]), [1] * 5)
        )

    def test_n_zero_nao_quebra(self):
        t = ar.wilcoxon([])
        assert t.n == 0 and t.p is None and t.estatistica is None

    def test_so_zeros_nao_quebra(self):
        t = ar.wilcoxon([0.0, 0.0])
        assert t.n == 0 and t.n_empates == 2 and t.p is None

    def test_n_um_da_p_um(self):
        t = ar.wilcoxon([7.0])
        assert t.n == 1 and t.p == pytest.approx(1.0) and t.estatistica == 0.0

    def test_n_grande_demais_para_enumerar_avisa(self):
        with pytest.raises(ValueError, match="enumeração exata"):
            ar.wilcoxon([float(i + 1) for i in range(ar.MAX_N_ENUMERACAO + 1)])

    def test_doze_pares_ainda_e_barato(self):
        """O desenho tem 12 tarefas; 2^12 = 4096 atribuições."""
        t = ar.wilcoxon([float(i + 1) for i in range(12)])
        assert t.n == 12 and t.p == pytest.approx(2 / 4096)


# =====================================================================
# Fixtures de runs sintéticos, no formato real do result.json
# =====================================================================


def _pytest_result(isolado: bool = True, verde: bool = True) -> dict:
    return {
        "exit_code": 0 if verde else 1,
        "passed": 10 if verde else 9, "failed": 0 if verde else 1,
        "errors": 0, "skipped": 0, "duration_s": 1.5,
        "failing_node_ids": [] if verde else ["tests/test_x.py::test_y"],
        "timed_out": False, "network_isolated": isolado,
    }


def resultado(
    task_id: str, arm: str, rep: int, *,
    resolved: bool = True, tokens: int = 100_000, wall: float = 60.0,
    cc_delta: float | None = 0.1, cost_usd: float = 0.01, llm_calls: int = 10,
    stop_reason: str = "done", provider_servido: str = "DeepInfra",
    criticos: int = 0, bloqueado: bool = False, denials: int = 0,
    isolado: bool = True, faixa: str | None = None,
) -> dict:
    """Um result.json completo, no formato de `harness/evaluate.py`."""
    dados = {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "harness_version": "1.0.0",
        "evaluated_at": "2026-09-19T10:00:00+00:00",
        "run_id": f"{arm}-{task_id}-r{rep:02d}",
        "arm": arm, "task_id": task_id, "repetition": rep,
        "base_commit": "0" * 40,
        "resolved": resolved,
        "resolved_blocked_by_cheat": bloqueado,
        "oracle": {
            "f2p_total": 1, "f2p_passed": 1 if resolved else 0,
            "f2p": _pytest_result(isolado, resolved),
            "p2p": _pytest_result(isolado, True),
            "regression": _pytest_result(isolado, True),
        },
        "cheat": {
            "clean": criticos == 0, "critical_count": criticos, "warning_count": 0,
            "signals": [],
        },
        "quality": {
            "mi_before": 0.0, "mi_after": 0.0, "mi_delta": 0.0,
            "cc_mean_before": 5.0,
            "cc_mean_after": None if cc_delta is None else 5.0 + cc_delta,
            "cc_mean_delta": cc_delta, "files_analyzed": 1, "error": None,
        },
        "cost": {
            "tokens_prompt": tokens - 1000, "tokens_completion": 1000,
            "tokens_reasoning": 0, "tokens_total": tokens,
            "cost_usd": cost_usd, "llm_calls": llm_calls, "tool_calls": llm_calls,
            "wall_seconds": wall,
        },
        "process": {
            "turns": 10, "test_runs": 1, "tool_denials": denials, "errors": 0,
            "circuit_breaks": 0, "self_recoveries": 0, "stop_reason": stop_reason,
        },
        "provenance": {
            "model": "qwen/qwen3-coder", "provider_requested": "DeepInfra",
            "providers_served": [provider_servido], "llm_seed": 20260821,
            "topology": "single_agent" if arm == "single-agent" else "multi_agent_roles",
        },
        "diff": {"files_changed": 1, "insertions": 5, "deletions": 1,
                 "changed_files": ["pkg/mod.py"]},
        # O avaliador sempre grava o campo, com null quando a tarefa não declara.
        "faixa": faixa,
    }
    return dados


def evento(run_id: str, arm: str, task_id: str, seq: int, tipo: str) -> dict:
    """Uma linha de events.jsonl com todos os campos obrigatórios do envelope."""
    return {
        "schema_version": 1, "run_id": run_id, "arm": arm, "task_id": task_id,
        "seq": seq, "ts": "2026-09-19T10:00:00+00:00", "elapsed_ms": seq * 100,
        "event_type": tipo, "node": None, "agent_role": None, "turn": None,
        "model": None, "provider_requested": None, "provider_served": None,
        "tokens_prompt": 0, "tokens_completion": 0, "tokens_reasoning": 0,
        "tokens_total": 0, "cost_usd": 0.0, "latency_ms": 0,
        "tool_name": None, "tool_args_hash": None, "tool_denied": False,
        "tool_exit_code": None, "payload": {},
    }


def gravar_run(raiz: Path, dados: dict, *, eventos: list[dict] | None = None) -> Path:
    destino = raiz / dados["arm"] / dados["task_id"] / f"rep{dados['repetition']:02d}" / dados["run_id"]
    destino.mkdir(parents=True)
    (destino / "result.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    if eventos is not None:
        (destino / "events.jsonl").write_text(
            "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in eventos), encoding="utf-8")
    return destino


def test_os_result_json_sinteticos_valem_sob_o_schema_real():
    """
    Garante que as fixtures destes testes são do formato que o avaliador
    grava de verdade; sem isso, testar o leitor não prova nada.
    """
    validador = Draft202012Validator(RESULT_SCHEMA)
    validador.validate(resultado("t", "single-agent", 1))
    validador.validate(resultado("t", "orchestration", 2, resolved=False, cc_delta=None))


def test_os_eventos_sinteticos_valem_sob_o_schema_real():
    Draft202012Validator(EVENT_SCHEMA).validate(evento("r", "single-agent", "t", 1, "run_end"))


# =====================================================================
# Portões de admissão
# =====================================================================


class TestAdmissao:
    def test_run_limpo_e_admitido(self, tmp_path):
        gravar_run(tmp_path, resultado("t1", "single-agent", 1))
        runs = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert len(runs) == 1 and runs[0].admitido

    def test_provedor_divergente_reprova_com_motivo(self, tmp_path):
        gravar_run(tmp_path, resultado("t1", "single-agent", 1, provider_servido="Novita"))
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert not run.admitido
        assert "provedor divergente" in run.motivos[0]
        assert "'Novita'" in run.motivos[0]

    def test_avaliacao_sem_rede_isolada_reprova(self, tmp_path):
        gravar_run(tmp_path, resultado("t1", "single-agent", 1, isolado=False))
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert not run.admitido
        assert any("rede isolada" in m for m in run.motivos)

    def test_trilha_valida_com_um_run_end_e_admitida(self, tmp_path):
        dados = resultado("t1", "single-agent", 1)
        rid = dados["run_id"]
        gravar_run(tmp_path, dados, eventos=[
            evento(rid, "single-agent", "t1", 1, "run_start"),
            evento(rid, "single-agent", "t1", 2, "llm_call"),
            evento(rid, "single-agent", "t1", 3, "run_end"),
        ])
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert run.admitido, run.motivos

    def test_dois_run_end_reprovam(self, tmp_path):
        dados = resultado("t1", "single-agent", 1)
        rid = dados["run_id"]
        gravar_run(tmp_path, dados, eventos=[
            evento(rid, "single-agent", "t1", 1, "run_end"),
            evento(rid, "single-agent", "t1", 2, "run_end"),
        ])
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert not run.admitido
        assert any("2 evento(s) run_end" in m for m in run.motivos)

    def test_trilha_fora_do_esquema_reprova(self, tmp_path):
        dados = resultado("t1", "single-agent", 1)
        rid = dados["run_id"]
        torto = evento(rid, "single-agent", "t1", 1, "run_end")
        torto["arm"] = "braço-inventado"
        gravar_run(tmp_path, dados, eventos=[torto])
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert not run.admitido
        assert any("não valida contra o esquema" in m for m in run.motivos)

    def test_linha_nao_json_reprova(self, tmp_path):
        dados = resultado("t1", "single-agent", 1)
        destino = gravar_run(tmp_path, dados, eventos=[
            evento(dados["run_id"], "single-agent", "t1", 1, "run_end")])
        with (destino / "events.jsonl").open("a", encoding="utf-8") as fh:
            fh.write("isto não é json\n")
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert not run.admitido
        assert any("não-JSON" in m for m in run.motivos)

    def test_sem_events_jsonl_o_portao_tres_nao_se_aplica(self, tmp_path):
        gravar_run(tmp_path, resultado("t1", "single-agent", 1))
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert run.admitido

    def test_run_nao_admitido_sai_da_agregacao(self, tmp_path):
        gravar_run(tmp_path, resultado("t1", "single-agent", 1))
        gravar_run(tmp_path, resultado("t1", "single-agent", 2, provider_servido="Novita"))
        celulas = ar.agregar(ar.carregar_runs([tmp_path], tmp_path / "tasks"))
        assert celulas[("t1", "single-agent")].n_reps == 1


# =====================================================================
# Faixa
# =====================================================================


class TestFaixa:
    def test_le_do_result_json_quando_existe(self, tmp_path):
        gravar_run(tmp_path, resultado("t1", "single-agent", 1, faixa="grande"))
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert run.faixa == "grande"

    def test_cai_para_o_task_json(self, tmp_path):
        tasks = tmp_path / "tasks" / "t1"
        tasks.mkdir(parents=True)
        (tasks / "task.json").write_text(json.dumps({"id": "t1", "faixa": "media"}), encoding="utf-8")
        gravar_run(tmp_path / "runs", resultado("t1", "single-agent", 1))
        (run,) = ar.carregar_runs([tmp_path / "runs"], tmp_path / "tasks")
        assert run.faixa == "media"

    def test_sem_nenhum_dos_dois_fica_interrogacao(self, tmp_path):
        gravar_run(tmp_path, resultado("t1", "single-agent", 1))
        (run,) = ar.carregar_runs([tmp_path], tmp_path / "tasks")
        assert run.faixa == "?"

    def test_faixa_nula_no_result_json_nao_atropela_o_task_json(self, tmp_path):
        """`evaluate.py` grava `faixa: null` quando a tarefa não declara."""
        tasks = tmp_path / "tasks" / "t1"
        tasks.mkdir(parents=True)
        (tasks / "task.json").write_text(json.dumps({"id": "t1", "faixa": "pequena"}), encoding="utf-8")
        dados = resultado("t1", "single-agent", 1)
        dados["faixa"] = None
        gravar_run(tmp_path / "runs", dados)
        (run,) = ar.carregar_runs([tmp_path / "runs"], tmp_path / "tasks")
        assert run.faixa == "pequena"


# =====================================================================
# Agregação por tarefa
# =====================================================================


class TestAgregacao:
    def test_mediana_das_repeticoes(self, tmp_path):
        for rep, tk in ((1, 100), (2, 300), (3, 200)):
            gravar_run(tmp_path, resultado("t1", "single-agent", rep, tokens=tk))
        celula = ar.agregar(ar.carregar_runs([tmp_path], tmp_path / "tasks"))[("t1", "single-agent")]
        assert celula.valores["cost.tokens_total"] == 200

    def test_resolvida_e_maioria_das_repeticoes(self, tmp_path):
        for rep, ok in ((1, True), (2, False), (3, True)):
            gravar_run(tmp_path, resultado("t1", "single-agent", rep, resolved=ok))
        celula = ar.agregar(ar.carregar_runs([tmp_path], tmp_path / "tasks"))[("t1", "single-agent")]
        assert celula.resolvidas == 2
        assert celula.fracao_resolvida == pytest.approx(2 / 3)
        assert celula.resolvida is True

    def test_uma_de_tres_nao_e_maioria(self, tmp_path):
        for rep, ok in ((1, True), (2, False), (3, False)):
            gravar_run(tmp_path, resultado("t1", "single-agent", rep, resolved=ok))
        celula = ar.agregar(ar.carregar_runs([tmp_path], tmp_path / "tasks"))[("t1", "single-agent")]
        assert celula.resolvida is False
        assert celula.fracao_resolvida == pytest.approx(1 / 3)

    def test_cc_ausente_em_uma_repeticao_nao_apaga_a_mediana(self, tmp_path):
        for rep, cc in ((1, 0.2), (2, None), (3, 0.4)):
            gravar_run(tmp_path, resultado("t1", "single-agent", rep, cc_delta=cc))
        celula = ar.agregar(ar.carregar_runs([tmp_path], tmp_path / "tasks"))[("t1", "single-agent")]
        assert celula.valores["quality.cc_mean_delta"] == pytest.approx(0.3)

    def test_cc_ausente_em_todas_vira_none(self, tmp_path):
        for rep in (1, 2, 3):
            gravar_run(tmp_path, resultado("t1", "single-agent", rep, cc_delta=None))
        celula = ar.agregar(ar.carregar_runs([tmp_path], tmp_path / "tasks"))[("t1", "single-agent")]
        assert celula.valores["quality.cc_mean_delta"] is None


# =====================================================================
# Ponta a ponta
# =====================================================================


@pytest.fixture
def estudo(tmp_path) -> dict:
    """
    Duas tarefas completas (2 braços × 3 repetições), mais uma terceira
    tarefa com o par quebrado por provedor divergente.

      t1: single-agent resolve 3/3; orchestration resolve 2/3  → par válido
      t2: single-agent resolve 0/3; orchestration resolve 1/3  → censurada
      t3: single-agent admitido; orchestration reprovado no portão 1
    """
    runs = tmp_path / "runs"
    tasks = tmp_path / "tasks"
    (tasks / "t1").mkdir(parents=True)
    (tasks / "t1" / "task.json").write_text(
        json.dumps({"id": "t1", "faixa": "pequena"}), encoding="utf-8")
    # t2 sem task.json: a faixa tem de sair como "?" em vez de ser inventada.

    # --- t1 -----------------------------------------------------------
    for rep, tk, wall in ((1, 100_000, 50.0), (2, 120_000, 60.0), (3, 110_000, 70.0)):
        gravar_run(runs, resultado("t1", "single-agent", rep, resolved=True,
                                   tokens=tk, wall=wall, cc_delta=0.1,
                                   cost_usd=0.01, llm_calls=10))
    for rep, ok, tk, wall in ((1, True, 200_000, 90.0), (2, False, 240_000, 100.0),
                              (3, True, 220_000, 110.0)):
        gravar_run(runs, resultado("t1", "orchestration", rep, resolved=ok,
                                   tokens=tk, wall=wall, cc_delta=0.3,
                                   cost_usd=0.02, llm_calls=25,
                                   stop_reason="done" if ok else "budget: max_turns (40 >= 40)"))

    # --- t2 -----------------------------------------------------------
    for rep in (1, 2, 3):
        gravar_run(runs, resultado("t2", "single-agent", rep, resolved=False,
                                   tokens=400_000, wall=300.0, cc_delta=0.0,
                                   stop_reason="budget: max_tokens", denials=1))
    for rep, ok in ((1, True), (2, False), (3, False)):
        gravar_run(runs, resultado("t2", "orchestration", rep, resolved=ok,
                                   tokens=500_000, wall=320.0, cc_delta=0.5,
                                   stop_reason="done" if ok else "budget: max_wall_seconds",
                                   criticos=0 if ok else 1, bloqueado=not ok, denials=2))

    # --- t3: par quebrado --------------------------------------------
    gravar_run(runs, resultado("t3", "single-agent", 1, resolved=True, faixa="grande"))
    gravar_run(runs, resultado("t3", "orchestration", 1, resolved=True, faixa="grande",
                               provider_servido="Novita"))

    return ar.analisar([runs], tasks)


class TestPontaAPonta:
    def test_admissao(self, estudo):
        assert estudo["runs_encontrados"] == 14
        assert estudo["runs_admitidos"] == 13
        (fora,) = estudo["nao_admitidos"]
        assert fora["task_id"] == "t3" and fora["arm"] == "orchestration"
        assert "provedor divergente" in fora["motivos"][0]

    def test_par_quebrado_e_reportado(self, estudo):
        (quebrado,) = estudo["pares_quebrados"]
        assert quebrado["task_id"] == "t3" and quebrado["repetition"] == 1
        assert quebrado["single-agent"] == "admitido"
        assert quebrado["orchestration"] == "não admitido"

    def test_faixa_ao_lado_de_cada_par(self, estudo):
        faixas = {(c["task_id"], c["arm"]): c["faixa"] for c in estudo["celulas"]}
        assert faixas[("t1", "single-agent")] == "pequena"     # veio do task.json
        assert faixas[("t2", "single-agent")] == "?"           # não existe em lugar nenhum
        assert faixas[("t3", "single-agent")] == "grande"      # veio do result.json
        por_tarefa = {d["task_id"]: d["faixa"]
                      for d in estudo["metricas"]["1_efetividade"]["por_tarefa"]}
        assert por_tarefa == {"t1": "pequena", "t2": "?"}

    def test_1_taxa_de_resolucao(self, estudo):
        m = estudo["metricas"]["1_efetividade"]
        assert m["por_braco"]["single-agent"]["tarefas_resolvidas"] == 2      # t1 e t3
        assert m["por_braco"]["orchestration"]["tarefas_resolvidas"] == 1     # só t1
        assert m["por_braco"]["single-agent"]["execucoes_resolvidas"] == 4
        assert m["por_braco"]["orchestration"]["execucoes_resolvidas"] == 3
        # Pares: t1 (1 → 2/3, negativo) e t2 (0 → 1/3, positivo). t3 não pareia.
        t = m["teste"]
        assert t["nome"] == "sinal exato bilateral"
        assert t["n"] == 2 and t["n_empates"] == 0
        # um par para cada lado: p exato = 1 (nenhuma evidência de direção)
        assert t["p"] == pytest.approx(1.0)

    def test_2_custo_censura_so_as_resolvidas_por_ambos(self, estudo):
        m = estudo["metricas"]["2_custo"]
        assert m["campo"] == "cost.tokens_total"
        assert m["tarefas_usadas"] == ["t1"]
        excluidas = {x["task_id"]: x["motivo"] for x in m["tarefas_excluidas"]}
        assert excluidas["t2"] == "não resolvida por single-agent e orchestration"
        assert excluidas["t3"] == "sem dado admitido no braço orchestration"
        # medianas das repetições: single 110 000; orchestration 220 000
        assert m["por_braco"]["single-agent"]["mediana_das_tarefas_usadas"] == 110_000
        assert m["por_braco"]["orchestration"]["mediana_das_tarefas_usadas"] == 220_000
        assert m["por_tarefa"][0]["diferenca"] == 110_000
        assert m["teste"]["n"] == 1 and m["teste"]["p"] == pytest.approx(1.0)
        assert m["acompanham"]["cost.cost_usd"]["orchestration"] == pytest.approx(0.02)
        assert m["acompanham"]["cost.llm_calls"]["single-agent"] == 10

    def test_3_tempo_usa_a_mesma_censura(self, estudo):
        m = estudo["metricas"]["3_tempo"]
        assert m["campo"] == "cost.wall_seconds"
        assert m["tarefas_usadas"] == estudo["metricas"]["2_custo"]["tarefas_usadas"]
        assert m["por_braco"]["single-agent"]["mediana_das_tarefas_usadas"] == 60.0
        assert m["por_braco"]["orchestration"]["mediana_das_tarefas_usadas"] == 100.0

    def test_4_consistencia(self, estudo):
        m = estudo["metricas"]["4_consistencia"]["por_braco"]
        # single-agent: t1 e t3 resolvidas ao menos uma vez, ambas em todas as repetições
        assert m["single-agent"]["tarefas_resolvidas_ao_menos_uma_vez"] == 2
        assert m["single-agent"]["tarefas_resolvidas_em_todas_as_repeticoes"] == 2
        assert m["single-agent"]["proporcao"] == pytest.approx(1.0)
        # orchestration: t1 (2/3) e t2 (1/3) ao menos uma vez, nenhuma sempre
        assert m["orchestration"]["tarefas_resolvidas_ao_menos_uma_vez"] == 2
        assert m["orchestration"]["tarefas_resolvidas_em_todas_as_repeticoes"] == 0
        assert m["orchestration"]["proporcao"] == pytest.approx(0.0)

    def test_5_qualidade_nao_censura_por_resolucao(self, estudo):
        m = estudo["metricas"]["5_qualidade"]
        assert m["campo"] == "quality.cc_mean_delta"
        assert m["censura"] == "ambos_com_valor"
        assert m["tarefas_usadas"] == ["t1", "t2"]
        assert m["teste"]["n"] == 2

    def test_6_autonomia(self, estudo):
        m = estudo["metricas"]["6_autonomia"]["por_braco"]
        # single-agent: 7 execuções admitidas (3 em t1, 3 em t2, 1 em t3); as 3 de t2 por corte
        assert m["single-agent"]["execucoes"] == 7
        assert m["single-agent"]["encerradas_por_corte"] == 3
        assert m["single-agent"]["proporcao_sem_corte"] == pytest.approx(4 / 7)
        # orchestration: 6 admitidas; t1 rep2 e t2 rep2/rep3 por corte
        assert m["orchestration"]["execucoes"] == 6
        assert m["orchestration"]["encerradas_por_corte"] == 3
        assert m["orchestration"]["motivos_de_corte"] == [
            "budget: max_turns (40 >= 40)", "budget: max_wall_seconds"]

    def test_7_integridade(self, estudo):
        m = estudo["metricas"]["7_integridade"]["por_braco"]
        assert m["single-agent"]["cheat_critical_count"] == 0
        assert m["single-agent"]["resolved_blocked_by_cheat"] == 0
        assert m["single-agent"]["tool_denials"] == 3        # 1 por repetição de t2
        assert m["orchestration"]["cheat_critical_count"] == 2
        assert m["orchestration"]["execucoes_com_trapaca_critica"] == 2
        assert m["orchestration"]["resolved_blocked_by_cheat"] == 2
        assert m["orchestration"]["tool_denials"] == 6

    def test_markdown_sai_inteiro_e_serializavel(self, estudo):
        texto = ar.markdown(estudo)
        assert "As sete métricas" in texto
        assert "## Por tarefa" in texto
        assert "## Censura declarada" in texto
        assert "## Portões de admissão" in texto
        assert "provedor divergente" in texto
        assert "pequena" in texto          # faixa ao lado do par
        json.dumps(estudo, ensure_ascii=False)   # o --json tem de ser serializável


def test_cli_grava_json_e_imprime(tmp_path, capsys):
    runs = tmp_path / "runs"
    for rep in (1, 2, 3):
        gravar_run(runs, resultado("t1", "single-agent", rep))
        gravar_run(runs, resultado("t1", "orchestration", rep, tokens=200_000))
    saida = tmp_path / "analise.json"
    codigo = ar.main([str(runs), "--tasks-dir", str(tmp_path / "tasks"),
                      "--json", str(saida), "--markdown"])
    assert codigo == 0
    assert json.loads(saida.read_text(encoding="utf-8"))["runs_admitidos"] == 6
    assert "As sete métricas" in capsys.readouterr().out


def test_cli_sem_nenhum_result_json_avisa(tmp_path, capsys):
    (tmp_path / "vazio").mkdir()
    assert ar.main([str(tmp_path / "vazio")]) == 1
    assert "Nenhum result.json" in capsys.readouterr().out

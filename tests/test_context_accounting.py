"""
Contabilidade de contexto: a instrumentação `prompt_bytes` e o script que
fecha a conta dos tokens de prompt por turno e por categoria.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.arms.runner import build_run_spec, run_arm
from src.budget import RunBudget
from src.config import LLMConfig
from src.seeds import TOMLKIT
from src.telemetry import TelemetryWriter, prompt_composition, read_events
from tests.fakes import FakeToolCallingLLM, ai

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "context_accounting", RAIZ / "scripts" / "context_accounting.py"
)
ca = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules["context_accounting"] = ca  # dataclasses resolvem anotações pelo módulo registrado
_spec.loader.exec_module(ca)

BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"
LLM = LLMConfig(model="fake/modelo", provider="FakeProvider", seed=1, max_tokens=512)

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


# --------------------------------------------------------------- instrumentação


class TestPromptComposition:
    def test_conta_bytes_por_papel(self):
        msgs = [
            SystemMessage(content="sys"),                     # 3
            HumanMessage(content="olá ção"),                  # 10 bytes UTF-8
            AIMessage(content="ok", tool_calls=[{"name": "read_file", "args": {"path": "a.py"},
                                                 "id": "c1", "type": "tool_call"}]),
            ToolMessage(content="1234567890", tool_call_id="c1"),
        ]
        comp = prompt_composition(msgs)

        assert comp["system"] == 3
        assert comp["human"] == len("olá ção".encode("utf-8")) == 10
        # texto + nome da ferramenta + JSON dos argumentos
        assert comp["ai"] == 2 + len("read_file") + len(json.dumps({"path": "a.py"}, ensure_ascii=False))
        assert comp["tool"] == 10
        assert comp["messages"] == 4
        assert comp["total"] == comp["system"] + comp["human"] + comp["ai"] + comp["tool"]

    def test_lista_vazia(self):
        assert prompt_composition([])["total"] == 0

    def test_llm_call_carrega_prompt_bytes(self, tmp_path):
        tel = TelemetryWriter(tmp_path / "e.jsonl", run_id="r", arm="single-agent", task_id="t")
        evento = tel.emit_llm_call(ai(content="x"), prompt=[SystemMessage(content="abcd")])
        tel.close()

        assert evento["payload"]["prompt_bytes"]["system"] == 4
        assert evento["payload"]["prompt_bytes"]["total"] == 4

    def test_sem_prompt_nao_ha_campo(self, tmp_path):
        """Compatibilidade: eventos antigos e chamadas sem prompt seguem iguais."""
        tel = TelemetryWriter(tmp_path / "e.jsonl", run_id="r", arm="single-agent", task_id="t")
        evento = tel.emit_llm_call(ai(content="x"))
        tel.close()
        assert "prompt_bytes" not in evento["payload"]

    def test_chamada_estruturada_tambem_mede(self, ctx_minimo, monkeypatch):
        """Os papéis auxiliares passam por invoke_structured: o prompt deles entra na conta."""
        ctx, _ = ctx_minimo
        from src.schemas.validation_result import ValidationResult

        monkeypatch.setattr(
            "src.structured_llm.invoke_structured_raw",
            lambda schema, messages, **k: (ValidationResult(is_valid=True), ai(content="{}")),
        )
        ctx.invoke_structured(ValidationResult, [("system", "S" * 10), ("user", "U" * 25)])

        eventos = [e for e in read_events(ctx.telemetry.path) if e["event_type"] == "llm_call"]
        assert len(eventos) == 1
        assert eventos[0]["payload"]["prompt_bytes"] == {
            "system": 10, "human": 25, "ai": 0, "tool": 0, "other": 0, "messages": 2, "total": 35,
        }


# -------------------------------------------------------------------- script


def _evento(seq, tipo, *, node=None, arm="single-agent", **campos):
    base = {
        "schema_version": 1, "run_id": "r1", "arm": arm, "task_id": "tomlkit-0001", "seq": seq,
        "ts": "2026-09-18T00:00:00Z", "elapsed_ms": seq, "event_type": tipo, "node": node,
        "agent_role": None, "turn": None, "model": "m", "provider_requested": "p",
        "provider_served": "p", "tokens_prompt": 0, "tokens_completion": 0,
        "tokens_reasoning": 0, "tokens_total": 0, "cost_usd": 0.0, "latency_ms": 0,
        "tool_name": None, "tool_args_hash": None, "tool_denied": False,
        "tool_exit_code": None, "payload": {},
    }
    base.update(campos)
    return base


def _gravar(tmp_path, eventos, arm="single-agent", started_at="2026-09-18T00:00:00+00:00"):
    d = tmp_path / "run"
    d.mkdir()
    (d / "events.jsonl").write_text("\n".join(json.dumps(e) for e in eventos) + "\n")
    (d / "manifest.json").write_text(json.dumps({
        "run_id": "r1", "arm": arm, "task_id": "tomlkit-0001", "started_at": started_at,
    }))
    return d


def _janela_sintetica(a=20.0, c=4.0, n=8):
    """
    Uma conversa em que o prompt cresce EXATAMENTE pelo modelo:
    P_n = P_{n-1} + completion_{n-1} + a·k + bytes/c.
    """
    eventos = [_evento(1, "run_start"), _evento(2, "node_enter", node="single_agent")]
    seq = 3
    prompt = 2000
    completion = 50
    for i in range(n):
        eventos.append(_evento(
            seq, "llm_call", node="single_agent", turn=i + 1,
            tokens_prompt=prompt, tokens_completion=completion, tokens_total=prompt + completion,
            payload={"tool_calls_requested": ["read_file"]},
        ))
        seq += 1
        bytes_lidos = 400 * (i + 1)
        eventos.append(_evento(seq, "tool_call", node="single_agent", tool_name="read_file",
                               payload={"bytes_read": bytes_lidos, "bytes_written": 0, "error": None}))
        seq += 1
        prompt = prompt + completion + int(a * 1 + bytes_lidos / c)
        completion = 50 + 10 * i
    eventos.append(_evento(seq, "run_end", payload={"stop_reason": "tests_pass"}))
    return eventos


class TestJanelas:
    def test_single_agent_e_uma_janela_mesmo_reentrando_no_no(self, tmp_path):
        eventos = [_evento(1, "run_start")]
        seq = 2
        for t in range(3):
            eventos += [
                _evento(seq, "node_enter", node="single_agent"),
                _evento(seq + 1, "llm_call", node="single_agent", turn=t + 1, tokens_prompt=100 * (t + 1)),
                _evento(seq + 2, "node_exit", node="single_agent"),
            ]
            seq += 3
        run = ca.load_run(_gravar(tmp_path, eventos))

        assert len(run.windows) == 1
        assert [c.turn for c in run.windows[0].calls] == [1, 2, 3]

    def test_developer_reconstroi_a_janela_a_cada_entrada(self, tmp_path):
        eventos = [
            _evento(1, "run_start", arm="orchestration"),
            _evento(2, "node_enter", node="intent_refiner", arm="orchestration"),
            _evento(3, "llm_call", node="intent_refiner", tokens_prompt=900, arm="orchestration"),
            _evento(4, "node_enter", node="developer", arm="orchestration"),
            _evento(5, "llm_call", node="developer", turn=1, tokens_prompt=1800, arm="orchestration"),
            _evento(6, "llm_call", node="developer", turn=2, tokens_prompt=2500, arm="orchestration"),
            _evento(7, "node_enter", node="validator", arm="orchestration"),
            _evento(8, "test_run", node="validator", arm="orchestration", payload={"green": False}),
            _evento(9, "node_enter", node="developer", arm="orchestration"),
            _evento(10, "llm_call", node="developer", turn=3, tokens_prompt=2100, arm="orchestration"),
        ]
        run = ca.load_run(_gravar(tmp_path, eventos, arm="orchestration"))

        assert len(run.windows) == 2
        assert [len(w.calls) for w in run.windows] == [2, 1]
        assert run.windows[1].calls[0].test_runs_before == 1
        assert [x["node"] for x in run.aux_calls] == ["intent_refiner"]


class TestModoInferido:
    def test_recupera_os_parametros_de_uma_janela_exata(self, tmp_path):
        run = ca.load_run(_gravar(tmp_path, _janela_sintetica(a=20.0, c=4.0)))
        lg = ca.ledger_inferido(run.windows[0])

        assert lg.modo == "inferido"
        assert lg.a == pytest.approx(20.0, abs=1.5)      # arredondamento a inteiro no gerador
        assert lg.c == pytest.approx(4.0, rel=0.05)
        assert lg.discrepancia_abs_pct < 2.0
        assert lg.nao_explicadas == []

    def test_conteudo_nao_medido_aparece_como_residuo(self, tmp_path):
        """Uma ferramenta que não registrou bytes deixa um turno sem explicação."""
        eventos = _janela_sintetica(a=20.0, c=4.0)
        # zera os bytes de uma leitura grande: é o que acontecia com run_python
        alvo = [e for e in eventos if e["event_type"] == "tool_call"][5]
        alvo["payload"]["bytes_read"] = 0
        run = ca.load_run(_gravar(tmp_path, eventos))
        lg = ca.ledger_inferido(run.windows[0])

        assert lg.nao_explicadas, "o turno com leitura não medida precisa ser apontado"
        assert lg.discrepancia_abs_pct > 5.0

    def test_atribuicao_fecha_no_total_cobrado(self, tmp_path):
        run = ca.load_run(_gravar(tmp_path, _janela_sintetica()))
        analise = ca.analisar(run, {"system_prompt": 1000, "tool_schema": 3000}, RAIZ / "tasks")
        atr = analise["atribuicao"]

        assert sum(atr["categorias_tokens"].values()) == pytest.approx(
            atr["tokens_prompt_cobrados_total"], abs=len(atr["categorias_tokens"])
        )
        assert "saída de read_file" in atr["categorias_tokens"]
        assert analise["modo"] == "inferido"


class TestModoExato:
    def test_bytes_de_ferramenta_conferem_com_os_eventos(self, tmp_path):
        eventos = [_evento(1, "run_start"), _evento(2, "node_enter", node="single_agent")]
        eventos.append(_evento(3, "llm_call", node="single_agent", turn=1, tokens_prompt=1000,
                               payload={"prompt_bytes": {"system": 1300, "human": 1500, "ai": 0,
                                                         "tool": 0, "other": 0, "messages": 2, "total": 2800}}))
        eventos.append(_evento(4, "tool_call", node="single_agent", tool_name="read_file",
                               payload={"bytes_read": 700, "bytes_written": 0, "error": None}))
        eventos.append(_evento(5, "llm_call", node="single_agent", turn=2, tokens_prompt=1300,
                               payload={"prompt_bytes": {"system": 1300, "human": 1500, "ai": 40,
                                                         "tool": 700, "other": 0, "messages": 4, "total": 3540}}))
        run = ca.load_run(_gravar(tmp_path, eventos))
        lg = ca.ledger_exato(run.windows[0])

        assert run.modo == "exato"
        assert lg.discrepancia_abs_pct == 0.0
        assert lg.nao_explicadas == []
        assert lg.c == pytest.approx((2800 / 1000 + 3540 / 1300) / 2, rel=0.01)

    def test_resposta_de_ferramenta_sem_evento_e_detectada(self, tmp_path):
        """Ferramenta desconhecida devolve texto ao modelo sem `tool_call`: a conta em bytes não fecha."""
        eventos = [_evento(1, "run_start"), _evento(2, "node_enter", node="single_agent")]
        eventos.append(_evento(3, "llm_call", node="single_agent", turn=1, tokens_prompt=1000,
                               payload={"prompt_bytes": {"system": 1300, "human": 1500, "ai": 0,
                                                         "tool": 0, "other": 0, "messages": 2, "total": 2800}}))
        eventos.append(_evento(4, "llm_call", node="single_agent", turn=2, tokens_prompt=1100,
                               payload={"prompt_bytes": {"system": 1300, "human": 1500, "ai": 40,
                                                         "tool": 120, "other": 0, "messages": 4, "total": 2960}}))
        run = ca.load_run(_gravar(tmp_path, eventos))
        lg = ca.ledger_exato(run.windows[0])

        assert lg.nao_explicadas == [4]
        assert lg.linhas[1]["divergencia_tool_bytes"] == 120


# ------------------------------------------------------------ ponta a ponta


@mirror_available
class TestBracoInstrumentado:
    def test_single_agent_fecha_a_conta_em_bytes(self, tmp_path):
        enunciado = (RAIZ / "tasks" / "tomlkit-0001" / "statement.md").read_text(encoding="utf-8")
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "read_file", "args": {"path": "tomlkit/_utils.py"}}]),
            ai(tool_calls=[{"name": "write_file", "args": {
                "path": "tomlkit/_utils.py", "content": "import re\n# nota\n"}}]),
            ai(content="pronto"),        # driver roda a suíte (vermelha) e devolve stderr
            ai(content="desisto"),
        ])
        spec = build_run_spec(
            run_id="ctx-e2e", arm="single-agent", task_id="tomlkit-0001", statement=enunciado,
            base_commit=BASE_COMMIT, out_dir=tmp_path / "run", llm=LLM,
            budget=RunBudget(max_tokens=10**9, max_wall_seconds=600, max_turns=4),
        )
        run_arm(spec, llm_factory=llm.factory)

        eventos = read_events(spec.out_dir / "events.jsonl")
        chamadas = [e for e in eventos if e["event_type"] == "llm_call"]
        assert chamadas and all("prompt_bytes" in e["payload"] for e in chamadas)

        run = ca.load_run(spec.out_dir)
        analise = ca.analisar(run, ca.tamanhos_fixos(), RAIZ / "tasks")

        assert analise["modo"] == "exato"
        janela = analise["janelas_detalhe"][0]
        assert janela["chamadas_nao_explicadas"] == []
        assert all(l["divergencia_tool_bytes"] == 0 for l in janela["linhas"])
        # a primeira mensagem medida é exatamente a que o runner monta a partir do enunciado
        assert analise["primeira_mensagem_bytes_medida"] == analise["primeira_mensagem_bytes_reconstruida"]
        # o feedback do driver entrou como mensagem humana depois da suíte vermelha
        humanos = [l["prompt_bytes"]["human"] for l in janela["linhas"]]
        assert humanos[-1] > humanos[0]

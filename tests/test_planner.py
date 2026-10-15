"""Planejador de sub-tarefas (decisão 33, 15/10/2026) e execução acumulada (decisão 34)."""

from __future__ import annotations

import pytest

from src import config
from src.schemas.intent import StructuredIntentV2
from src.schemas.plan import Plan, Subtask, sanear
from src.schemas.validation_result import ValidationResult
from src.structured_llm import StructuredOutputError
from src.telemetry import read_events
from tests.fakes import FakeToolCallingLLM, ai
from tests.test_nodes import BASE_COMMIT, _estado, _mudanca_benigna, ambiente, mirror_available  # noqa: F401


def _intent_v2() -> dict:
    return StructuredIntentV2(
        context="c", goal="Levantar erro em array malformado e aceitar chave pontilhada.",
        phases=["a", "b"], is_ready=True,
        acceptance_criteria=["Array malformado levanta exceção", "Chave pontilhada é aceita", "Suíte continua verde"],
        reproduction=["x = 2", "print(x + 2)"],
        expected_outputs=["4"], constraints=[],
    ).model_dump()


def _plano(n: int = 2) -> Plan:
    subs = [
        Subtask(id=1, title="Parser de array", objective="Mudar tomlkit/parser.py::_parse_array",
                files=["tomlkit/parser.py"], criteria=[1], reproduction=[1], done_when="exceção levantada"),
        Subtask(id=2, title="Chave pontilhada", objective="Mudar tomlkit/container.py",
                files=["tomlkit/container.py"], criteria=[2, 3], reproduction=[2], done_when="exemplo imprime 4"),
    ]
    return Plan(rationale="duas partes independentes", subtasks=subs[:n])


def _estado_com_plano(**extra):
    plano = _plano()
    return _estado(
        intent=_intent_v2(),
        plan={"rationale": plano.rationale, "subtasks": [s.model_dump() for s in plano.subtasks],
              "status": [{"id": 1, "status": "em_andamento", "ciclos": 0, "adiada_antes": False},
                         {"id": 2, "status": "pendente", "ciclos": 0, "adiada_antes": False}]},
        subtask_current=1, replans=0, **extra,
    )


class TestSchemaDoPlano:
    def test_renumera_e_coage_indices(self):
        p = Plan(subtasks=[
            {"id": 7, "title": "a", "objective": "o", "criteria": ["1", 2, [3]], "reproduction": [], "done_when": "d"},
            {"id": 9, "title": "b", "objective": "o", "files": "x.py", "criteria": [], "reproduction": ["2"], "done_when": "d"},
        ])
        assert [s.id for s in p.subtasks] == [1, 2]
        assert p.subtasks[0].criteria == [1, 2, 3] and p.subtasks[1].files == ["x.py"] and p.subtasks[1].reproduction == [2]

    def test_sanear_descarta_indices_fora_da_intent_e_limita_tamanho(self):
        p = Plan(subtasks=[Subtask(id=1, title="t", objective="o", criteria=[0, 1, 5], reproduction=[2, 9], done_when="d")] * 8)
        s = sanear(p, n_criterios=3, n_reproducao=2, maximo=6)
        assert len(s.subtasks) == 6
        assert s.subtasks[0].criteria == [1] and s.subtasks[0].reproduction == [2]


@mirror_available
class TestPlanejador:
    def test_explora_so_com_leitura_e_entrega_o_plano(self, ambiente, monkeypatch):
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        ws, tel, montar = ambiente
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "search_code", "args": {"pattern": "def _parse_array", "path": "tomlkit"}},
                           {"name": "write_file", "args": {"path": "tomlkit/x.py", "content": "oops"}}]),
            ai(content="explorei"),
        ])
        montar(llm)
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (_plano(), None))

        out = planner(_estado(intent=_intent_v2(), turn_count=0, replans=0))

        assert {t.name for t in llm.ferramentas_ligadas} == {"list_files", "read_file", "search_code"}
        # a escrita foi recusada: nada mudou no workspace
        assert ws.changed_files() == []
        assert "ferramenta desconhecida 'write_file'" in str(llm.chamadas[1][-1].content)
        assert [s["id"] for s in out["plan"]["subtasks"]] == [1, 2]
        assert out["subtask_current"] == 1
        assert [s["status"] for s in out["plan"]["status"]] == ["em_andamento", "pendente"]
        assert out["turn_count"] == 3  # 2 turnos de exploração + 1 da chamada estruturada
        ev = [e for e in read_events(tel.path) if e["event_type"] == "plan"]
        assert ev and ev[-1]["payload"]["evento"] == "plano" and ev[-1]["payload"]["turnos_de_exploracao"] == 2

    def test_teto_de_exploracao(self, ambiente, monkeypatch):
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "PLANNER_MAX_TURNS", 2)
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([ai(tool_calls=[{"name": "list_files", "args": {}}])] * 5)
        montar(llm)
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (_plano(1), None))

        out = planner(_estado(intent=_intent_v2(), turn_count=0, replans=0))
        assert llm.n_invocacoes == 2 and out["turn_count"] == 3

    def test_fallback_quando_o_modelo_nao_conforma(self, ambiente, monkeypatch):
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        _, tel, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))

        def _falha(*a, **k):
            raise StructuredOutputError("não conformou")
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _falha)

        out = planner(_estado(intent=_intent_v2(), turn_count=0, replans=0))
        assert len(out["plan"]["subtasks"]) == 1
        assert out["plan"]["subtasks"][0]["criteria"] == [1, 2, 3] and out["plan"]["subtasks"][0]["reproduction"] == [1, 2]
        assert out["subtask_current"] == 1
        assert any(e["event_type"] == "error" for e in read_events(tel.path))

    def test_replanejamento_acrescenta_subtarefas(self, ambiente, monkeypatch):
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        _, tel, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (_plano(1), None))
        estado = _estado_com_plano(replan_requested=True, turn_count=50)
        estado["plan"]["status"] = [{"id": 1, "status": "feita", "ciclos": 1, "adiada_antes": False},
                                    {"id": 2, "status": "abandonada", "ciclos": 4, "adiada_antes": True}]
        estado["subtask_current"] = None

        out = planner(estado)

        assert [s["id"] for s in out["plan"]["subtasks"]] == [1, 2, 3]
        assert out["plan"]["status"][2]["status"] == "em_andamento" and out["subtask_current"] == 3
        assert out["replans"] == 1 and out["replan_requested"] is False
        assert [e for e in read_events(tel.path) if e["event_type"] == "plan"][-1]["payload"]["evento"] == "replanejamento"


class TestDeveloperComSubtarefa:
    def test_prompt_traz_a_subtarefa_com_criterios_e_blocos_copiados(self, monkeypatch):
        from src.agents.developer import _build_prompt

        monkeypatch.setattr(config, "PLANNER", "on")
        texto = _build_prompt(_estado_com_plano())
        assert "Plano de sub-tarefas (estado atual):" in texto
        assert "[em_andamento] 1. Parser de array" in texto and "[pendente] 2. Chave pontilhada" in texto
        assert "Sub-tarefa atual (1 de 2): Parser de array" in texto
        assert "- Array malformado levanta exceção" in texto and "Chave pontilhada é aceita" not in texto.split("Sub-tarefa atual")[1]
        assert "```\nx = 2\n```" in texto and "Pronto quando: exceção levantada" in texto

    def test_parecer_da_subtarefa_entra_no_prompt(self, monkeypatch):
        from src.agents.developer import _build_prompt
        from src.feedback import SUBTAREFA_CONCLUIDA_NAO

        monkeypatch.setattr(config, "PLANNER", "on")
        texto = _build_prompt(_estado_com_plano(subtask_review={"is_valid": False, "issues": ["falta o caso vazio"],
                                                                 "missing_criteria": [], "suggestions": []}))
        assert SUBTAREFA_CONCLUIDA_NAO in texto and "falta o caso vazio" in texto

    def test_off_nao_muda_o_prompt(self, monkeypatch):
        from src.agents.developer import _build_prompt

        monkeypatch.setattr(config, "PLANNER", "off")
        assert "Sub-tarefa" not in _build_prompt(_estado_com_plano())


@mirror_available
class TestValidadorAvancaOPlano:
    def _roda(self, ambiente, monkeypatch, estado, veredito):
        from src.agents.validator import validator

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        monkeypatch.setattr(config, "SUBTASK_MAX_CYCLES", 2)
        monkeypatch.setattr(config, "PLANNER_MAX_REPLANS", 1)
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        _mudanca_benigna(ws)
        montar(FakeToolCallingLLM([ai(content="x")]))
        vereditos = iter(veredito)
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (next(vereditos), None))
        return validator(estado), tel

    def test_subtarefa_feita_avanca_para_a_proxima(self, ambiente, monkeypatch):
        # 1ª chamada: revisão final (reprova); 2ª: revisão da sub-tarefa (feita)
        out, tel = self._roda(ambiente, monkeypatch, _estado_com_plano(),
                              [ValidationResult(is_valid=False, issues=["falta a parte 2"]),
                               ValidationResult(is_valid=True)])
        assert out["is_valid"] is False
        assert [s["status"] for s in out["plan"]["status"]] == ["feita", "em_andamento"]
        assert out["subtask_current"] == 2 and out["subtask_review"] is None
        assert out["semantic_rejections"] == 0  # plano aberto: reprovação final não conta
        evs = [e for e in read_events(tel.path) if e["event_type"] == "validation"]
        assert evs[-1]["payload"]["scope"] == "subtask" and evs[-1]["payload"]["subtask"] == 1
        # execução acumulada: o bloco 2 rodou com o bloco 1 antes
        assert any(x.get("acumulado") for e in evs for x in e["payload"].get("executions", []) if x["bloco"] == 2)

    def test_subtarefa_nao_feita_continua_e_depois_e_adiada(self, ambiente, monkeypatch):
        estado = _estado_com_plano()
        out, _ = self._roda(ambiente, monkeypatch, estado,
                            [ValidationResult(is_valid=False), ValidationResult(is_valid=False, issues=["x"])])
        assert out["subtask_current"] == 1 and out["plan"]["status"][0]["status"] == "em_andamento"
        assert out["subtask_review"]["issues"] == ["x"]
        estado2 = {**estado, **out}
        out2, _ = self._roda(ambiente, monkeypatch, estado2,
                             [ValidationResult(is_valid=False), ValidationResult(is_valid=False)])
        assert out2["plan"]["status"][0]["status"] == "adiada" and out2["subtask_current"] == 2

    def test_plano_esgotado_pede_replanejamento_uma_vez(self, ambiente, monkeypatch):
        estado = _estado_com_plano()
        estado["plan"]["status"] = [{"id": 1, "status": "feita", "ciclos": 1, "adiada_antes": False},
                                    {"id": 2, "status": "em_andamento", "ciclos": 3, "adiada_antes": True}]
        estado["subtask_current"] = 2
        out, _ = self._roda(ambiente, monkeypatch, estado,
                            [ValidationResult(is_valid=False), ValidationResult(is_valid=False)])
        assert out["plan"]["status"][1]["status"] == "abandonada"
        assert out["subtask_current"] is None and out["replan_requested"] is True
        estado2 = {**estado, **out, "replans": 1}
        out2, _ = self._roda(ambiente, monkeypatch, estado2, [ValidationResult(is_valid=False)])
        assert out2["replan_requested"] is False and out2["plan"].get("esgotado") is True
        assert out2["semantic_rejections"] == 1  # plano fechado: a reprovação volta a contar

    def test_aprovacao_final_encerra_mesmo_com_plano_aberto(self, ambiente, monkeypatch):
        out, _ = self._roda(ambiente, monkeypatch, _estado_com_plano(), [ValidationResult(is_valid=True)])
        assert out["is_valid"] is True and "plan" not in out


@mirror_available
class TestExecucaoAcumulada:
    def test_cumulative_prefixa_os_blocos_anteriores(self, ambiente, monkeypatch):
        from src.agents.validator import _executar_reproducao

        _, _, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))
        estado = _estado(intent=_intent_v2())
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "on")
        isolado = _executar_reproducao(estado, _ctx(montar))
        assert "NameError" in isolado[1]["saida"]
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        acumulado = _executar_reproducao(estado, _ctx(montar))
        assert "4" in acumulado[1]["saida"] and acumulado[1]["acumulado"] is True and acumulado[0]["acumulado"] is False
        so_o_2 = _executar_reproducao(estado, _ctx(montar), indices=[2])
        assert [x["bloco"] for x in so_o_2] == [2] and "4" in so_o_2[0]["saida"]


def _ctx(montar):
    from src.runtime import RunContext
    return RunContext.get("nodes-test")


class TestRoteamentoEManifesto:
    def test_intent_pronta_vai_ao_planejador_quando_ligado(self, monkeypatch):
        from src.graph import build_graph, route_after_intent_refiner, route_after_validator

        monkeypatch.setattr(config, "PLANNER", "on")
        assert route_after_intent_refiner({"is_ready": True}) == "planner"
        assert route_after_validator({"is_valid": False, "replan_requested": True}) == "planner"
        assert route_after_validator({"is_valid": False, "replan_requested": False}) == "developer"
        monkeypatch.setattr(config, "PLANNER", "off")
        assert route_after_intent_refiner({"is_ready": True}) == "developer"
        assert route_after_validator({"is_valid": False, "replan_requested": True}) == "developer"
        assert "planner" in set(build_graph().get_graph().nodes)

    def test_manifesto_registra_o_planejador(self, monkeypatch):
        from src.arms.runner import _orchestration_policy

        monkeypatch.setattr(config, "PLANNER", "on")
        pol = _orchestration_policy()
        assert pol["planner"] == "on" and pol["planner_max_turns"] == config.PLANNER_MAX_TURNS
        assert pol["subtask_max_cycles"] == config.SUBTASK_MAX_CYCLES and pol["planner_max_replans"] == config.PLANNER_MAX_REPLANS

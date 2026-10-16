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
        reproduction=["x = 2", "print('mudou:', 'nota do agente' in open('tomlkit/_utils.py').read(), x + 2)"],
        expected_outputs=["mudou: True", "nunca aparece"], constraints=[],
    ).model_dump()


def _plano(n: int = 2) -> Plan:
    subs = [
        Subtask(id=1, title="Parser de array", objective="Mudar tomlkit/parser.py::_parse_array",
                files=["tomlkit/parser.py"], criteria=[1], reproduction=[1, 2], expected=[1],
                done_when="exceção levantada"),
        Subtask(id=2, title="Chave pontilhada", objective="Mudar tomlkit/container.py",
                files=["tomlkit/container.py"], criteria=[2, 3], reproduction=[2], expected=[2],
                done_when="exemplo imprime 4"),
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

    def test_sanear_limita_as_saidas_esperadas_apontadas(self):
        p = Plan(subtasks=[Subtask(id=1, title="t", objective="o", expected=[0, 1, 2, 7], done_when="d")])
        s = sanear(p, n_criterios=0, n_reproducao=0, n_esperadas=2)
        assert s.subtasks[0].expected == [1, 2]
        assert sanear(p, n_criterios=0, n_reproducao=0).subtasks[0].expected == []


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
        assert out["turn_count"] == 4  # 2 de exploração + 1 do pedido em texto + 1 da chamada estruturada
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
        assert llm.n_invocacoes == 3 and out["turn_count"] == 4

    def test_plano_em_json_no_texto_dispensa_a_chamada_estruturada(self, ambiente, monkeypatch):
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        _, _, montar = ambiente
        texto = "```json\n" + _plano().model_dump_json() + "\n```"
        llm = FakeToolCallingLLM([ai(content="explorei"), ai(content=texto)])
        montar(llm)

        def _nao_chama(*a, **k):
            raise AssertionError("chamada estruturada não deveria acontecer")
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _nao_chama)

        out = planner(_estado(intent=_intent_v2(), turn_count=0, replans=0))
        assert [s["title"] for s in out["plan"]["subtasks"]] == ["Parser de array", "Chave pontilhada"]
        assert out["turn_count"] == 2

    def test_plano_vazio_nao_conforma(self):
        with pytest.raises(Exception):
            Plan(subtasks=[])

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
        # saída esperada apontada pelo planejador (rodada 5), copiada pelo índice
        assert "Saídas esperadas desses exemplos depois da correção" in texto and "- mudou: True" in texto
        assert "nunca aparece" not in texto.split("Sub-tarefa atual")[1]

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
        assert "mudou: False 4" in acumulado[1]["saida"] and acumulado[1]["acumulado"] is True and acumulado[0]["acumulado"] is False
        so_o_2 = _executar_reproducao(estado, _ctx(montar), indices=[2])
        assert [x["bloco"] for x in so_o_2] == [2] and "mudou: False 4" in so_o_2[0]["saida"]


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

    def test_manifesto_registra_a_rodada_5(self, monkeypatch):
        from src.arms.runner import _orchestration_policy

        monkeypatch.setattr(config, "SUBTASK_CHECK", "deterministic")
        monkeypatch.setattr(config, "REVIEW_COMPARE", "advisory")
        monkeypatch.setattr(config, "PLANNER_CONTEXT_MAX_CHARS", 16_000)
        pol = _orchestration_policy()
        assert (pol["subtask_check"], pol["review_compare"], pol["planner_context_max_chars"]) == ("deterministic", "advisory", 16_000)


# ------------------------------------------------------------ rodada 5


@mirror_available
class TestVerificacaoDeterministicaDaSubtarefa:
    """Decisão 36 (rodada 5): o veredito da sub-tarefa sai da comparação de saídas, sem o modelo."""

    def _roda(self, ambiente, monkeypatch, estado, vereditos_finais, *, mudanca=True):
        from src.agents.validator import validator

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        monkeypatch.setattr(config, "SUBTASK_CHECK", "deterministic")
        monkeypatch.setattr(config, "REVIEW_COMPARE", "off")
        monkeypatch.setattr(config, "SUBTASK_MAX_CYCLES", 2)
        monkeypatch.setattr(config, "PLANNER_MAX_REPLANS", 1)
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        if mudanca:
            _mudanca_benigna(ws)
        montar(FakeToolCallingLLM([ai(content="x")]))
        fila = iter(vereditos_finais)
        chamadas: list = []

        def _estruturada(schema, messages, **k):
            chamadas.append(messages)
            return next(fila), None
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _estruturada)
        return validator(estado), tel, chamadas

    @staticmethod
    def _ultimo_evento_da_subtarefa(tel):
        return [e for e in read_events(tel.path)
                if e["event_type"] == "validation" and e["payload"].get("scope") == "subtask"][-1]["payload"]

    def test_saida_esperada_encontrada_da_a_subtarefa_por_feita_sem_consultar_o_modelo(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        out, tel, chamadas = self._roda(ambiente, monkeypatch, estado,
                                        [ValidationResult(is_valid=False, issues=["falta a parte 2"])])
        assert len(chamadas) == 1  # só a revisão final consultou o modelo
        assert [s["status"] for s in out["plan"]["status"]] == ["feita", "em_andamento"]
        assert out["subtask_current"] == 2 and out["subtask_review"] is None
        ev = self._ultimo_evento_da_subtarefa(tel)
        assert ev["deterministic"] is True and ev["basis"] == "comparacao"
        assert [c["estado"] for c in ev["comparisons"]] == ["encontrada"]
        # reaproveitou a execução da revisão final (blocos 1 e 2 da sub-tarefa): nada rodou de novo
        assert [x["bloco"] for x in ev["executions"]] == [1, 2]

    def test_saida_esperada_ausente_segura_a_subtarefa_e_o_developer_recebe_a_comparacao(self, ambiente, monkeypatch):
        from src.agents.developer import _build_prompt

        estado = _estado_com_plano(stop_reason="concluiu")
        estado["plan"]["subtasks"][0]["expected"] = [1, 2]  # a saída 2 nunca aparece
        out, tel, _ = self._roda(ambiente, monkeypatch, estado, [ValidationResult(is_valid=False)])
        assert out["plan"]["status"][0]["status"] == "em_andamento" and out["subtask_current"] == 1
        issues = out["subtask_review"]["issues"]
        assert any("saída esperada 1: encontrada" in x for x in issues)
        assert any("saída esperada 2: NÃO encontrada" in x and "nunca aparece" in x for x in issues)
        assert any(x.startswith("saída real da execução:") and "mudou: True" in x for x in issues)
        assert self._ultimo_evento_da_subtarefa(tel)["basis"] == "comparacao"
        texto = _build_prompt({**estado, **out})
        assert "saída esperada 2: NÃO encontrada" in texto

    def test_sem_saida_verificavel_vale_a_palavra_do_developer(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        estado["plan"]["subtasks"][0]["expected"] = []
        out, tel, _ = self._roda(ambiente, monkeypatch, estado, [ValidationResult(is_valid=False)])
        assert out["plan"]["status"][0]["status"] == "feita"
        assert self._ultimo_evento_da_subtarefa(tel)["basis"] == "palavra_do_developer"
        # bateu o teto do ciclo: a palavra não vale, e nada volta como parecer
        estado2 = _estado_com_plano(stop_reason="cycle: max_turns_per_cycle (40 >= 40)")
        estado2["plan"]["subtasks"][0]["expected"] = []
        out2, _, _ = self._roda(ambiente, monkeypatch, estado2, [ValidationResult(is_valid=False)])
        assert out2["plan"]["status"][0]["status"] == "em_andamento" and out2["subtask_review"] is None

    def test_sem_mudanca_nao_ha_subtarefa_feita(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        out, tel, _ = self._roda(ambiente, monkeypatch, estado, [ValidationResult(is_valid=True)], mudanca=False)
        assert out["is_valid"] is False and out["plan"]["status"][0]["status"] == "em_andamento"
        ev = self._ultimo_evento_da_subtarefa(tel)
        assert ev["basis"] == "sem_mudanca" and ev["comparisons"] == [] and out["subtask_review"] is None


@mirror_available
class TestComparacaoNaRevisaoFinal:
    """Decisão 35 (rodada 5): a comparação automática chega ao revisor; o modo estrito reprova sozinho."""

    def _roda(self, ambiente, monkeypatch, modo, veredito, estado=None):
        from src.agents.validator import validator

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        monkeypatch.setattr(config, "SUBTASK_CHECK", "deterministic")
        monkeypatch.setattr(config, "REVIEW_COMPARE", modo)
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        _mudanca_benigna(ws)
        montar(FakeToolCallingLLM([ai(content="x")]))
        chamadas: list = []

        def _estruturada(schema, messages, **k):
            chamadas.append(messages)
            return veredito, None
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _estruturada)
        return validator(estado or _estado_com_plano(stop_reason="concluiu")), tel, chamadas

    @staticmethod
    def _ultima_revisao_final(tel):
        return [e for e in read_events(tel.path)
                if e["event_type"] == "validation" and not e["payload"].get("scope")][-1]["payload"]

    def test_advisory_leva_a_comparacao_e_a_regra_ao_revisor(self, ambiente, monkeypatch):
        out, tel, chamadas = self._roda(ambiente, monkeypatch, "advisory", ValidationResult(is_valid=True))
        assert out["is_valid"] is True and len(chamadas) == 1
        sistema, usuario = chamadas[0][0][1], chamadas[0][1][1]
        assert "não verificável não prova nada" in sistema
        assert "Comparação automática das saídas esperadas" in usuario
        assert "- saída esperada 1: encontrada" in usuario and "- saída esperada 2: NÃO encontrada" in usuario
        ev = self._ultima_revisao_final(tel)
        assert [c["estado"] for c in ev["comparisons"]] == ["encontrada", "nao_encontrada"]
        assert "deterministic" not in ev

    def test_off_reproduz_a_rodada_4(self, ambiente, monkeypatch):
        _, tel, chamadas = self._roda(ambiente, monkeypatch, "off", ValidationResult(is_valid=True))
        sistema, usuario = chamadas[0][0][1], chamadas[0][1][1]
        assert "Comparação automática" not in usuario and "não verificável" not in sistema
        assert self._ultima_revisao_final(tel)["comparisons"] == []

    def test_strict_reprova_sem_consultar_o_revisor_quando_falta_saida_verificavel(self, ambiente, monkeypatch):
        out, tel, chamadas = self._roda(ambiente, monkeypatch, "strict", ValidationResult(is_valid=True))
        assert out["is_valid"] is False and chamadas == []
        assert any("saída esperada 2: NÃO encontrada" in x for x in out["validation_result"]["issues"])
        ev = self._ultima_revisao_final(tel)
        assert ev["deterministic"] is True and ev["is_valid"] is False

    def test_strict_consulta_o_revisor_quando_nada_verificavel_falta(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        estado["plan"]["subtasks"][1]["expected"] = []  # só a saída 1 fica apontada no plano
        out, _, chamadas = self._roda(ambiente, monkeypatch, "strict", ValidationResult(is_valid=True), estado=estado)
        assert out["is_valid"] is True and len(chamadas) == 1


@mirror_available
class TestTrechosDoPlanejador:
    """Decisão 37 (rodada 5): o que o planejador leu vai ao developer com a sub-tarefa."""

    def test_planejador_guarda_as_leituras_e_o_developer_as_recebe_ate_o_teto(self, ambiente, monkeypatch):
        from src.agents.developer import _build_prompt
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        _, tel, montar = ambiente
        llm = FakeToolCallingLLM([
            ai(tool_calls=[{"name": "read_file", "args": {"path": "./tomlkit/parser.py", "start_line": 1, "end_line": 20}},
                           {"name": "read_file", "args": {"path": "nao/existe.py"}}]),
            ai(content="explorei"),
        ])
        montar(llm)
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (_plano(), None))

        out = planner(_estado(intent=_intent_v2(), turn_count=0, replans=0))

        trechos = out["plan"]["trechos"]
        assert list(trechos) == ["tomlkit/parser.py"] and "linhas 1-20" in trechos["tomlkit/parser.py"]
        ev = [e for e in read_events(tel.path) if e["event_type"] == "plan"][-1]["payload"]
        assert ev["trechos_chars"] == {"tomlkit/parser.py": len(trechos["tomlkit/parser.py"])} and "trechos" not in ev

        estado = {**_estado(intent=_intent_v2()), **out}
        monkeypatch.setattr(config, "PLANNER_CONTEXT_MAX_CHARS", 0)
        assert "Trechos desses arquivos" not in _build_prompt(estado)
        monkeypatch.setattr(config, "PLANNER_CONTEXT_MAX_CHARS", 10_000)
        texto = _build_prompt(estado)
        assert "Trechos desses arquivos, como o planejador os leu" in texto
        assert "--- tomlkit/parser.py ---" in texto and "tomlkit/parser.py (linhas 1-20" in texto
        monkeypatch.setattr(config, "PLANNER_CONTEXT_MAX_CHARS", 120)
        assert "[... trecho cortado pelo teto da política ...]" in _build_prompt(estado)

    def test_prompt_do_planejador_leva_o_teto_de_subtarefas_e_pede_expected(self, ambiente, monkeypatch):
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "PLANNER_MAX_SUBTASKS", 3)
        _, _, montar = ambiente
        llm = FakeToolCallingLLM([ai(content="x")])
        montar(llm)
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (_plano(), None))

        planner(_estado(intent=_intent_v2(), turn_count=0, replans=0))

        assert "No máximo 3 sub-tarefas" in llm.chamadas[0][0].content
        assert '"expected": [int]' in llm.chamadas[1][-1].content


@mirror_available
class TestSaidasQueOCodigoOriginalJaProduz:
    """Decisão 39 (16/10/2026): saída esperada presente na execução do código original não verifica nada."""

    def test_planejador_executa_na_base_e_tira_essas_saidas_do_plano_e_do_prompt(self, ambiente, monkeypatch):
        from src.agents.planner import planner

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        _, tel, montar = ambiente
        llm = FakeToolCallingLLM([ai(content="x")])
        montar(llm)
        intent = {**_intent_v2(), "expected_outputs": ["mudou: True", "nunca aparece", "False 4"]}
        plano = Plan(subtasks=[Subtask(id=1, title="t", objective="o", files=["tomlkit/parser.py"],
                                       reproduction=[1, 2], expected=[1, 2, 3], done_when="d")])
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", lambda *a, **k: (plano, None))

        out = planner(_estado(intent=intent, turn_count=0, replans=0))

        # "False 4" já sai do código original (bloco 2 imprime "mudou: False 4"): não discrimina
        assert out["plan"]["saidas_na_base"] == [3]
        assert out["plan"]["subtasks"][0]["expected"] == [1, 2]
        cabecalho = llm.chamadas[0][1].content
        assert "JÁ produz" in cabecalho and cabecalho.rstrip().endswith("3.")
        ev = [e for e in read_events(tel.path) if e["event_type"] == "plan"][-1]["payload"]
        assert ev["saidas_na_base"] == [3] and [x["bloco"] for x in ev["execucoes_base"]] == [1, 2]

    def test_validador_ignora_essas_saidas_na_subtarefa_e_avisa_o_revisor(self, ambiente, monkeypatch):
        from src.agents.validator import validator

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        monkeypatch.setattr(config, "SUBTASK_CHECK", "deterministic")
        monkeypatch.setattr(config, "REVIEW_COMPARE", "advisory")
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        _mudanca_benigna(ws)
        montar(FakeToolCallingLLM([ai(content="x")]))
        chamadas: list = []

        def _estruturada(schema, messages, **k):
            chamadas.append(messages)
            return ValidationResult(is_valid=False, issues=["ainda falta"]), None
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _estruturada)
        estado = _estado_com_plano(stop_reason="concluiu")
        estado["plan"]["saidas_na_base"] = [2]
        estado["plan"]["subtasks"][0]["expected"] = [1, 2]  # 2 não foi saneada: o validador filtra de novo

        out = validator(estado)

        assert out["plan"]["status"][0]["status"] == "feita"  # só a saída 1 conta, e ela aparece
        usuario = chamadas[0][1][1]
        assert "fora da comparação: 2" in usuario and "saída esperada 2:" not in usuario
        ev = [e for e in read_events(tel.path) if e["event_type"] == "validation" and not e["payload"].get("scope")][-1]["payload"]
        assert [c["indice"] for c in ev["comparisons"]] == [1]


# ------------------------------------------------------------ rodada 6


@mirror_available
class TestRodada6:
    """
    Decisões 40 a 42 (16/10/2026, aprovadas por escrito): veredito híbrido da
    sub-tarefa, revisor final sem a frase de leniência e coerente, bloco de
    reprodução que não compila fora da evidência.
    """

    def _roda(self, ambiente, monkeypatch, estado, vereditos, *, mudanca=True, compare="neutral", strict="on"):
        from src.agents.validator import validator

        monkeypatch.setattr(config, "PLANNER", "on")
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        monkeypatch.setattr(config, "SUBTASK_CHECK", "hybrid")
        monkeypatch.setattr(config, "REVIEW_COMPARE", compare)
        monkeypatch.setattr(config, "REVIEW_STRICT", strict)
        monkeypatch.setattr(config, "REPRODUCTION_COMPILE_CHECK", "on")
        monkeypatch.setattr(config, "SUBTASK_MAX_CYCLES", 2)
        monkeypatch.setattr(config, "PLANNER_MAX_REPLANS", 1)
        monkeypatch.setenv("SEMANTIC_REVIEW", "true")
        ws, tel, montar = ambiente
        if mudanca:
            _mudanca_benigna(ws)
        montar(FakeToolCallingLLM([ai(content="x")]))
        fila = iter(vereditos)
        chamadas: list = []

        def _estruturada(schema, messages, **k):
            chamadas.append(messages)
            return next(fila), None
        monkeypatch.setattr("src.structured_llm.invoke_structured_raw", _estruturada)
        return validator(estado), tel, chamadas

    @staticmethod
    def _eventos(tel, scope):
        return [e["payload"] for e in read_events(tel.path)
                if e["event_type"] == "validation" and e["payload"].get("scope") == scope]

    def test_hibrido_com_saida_verificavel_decide_pela_comparacao_sem_o_modelo(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        out, tel, chamadas = self._roda(ambiente, monkeypatch, estado,
                                        [ValidationResult(is_valid=False, issues=["falta a parte 2"])])
        assert len(chamadas) == 1  # só a revisão final consultou o modelo
        assert [s["status"] for s in out["plan"]["status"]] == ["feita", "em_andamento"]
        ev = self._eventos(tel, "subtask")[-1]
        assert ev["basis"] == "comparacao" and ev["deterministic"] is True

    def test_hibrido_sem_saida_verificavel_consulta_o_revisor_de_subtarefa_e_a_palavra_nao_vale(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        estado["plan"]["subtasks"][0]["expected"] = []
        # 1ª chamada: revisão final (reprova); 2ª: revisão da sub-tarefa (não feita, com motivo)
        out, tel, chamadas = self._roda(
            ambiente, monkeypatch, estado,
            [ValidationResult(is_valid=False), ValidationResult(is_valid=False, issues=["falta tratar o caso x"])],
        )
        assert len(chamadas) == 2
        assert out["plan"]["status"][0]["status"] == "em_andamento" and out["subtask_current"] == 1
        assert out["subtask_review"]["issues"] == ["falta tratar o caso x"]
        ev = self._eventos(tel, "subtask")[-1]
        assert ev["basis"] == "revisao_do_modelo" and "deterministic" not in ev
        assert "Execução dos exemplos desta sub-tarefa" in chamadas[1][1][1]  # execução reaproveitada
        # quando o revisor de sub-tarefa a dá por feita, o plano avança
        out2, _, chamadas2 = self._roda(ambiente, monkeypatch, estado,
                                        [ValidationResult(is_valid=False), ValidationResult(is_valid=True)])
        assert len(chamadas2) == 2
        assert out2["plan"]["status"][0]["status"] == "feita" and out2["subtask_current"] == 2
        # e aprovar listando critério faltando não fecha (REVIEW_STRICT=on vale na sub-tarefa)
        out3, _, _ = self._roda(ambiente, monkeypatch, estado,
                                [ValidationResult(is_valid=False), ValidationResult(is_valid=True, missing_criteria=["2"])])
        assert out3["plan"]["status"][0]["status"] == "em_andamento"

    def test_hibrido_com_suite_vermelha_nao_consulta_o_modelo(self, ambiente, monkeypatch):
        ws, _, _ = ambiente
        ws.resolve("tomlkit/_utils.py").write_text("def (\n")  # suíte não coleta
        estado = _estado_com_plano(stop_reason="concluiu")
        estado["plan"]["subtasks"][0]["expected"] = []
        out, tel, chamadas = self._roda(ambiente, monkeypatch, estado, [], mudanca=False)
        assert chamadas == [] and out["is_valid"] is False
        ev = self._eventos(tel, "subtask")[-1]
        assert ev["basis"] == "suite_vermelha" and out["plan"]["status"][0]["status"] == "em_andamento"

    def test_neutral_leva_a_comparacao_sem_a_regra_e_strict_rebaixa_aprovacao_com_criterio_faltando(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        out, tel, chamadas = self._roda(ambiente, monkeypatch, estado,
                                        [ValidationResult(is_valid=True, missing_criteria=["5"])])
        assert len(chamadas) == 1  # revisão final coagida; sub-tarefa 1 feita por comparação, sem o modelo
        sistema, usuario = chamadas[0][0][1], chamadas[0][1][1]
        assert "não verificável não prova nada" not in sistema
        assert "Comparação automática das saídas esperadas" in usuario and "- saída esperada 1: encontrada" in usuario
        final = self._eventos(tel, None)[-1]
        assert final["strict_coerced"] is True and final["is_valid"] is False and out["is_valid"] is False
        assert out["plan"]["status"][0]["status"] == "feita"

    def test_bloco_que_nao_compila_sai_da_cadeia_e_e_rotulado(self, ambiente, monkeypatch):
        from src.agents.validator import _executar_reproducao
        from src.verificacao import comparar_saidas

        _, _, montar = ambiente
        montar(FakeToolCallingLLM([ai(content="x")]))
        intent = _intent_v2()
        intent["reproduction"] = ["x = 2", "a = [{a]", "print('soma:', x + 2)"]
        estado = _estado(intent=intent)
        monkeypatch.setattr(config, "REVIEW_EXECUTION", "cumulative")
        monkeypatch.setattr(config, "REPRODUCTION_COMPILE_CHECK", "off")
        sem = _executar_reproducao(estado, _ctx(montar))
        assert "SyntaxError" in sem[1]["saida"] and "SyntaxError" in sem[2]["saida"]  # rodada 5: o 2º envenena o 3º
        monkeypatch.setattr(config, "REPRODUCTION_COMPILE_CHECK", "on")
        com = _executar_reproducao(estado, _ctx(montar))
        assert com[1]["executado"] is False and com[1]["nao_compila"] is True
        assert "não compila como Python" in com[1]["saida"] and "SyntaxError na linha 1" in com[1]["saida"]
        assert com[2]["executado"] is True and com[2]["acumulado"] is True and "soma: 4" in com[2]["saida"]
        # a comparação vê o que rodou; o que falta com um bloco do conjunto parado é não verificável, nunca "NÃO encontrada"
        assert [c["estado"] for c in comparar_saidas([(1, "soma: 4"), (2, "nunca")], com)] == ["encontrada", "nao_verificavel"]
        assert [c["estado"] for c in comparar_saidas([(1, "soma: 4"), (2, "nunca")], [com[0], com[2]])] == ["encontrada", "nao_encontrada"]
        assert [c["estado"] for c in comparar_saidas([(1, "soma: 4")], [com[1]])] == ["nao_verificavel"]

    def test_bloco_nao_executado_e_linha_nao_verificavel_nao_chegam_ao_revisor(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        estado["intent"]["reproduction"] = [
            "x = 2", "a = [{a]", "print('mudou:', 'nota do agente' in open('tomlkit/_utils.py').read(), x + 2)",
        ]
        estado["plan"]["subtasks"][0].update(reproduction=[1, 2, 3], expected=[1, 2])
        out, tel, chamadas = self._roda(ambiente, monkeypatch, estado, [ValidationResult(is_valid=False)])
        usuario = chamadas[0][1][1]
        assert "[bloco 1]" in usuario and "[bloco 3]" in usuario and "mudou: True" in usuario
        assert "[bloco 2]" not in usuario and "não compila" not in usuario and "SyntaxError" not in usuario
        assert "- saída esperada 1: encontrada" in usuario and "saída esperada 2" not in usuario
        final = self._eventos(tel, None)[-1]
        # o evento guarda tudo: as três execuções (uma rotulada) e os dois estados
        assert [e["executado"] for e in final["executions"]] == [True, False, True]
        assert [c["estado"] for c in final["comparisons"]] == ["encontrada", "nao_verificavel"]
        assert out["plan"]["status"][0]["status"] == "feita"  # sub-tarefa fechou pela saída 1, encontrada

    def test_comparacao_final_por_subtarefa_nao_inventa_nao_encontrada(self, ambiente, monkeypatch):
        estado = _estado_com_plano(stop_reason="concluiu")
        estado["plan"]["subtasks"][1]["reproduction"] = []  # saída 2 apontada por sub-tarefa sem bloco
        _, tel, chamadas = self._roda(ambiente, monkeypatch, estado, [ValidationResult(is_valid=False)])
        final = self._eventos(tel, None)[-1]
        assert [(c["indice"], c["estado"]) for c in final["comparisons"]] == [(1, "encontrada"), (2, "nao_verificavel")]
        assert "saída esperada 2" not in chamadas[0][1][1]
        # com o bloco apontado, a saída 2 volta a ser "NÃO encontrada" de verdade (rodada 5 e `advisory` idem)
        estado2 = _estado_com_plano(stop_reason="concluiu")
        _, tel2, chamadas2 = self._roda(ambiente, monkeypatch, estado2, [ValidationResult(is_valid=False)])
        assert [c["estado"] for c in self._eventos(tel2, None)[-1]["comparisons"]] == ["encontrada", "nao_encontrada"]
        assert "- saída esperada 2: NÃO encontrada" in chamadas2[0][1][1]

    def test_manifesto_registra_a_rodada_6(self, monkeypatch):
        from src.arms.runner import _orchestration_policy

        monkeypatch.setattr(config, "SUBTASK_CHECK", "hybrid")
        monkeypatch.setattr(config, "REVIEW_COMPARE", "neutral")
        monkeypatch.setattr(config, "REVIEW_STRICT", "on")
        monkeypatch.setattr(config, "REPRODUCTION_COMPILE_CHECK", "on")
        pol = _orchestration_policy()
        assert (pol["subtask_check"], pol["review_compare"], pol["review_strict"], pol["reproduction_compile_check"]) \
            == ("hybrid", "neutral", "on", "on")

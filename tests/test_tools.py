"""Testes das ferramentas do agente sobre um workspace real do tomlkit."""

from __future__ import annotations

import pytest

from src.schemas.test_report import TestReport
from src.seeds import TOMLKIT
from src.tools import TOOL_NAMES, build_toolset
from src.tools.base import ToolCallRecord
from src.tools.exec import parse_pytest_output, run_pytest
from src.tools.fs import DENIED_PREFIX, ERROR_PREFIX
from src.workspace import Workspace, WorkspaceSpec

BASE_COMMIT = "11e22aefccd8069a90ae75d20613b9b1068754a1"

mirror_available = pytest.mark.skipif(
    not TOMLKIT.mirror_path.exists(),
    reason="espelho ausente — rode scripts/setup_mirror.py tomlkit",
)


@pytest.fixture(scope="module")
def ws(tmp_path_factory) -> Workspace:
    spec = WorkspaceSpec(seed_repo=TOMLKIT, base_commit=BASE_COMMIT)
    dest = tmp_path_factory.mktemp("uranium_tools") / "tomlkit"
    return Workspace.materialize(spec, run_id="tools-test", dest=dest)


@pytest.fixture
def captured() -> list[ToolCallRecord]:
    return []


@pytest.fixture
def tools(ws, captured):
    """Toolset com emissor capturando os registros de telemetria."""
    return {t.name: t for t in build_toolset(ws, emit=captured.append)}


@pytest.fixture(autouse=True)
def _restaura_workspace(request, ws):
    """Desfaz qualquer alteração entre testes — cada um começa do commit-base."""
    yield
    if "ws" in request.fixturenames:
        import subprocess
        subprocess.run(["git", "checkout", "--quiet", "--", "."], cwd=ws.root)
        subprocess.run(["git", "clean", "-qfd", "--exclude=tests/toml-test"], cwd=ws.root)


# ------------------------------------------------------------------- contrato


@mirror_available
def test_toolset_expoe_exatamente_as_ferramentas_acordadas(tools):
    """Os dois braços recebem o mesmo conjunto; divergência quebra a comparação."""
    assert set(tools) == set(TOOL_NAMES)


@mirror_available
def test_todas_as_ferramentas_tem_schema_de_args(tools):
    for name, tool in tools.items():
        assert tool.args_schema is not None, name
        assert tool.description, name


# --------------------------------------------------------------- list / read


@mirror_available
class TestLeitura:
    def test_list_files_encontra_fonte(self, tools):
        out = tools["list_files"].invoke({"path": "tomlkit", "pattern": "*.py"})
        assert "tomlkit/items.py" in out and "tomlkit/container.py" in out

    def test_read_file_numera_linhas(self, tools):
        out = tools["read_file"].invoke({"path": "tomlkit/_utils.py", "start_line": 1, "end_line": 5})
        assert "linhas 1-5 de" in out
        numeradas = [l for l in out.splitlines()[1:] if "\t" in l]
        assert len(numeradas) == 5
        assert [l.split("\t")[0].strip() for l in numeradas] == ["1", "2", "3", "4", "5"]

    def test_read_file_faixa_respeitada(self, tools):
        out = tools["read_file"].invoke({"path": "tomlkit/_utils.py", "start_line": 10, "end_line": 12})
        assert "linhas 10-12" in out
        assert len([l for l in out.splitlines() if "\t" in l]) == 3

    def test_read_file_arquivo_grande_vem_truncado(self, tools):
        """items.py tem ~2400 linhas; o agente é forçado a paginar ou buscar."""
        out = tools["read_file"].invoke({"path": "tomlkit/items.py"})
        assert "truncado" in out

    def test_read_file_inexistente_devolve_erro_recuperavel(self, tools):
        out = tools["read_file"].invoke({"path": "tomlkit/nao_existe.py"})
        assert out.startswith(ERROR_PREFIX)

    def test_read_file_diretorio_orienta_uso_correto(self, tools):
        out = tools["read_file"].invoke({"path": "tomlkit"})
        assert out.startswith(ERROR_PREFIX) and "list_files" in out


# ------------------------------------------------------------------- search


@mirror_available
class TestBusca:
    def test_search_code_localiza_definicao(self, tools):
        out = tools["search_code"].invoke({"pattern": r"class Container", "path": "tomlkit"})
        assert "tomlkit/container.py:" in out

    def test_search_code_literal(self, tools):
        out = tools["search_code"].invoke(
            {"pattern": "def parse(", "path": "tomlkit", "is_regex": False}
        )
        assert ".py:" in out

    def test_search_code_regex_invalida_nao_derruba(self, tools):
        out = tools["search_code"].invoke({"pattern": "[unclosed", "path": "tomlkit"})
        assert out.startswith(ERROR_PREFIX)

    def test_search_code_sem_ocorrencia(self, tools):
        out = tools["search_code"].invoke({"pattern": "zzz_nao_existe_zzz", "path": "tomlkit"})
        assert "Nenhuma ocorrência" in out


# -------------------------------------------------------------------- escrita


@mirror_available
class TestEscrita:
    def test_write_file_grava_em_fonte(self, tools, ws):
        out = tools["write_file"].invoke(
            {"path": "tomlkit/marcador.py", "content": "VALOR = 42\n"}
        )
        assert out.startswith("Gravado")
        assert (ws.root / "tomlkit" / "marcador.py").read_text() == "VALOR = 42\n"
        assert "tomlkit/marcador.py" in ws.changed_files()

    @pytest.mark.parametrize(
        "protegido",
        ["tests/test_items.py", "pyproject.toml", "tox.ini", "tests/novo_teste.py"],
    )
    def test_write_file_recusa_area_protegida(self, tools, ws, protegido):
        antes = (ws.root / protegido).read_bytes() if (ws.root / protegido).exists() else None
        out = tools["write_file"].invoke({"path": protegido, "content": "# trapaca\n"})
        assert out.startswith(DENIED_PREFIX)
        # o arquivo em disco não pode ter mudado
        depois = (ws.root / protegido).read_bytes() if (ws.root / protegido).exists() else None
        assert antes == depois
        assert ws.protected_touched() == []

    def test_write_file_recusa_escape_do_workspace(self, tools):
        out = tools["write_file"].invoke({"path": "../../invadido.py", "content": "x"})
        assert out.startswith(DENIED_PREFIX)

    def test_write_file_recusa_area_git(self, tools):
        out = tools["write_file"].invoke({"path": ".git/config", "content": "x"})
        assert out.startswith(DENIED_PREFIX)

    def test_write_file_cria_diretorio_intermediario(self, tools, ws):
        out = tools["write_file"].invoke({"path": "tomlkit/sub/novo.py", "content": "A = 1\n"})
        assert out.startswith("Gravado")
        assert (ws.root / "tomlkit" / "sub" / "novo.py").exists()


# ------------------------------------------------------------------- execução


@mirror_available
class TestExecucao:
    def test_run_tests_verde_no_commit_base(self, tools):
        out = tools["run_tests"].invoke({"node_ids": []})
        assert "Suíte verde" in out, out[:500]

    def test_run_pytest_devolve_report_estruturado(self, ws):
        report = run_pytest(ws)
        assert isinstance(report, TestReport)
        assert report.green and report.exit_code == 0
        assert report.passed > 1000
        assert report.failing_node_ids == []

    def test_bug_injetado_reprova_e_da_node_id(self, ws, tools):
        """O ponto do experimento: falha real, com node id reutilizável."""
        alvo = ws.root / "tomlkit" / "_utils.py"
        original = alvo.read_text()
        alvo.write_text(original.replace("import re", "import re\nraise RuntimeError('bug')", 1))

        report = run_pytest(ws)
        alvo.write_text(original)

        assert not report.green
        assert report.exit_code != 0
        assert report.errors + report.failed > 0

    def test_run_tests_com_node_ids_roda_subconjunto(self, ws):
        report = run_pytest(ws, ["tests/test_api.py"])
        assert report.green
        assert 0 < report.passed < 1000  # subconjunto, não a suíte toda

    def test_node_id_que_escapa_e_ignorado(self, ws):
        """Node id malicioso não pode fazer o pytest rodar fora do workspace."""
        report = run_pytest(ws, ["../../../etc/passwd::test_x"])
        # sem alvos válidos, roda a suíte inteira em vez de sair do workspace
        assert report.passed > 1000

    def test_timeout_marcado_no_report(self, ws):
        report = run_pytest(ws, timeout_s=0)
        assert report.timed_out and report.exit_code == -1


# ------------------------------------------------------------------- parsing


class TestParsePytestOutput:
    """O parser não pode depender de workspace — testado isoladamente."""

    def test_tudo_verde(self):
        r = parse_pytest_output("1030 passed in 1.84s", 0, 0.0)
        assert r["passed"] == 1030 and r["failed"] == 0 and r["duration_s"] == 1.84

    def test_falhas_com_node_ids(self):
        out = (
            "FAILED tests/test_items.py::test_integer - assert 1 == 2\n"
            "ERROR tests/test_api.py::test_parse\n"
            "1 failed, 1 error, 1028 passed in 2.10s"
        )
        r = parse_pytest_output(out, 1, 0.0)
        assert r["failed"] == 1 and r["errors"] == 1 and r["passed"] == 1028
        assert r["failing_node_ids"] == [
            "tests/test_api.py::test_parse",
            "tests/test_items.py::test_integer",
        ]

    def test_plural_de_errors(self):
        r = parse_pytest_output("3 errors in 0.5s", 1, 0.0)
        assert r["errors"] == 3

    def test_skipped_e_xfailed(self):
        r = parse_pytest_output("10 passed, 2 skipped, 1 xfailed in 0.3s", 0, 0.0)
        assert r["skipped"] == 2 and r["xfailed"] == 1

    def test_sem_testes_coletados(self):
        r = parse_pytest_output("no tests ran in 0.01s", 5, 0.9)
        assert r["passed"] == 0 and r["duration_s"] == 0.9


# ---------------------------------------------------------------- telemetria


@mirror_available
class TestTelemetria:
    def test_uma_chamada_um_registro(self, tools, captured):
        tools["read_file"].invoke({"path": "tomlkit/_utils.py", "start_line": 1, "end_line": 3})
        assert len(captured) == 1
        assert captured[0].tool_name == "read_file"
        assert captured[0].bytes_read > 0
        assert captured[0].denied is False

    def test_recusa_e_marcada(self, tools, captured):
        tools["write_file"].invoke({"path": "tests/test_items.py", "content": "x"})
        assert captured[-1].denied is True
        assert captured[-1].bytes_written == 0

    def test_escrita_contabiliza_bytes(self, tools, captured):
        tools["write_file"].invoke({"path": "tomlkit/t.py", "content": "AB\n"})
        assert captured[-1].bytes_written == 3
        assert captured[-1].denied is False

    def test_args_hash_estavel_e_discriminante(self, tools, captured):
        args = {"path": "tomlkit/_utils.py", "start_line": 1, "end_line": 3}
        tools["read_file"].invoke(args)
        tools["read_file"].invoke(args)
        tools["read_file"].invoke({**args, "end_line": 9})
        assert captured[0].args_hash == captured[1].args_hash
        assert captured[2].args_hash != captured[0].args_hash

    def test_duracao_registrada(self, tools, captured):
        tools["run_tests"].invoke({"node_ids": ["tests/test_api.py"]})
        assert captured[-1].duration_ms > 0


# ------------------------------------------------- integração com a telemetria


@mirror_available
class TestIntegracaoTelemetria:
    """As ferramentas reais têm de produzir eventos válidos contra o schema."""

    @pytest.fixture
    def writer(self, tmp_path):
        from src.telemetry import TelemetryWriter

        w = TelemetryWriter(
            tmp_path / "events.jsonl",
            run_id="int-001", arm="orchestration", task_id="tomlkit-0001",
            model="vendor/modelo", provider_requested="Fireworks",
        )
        yield w
        w.close()

    def test_uso_real_das_ferramentas_gera_eventos_validos(self, ws, writer):
        import json
        from pathlib import Path

        from jsonschema import Draft202012Validator

        from src.telemetry import read_events

        validator = Draft202012Validator(
            json.loads(Path("harness/schema/event.schema.json").read_text())
        )
        tools = {t.name: t for t in build_toolset(ws, emit=writer.emit_tool_call)}

        writer.run_start(base_commit=BASE_COMMIT)
        with writer.node("developer", agent_role="developer"):
            writer.set_turn(1)
            tools["search_code"].invoke({"pattern": "class Container", "path": "tomlkit"})
            tools["read_file"].invoke({"path": "tomlkit/_utils.py", "start_line": 1, "end_line": 5})
            tools["write_file"].invoke({"path": "tests/test_items.py", "content": "# trapaca"})
            tools["write_file"].invoke({"path": "tomlkit/novo.py", "content": "A = 1\n"})
        writer.run_end(stop_reason="tests_pass")

        eventos = read_events(writer.path)
        for evento in eventos:
            validator.validate(evento)

        chamadas = [e for e in eventos if e["event_type"] == "tool_call"]
        assert len(chamadas) == 4
        assert [c["tool_name"] for c in chamadas] == [
            "search_code", "read_file", "write_file", "write_file",
        ]
        # a tentativa de escrever num teste ficou registrada como recusa
        assert [c["tool_denied"] for c in chamadas] == [False, False, True, False]
        # contexto do nó foi herdado por todas
        assert all(c["node"] == "developer" and c["turn"] == 1 for c in chamadas)

    def test_execucao_de_testes_vira_evento(self, ws, writer):
        from src.telemetry import read_events
        from src.tools.exec import run_pytest

        writer.emit_test_run(run_pytest(ws, ["tests/test_api.py"]))

        evento = read_events(writer.path)[-1]
        assert evento["event_type"] == "test_run"
        assert evento["tool_exit_code"] == 0
        assert evento["payload"]["green"] is True
        assert evento["payload"]["passed"] > 0


class TestNodeIdParametrizado:
    """
    O node id vai até o fim da linha, não até o primeiro espaço.

    `\\S+` truncava `test_x[SET NULL]` em `test_x[SET`, que o pytest não sabe
    reexecutar. Como o fail-to-pass de cada tarefa é escrito a partir dessa
    extração, o oráculo saía inútil — e em silêncio, porque um node id
    inexistente vira "erro de coleta", não "id errado".
    """

    SAIDA = (
        "FAILED tests/test_transform.py::test_refuses[SET NULL] - AssertionError: x\n"
        "FAILED tests/test_transform.py::test_refuses[CASCADE]\n"
        "ERROR tests/test_z.py\n"
        "2 failed, 3 passed in 0.5s"
    )

    def test_preserva_espaco_dentro_do_parametro(self):
        from src.tools.exec import parse_pytest_output

        ids = parse_pytest_output(self.SAIDA, 1, 0.5)["failing_node_ids"]
        assert "tests/test_transform.py::test_refuses[SET NULL]" in ids

    def test_descarta_a_mensagem_depois_do_hifen(self):
        from src.tools.exec import parse_pytest_output

        ids = parse_pytest_output(self.SAIDA, 1, 0.5)["failing_node_ids"]
        assert all("AssertionError" not in i for i in ids)
        assert len(ids) == 3

    def test_harness_extrai_igual_ao_src(self):
        """Divergência aqui faz o agente e o avaliador falarem de testes diferentes."""
        from harness.pytest_runner import parse_output
        from src.tools.exec import parse_pytest_output

        assert (sorted(parse_output(self.SAIDA, 0.5)["failing_node_ids"])
                == sorted(parse_pytest_output(self.SAIDA, 1, 0.5)["failing_node_ids"]))


class TestContabilidadeDeContexto:
    """
    Toda ferramenta mede o tamanho do que devolve ao modelo.

    O consumo de token cresce com o quadrado dos turnos porque o contexto é
    reenviado inteiro, e cada saída de ferramenta entra nele. Enquanto só
    read_file, search_code e list_files eram medidos, run_python e run_tests
    — metade das chamadas — ficavam fora da conta, e não dava para explicar
    de onde vinha a diferença de custo entre os braços.
    """

    def test_toda_ferramenta_registra_o_tamanho_da_saida(self, ws):
        from src.tools import TOOL_NAMES, build_toolset

        registros = []
        tools = {t.name: t for t in build_toolset(ws, emit=registros.append)}
        chamadas = {
            "list_files": {},
            "read_file": {"path": "tomlkit/parser.py", "start_line": 1, "end_line": 20},
            "search_code": {"pattern": "def parse"},
            "run_python": {"code": "print('oi')"},
            "write_file": {"path": "novo.py", "content": "x = 1\n"},
            "replace_in_file": {"path": "novo.py", "old_text": "x = 1", "new_text": "x = 2"},
        }
        for nome, args in chamadas.items():
            tools[nome].invoke(args)

        assert {r.tool_name for r in registros} == set(chamadas)
        for r in registros:
            assert r.bytes_read > 0, f"{r.tool_name} não mediu a saída devolvida ao modelo"

    def test_escrita_mede_os_dois_lados(self, ws):
        from src.tools import build_toolset

        registros = []
        tools = {t.name: t for t in build_toolset(ws, emit=registros.append)}
        tools["write_file"].invoke({"path": "n.py", "content": "a = 1\n" * 100})

        r = registros[0]
        assert r.bytes_written == len(("a = 1\n" * 100).encode())
        assert r.bytes_read > 0, "a confirmação devolvida ao modelo também ocupa contexto"

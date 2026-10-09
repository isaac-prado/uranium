"""
Testes do avaliador externo.

O ponto mais importante aqui é o primeiro: o harness não pode importar
nada de `src/`. Se importasse, a corretude reportada no TCC passaria a
depender das mesmas suposições que o agente usou para decidir que
terminou — deixaria de ser verificação independente.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from harness import HARNESS_VERSION, RESULT_SCHEMA_VERSION
from harness.cheat import CheatReport, CheatSignal, detect
from harness.cost import aggregate_cost, aggregate_process, providers_served, self_recoveries
from harness.pytest_runner import network_isolation_available, parse_output
from harness.quality import measure
from harness.taskspec import load_task

RAIZ = Path(__file__).resolve().parent.parent
TAREFA = RAIZ / "tasks" / "tomlkit-0001"


# ------------------------------------------------------------- independência


class TestIndependenciaDoPipeline:
    def test_harness_nao_importa_src(self):
        achados = subprocess.run(
            ["grep", "-rnE", r"^\s*(from|import)\s+src\b", "--include=*.py", "harness"],
            cwd=RAIZ, capture_output=True, text=True,
        ).stdout.strip()
        assert not achados, f"o avaliador passou a depender do pipeline:\n{achados}"

    def test_importa_sem_o_pipeline_no_path(self, tmp_path):
        """Precisa rodar mesmo num ambiente onde src/ não exista."""
        script = "import harness.evaluate, harness.oracle, harness.cheat; print('ok')"
        saida = subprocess.run(
            [sys.executable, "-c", script], cwd=RAIZ,
            capture_output=True, text=True, env={"PYTHONPATH": str(RAIZ), "PATH": "/usr/bin:/bin"},
        )
        assert saida.returncode == 0, saida.stderr
        assert "ok" in saida.stdout


# ------------------------------------------------------------------- schemas


class TestSchemas:
    def test_schema_de_resultado_e_valido(self):
        esquema = json.loads((RAIZ / "harness/schema/result.schema.json").read_text())
        Draft202012Validator.check_schema(esquema)

    def test_versoes_declaradas(self):
        assert RESULT_SCHEMA_VERSION == 2 and HARNESS_VERSION


# --------------------------------------------------------------- parsing


class TestParsePytest:
    def test_verde(self):
        r = parse_output("1030 passed in 1.8s", 0.0)
        assert r["passed"] == 1030 and r["failed"] == 0

    def test_falhas_com_node_ids(self):
        saida = (
            "FAILED tests/test_a.py::test_x - assert 1 == 2\n"
            "ERROR tests/test_b.py::test_y\n"
            "1 failed, 1 error, 100 passed in 3.0s"
        )
        r = parse_output(saida, 0.0)
        assert r["failed"] == 1 and r["errors"] == 1
        assert r["failing_node_ids"] == ["tests/test_a.py::test_x", "tests/test_b.py::test_y"]

    def test_isolamento_de_rede_disponivel(self):
        """O caminho de avaliação não pode depender de rede."""
        assert network_isolation_available(), "unshare indisponível: avaliação não isolada"


# ------------------------------------------------------------- agregação


class TestAgregacao:
    EVENTOS = [
        {"event_type": "llm_call", "tokens_total": 100, "cost_usd": 0.01, "turn": 1,
         "provider_served": "DeepInfra"},
        {"event_type": "tool_call", "tool_denied": True, "turn": 1},
        {"event_type": "test_run", "turn": 2, "payload": {"green": False}},
        {"event_type": "test_run", "turn": 3, "payload": {"green": True}},
        {"event_type": "run_end", "elapsed_ms": 45000, "payload": {"stop_reason": "tests_pass"}},
    ]

    def test_custo(self):
        c = aggregate_cost(self.EVENTOS)
        assert c["tokens_total"] == 100 and c["cost_usd"] == 0.01
        assert c["llm_calls"] == 1 and c["tool_calls"] == 1
        assert c["wall_seconds"] == 45.0

    def test_processo(self):
        p = aggregate_process(self.EVENTOS)
        assert p["turns"] == 3 and p["test_runs"] == 2
        assert p["tool_denials"] == 1 and p["self_recoveries"] == 1
        assert p["stop_reason"] == "tests_pass"

    def test_provedor_unico_significa_pino_mantido(self):
        assert providers_served(self.EVENTOS) == ["DeepInfra"]

    def test_provedor_variado_fica_visivel(self):
        eventos = self.EVENTOS + [{"event_type": "llm_call", "provider_served": "Novita"}]
        assert providers_served(eventos) == ["DeepInfra", "Novita"]

    def test_auto_recuperacao(self):
        assert self_recoveries([
            {"event_type": "test_run", "payload": {"green": False}},
            {"event_type": "test_run", "payload": {"green": True}},
        ]) == 1

    def test_telemetria_ausente_nao_derruba(self):
        assert aggregate_cost([])["tokens_total"] == 0
        assert aggregate_process([])["stop_reason"] is None


# ------------------------------------------------------- detector (unitário)


class TestDetectorAST:
    """
    As regras de AST comparam antes e depois: construção que já existia no
    commit-base não pode ser acusada.
    """

    @pytest.fixture
    def repo(self, tmp_path):
        """Repositório git mínimo, com tag de base."""
        r = tmp_path / "repo"
        (r / "pkg").mkdir(parents=True)
        (r / "pkg" / "mod.py").write_text(
            "def f(x):\n"
            "    try:\n"
            "        return int(x)\n"
            "    except ValueError:\n"
            "        pass\n"
        )
        for cmd in (["init", "-q"], ["add", "-A"]):
            subprocess.run(["git", *cmd], cwd=r, check=True, capture_output=True)
        for k, v in (("user.email", "t@t"), ("user.name", "t")):
            subprocess.run(["git", "config", k, v], cwd=r, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=r, check=True, capture_output=True)
        subprocess.run(["git", "tag", "uranium-base"], cwd=r, check=True)
        return r

    def test_repo_intocado_nao_dispara_nada(self, repo):
        assert detect(repo, ("tests/**",)).clean

    def test_except_pass_preexistente_nao_e_acusado(self, repo):
        """O try/except que já estava lá não é trapaça do agente."""
        (repo / "pkg" / "mod.py").write_text(
            (repo / "pkg" / "mod.py").read_text() + "\n\ndef g():\n    return 1\n"
        )
        r = detect(repo, ("tests/**",))
        assert not [s for s in r.signals if s.rule == "C6"]

    def test_except_pass_novo_vira_aviso(self, repo):
        (repo / "pkg" / "mod.py").write_text(
            (repo / "pkg" / "mod.py").read_text()
            + "\n\ndef g(y):\n    try:\n        return y.z\n    except AttributeError:\n        pass\n"
        )
        sinais = [s for s in detect(repo, ("tests/**",)).signals if s.rule == "C6"]
        assert len(sinais) == 1 and sinais[0].severity == "warning"

    def test_aviso_sozinho_nao_reprova(self, repo):
        (repo / "pkg" / "mod.py").write_text(
            (repo / "pkg" / "mod.py").read_text()
            + "\n\ndef g(y):\n    try:\n        return y.z\n    except AttributeError:\n        pass\n"
        )
        assert detect(repo, ("tests/**",)).clean

    def test_skip_em_docstring_nao_e_falso_positivo(self, repo):
        """Regex acusaria; AST não."""
        (repo / "pkg" / "mod.py").write_text(
            '"""Não use @pytest.mark.skip aqui."""\n\ndef f():\n    return 1\n'
        )
        assert not [s for s in detect(repo, ("tests/**",)).signals if s.rule == "C3"]

    def test_skip_real_e_acusado(self, repo):
        (repo / "pkg" / "mod.py").write_text(
            "import pytest\n\n\n@pytest.mark.skip\ndef f():\n    return 1\n"
        )
        sinais = [s for s in detect(repo, ("tests/**",)).signals if s.rule == "C3"]
        assert sinais and sinais[0].severity == "critical"

    def test_arquivo_protegido_alterado(self, repo):
        (repo / "tests").mkdir()
        (repo / "tests" / "test_x.py").write_text("def test_x(): assert True\n")
        r = detect(repo, ("tests/**",))
        assert not r.clean and any(s.rule == "C1" for s in r.signals)

    def test_conftest_criado(self, repo):
        (repo / "conftest.py").write_text("collect_ignore = ['pkg']\n")
        r = detect(repo, ())
        assert not r.clean and any(s.rule == "C4" for s in r.signals)

    def test_referencia_ao_diretorio_oculto(self, repo):
        (repo / "pkg" / "mod.py").write_text("PATH = 'tests/_uranium_hidden'\n")
        r = detect(repo, ())
        assert not r.clean and any(s.rule == "C7" for s in r.signals)

    def test_relatorio_serializavel(self, repo):
        (repo / "conftest.py").write_text("x = 1\n")
        d = detect(repo, ()).as_dict()
        assert json.loads(json.dumps(d)) == d
        assert d["critical_count"] >= 1


class TestSeveridade:
    def test_apenas_avisos_continua_limpo(self):
        r = CheatReport([CheatSignal("C6", "warning", "a.py", "x")])
        assert r.clean and r.as_dict()["warning_count"] == 1

    def test_um_critico_suja(self):
        r = CheatReport([CheatSignal("C1", "critical", "a.py", "x")])
        assert not r.clean


# ------------------------------------------------------------------ tarefa


class TestEspecificacaoDeTarefa:
    def test_carrega_a_primeira_tarefa(self):
        t = load_task(TAREFA)
        assert t.task_id == "tomlkit-0001"
        assert t.seed_repo_id == "tomlkit"
        assert len(t.fail_to_pass) >= 1
        assert len(t.reference_patches) >= 2, "duas referências são obrigatórias"
        assert len(t.cheat_patches) >= 1

    def test_enunciado_nao_revela_a_solucao(self):
        """O enunciado descreve o sintoma, não onde nem como corrigir."""
        enunciado = load_task(TAREFA).statement
        assert enunciado
        for vazamento in ("parser.py", "_parse_value", "try:", "except UnexpectedCharError"):
            assert vazamento not in enunciado, f"o enunciado entrega a solução: {vazamento}"

    def test_arquivos_referenciados_existem(self):
        t = load_task(TAREFA)
        for rel in (*t.hidden_tests, *t.reference_patches, *t.cheat_patches):
            assert (t.root / rel).exists(), rel

    def test_campos_obrigatorios_sao_exigidos(self, tmp_path):
        (tmp_path / "task.json").write_text('{"id": "x"}')
        with pytest.raises(ValueError, match="obrigatórios"):
            load_task(tmp_path)


# --------------------------------------------------------------------- faixa
#
# E3 item 2: `faixa` era gravada no task.json e ignorada pelo TaskSpec, então
# não aparecia no result.json — eixo de análise do TCC tratado como metadado
# decorativo. Os testes abaixo cobrem as duas pontas: o TaskSpec carrega a
# faixa (presente ou ausente, sem inventar valor) e o avaliador a propaga
# até o result.json, respeitando o schema.


class TestFaixa:
    def _task_minima(self, tmp_path: Path, *, com_faixa: bool) -> Path:
        raiz = tmp_path / "task"
        raiz.mkdir()
        dados = {
            "id": "faixa-0001",
            "seed_repo": "tomlkit",
            "base_commit": "11e22aefccd8069a90ae75d20613b9b1068754a1",
            "hidden_tests": ["hidden/test_x.py"],
            "fail_to_pass": ["tests/_uranium_hidden/test_x.py::test_x"],
        }
        if com_faixa:
            dados["faixa"] = "media"
        (raiz / "task.json").write_text(json.dumps(dados), encoding="utf-8")
        (raiz / "hidden").mkdir()
        (raiz / "hidden" / "test_x.py").write_text("def test_x():\n    assert True\n")
        return raiz

    def test_taskspec_carrega_faixa_presente(self, tmp_path):
        t = load_task(self._task_minima(tmp_path, com_faixa=True))
        assert t.faixa == "media"

    def test_taskspec_nao_inventa_faixa_ausente(self, tmp_path):
        t = load_task(self._task_minima(tmp_path, com_faixa=False))
        assert t.faixa is None

    def test_tarefas_reais_tem_ou_nao_faixa_conforme_task_json(self):
        """
        Documenta o estado real das duas tarefas de 19/09 (item 5 da
        exigência): as duas declaram faixa `pequena` desde 08/10/2026
        (tomlkit-0001 não tinha faixa; sqlite-utils-0001 era "media" e foi
        reclassificada pela regra da decisão 22: 1 arquivo, 34 linhas).
        O TaskSpec lê o que está no task.json e não inventa nada.
        """
        assert load_task(TAREFA).faixa == "pequena"
        assert load_task(RAIZ / "tasks" / "sqlite-utils-0001").faixa == "pequena"


class TestFaixaNoResultado:
    """O avaliador propaga `task.faixa` até o result.json, sob o schema."""

    def test_schema_aceita_faixa_null(self):
        esquema = json.loads((RAIZ / "harness/schema/result.schema.json").read_text())
        validador = Draft202012Validator(esquema)
        resultado = _resultado_minimo(faixa=None)
        validador.validate(resultado)

    def test_evaluate_run_preenche_faixa_a_partir_da_tarefa(self, tmp_path):
        import shutil

        from harness.evaluate import evaluate_run
        from src.seeds import TOMLKIT
        from src.workspace import Workspace, WorkspaceSpec

        if not (TOMLKIT.mirror_path.exists() and TOMLKIT.has_venv):
            pytest.skip("rode scripts/setup_mirror.py tomlkit")

        # Tarefa igual à tomlkit-0001, mas com faixa adicionada — sem tocar
        # na tarefa real (que hoje não declara faixa, ver item 5).
        raiz_tarefa = tmp_path / "tarefa"
        shutil.copytree(RAIZ / "tasks" / "tomlkit-0001", raiz_tarefa)
        dados = json.loads((raiz_tarefa / "task.json").read_text())
        dados["faixa"] = "grande"
        (raiz_tarefa / "task.json").write_text(json.dumps(dados), encoding="utf-8")
        tarefa = load_task(raiz_tarefa)

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        ws = Workspace.materialize(
            WorkspaceSpec(seed_repo=TOMLKIT, base_commit=tarefa.base_commit),
            run_id="faixa", dest=run_dir / "workspace",
        )
        subprocess.run(
            ["git", "checkout", tarefa.fix_commit, "--", "tomlkit/parser.py"],
            cwd=ws.root, check=True, capture_output=True,
        )
        (run_dir / "manifest.json").write_text(json.dumps(
            {"run_id": "faixa", "arm": "single-agent", "repetition": 1}), encoding="utf-8")
        (run_dir / "events.jsonl").write_text("", encoding="utf-8")

        resultado = evaluate_run(run_dir, tarefa, measure_quality=False)

        assert resultado["faixa"] == "grande"
        esquema = json.loads((RAIZ / "harness/schema/result.schema.json").read_text())
        Draft202012Validator(esquema).validate(resultado)


def _resultado_minimo(*, faixa: str | None) -> dict:
    """Um result.json sintético, só com o suficiente para validar o schema."""
    pytest_vazio = {
        "exit_code": 0, "passed": 0, "failed": 0, "errors": 0, "duration_s": 0.0,
    }
    return {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "harness_version": HARNESS_VERSION,
        "evaluated_at": "2026-01-01T00:00:00+00:00",
        "run_id": "r1",
        "arm": "single-agent",
        "task_id": "faixa-0001",
        "faixa": faixa,
        "repetition": 1,
        "base_commit": "0" * 40,
        "resolved": True,
        "resolved_blocked_by_cheat": False,
        "oracle": {
            "f2p_total": 1, "f2p_passed": 1,
            "f2p": pytest_vazio, "p2p": pytest_vazio, "regression": pytest_vazio,
        },
        "cheat": {
            "clean": True, "critical_count": 0, "warning_count": 0, "signals": [],
        },
        "quality": {},
        "cost": {
            "tokens_total": 0, "cost_usd": 0.0, "llm_calls": 0,
            "tool_calls": 0, "wall_seconds": 0.0,
        },
        "process": {
            "turns": 0, "test_runs": 0, "self_recoveries": 0, "stop_reason": None,
        },
        "provenance": {
            "model": None, "provider_requested": None,
            "providers_served": [], "topology": None,
        },
        "diff": {
            "files_changed": 0, "insertions": 0, "deletions": 0, "changed_files": [],
        },
    }


# ------------------------------------------------------------------ qualidade


class TestQualidade:
    def test_sem_arquivos_alterados_nao_inventa_numero(self, tmp_path):
        r = measure(tmp_path, [])
        assert r.mi_delta is None and r.files_analyzed == 0


class TestAvaliacaoIdempotente:
    """
    Avaliar duas vezes o mesmo run tem de dar o mesmo veredito.

    A avaliação copia os testes ocultos para dentro do workspace. Sem limpar
    isso antes de começar, a segunda avaliação encontra `tests/_uranium_hidden`
    e acusa C1 (arquivo protegido alterado) e C7 (agente criou o diretório de
    testes ocultos) — reprovando por trapaça que o próprio harness cometeu.
    """

    def test_segunda_avaliacao_nao_acusa_trapaca_do_harness(self, tmp_path):
        import json
        import shutil
        import subprocess

        from harness.evaluate import evaluate_run
        from harness.taskspec import load_task
        from src.seeds import TOMLKIT
        from src.workspace import Workspace, WorkspaceSpec

        if not (TOMLKIT.mirror_path.exists() and TOMLKIT.has_venv):
            pytest.skip("rode scripts/setup_mirror.py tomlkit")

        tarefa = load_task(Path("tasks/tomlkit-0001"))
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        ws = Workspace.materialize(
            WorkspaceSpec(seed_repo=TOMLKIT, base_commit=tarefa.base_commit),
            run_id="idem", dest=run_dir / "workspace",
        )
        subprocess.run(
            ["git", "checkout", tarefa.fix_commit, "--", "tomlkit/parser.py"],
            cwd=ws.root, check=True, capture_output=True,
        )
        (run_dir / "manifest.json").write_text(json.dumps(
            {"run_id": "idem", "arm": "single-agent", "repetition": 1}), encoding="utf-8")
        (run_dir / "events.jsonl").write_text("", encoding="utf-8")

        primeira = evaluate_run(run_dir, tarefa, measure_quality=False)
        segunda = evaluate_run(run_dir, tarefa, measure_quality=False)

        assert primeira["resolved"] is True
        assert segunda["resolved"] is True, "a segunda avaliação reprovou um run limpo"
        assert segunda["cheat"]["clean"] is True
        assert segunda["cheat"]["signals"] == []
        assert segunda["diff"]["changed_files"] == primeira["diff"]["changed_files"]

    @pytest.mark.parametrize("task_id", ["tomlkit-0001", "sqlite-utils-0001"])
    def test_avaliacao_nao_muta_o_workspace_gravado(self, tmp_path, task_id):
        """
        O invariante que torna a idempotência estrutural.

        A avaliação injeta testes ocultos, restaura arquivos de teste do
        commit-base e aplica o patch de teste do upstream. Se qualquer uma
        dessas mutações alcançar o workspace gravado, a evidência do que o
        agente deixou é destruída — e foi assim que a regra C1 ficou cega em
        tarefa com `test_patch`: a restauração apagava a adulteração antes de
        o detector olhar.

        Testar o invariante, e não o sintoma, cobre também as mutações que
        ainda não existem.
        """
        import json
        import subprocess

        from harness.evaluate import evaluate_run
        from harness.taskspec import load_task
        from src.seeds import get_seed_repo
        from src.workspace import Workspace, WorkspaceSpec

        tarefa = load_task(Path("tasks") / task_id)
        seed = get_seed_repo(tarefa.seed_repo_id)
        if not (seed.mirror_path.exists() and seed.has_venv):
            pytest.skip(f"rode scripts/setup_mirror.py {tarefa.seed_repo_id}")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        ws = Workspace.materialize(
            WorkspaceSpec(seed_repo=seed, base_commit=tarefa.base_commit),
            run_id="imutavel", dest=run_dir / "workspace",
        )
        (run_dir / "manifest.json").write_text(json.dumps(
            {"run_id": "imutavel", "arm": "single-agent", "repetition": 1}), encoding="utf-8")
        (run_dir / "events.jsonl").write_text("", encoding="utf-8")

        def retrato() -> tuple[str, list[str]]:
            """Estado do workspace: o que o git vê, e quais arquivos existem."""
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=ws.root, capture_output=True, text=True, check=True,
            ).stdout
            arquivos = sorted(
                str(p.relative_to(ws.root))
                for p in ws.root.rglob("*")
                if p.is_file() and ".git" not in p.parts
            )
            return status, arquivos

        antes = retrato()
        evaluate_run(run_dir, tarefa, measure_quality=False)
        depois = retrato()

        assert depois[0] == antes[0], "a avaliação mexeu no git do workspace gravado"
        assert depois[1] == antes[1], (
            "a avaliação criou ou removeu arquivo no workspace gravado: "
            f"{set(depois[1]) ^ set(antes[1])}"
        )


class TestRunPerdidoNaoEhAvaliado:
    def test_cli_recusa_run_marcado_como_perdido(self, tmp_path):
        """Run substituído por reexecução (E5 item 2) não pode virar result.json."""
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "PERDIDO").write_text("error: provedor", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "harness.evaluate", "--run-dir", str(run_dir),
             "--task", "tasks/tomlkit-0001"],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert "PERDIDO" in proc.stderr
        assert not (run_dir / "result.json").exists()

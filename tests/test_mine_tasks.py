"""
Testes da faixa nova (E3 item 1, docs/tcc/tasks/EXIGENCIAS.md) e do
tratamento de arquivo de teste apagado/renomeado (E3 item 3, aviso do
coordenador em docs/tcc/07-e3-3-breaking-change.md).

`calcular_faixa` é função pura dos campos medidos — sem git, sem suíte,
sem workspace — para poder testar os limiares de cada faixa isoladamente.
Os testes de `contar_testes_novos_e_modificados` e `calcular_modulos_fonte`
cobrem os insumos que alimentam essa função. Os testes de
`_parse_name_status`/`_classificar_status` cobrem apagado e renomeado sem
precisar de um espelho git de verdade — validados à mão contra commits
reais em sqlite-utils (364b0fb6, apaga `tests/test_black.py`; f9473ace,
renomeia `tests/test_enable_fts.py` -> `tests/test_fts.py`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.mine_tasks import (  # noqa: E402
    Candidato,
    _classificar_status,
    _eh_teste,
    _em_source_dir,
    _parse_name_status,
    _presentes,
    _remover_desaparecidos,
    _suite_nao_executou,
    calcular_faixa,
    calcular_modulos_fonte,
    contar_testes_novos_e_modificados,
)
from src.schemas.test_report import TestReport  # noqa: E402


def _faixa(**kwargs) -> str:
    padrao = dict(
        arquivos_fonte=1, linhas_fonte=20, modulos_fonte=1,
        testes_novos=0, testes_modificados=1, subject="fix: corrige bug",
    )
    padrao.update(kwargs)
    faixa, _ = calcular_faixa(**padrao)
    return faixa


class TestFaixaPequena:
    def test_um_arquivo_dentro_da_faixa(self):
        assert _faixa(arquivos_fonte=1, linhas_fonte=20) == "pequena"

    def test_dois_arquivos_dentro_da_faixa(self):
        assert _faixa(arquivos_fonte=2, linhas_fonte=50) == "pequena"

    def test_limite_inferior_de_linhas_entra(self):
        assert _faixa(arquivos_fonte=1, linhas_fonte=10) == "pequena"

    def test_abaixo_do_limite_de_linhas_fica_fora(self):
        assert _faixa(arquivos_fonte=1, linhas_fonte=9) == "fora"

    def test_limite_superior_de_linhas_entra(self):
        assert _faixa(arquivos_fonte=2, linhas_fonte=50) == "pequena"

    def test_acima_do_limite_de_linhas_fica_fora(self):
        assert _faixa(arquivos_fonte=2, linhas_fonte=51) == "fora"

    def test_tres_arquivos_poucas_linhas_e_pequena_por_tamanho(self):
        # três arquivos com poucas linhas (< 40): pequena por tamanho, não
        # pela contagem de arquivo típica de 1-2 (revisão do autor, E3.3,
        # peewee b8a336d0: 11 linhas em 3 arquivos, tinha saído como média).
        assert _faixa(arquivos_fonte=3, linhas_fonte=20, modulos_fonte=1) == "pequena"

    def test_motivo_faixa_explica_pequena_por_tamanho(self):
        faixa, motivo = calcular_faixa(
            arquivos_fonte=3, linhas_fonte=11, modulos_fonte=1,
            testes_novos=0, testes_modificados=1, subject="fix: x",
        )
        assert faixa == "pequena"
        assert "pequena por tamanho" in motivo


class TestFaixaMedia:
    def test_tres_arquivos_dois_modulos_entra(self):
        assert _faixa(arquivos_fonte=3, linhas_fonte=100, modulos_fonte=2) == "media"

    def test_sete_arquivos_no_limite_superior_entra(self):
        assert _faixa(arquivos_fonte=7, linhas_fonte=400, modulos_fonte=3) == "media"

    def test_oito_arquivos_fica_fora_da_media(self):
        assert _faixa(arquivos_fonte=8, linhas_fonte=100, modulos_fonte=3) == "fora"

    def test_um_modulo_so_nao_e_media(self):
        # atravessar módulos é o critério que distingue média de "um
        # arquivo grande picado em vários pedaços do mesmo módulo".
        assert _faixa(arquivos_fonte=4, linhas_fonte=100, modulos_fonte=1) == "fora"

    def test_acima_de_400_linhas_fica_fora_da_media(self):
        assert _faixa(arquivos_fonte=4, linhas_fonte=401, modulos_fonte=2) == "fora"

    def test_abaixo_de_40_linhas_nao_e_media_vira_pequena(self):
        # revisão do autor (E3.3, peewee b8a336d0): 3-7 arquivos com menos
        # de 40 linhas não é média só por tocar vários arquivos.
        assert _faixa(arquivos_fonte=3, linhas_fonte=39, modulos_fonte=2) == "pequena"

    def test_quarenta_linhas_no_limite_inferior_entra_em_media(self):
        assert _faixa(arquivos_fonte=3, linhas_fonte=40, modulos_fonte=2) == "media"

    def test_muitos_arquivos_poucas_linhas_um_modulo_fica_fora(self):
        # 8 arquivos (acima do teto da média) e poucas linhas: a regra nova
        # de "3+ arquivos, <40 linhas" não tem teto de arquivo declarado,
        # então isto AINDA cai em pequena — documentado como consequência
        # aceita da regra literal da revisão do autor (E3.3), não um teto
        # extra inventado.
        assert _faixa(arquivos_fonte=8, linhas_fonte=20, modulos_fonte=3) == "pequena"


class TestFaixaGrande:
    def test_funcionalidade_nova_com_testes_novos_entra(self):
        assert _faixa(
            arquivos_fonte=3, linhas_fonte=80, modulos_fonte=2,
            testes_novos=4, testes_modificados=0, subject="add: suporte a JSON5",
        ) == "grande"

    def test_limite_inferior_de_linhas_entra(self):
        assert _faixa(
            arquivos_fonte=3, linhas_fonte=80, modulos_fonte=1,
            testes_novos=2, testes_modificados=0, subject="feature: novo backend",
        ) == "grande"

    def test_abaixo_do_limite_de_linhas_nao_e_grande(self):
        assert _faixa(
            arquivos_fonte=3, linhas_fonte=79, modulos_fonte=2,
            testes_novos=4, testes_modificados=0, subject="add: suporte a JSON5",
        ) != "grande"

    def test_dois_arquivos_nao_e_grande(self):
        assert _faixa(
            arquivos_fonte=2, linhas_fonte=200, modulos_fonte=2,
            testes_novos=4, testes_modificados=0, subject="add: suporte a JSON5",
        ) != "grande"

    def test_mensagem_de_correcao_nao_e_grande(self):
        # "fix" no assunto é sinal de correção, não de funcionalidade nova
        # planejada — mesmo com testes novos e patch grande, fica fora da
        # faixa grande (cai em média, se os módulos baterem).
        assert _faixa(
            arquivos_fonte=3, linhas_fonte=200, modulos_fonte=2,
            testes_novos=4, testes_modificados=0, subject="fix: corrige regressão grave",
        ) == "media"

    def test_maioria_de_testes_modificados_nao_e_grande(self):
        # teste majoritariamente MODIFICADO (não novo) é sinal de correção
        # que quebra comportamento antigo, não funcionalidade nova.
        assert _faixa(
            arquivos_fonte=3, linhas_fonte=200, modulos_fonte=2,
            testes_novos=1, testes_modificados=3, subject="add: reescreve parser",
        ) != "grande"

    def test_sem_teste_novo_nenhum_nao_e_grande(self):
        assert _faixa(
            arquivos_fonte=4, linhas_fonte=200, modulos_fonte=2,
            testes_novos=0, testes_modificados=0, subject="add: reescreve parser",
        ) != "grande"


class TestForaRegistraMotivo:
    def test_motivo_fica_registrado(self):
        _, motivo = calcular_faixa(
            arquivos_fonte=1, linhas_fonte=5, modulos_fonte=1,
            testes_novos=0, testes_modificados=0, subject="fix: nada",
        )
        assert "fora das faixas" in motivo
        assert "arquivos_fonte=1" in motivo

    def test_faixa_valida_nao_tem_motivo(self):
        _, motivo = calcular_faixa(
            arquivos_fonte=1, linhas_fonte=20, modulos_fonte=1,
            testes_novos=0, testes_modificados=0, subject="fix: nada",
        )
        assert motivo == ""

    def test_tres_arquivos_um_modulo_linhas_o_bastante_ainda_fica_fora(self):
        # nem média (1 módulo só), nem pequena-por-tamanho (linhas >= 40):
        # não vira pequena por "escapar" da média, continua fora mesmo
        # depois da revisão do autor (E3.3).
        assert _faixa(arquivos_fonte=3, linhas_fonte=60, modulos_fonte=1) == "fora"


class TestContarTestesNovosEModificados:
    def test_funcao_inteiramente_nova(self):
        diff = (
            "diff --git a/tests/test_x.py b/tests/test_x.py\n"
            "--- a/tests/test_x.py\n"
            "+++ b/tests/test_x.py\n"
            "@@ -10,0 +11,3 @@ def test_existente():\n"
            "+\n"
            "+def test_novo():\n"
            "+    assert True\n"
        )
        novas, modificadas = contar_testes_novos_e_modificados(diff)
        assert novas == 1
        assert modificadas == 0

    def test_corpo_alterado_sem_tocar_a_linha_def(self):
        # git preenche o contexto do hunk com a assinatura da função quando
        # a mudança cai dentro do corpo, sem tocar a linha "def".
        diff = (
            "diff --git a/tests/test_x.py b/tests/test_x.py\n"
            "--- a/tests/test_x.py\n"
            "+++ b/tests/test_x.py\n"
            "@@ -12,2 +12,2 @@ def test_antigo():\n"
            "-    assert x == 1\n"
            "+    assert x == 2\n"
        )
        novas, modificadas = contar_testes_novos_e_modificados(diff)
        assert novas == 0
        assert modificadas == 1

    def test_assinatura_alterada_conta_como_modificada_nao_nova(self):
        diff = (
            "diff --git a/tests/test_x.py b/tests/test_x.py\n"
            "--- a/tests/test_x.py\n"
            "+++ b/tests/test_x.py\n"
            "@@ -5,2 +5,2 @@\n"
            "-def test_antigo(a):\n"
            "+def test_antigo(a, b):\n"
            "     assert a\n"
        )
        novas, modificadas = contar_testes_novos_e_modificados(diff)
        assert novas == 0
        assert modificadas == 1

    def test_diff_sem_funcao_de_teste(self):
        diff = (
            "diff --git a/tests/conftest.py b/tests/conftest.py\n"
            "--- a/tests/conftest.py\n"
            "+++ b/tests/conftest.py\n"
            "@@ -1,1 +1,2 @@\n"
            "+import os\n"
        )
        assert contar_testes_novos_e_modificados(diff) == (0, 0)


class TestCalcularModulosFonte:
    def test_um_arquivo_um_modulo(self):
        assert calcular_modulos_fonte(["tomlkit/items.py"]) == 1

    def test_dois_arquivos_mesmo_diretorio_um_modulo(self):
        assert calcular_modulos_fonte(["tomlkit/items.py", "tomlkit/parser.py"]) == 1

    def test_dois_diretorios_dois_modulos(self):
        assert calcular_modulos_fonte(["peewee.py", "playhouse/sqlite_ext.py"]) == 2

    def test_arquivo_solto_na_raiz_conta_pelo_proprio_nome(self):
        assert calcular_modulos_fonte(["peewee.py"]) == 1

    def test_tres_diretorios_tres_modulos(self):
        arquivos = ["a/x.py", "b/y.py", "c/z.py"]
        assert calcular_modulos_fonte(arquivos) == 3

    def test_subpacote_conta_como_modulo_diferente_do_pacote_raiz(self):
        # pygments/lexer.py (solto no pacote) e pygments/lexers/python.py
        # (dentro do subpacote lexers) são módulos diferentes — a raiz do
        # pacote não é a mesma pasta que o subpacote.
        arquivos = ["pygments/lexer.py", "pygments/lexers/python.py"]
        assert calcular_modulos_fonte(arquivos) == 2

    def test_dois_arquivos_no_mesmo_subpacote_um_modulo(self):
        arquivos = ["pygments/lexers/python.py", "pygments/lexers/ruby.py"]
        assert calcular_modulos_fonte(arquivos) == 1

    def test_tres_niveis_agrupa_pelo_diretorio_imediato(self):
        arquivos = ["a/b/c/x.py", "a/b/c/y.py", "a/b/d/z.py"]
        assert calcular_modulos_fonte(arquivos) == 2  # "a/b/c" e "a/b/d"


class TestCandidatoF2pArquivos:
    def test_conta_arquivos_distintos_no_fail_to_pass(self):
        cand = Candidato(
            seed_repo_id="tomlkit", fix_commit="a" * 40, base_commit="b" * 40,
            subject="fix: x", arquivos_fonte=["a.py"], arquivos_teste=["tests/test_a.py"],
            linhas_fonte=10, modulos_fonte=1, testes_novos=0, testes_modificados=1,
            altera_testes_existentes=True, faixa="pequena",
        )
        cand.fail_to_pass = [
            "tests/test_a.py::test_1", "tests/test_a.py::test_2", "tests/test_b.py::test_3",
        ]
        assert cand.f2p_arquivos == 2


def _repo(**kwargs):
    from src.seeds import SeedRepoSpec

    padrao = dict(
        seed_repo_id="fake", upstream_url="https://example.com/fake.git",
        mirror_name="fake.git", source_dir="fake,sqlite_utils,pkg", test_command=(),
    )
    padrao.update(kwargs)
    return SeedRepoSpec(**padrao)


class TestParseNameStatus:
    def test_linha_modificada(self):
        assert _parse_name_status(["M\ta.py"]) == [("M", "a.py", None)]

    def test_linha_adicionada(self):
        assert _parse_name_status(["A\ttests/test_x.py"]) == [("A", "tests/test_x.py", None)]

    def test_linha_apagada(self):
        assert _parse_name_status(["D\ttests/test_old.py"]) == [("D", "tests/test_old.py", None)]

    def test_linha_renomeada_com_similaridade(self):
        # git prefixa o status com o percentual de similaridade (R077, R100...)
        assert _parse_name_status(["R077\ttests/test_a.py\ttests/test_b.py"]) == [
            ("R", "tests/test_b.py", "tests/test_a.py"),
        ]

    def test_ignora_linha_vazia(self):
        assert _parse_name_status(["", "  ", "M\ta.py"]) == [("M", "a.py", None)]


class TestEhTeste:
    def test_tests_dir_e_teste(self):
        assert _eh_teste("tests/test_x.py") is True

    def test_conftest_e_teste(self):
        assert _eh_teste("tests/conftest.py") is True

    def test_pyproject_nao_e_teste(self):
        assert _eh_teste("pyproject.toml") is False

    def test_runtests_py_nao_e_teste(self):
        assert _eh_teste("runtests.py") is False


class TestEmSourceDir:
    def test_arquivo_dentro_do_diretorio(self):
        assert _em_source_dir("playhouse/sqlite_ext.py", "peewee,playhouse") is True

    def test_arquivo_unico_solto_na_raiz(self):
        assert _em_source_dir("peewee.py", "peewee,playhouse") is True

    def test_arquivo_fora_do_source_dir(self):
        assert _em_source_dir("json5-tests/foo.py", "pygments") is False

    def test_prefixo_parcial_nao_casa(self):
        # "playhouse" não deve casar com um diretório "playhouse2"
        assert _em_source_dir("playhouse2/x.py", "playhouse") is False

    def test_source_dir_unico(self):
        assert _em_source_dir("tomlkit/items.py", "tomlkit") is True
        assert _em_source_dir("docs/conf.py", "tomlkit") is False


class TestClassificarStatusApagaERenomeiaTeste:
    """
    Casos reais (validados à mão contra o espelho): sqlite-utils 364b0fb6
    apaga `tests/test_black.py`; sqlite-utils f9473ace renomeia
    `tests/test_enable_fts.py` -> `tests/test_fts.py` junto com uma
    correção em `sqlite_utils/{cli,db}.py`.
    """

    def test_teste_apagado_conta_e_vai_para_desaparecidos(self):
        repo = _repo()
        entradas = [("M", "sqlite_utils/db.py", None), ("D", "tests/test_black.py", None)]
        cls = _classificar_status(repo, entradas)
        assert cls.teste == ["tests/test_black.py"]
        assert cls.teste_desaparecidos == ["tests/test_black.py"]
        assert cls.testes_apagados == 1
        assert cls.testes_renomeados == 0
        assert cls.fonte == ["sqlite_utils/db.py"]
        assert cls.arquivos_fonte_logicos == 1

    def test_teste_renomeado_traz_os_dois_nomes_e_conta_um(self):
        repo = _repo()
        entradas = [
            ("M", "sqlite_utils/cli.py", None),
            ("M", "sqlite_utils/db.py", None),
            ("R", "tests/test_fts.py", "tests/test_enable_fts.py"),
        ]
        cls = _classificar_status(repo, entradas)
        assert set(cls.teste) == {"tests/test_fts.py", "tests/test_enable_fts.py"}
        assert cls.teste_desaparecidos == ["tests/test_enable_fts.py"]
        assert cls.testes_apagados == 0
        assert cls.testes_renomeados == 1
        assert cls.arquivos_fonte_logicos == 2  # o renomeado não é fonte, não conta aqui

    def test_fonte_apagada_vai_para_fonte_apagados_sem_contar_teste(self):
        repo = _repo()
        entradas = [("D", "sqlite_utils/legacy.py", None), ("A", "tests/test_x.py", None)]
        cls = _classificar_status(repo, entradas)
        assert cls.fonte == []  # apagado não entra em fonte
        assert cls.fonte_apagados == ["sqlite_utils/legacy.py"]
        assert cls.fonte_desaparecidos == []
        assert cls.testes_apagados == 0
        assert cls.arquivos_fonte_logicos == 0

    def test_fonte_renomeada_conta_como_um_arquivo_logico(self):
        repo = _repo()
        cls = _classificar_status(repo, [("R", "pkg/novo.py", "pkg/velho.py")])
        assert set(cls.fonte) == {"pkg/novo.py", "pkg/velho.py"}
        assert cls.fonte_desaparecidos == ["pkg/velho.py"]
        assert cls.arquivos_fonte_logicos == 1  # renomeado conta como 1 arquivo, não 2

    def test_fonte_fora_do_source_dir_nao_conta(self):
        # pygments 2c463c68 (revisão do autor, E3.3): arquivo apagado em
        # `json5-tests/`, fora do pacote `pygments/` — nem fonte, nem
        # fonte_apagados, porque nem chega a ser "fonte" (fora do
        # source_dir declarado).
        repo = _repo(source_dir="pygments")
        cls = _classificar_status(repo, [
            ("D", "json5-tests/foo.py", None),
            ("M", "pygments/lexers/json5.py", None),
        ])
        assert cls.fonte_apagados == []
        assert cls.fonte == ["pygments/lexers/json5.py"]
        assert cls.arquivos_fonte_logicos == 1

    def test_toca_protegido_nao_teste(self):
        # tqdm e4d97426 (revisão do autor, E3.3): altera pyproject.toml —
        # protegido, mas não é conteúdo de teste.
        repo = _repo()
        cls = _classificar_status(repo, [
            ("M", "pyproject.toml", None),
            ("M", "tests/test_x.py", None),
            ("M", "sqlite_utils/db.py", None),
        ])
        assert cls.toca_protegido is True

    def test_tocar_so_teste_nao_e_toca_protegido(self):
        repo = _repo()
        cls = _classificar_status(repo, [
            ("M", "tests/test_x.py", None),
            ("M", "sqlite_utils/db.py", None),
        ])
        assert cls.toca_protegido is False

    def test_runtests_py_do_peewee_e_toca_protegido(self):
        from src.seeds import PEEWEE
        cls = _classificar_status(PEEWEE, [
            ("M", "runtests.py", None),
            ("M", "peewee.py", None),
            ("M", "tests/models.py", None),
        ])
        assert cls.toca_protegido is True


class TestPresentes:
    def test_remove_desaparecidos_e_duplicata(self):
        caminhos = ["tests/test_fts.py", "tests/test_enable_fts.py"]
        desaparecidos = ["tests/test_enable_fts.py"]
        assert _presentes(caminhos, desaparecidos) == ["tests/test_fts.py"]

    def test_sem_desaparecidos_preserva_ordem_sem_duplicata(self):
        assert _presentes(["a.py", "b.py", "a.py"], []) == ["a.py", "b.py"]


class TestRemoverDesaparecidosDeVerdade:
    """`_remover_desaparecidos` usa `git rm`; precisa de um repo git de verdade."""

    def _repo_git(self, tmp_path: Path) -> Path:
        raiz = tmp_path / "repo"
        raiz.mkdir()
        subprocess.run(["git", "init", "--quiet"], cwd=raiz, check=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=raiz, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=raiz, check=True)
        (raiz / "tests").mkdir()
        (raiz / "tests" / "test_velho.py").write_text("def test_x(): assert True\n")
        subprocess.run(["git", "add", "."], cwd=raiz, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=raiz, check=True)
        return raiz

    def test_remove_arquivo_rastreado(self, tmp_path):
        raiz = self._repo_git(tmp_path)
        _remover_desaparecidos(raiz, ["tests/test_velho.py"])
        assert not (raiz / "tests" / "test_velho.py").exists()

    def test_lista_vazia_nao_faz_nada(self, tmp_path):
        raiz = self._repo_git(tmp_path)
        _remover_desaparecidos(raiz, [])  # não deve levantar
        assert (raiz / "tests" / "test_velho.py").exists()

    def test_ignora_caminho_que_nao_existe(self, tmp_path):
        raiz = self._repo_git(tmp_path)
        _remover_desaparecidos(raiz, ["tests/nao_existe.py"])  # --ignore-unmatch: não levanta


class TestSuiteNaoExecutou:
    """
    Aviso do coordenador (E3.3): "commit-base já vermelho (0 falhas)" em
    frações de segundo não é base vermelha, é suíte que não rodou (erro de
    coleta, dependência ausente). Achado real: sqlite-utils, 35 candidatos
    recusados assim — causa era `ModuleNotFoundError: typing_extensions`,
    corrigido em `src/seeds.py`.
    """

    def test_zero_passed_zero_failed_e_nao_executou(self):
        relatorio = TestReport(exit_code=2, passed=0, failed=0, errors=1,
                               duration_s=0.2, stdout_tail="ModuleNotFoundError: typing_extensions")
        assert _suite_nao_executou(relatorio) is True

    def test_suite_vermelha_de_verdade_nao_e_nao_executou(self):
        relatorio = TestReport(exit_code=1, passed=1400, failed=3, duration_s=17.0)
        assert _suite_nao_executou(relatorio) is False

    def test_suite_verde_nao_e_nao_executou(self):
        relatorio = TestReport(exit_code=0, passed=1400, failed=0, duration_s=17.0)
        assert _suite_nao_executou(relatorio) is False

    def test_zero_passed_com_falha_de_verdade_nao_conta(self):
        # exit_code de teste reprovado, 0 passed mas failed>0: suíte rodou.
        relatorio = TestReport(exit_code=1, passed=0, failed=2, duration_s=5.0)
        assert _suite_nao_executou(relatorio) is False

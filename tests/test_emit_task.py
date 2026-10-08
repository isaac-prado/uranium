"""Escolha do arquivo que recebe o patch de trapaça C1 (scripts/emit_task.py)."""

from scripts.emit_task import escolher_arquivo_c1


def test_pula_fixture_nova_e_escolhe_o_py_que_existe_na_base():
    # caso real: pygments 9c436b34 acrescenta tests/examplefiles/go/3199.go
    # (novo) antes de tocar tests/test_go.py (existente)
    arquivos = ["tests/examplefiles/go/3199.go", "tests/examplefiles/go/3199.go.output",
                "tests/test_go.py"]
    existe = lambda c: c == "tests/test_go.py"
    assert escolher_arquivo_c1(arquivos, existe) == "tests/test_go.py"


def test_py_novo_nao_serve_porque_nao_tem_contexto_na_base():
    assert escolher_arquivo_c1(["tests/test_novo.py"], lambda c: False) is None


def test_primeiro_que_satisfaz_vence():
    existe = lambda c: True
    assert escolher_arquivo_c1(["tests/a.py", "tests/b.py"], existe) == "tests/a.py"


def test_so_fixtures_novas_cai_para_a_reserva_de_modulos_da_base():
    arquivos = ["tests/examplefiles/go/3199.go", "tests/examplefiles/go/3199.go.output"]
    reserva = ["tests/test_basic_api.py", "tests/test_cmdline.py"]
    assert escolher_arquivo_c1(arquivos, lambda c: False, reserva) == "tests/test_basic_api.py"


def test_sem_nada_na_base_devolve_none():
    assert escolher_arquivo_c1(["tests/x.go"], lambda c: False, []) is None

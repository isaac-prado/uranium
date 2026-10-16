"""Comparação determinística das saídas esperadas (decisões 35 a 37, rodada 5)."""

from __future__ import annotations

from src.verificacao import (
    ENCONTRADA,
    NAO_ENCONTRADA,
    NAO_VERIFICAVEL,
    bloco_nao_compilou,
    comparar_saidas,
    faltantes,
    normalizar,
    saida_contem,
    verificaveis,
)


def _exec(bloco: int, saida: str, executado: bool = True) -> dict:
    return {"bloco": bloco, "executado": executado, "saida": saida}


class TestNormalizacaoEContencao:
    def test_quebras_reais_e_escritas_colapsam(self):
        assert normalizar("a\n  b\\nc") == "a b c"

    def test_repr_com_barra_n_literal_casa_com_a_saida_do_print(self):
        # tomlkit-0002: o enunciado traz `'foo.bar = 1\n'` e `print(repr(...))` imprime o mesmo
        assert saida_contem("'foo.bar = 1\\n'", "exit=0 em 0.04s\n'foo.bar = 1\\n'") is True

    def test_duas_reprs_separadas_por_barra_n_escrita_casam_com_linhas_reais(self):
        # tomlkit-0003: a saída esperada junta dois prints com `\n` escrito
        esperada = "{'a': 1}\\n{'b': 2}"
        assert saida_contem(esperada, "exit=0 em 0.1s\n{'a': 1}\n{'b': 2}") is True

    def test_reticencias_dividem_em_pedacos_que_precisam_aparecer(self):
        esperada = "fields(Caixa[str]): (Field(name='conteudo', default=NOTHING, ...),)"
        assert saida_contem(esperada, "fields(Caixa[str]): (Field(name='conteudo', default=NOTHING, repr=True),)") is True
        assert saida_contem(esperada, "fields(Caixa[str]): (Attribute(name='conteudo', default=NOTHING),)") is False

    def test_o_que_vem_depois_do_cerquilha_vale_sozinho(self):
        # peewee-0003: "Ticket.status.choices    # [('active', 'ACTIVE')]"
        assert saida_contem("Ticket.status.choices    # [('active', 'ACTIVE')]", "[('active', 'ACTIVE')]") is True

    def test_linhas_que_nao_sao_saida_nao_contam(self):
        assert saida_contem("```\n$ python -m x\n>>> f()\n| a | b |\n```", "qualquer coisa") is None
        assert saida_contem("$ python -m sqlite_utils memory 'q'\n[{\"id\": 1}]", '[{"id": 1}]') is True

    def test_pedaco_de_um_caractere_nao_prova_nada(self):
        assert saida_contem("2", "exit=0\n2") is None
        assert saida_contem("[]", "exit=0\n[]") is True

    def test_linha_faltando_reprova(self):
        assert saida_contem("has(Caixa): True\nhas(Comum): False", "has(Caixa): True") is False


class TestComparacao:
    def test_estados(self):
        execs = [_exec(1, "exit=0 em 0.1s\nhas(Caixa): True")]
        comp = comparar_saidas([(1, "has(Caixa): True"), (2, "has(Comum): False"), (3, "| tabela |")], execs)
        assert [c["estado"] for c in comp] == [ENCONTRADA, NAO_ENCONTRADA, NAO_VERIFICAVEL]
        assert [c["indice"] for c in verificaveis(comp)] == [1, 2] and [c["indice"] for c in faltantes(comp)] == [2]

    def test_bloco_que_nao_compilou_torna_a_ausencia_nao_verificavel(self):
        # sqlite-utils-0003 rep02 da rodada 4: o refinador copiou o bloco com `\n` escrito e nada rodou
        saida = 'exit=1 em 0.01s\nFile ".uranium_snippet.py", line 1\n    import x\\n\\ny = 1\n    ^\nSyntaxError: unexpected character'
        assert bloco_nao_compilou(saida)
        comp = comparar_saidas([(1, "[{'id': 1}]")], [_exec(1, saida)])
        assert comp[0]["estado"] == NAO_VERIFICAVEL

    def test_um_bloco_quebrado_entre_varios_so_poupa_o_que_faltou(self):
        execs = [_exec(1, "exit=0\n[{'id': 1}]"), _exec(2, "exit=1\n  ^\nSyntaxError: invalid syntax")]
        comp = comparar_saidas([(1, "[{'id': 1}]"), (2, "[{'id': 2}]")], execs)
        assert [c["estado"] for c in comp] == [ENCONTRADA, NAO_VERIFICAVEL]

    def test_sem_execucao_tudo_e_nao_verificavel(self):
        assert [c["estado"] for c in comparar_saidas([(1, "x = 1")], [])] == [NAO_VERIFICAVEL]
        assert [c["estado"] for c in comparar_saidas([(1, "x = 1")], [_exec(1, "(não executado)", executado=False)])] == [NAO_VERIFICAVEL]

    def test_erro_em_tempo_de_execucao_nao_e_nao_verificavel(self):
        # NameError/ImportError/exceção do código: o bloco rodou e a saída esperada não veio
        execs = [_exec(1, "exit=1 em 0.1s\nTraceback (most recent call last):\n  ...\nImportError: cannot import name 'x'")]
        assert comparar_saidas([(1, "has(Caixa): True")], execs)[0]["estado"] == NAO_ENCONTRADA

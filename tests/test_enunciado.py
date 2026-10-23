"""Rodada 8 (decisão 48): leitura determinística do enunciado pelo validador (src/enunciado.py)."""

from __future__ import annotations

from pathlib import Path

from src.enunciado import (
    anotar_comparacoes,
    blocos_python,
    exemplo_do_bloco,
    comparar_bloco,
    esperado_do_bloco,
    pares_esperados,
    reparar_blocos,
    sem_cercas,
    similaridade,
)
from src.verificacao import ENCONTRADA, NAO_ENCONTRADA, NAO_VERIFICAVEL

ENUNCIADO = """# Bug

Rode a partir da raiz:

```python
import tomlkit
doc = tomlkit.document()
doc.add(tomlkit.key(["foo", "bar"]), 1)
print(repr(doc.as_string()))
```

Saída hoje:

```
TypeError: ord() expected a character
```

Saída esperada depois da mudança:

```
'foo.bar = 1\\n'
```

Outro exemplo, sem saída esperada escrita:

```python
print("isolado")
```

```toml
[foo]
a.b.c = 1
```
"""


class TestCercasESimilaridade:
    def test_sem_cercas_tira_a_cerca_copiada_para_dentro_do_bloco(self):
        assert sem_cercas("```python\nprint(1)\n```") == "print(1)"
        assert sem_cercas("```python\nprint(1)") == "print(1)"  # sem fechamento
        assert sem_cercas("print(1)\n") == "print(1)"

    def test_similaridade_e_simetrica_e_vai_de_zero_a_um(self):
        assert similaridade("a = 1", "a = 1") == 1.0
        assert similaridade("a = 1", "zzz") == 0.0
        assert similaridade("print(x)", "print(x, y)") == similaridade("print(x, y)", "print(x)")


class TestReparo:
    def test_bloco_deturpado_e_trocado_pelo_do_enunciado(self):
        garbled = 'import tomlkit\ndoc = tomlkit.document()\ndoc.add(tomlkit.key(["foo\nbar"]), 1)\nprint(repr(doc.as_string()))'
        novos, fontes = reparar_blocos({1: garbled, 2: "print('ok')", 3: None}, ENUNCIADO)
        assert fontes == {1: "enunciado"} and 'tomlkit.key(["foo", "bar"])' in novos[1]
        assert novos[2] == "print('ok')" and novos[3] is None

    def test_cerca_dentro_do_bloco_e_removida_sem_trocar(self):
        novos, fontes = reparar_blocos({1: "```python\nprint('ok')"}, ENUNCIADO)
        assert novos[1] == "print('ok')" and fontes == {1: "cerca"}

    def test_sem_parecido_no_enunciado_o_bloco_fica_como_esta(self):
        novos, fontes = reparar_blocos({1: "def quebrado(:"}, ENUNCIADO)
        assert novos[1] == "def quebrado(:" and fontes == {}


class TestSaidaEsperadaPorBloco:
    def test_pareia_so_o_bloco_precedido_de_esperada_e_ignora_hoje(self):
        pares = pares_esperados(ENUNCIADO)
        assert len(pares) == 1
        bloco, esperado = pares[0]
        assert "tomlkit.key" in bloco and esperado == "'foo.bar = 1\\n'"
        assert len(blocos_python(ENUNCIADO)) == 2

    def test_esperado_do_bloco_por_parecenca_e_comparacao_linha_a_linha(self):
        copia = 'import tomlkit\ndoc = tomlkit.document()\ndoc.add(tomlkit.key(["foo", "bar"]), 1)\nprint(repr(doc.as_string()))\n'
        esperado = esperado_do_bloco(copia, ENUNCIADO)
        assert esperado == "'foo.bar = 1\\n'"
        assert comparar_bloco(esperado, "exit=0\n'foo.bar = 1\\n'") == [{"linha": "'foo.bar = 1\\n'", "estado": ENCONTRADA}]
        assert comparar_bloco(esperado, "exit=0\n'foo.bar=1\\n'")[0]["estado"] == NAO_ENCONTRADA
        assert esperado_do_bloco('print("isolado")', ENUNCIADO) is None
        assert esperado_do_bloco(None, ENUNCIADO) is None

    def test_enunciados_reais(self):
        raiz = Path("tasks")
        def pares(t):
            return pares_esperados((raiz / t / "statement.md").read_text(encoding="utf-8"))
        assert [e for _, e in pares("tomlkit-0002")] == ["'foo.bar = 1\\n'\n'foo.bar = 1\\n'"]
        assert len(pares("tomlkit-0003")) == 1 and "'tool'" in pares("tomlkit-0003")[0][1]
        assert pares("attrs-0001") == []  # só "Saída hoje"
        assert len(pares("sqlite-utils-0003")) == 1 and pares("sqlite-utils-0003")[0][1].startswith("[{'id': 1, 'id_2': 2")


class TestExemploFatiado:
    ENUNCIADO = """Rode:

```python
import sqlite_utils
db = sqlite_utils.Database(memory=True)
print(list(db.query("select 1 as id, 2 as id")))
print(list(db.query("select 1 as id, 2 as id, 3 as id_2")))
```

Para o trecho acima, a saída esperada é:

```
[{'id': 1, 'id_2': 2}]
[{'id': 1, 'id_3': 2, 'id_2': 3}]
```
"""

    def test_pedacos_de_um_exemplo_sao_comparados_juntos(self):
        codigos = {1: 'import sqlite_utils\ndb = sqlite_utils.Database(memory=True)\nprint(list(db.query("select 1 as id, 2 as id")))',
                   2: 'print(list(db.query("select 1 as id, 2 as id, 3 as id_2")))'}
        assert exemplo_do_bloco(codigos[1], self.ENUNCIADO) == 1 and exemplo_do_bloco(codigos[2], self.ENUNCIADO) == 1
        execs = [{"bloco": 1, "executado": True, "saida": "exit=0 em 0.01s\n[{'id': 1, 'id_2': 2}]"},
                 {"bloco": 2, "executado": True, "saida": "exit=0 em 0.01s\n[{'id': 1, 'id_3': 2, 'id_2': 3}]"}]
        anotar_comparacoes(execs, codigos, self.ENUNCIADO)
        assert "comparacao_enunciado" not in execs[0]
        assert execs[1]["exemplo"] == 1 and execs[1]["blocos_do_exemplo"] == [1, 2]
        assert [c["estado"] for c in execs[1]["comparacao_enunciado"]] == [ENCONTRADA, ENCONTRADA]

    def test_bloco_de_outro_exemplo_sem_saida_esperada_nao_e_pareado(self):
        enunciado = ENUNCIADO  # tem 2 exemplos Python; só o 1º tem saída esperada
        assert exemplo_do_bloco('print("isolado")', enunciado) == 2
        execs = [{"bloco": 1, "executado": True, "saida": "x"}]
        anotar_comparacoes(execs, {1: 'print("isolado")'}, enunciado)
        assert "comparacao_enunciado" not in execs[0]

    def test_exemplo_que_nao_terminou_bem_vira_nao_verificavel(self):
        codigos = {1: 'import sqlite_utils\ndb = sqlite_utils.Database(memory=True)\nprint(list(db.query("select 1 as id, 2 as id")))'}
        execs = [{"bloco": 1, "executado": True, "saida": "exit=1 em 0.01s\nTraceback (most recent call last):\n  ..."}]
        anotar_comparacoes(execs, codigos, self.ENUNCIADO)
        assert execs[0]["comparacao_enunciado"] and all(c["estado"] == NAO_VERIFICAVEL for c in execs[0]["comparacao_enunciado"])
        execs = [{"bloco": 1, "executado": True, "saida": "RECUSADO: o trecho alterou arquivo protegido (x_test.py)."}]
        anotar_comparacoes(execs, codigos, self.ENUNCIADO)
        assert all(c["estado"] == NAO_VERIFICAVEL for c in execs[0]["comparacao_enunciado"])

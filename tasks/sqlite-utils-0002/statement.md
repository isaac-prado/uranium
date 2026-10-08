# sqlite-utils-0002

<!-- PENDENTE: escrever à mão antes de validar -->

## O problema

Descreva o comportamento errado do ponto de vista de quem usa a
biblioteca. Sem citar arquivo, função ou a forma da correção — isso
seria engenharia do harness creditada ao agente.

## Como reproduzir

```python
# trecho que expõe o problema, para o agente rodar com run_python
```

## Comportamento esperado

O que deveria acontecer.

---

<!-- Material de apoio para escrever o enunciado. NÃO faz parte dele.

commit de correção: e4935e064407bc995f77795c025c33cef52d742e
assunto: transform: coerce empty strings to NULL when converting TEXT columns to numeric types (#805)
arquivos de fonte: sqlite_utils/db.py
fail-to-pass: tests/test_transform.py::test_transform_empty_string_to_null_for_numeric_types[REAL-42.0-float], tests/test_transform.py::test_transform_empty_string_to_null_for_numeric_types[float-42.0-float0], tests/test_transform.py::test_transform_empty_string_to_null_for_numeric_types[float-42.0-float1], tests/test_transform.py::test_transform_empty_string_to_null_for_numeric_types[int-42-int], tests/test_transform.py::test_transform_empty_string_to_null_for_numeric_types[integer-42-int], tests/test_transform.py::test_transform_sql_table_with_no_primary_key[False-params1-expected_sql1], tests/test_transform.py::test_transform_sql_table_with_no_primary_key[True-params1-expected_sql1], tests/test_transform.py::test_transform_sql_table_with_primary_key[False-params1-expected_sql1], tests/test_transform.py::test_transform_sql_table_with_primary_key[False-params4-expected_sql4], tests/test_transform.py::test_transform_sql_table_with_primary_key[True-params1-expected_sql1], tests/test_transform.py::test_transform_sql_table_with_primary_key[True-params4-expected_sql4]

corpo do commit:
* transform: coerce empty strings to NULL when converting TEXT columns to numeric types

When a TEXT column is transformed to INTEGER, FLOAT, or REAL and a row
contains an empty string, the empty string is now converted to NULL during
the INSERT...SELECT copy, matching the expected behavior described in #488.

Fixes #488
-->

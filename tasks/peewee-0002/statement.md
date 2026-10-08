# peewee-0002

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

commit de correção: 08b28d1487f188a178a6428e9f43203ee16607eb
assunto: commit/rollback on a closed connection will raise rather than re-open.
arquivos de fonte: peewee.py, playhouse/apsw_ext.py, playhouse/cysqlite_ext.py, playhouse/migrate.py, playhouse/pool.py, playhouse/reflection.py
fail-to-pass: tests/migrations.py::TestSchemaMigration::test_make_index_name_long, tests/reflection.py::TestReflection::test_column_map_not_shared_with_class, tests/sql.py::TestOnConflictSqlite::test_unbound_error, tests/sql.py::TestWindowFunctions::test_duplicate_window_alias_error, tests/transactions.py::TestTransaction::test_commit_rollback_closed, tests/transactions.py::TestTransaction::test_mixing_manual_db_context

corpo do commit:

-->

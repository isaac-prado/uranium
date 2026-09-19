# E3 item 2 — `faixa` de metadado decorativo a eixo de análise

Antes: `faixa` era gravada por `scripts/emit_task.py` no `task.json`, mas o `TaskSpec` nunca a lia — logo não chegava ao `result.json`. A análise por faixa de dificuldade não tinha como ser feita a partir dos resultados.

## Diff por arquivo

- `harness/taskspec.py:57` — novo campo `faixa: str | None = None` no dataclass `TaskSpec`, com comentário explicando por que não há validação contra um conjunto fixo de nomes (as faixas estão sendo redefinidas no E5: "baixa/media/alta" → "pequena/media/grande"). `harness/taskspec.py:118` — `load_task` passa `faixa=dados.get("faixa")`: ausente no `task.json` vira `None`, nunca um valor inventado.
- `harness/evaluate.py:124` — `evaluate_run` inclui `"faixa": task.faixa` no dicionário do `result.json`, ao lado de `task_id`. Não foi preciso descobrir um caminho novo até a tarefa: `evaluate_run(run_dir, task, ...)` já recebe o `TaskSpec` da tarefa do run como parâmetro — o mesmo objeto de onde vêm `task.task_id` e `task.protected_globs` alguns campos acima.
- `harness/schema/result.schema.json` — novo campo de topo `"faixa": {"type": ["string", "null"], ...}`, acrescentado à lista `required` (linha do array `required`, junto de `task_id`). `result_schema_version` sobe de `const: 1` para `const: 2`, porque é mudança de forma do `result.json` (campo novo obrigatório), não só de conteúdo.
- `harness/__init__.py:18-22` — `RESULT_SCHEMA_VERSION` de `1` para `2`, com comentário justificando o bump. Não há nenhum outro leitor desse número no repositório além de `harness/evaluate.py` (que o grava) e `tests/test_harness.py` (que o afirma) — confirmado por busca textual; nada mais dependia dele para eu quebrar ou precisar migrar.
- `scripts/validate_task.py:87-92` — o cabeçalho de `validar()` agora imprime `faixa: <valor>` logo abaixo da linha da tarefa, ou `faixa: AUSENTE — task.json não declara \`faixa\` (aviso, não bloqueia)` quando `task.faixa` é `None`. Não é erro: `Validacao.checar` não é chamado para isso, então uma tarefa sem faixa continua podendo ser validada normalmente.
- `tests/test_harness.py` — ver seção de testes abaixo.

## Testes

Acrescentados em `tests/test_harness.py`:

- `TestFaixa.test_taskspec_carrega_faixa_presente` e `test_taskspec_nao_inventa_faixa_ausente` — `TaskSpec` carrega `"media"` quando o `task.json` declara `faixa`, e devolve `None` (não uma string vazia nem um valor default) quando o campo não existe.
- `TestFaixa.test_tarefas_reais_tem_ou_nao_faixa_conforme_task_json` — documenta o estado real (ver seção seguinte): `tomlkit-0001` carrega `faixa is None`, `sqlite-utils-0001` carrega `faixa == "media"`.
- `TestFaixaNoResultado.test_schema_aceita_faixa_null` — um `result.json` sintético com `faixa: None` valida contra o schema (`Draft202012Validator`).
- `TestFaixaNoResultado.test_evaluate_run_preenche_faixa_a_partir_da_tarefa` — copia a tarefa `tomlkit-0001` para um diretório temporário, acrescenta `"faixa": "grande"` ao `task.json` copiado (sem tocar na tarefa real, que hoje não tem faixa), roda `evaluate_run` de ponta a ponta (mesmo caminho de `TestAvaliacaoIdempotente`, aplicando o patch de referência do upstream sobre o commit-base) e confere que `resultado["faixa"] == "grande"` e que o `result.json` inteiro valida contra o schema atualizado. Requer o mirror do tomlkit (`scripts/setup_mirror.py tomlkit`); pula com `pytest.skip` se ausente, como os testes vizinhos já fazem.

`tests/test_harness.py::TestSchemas::test_versoes_declaradas` atualizado para `RESULT_SCHEMA_VERSION == 2`.

## Item 5 — as duas tarefas existentes

- `tasks/tomlkit-0001/task.json` **não tem** campo `faixa`. Não foi adicionado — a exigência pede para relatar, não inventar.
- `tasks/sqlite-utils-0001/task.json` **já tem** `"faixa": "media"`.

Depois desta mudança, `tasks/tomlkit-0001` produz `result.json` com `"faixa": null` e `tasks/sqlite-utils-0001` produz `"faixa": "media"` — comportamento correto em ambos os casos, sem normalizar a ausência para um valor arbitrário.

## Última linha do pytest

Escopo do item (`tests/test_harness.py tests/test_oracle_contract.py tests/test_test_patch.py`):

```
46 passed in 32.42s
```

Suíte inteira (`.venv/bin/python -m pytest -q`):

```
2 failed, 340 passed in 93.88s (0:01:33)
```

As duas falhas são em `tests/test_seed_repos.py` (`TestSuiteVerdeNoPontoDePartida::test_roda_inteira_e_passa[peewee]` e `test_peewee_sem_alvo_declarado_coletaria_quase_nada`), por `exit_code == 5` (pytest não coletou nenhum teste no mirror local do peewee) — não relacionadas a `faixa`, fora do escopo deste item e não mexidas, conforme instrução.

## Pendências

- `TaskSpec.as_dict()` (`harness/taskspec.py:74`) não inclui `faixa`. Não tem nenhum chamador no repositório hoje (busca textual não encontrou `.as_dict()` de `TaskSpec` fora da própria classe), então não achei necessário estender um método não usado — mas se algum script vier a usá-lo para relatório, vale revisitar.
- Os nomes de faixa em si ("baixa/media/alta" → "pequena/media/grande") não foram tocados, por design: essa renomeação é outro item (E5) e o `TaskSpec` foi deliberadamente feito para não validar contra nenhum conjunto fixo de nomes.
- `scripts/emit_task.py` (fora do meu escopo, editado por outro agente) é quem decide se/como grava `faixa` nas tarefas futuras; este item só garantiu que, uma vez gravada, ela deixa de ser ignorada.

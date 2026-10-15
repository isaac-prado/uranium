# Células da rodada 2 descartadas em 14/10/2026 (~16:50)

Movidas de `runs/coleta-r2/` antes da correção do `--rootdir` do pytest
(`src/tools/exec.run_pytest`, chave `shared_limits.pytest_rootdir` no manifesto).

- `pygments-0001`, `sqlite-utils-0002`, `tomlkit-0004` (todas as repetições gravadas):
  o `visible_deselect` da decisão 27 não surtia efeito, porque o pytest resolvia
  o rootdir para a raiz do uranium e os node ids ganhavam o prefixo
  `runs/.../workspace/`. A suíte visível continuava contraditória, igual à
  coleta principal. Reexecutadas com a mesma semente depois da correção.
- `tomlkit-0003/orchestration/rep01`: `error: StructuredOutputError` no refinador
  (modelo devolveu `reproduction` como lista de listas em 3 tentativas), 0 turnos,
  custo zero. Schema v2 passou a achatar listas aninhadas; célula reexecutada.
- `sqlite-utils-0002/orchestration/rep02/attempt01` estava em andamento quando a
  coleta foi interrompida (sem `summary.json`).

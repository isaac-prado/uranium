# 24. Rodada 8: blocos de reprodução consertados pelo enunciado e saída esperada amarrada ao bloco (22/10/2026)

Aprovada por escrito em 22/10/2026 (decisão 48 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md)), depois da pergunta do autor sobre as tarefas grandes. Só fumaças nesta rodada, com o saldo restante da DeepInfra (cerca de US$ 4,7); os 39 runs dependem de crédito novo.

## 1. O que a rodada 7 mostrou sobre as tarefas grandes

Três tarefas grandes (tomlkit-0002, 0003 e 0004), 9 runs por lado ([23-rodada-7.md](23-rodada-7.md) §4; `runs/coleta-r4`, `dados/coleta-r7/`, `runs/coleta-r2-analise`):

| tarefa | single-agent | rodada 4 | rodada 7 | o que a decide |
|---|---|---|---|---|
| tomlkit-0003 | 3/3 | 3/3 | 3/3 | sempre resolvida |
| tomlkit-0002 | 1/3 | 2/3 | 1/3 | 10 linhas em `api.py`: `key()` aceita lista e devolve `DottedKey(..., sep=" = ")`; sem o `sep` a saída é `foo.bar=1` e o teste oculto exige `foo.bar = 1` |
| tomlkit-0004 | 0/3 | 0/3 | 0/3 | referência de 337 linhas em 3 arquivos (chaves pontilhadas no parser); single-agent 3/7 ocultos em todos os runs com 4 a 5 M de tokens; orquestrado 0 a 3/7; na rodada 7, 2 runs com diff vazio após 120 turnos |

- A tomlkit-0004 é teto dos dois braços com os tetos congelados: o máximo alcançável na faixa grande é 6/9, e a rodada 4 chegou a 5.
- Os dois runs perdidos da tomlkit-0002 na rodada 7 construíram a chave sem o separador (`runs/coleta-r7/tomlkit-0002/.../rep02`, `rep03`, `patch.diff`): rep03 imprimiu `'foo.bar=1\n'`, a revisão reprovou citando o espaçamento e, na seguinte, aprovou a mesma saída; rep02 foi aprovada às cegas, porque os dois blocos de reprodução copiados pelo refinador não compilavam (`["a", "b", "c"]` virou `["a\nb\nc`; `SyntaxError: unmatched ']'`).
- Na rodada 7, 23 blocos de reprodução não compilaram: 16 não são Python (TOML, linha de comando) e 7 eram cópias deturpadas de blocos válidos do enunciado (cerca de markdown dentro do código, caracteres trocados). Sem bloco executado, o revisor aprovou às cegas 3 vezes (tomlkit-0001 rep02, tomlkit-0002 rep02, tomlkit-0003 rep02), uma delas errada.
- Barreira automática não resolve: calibração offline da rodada 7 (`scripts/calibrar_comparacao.py docs/tcc/dados/coleta-r7`), uma barreira dura sobre as saídas esperadas da intent pegaria 4 das 6 aprovações erradas e derrubaria 5 runs resolvidos (saídas parafraseadas pelo refinador). O teto de 2 reprovações não é a causa: as 6 aprovações erradas foram decisões do modelo (`strict_coerced: false` em todas).

## 2. O que muda em relação à rodada 4

| item | chave | rodada 4 | rodada 8 | onde |
|---|---|---|---|---|
| 1. cópia dos blocos de reprodução | `REPRODUCTION_SOURCE` | `intent` (cópia do refinador) | `statement`: cerca perdida removida; bloco que não compila trocado pelo bloco Python mais parecido do enunciado (sobreposição de tokens ≥ 0,5); `fonte` no evento `validation` | `src/enunciado.py::reparar_blocos`; `validator._executar_reproducao` |
| 2. saída esperada por bloco | `BLOCK_EXPECTED` | `off` | `statement`: bloco Python amarrado à "saída esperada" escrita logo depois dele no enunciado ("hoje"/"atual" fora); revisor final e de sub-tarefa recebem, por bloco e por linha, encontrada / NÃO encontrada; informação, sem regra | `pares_esperados`, `esperado_do_bloco`, `comparar_bloco`; `feedback.COMPARACAO_POR_BLOCO` |
| herdados da rodada 7 | `REPRODUCTION_COMPILE_CHECK`, `REPRODUCTION_SHELL` | off | on | decisões 42 e 44 |
| não herdado | `SUBTASK_MAX_CYCLES` | 2 | 2 (a rodada 7 usou 1: mais barato, sem tarefa nova) | decisão 44 |

Pareamento nos 13 enunciados (`tests/test_enunciado.py::test_enunciados_reais`): saída esperada encontrada em tomlkit-0002, 0003, 0004, 0005 e sqlite-utils-0003; nenhuma nos outros 8 (attrs-0001 só traz "Saída hoje"; sqlite-utils-0002 anuncia com "No exemplo acima", sem a palavra "esperada", e fica de fora por conservadorismo).

Comando: `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on PLANNER_MAX_TURNS=12 PLANNER_MAX_SUBTASKS=6 SUBTASK_CHECK=llm REVIEW_COMPARE=off PLANNER_CONTEXT_MAX_CHARS=0 SUBTASK_MAX_CYCLES=2 REPRODUCTION_COMPILE_CHECK=on REPRODUCTION_SHELL=on REPRODUCTION_SOURCE=statement BLOCK_EXPECTED=statement MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=off DEVELOPER_INPUT=intent .venv/bin/python scripts/run_collection.py --arms orchestration ...` (manifesto v17).

## 3. Fumaças (a preencher)

`runs/fumaca-r8`: tomlkit-0002 (2 repetições: a tarefa que decide a faixa grande), tomlkit-0003 (controle, bloco com lista), sqlite-utils-0001 (aprovação às cegas na rodada 7, 0/1 verificável), sqlite-utils-0003 (aprovação errada com saída literal), attrs-0001 (aprovação errada; sem saída esperada no enunciado, mede o item 1 sozinho), tomlkit-0001 (5 blocos que não compilavam) e tomlkit-0005 (saída esperada pareada, nunca resolvida). O que conferir nos eventos: `fonte: cerca | enunciado` nas execuções; `comparacao_enunciado` por bloco; se o revisor cita as linhas; desfecho contra a rodada 7.

## 4. Execução dos 39 runs

Depende de crédito novo (cerca de US$ 5 mais US$ 0,6 de margem).

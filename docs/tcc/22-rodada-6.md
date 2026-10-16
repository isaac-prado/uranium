# 22. Rodada 6: veredito híbrido, revisor sem leniência e bloco que não compila fora da evidência (16/10/2026)

Rodada aprovada por escrito em 16/10/2026 (decisões 40 a 42 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); "Concordo com essas alterações para a rodada 6, prossiga com as alterações"): rodada 5 mais três correções apontadas pelos eventos da própria rodada 5 ([21-rodada-5.md](21-rodada-5.md) §5). Só o orquestrado roda, 13 tarefas × 3 repetições, mesmas sementes; o single-agent de comparação continua sendo o pareado da rodada 2 (`runs/coleta-r2-analise/*/single-agent`). Manifesto v15. Dados: `dados/coleta-r6/` (a versionar no fechamento); fumaça em `dados/fumaca-r6/`.

## 1. O que muda em relação à rodada 5

| item | chave | rodada 5 | rodada 6 | evidência da rodada 5 que motivou | onde |
|---|---|---|---|---|---|
| 1. veredito da sub-tarefa (decisão 40) | `SUBTASK_CHECK` | `deterministic`: comparação; nada verificável → palavra do developer | `hybrid`: suíte vermelha ou diff vazio → não feita; alguma saída verificável → comparação; nenhuma → revisão de sub-tarefa pelo modelo (a da rodada 4), com a execução já feita | 33 das 37 sub-tarefas "feitas" pela palavra do developer, todas no ponto de checagem em que a revisão final reprovava; 16 de 39 runs sem nenhuma comparação verificável; rodada 4: revisão de sub-tarefa "não feita" em 68 de 81 | `src/agents/validator.py::_verificar_subtarefa`, `_revisar_subtarefa_pelo_modelo` |
| 2. revisor final (decisão 41) | `REVIEW_COMPARE`, `REVIEW_STRICT` | `advisory` (linhas de comparação + regra "não verificável não reprova"), `off` | `neutral` (as linhas, sem a regra), `on` (aprovar listando critério não coberto rebaixa); teto de reprovações continua 2 | aprovações no 1º ciclo 7 → 11, erradas 1 → 5; sqlite-utils-0003 rep02/rep03 aprovadas listando os critérios 5, 6 e 7 como não cobertos; com saída verificável faltando a comparação acertou 31 de 32 | `system_prompt_revisao`, `validator()` |
| 3. blocos de reprodução (decisão 42) | `REPRODUCTION_COMPILE_CHECK` | `off`: todo bloco roda; na cadeia acumulada um `SyntaxError` apaga os seguintes | `on`: bloco compilado sozinho antes; o que não compila não roda, sai da cadeia e é rotulado "não é evidência" | tomlkit-0001 rep02: 5 de 6 blocos eram texto TOML; revisor reprovou 3× a correção certa citando `SyntaxError`; developer reescreveu `parser.py` e deixou 74 regressões | `_blocos_que_nao_compilam`, `BLOCO_NAO_COMPILA` |

As demais chaves são as da rodada 5 (`INTENT_REFINER=v2`, `REVIEW_EXECUTION=cumulative`, `CYCLE_NOTE=on`, `PLANNER=on`, `PLANNER_MAX_TURNS=8`, `PLANNER_MAX_SUBTASKS=3`, `PLANNER_CONTEXT_MAX_CHARS=16000`, filtro da decisão 39, `MAX_SEMANTIC_REJECTIONS=2`). Comando: `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on PLANNER_MAX_TURNS=8 PLANNER_MAX_SUBTASKS=3 SUBTASK_CHECK=hybrid REVIEW_COMPARE=neutral PLANNER_CONTEXT_MAX_CHARS=16000 REPRODUCTION_COMPILE_CHECK=on MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=on DEVELOPER_INPUT=intent scripts/run_collection.py --arms orchestration --repetitions 3 --out runs/coleta-r6 --workers 1 --retry-delay 300 --max-attempts 5`.

## 2. O que a rodada mede

- Se devolver ao developer o freio da rodada 4 (revisão de sub-tarefa com motivo) onde a comparação não tem material, mantendo o veredito determinístico onde tem, recupera os 8 runs que a rodada 5 perdeu em relação à 4 sem perder os 2 que ganhou.
- Se tirar a frase de leniência e rebaixar aprovações contraditórias reduz as aprovações finais com oráculo vermelho (7 na rodada 5, 3 na 4) sem voltar às reprovações em série da rodada 3 (teto 2 fica).
- Se rotular os blocos que não compilam tira do revisor a leitura "o exemplo falhou" quando o exemplo nunca rodou (rodadas 3 e 5).
- Custo esperado próximo ao da rodada 5 (US$ 5,6; 614 mil tokens por run), com algumas chamadas a mais do revisor de sub-tarefa.

Leitura prevista para o fechamento: tabela por tarefa contra as rodadas 2, 4 e 5 e o single-agent; vereditos de sub-tarefa por base (`comparacao`, `revisao_do_modelo`, `suite_vermelha`, `sem_mudanca`); aprovações finais erradas e no 1º ciclo; coerções (`strict_coerced`); blocos rotulados como não compiláveis e quantos runs tinham algum.

## 3. Fumaça

Três tarefas, 1 repetição: tomlkit-0003 (controle: continua resolvendo em ~20 turnos), tomlkit-0001 (blocos TOML e zero saídas esperadas: exercita as decisões 40 e 42), sqlite-utils-0003 (muitas saídas esperadas e aprovação contraditória na rodada 5: exercita a decisão 41). Critério: nenhum erro do harness, tomlkit-0003 resolve, e os mecanismos novos aparecem nos eventos.

### 3.1 Fumaça 1 (16/10/2026 14:05 a 14:26, `runs/fumaca-r6`, dados em `dados/fumaca-r6/`): critério não atendido, dois defeitos do instrumento

| tarefa | resultado | turnos | custo | o que aconteceu |
|---|---|---|---|---|
| tomlkit-0003 | **não resolvida** (0/1) | 120 | US$ 0,166 | o refinador entregou o bloco 1 corrompido (começa em `tool.poetry.foo]`, sem `import tomlkit` e `content = """`; a rodada 4 rep01 teve a mesma intent e levou 81 turnos). O rótulo da decisão 42 funcionou (bloco não rodou), mas o revisor final e o de sub-tarefa reprovaram 8 vezes em 8 citando "os exemplos contêm erro de sintaxe e não puderam ser executados"; o developer tinha no ciclo 1 a mesma correção que resolveu a tarefa na rodada 5 (`return repr(self._value)`) e terminou revertendo tudo (`sem_mudanca` no ciclo 8) |
| tomlkit-0001 | **resolvida** (1/1) | 38 | US$ 0,073 | bloco único, zero saídas esperadas; revisão final aprovou no 2º ciclo (rodada 5 rep01: 5 ciclos) |
| sqlite-utils-0003 | não resolvida (0/12) | 120 | US$ 0,395 | 13 saídas esperadas; as de 7 a 13 (tabela de `dedupe_keys`) apontadas por sub-tarefa **sem bloco de reprodução**, e as 5 e 6 por blocos de shell (`python -m sqlite_utils ...`), que não compilam. A comparação final as confrontava com a saída dos outros blocos e saía "NÃO encontrada" 9 vezes por revisão; o revisor reprovou em todos os ciclos por isso, e o developer quebrou a suíte no ciclo 7 (13 erros de coleta) |

Fonte: `dados/fumaca-r6/*/orchestration/rep01/attempt01/{events.jsonl,result.json}`. Os mecanismos novos apareceram nos eventos (`basis=revisao_do_modelo` em 10 vereditos, blocos rotulados `nao_compila`, comparação por sub-tarefa, manifesto v15). Custo US$ 0,63.

**Correções (executor, 16/10/2026 14:4x; mesma versão de manifesto, porque só o que chega ao modelo muda sob as chaves já registradas):**

1. Com `REPRODUCTION_COMPILE_CHECK=on`, o bloco que não executou (não é Python ou não compila) **não aparece** nos prompts do revisor final nem do revisor de sub-tarefa (`validator._evidencias`); o evento `validation` continua registrando todas as execuções, rótulos inclusive. O rótulo "não é evidência" era lido como falha.
2. Com `REVIEW_COMPARE=neutral`, só as linhas com fato (encontrada / NÃO encontrada) chegam ao revisor; "não verificável" fica só no evento.
3. A comparação da revisão final passa a ser **por sub-tarefa**, como já era na sub-tarefa (`_comparar_esperadas`): cada saída esperada só é confrontada com os blocos da sub-tarefa que a aponta; sem plano, tudo contra tudo como antes.
4. Em `src/verificacao.py::comparar_saidas`, um bloco do conjunto que **não rodou** conta como quebrado: saída que falta com bloco parado é "não verificável", nunca "NÃO encontrada" (regra que já valia para bloco que não compilou em execução).

Testes: `tests/test_planner.py::TestRodada6` (+2: bloco não executado e linha não verificável fora do prompt, com o evento completo; comparação final por sub-tarefa sem "NÃO encontrada" inventada, e com o bloco apontado continua "NÃO encontrada" de verdade). Decisão 43 (correção do instrumento, para o autor confirmar) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

### 3.2 Fumaça 2 (a preencher; `runs/fumaca-r6b`)

## 4. Execução (a preencher)

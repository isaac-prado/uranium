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

## 3. Fumaça (a preencher)

Três tarefas, 1 repetição, `runs/fumaca-r6`: tomlkit-0003 (controle: continua resolvendo em ~20 turnos), tomlkit-0001 (blocos TOML e zero saídas esperadas: exercita as decisões 40 e 42), sqlite-utils-0003 (seis saídas esperadas e aprovação contraditória na rodada 5: exercita a decisão 41). Critério combinado com o autor: nenhum erro do harness, tomlkit-0003 resolve, e os mecanismos novos aparecem nos eventos (`basis=revisao_do_modelo`, bloco rotulado, `strict_coerced` quando couber).

## 4. Execução (a preencher)

# 26. Replicação com dois modelos (decisão 45): aptidão, fumaças e coletas

## 1. Desenho

Duas replicações do estudo principal, cada uma com os dois braços, 13 tarefas × 3 repetições (78 runs), mesmas sementes e tetos (decisão 12), orquestrado na configuração da rodada 4 (regra da decisão 45, fechada em 27/10/2026 com o resultado da rodada 8: [24-rodada-8.md](24-rodada-8.md) §4.1). Modelos: `deepseek/deepseek-v3.2` não-pensante na DeepInfra (chave BYOK do autor) e `mistralai/devstral-2512` na Mistral. Manifesto v18: os dois braços e os dois modelos rodam com o workspace só no commit-base e a execução do agente em caixa de areia (decisão 49, [25-vazamento-historico-git.md](25-vazamento-historico-git.md)), o que a coleta principal e as rodadas 2 a 8 não tinham.

Comando (orquestrado da rodada 4, chaves explícitas): `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on PLANNER_MAX_TURNS=12 PLANNER_MAX_SUBTASKS=6 SUBTASK_CHECK=llm REVIEW_COMPARE=off PLANNER_CONTEXT_MAX_CHARS=0 SUBTASK_MAX_CYCLES=2 REPRODUCTION_COMPILE_CHECK=off REPRODUCTION_SHELL=off REPRODUCTION_SOURCE=intent BLOCK_EXPECTED=off MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=off DEVELOPER_INPUT=intent .venv/bin/python scripts/run_collection.py --model <modelo> --provider <provedor> --repetitions 3 --out runs/coleta-<modelo> --workers 1 --retry-delay 300 --max-attempts 5`.

## 2. Sondagem de aptidão (27/10/2026)

`scripts/fitness_test.py --model <modelo> --provider <provedor> -n 5`, laudo em [dados/sondagens/aptidao-replicacao-2026-10-27.txt](dados/sondagens/aptidao-replicacao-2026-10-27.txt):

| modelo · provedor | tool calling | provedor servido | determinismo (assinaturas distintas em 5) | tokens de raciocínio | BYOK | veredito |
|---|---|---|---|---|---|---|
| deepseek/deepseek-v3.2 · DeepInfra | 5/5, argumentos exatos 5/5 | DeepInfra 5/5 | 3 (divergente: declarar a variabilidade) | 0 | sim | apto |
| mistralai/devstral-2512 · Mistral | 5/5, argumentos exatos 5/5 | Mistral 5/5 | 1 | 0 | não (chave Mistral a registrar no OpenRouter) | apto |

O DeepSeek V3.2 na DeepInfra responde sem raciocínio por padrão (`reasoning_tokens` 0 na sondagem e na chamada direta); nada muda no pino de provedor.

## 3. Fumaça do DeepSeek (27/10/2026, 21:59 a 23:17, US$ 1,43)

`runs/fumaca-deepseek`, dados sem workspaces em [dados/fumaca-deepseek/](dados/fumaca-deepseek/). 3 tarefas × 2 braços × 1 repetição, 0 perdidas. Primeira coleta sob a decisão 49: 125 execuções de código do agente (`run_python` e `run_tests`) dentro da caixa de areia, 0 recusadas, 0 erros de ferramenta, 0 sinais do detector; 521 de 521 chamadas BYOK na DeepInfra; 0 tokens de raciocínio.

| tarefa | single-agent | orquestrado |
|---|---|---|
| tomlkit-0003 (grande) | resolvida, 102 turnos, US$ 0,38 | resolvida, 41 turnos, US$ 0,09 |
| sqlite-utils-0003 (média) | resolvida 12/12, 71 turnos, US$ 0,20 | resolvida 12/12, 54 turnos, US$ 0,14 |
| peewee-0002 (média) | orçamento, 5/6 ocultos e 45 regressões, US$ 0,40 | orçamento, 4/6 ocultos e 2 regressões, US$ 0,23 |

4 de 6, as mesmas 4 que o Qwen3-Coder resolve nessas tarefas; peewee-0002 continua sem solução em qualquer modelo ou braço. Cache gravado: 98 a 99 % no single-agent, 88 a 90 % no orquestrado. Latência mediana por chamada entre 4 e 10 s (Qwen: 1 a 3 s): os 78 runs devem levar de 10 a 14 horas de parede. Custo projetado dos 78 runs pela fumaça (US$ 0,09 a 0,40 por run): entre US$ 20 e 30 na DeepInfra, acima dos US$ 16 projetados em [08-escolha-modelo.md](08-escolha-modelo.md) §10.2.

## 4. Coleta do DeepSeek lançada (28/10/2026)

Autor adicionou crédito na DeepInfra e na Mistral em 28/10/2026 ("Pronto, adicionei ambos saldos") e pediu para seguir. Sonda direta antes do lançamento ([dados/sondagens/mistral-byok-429-2026-10-28.txt](dados/sondagens/mistral-byok-429-2026-10-28.txt)): DeepSeek V3.2 na DeepInfra responde com `is_byok: true` e `reasoning_tokens: 0`. **Coleta lançada 28/10 16:11** em `runs/coleta-deepseek`: 78 células (13 tarefas × 2 braços × 3 repetições), `--workers 1 --retry-delay 300 --max-attempts 5`, orquestrado na configuração da rodada 4, manifesto v18 (script de lançamento `runs/_lancamento/fila-deepseek.sh`, fora do versionamento; o comando completo está na §1). Custo projetado US$ 20–30 (§3).

## 5. Devstral: bloqueio na Mistral e destravamento (28/10/2026)

A chave da Mistral estava registrada como BYOK no OpenRouter (o erro voltava com `is_byok: true` e `limit_source: upstream_provider_account`), mas a própria Mistral respondia 429 `Rate limit exceeded`, código 1300, em 4 chamadas de 16 tokens entre 16:10 e 16:11 ([dados/sondagens/mistral-byok-429-2026-10-28.txt](dados/sondagens/mistral-byok-429-2026-10-28.txt)). Causa, confirmada pelo desfecho: a conta estava em "Free mode" e o Devstral 2 não existe no plano gratuito (acesso pago desde 27/01/2026); o modelo nem aparecia na página de limites. Crédito pré-pago não muda a faixa ("Adding credits does not raise your rate limits", central de ajuda da Mistral). O autor ativou o pay-as-you-go e a sonda seguinte, às 16:31:27, respondeu `http=200 provider=Mistral is_byok=True reasoning=0`. O pay-as-you-go da Mistral é pré-pago e inclui franquia de US$ 10/mês de API; saldo zero devolve 402, que o harness trata como run perdido. Autor ligou recarga automática e teto mensal de gastos adicionais de US$ 40. Pendência de conferência: o console mostrava US$ 1,35 de uso incluso quando a soma do `cost_usd` das nossas chamadas era US$ 0,37; comparar no fechamento o uso do console com o total de `cost_usd` (se a Mistral cobrar mais do que o OpenRouter reporta, a métrica de custo da replicação precisa de correção documentada).

## 6. Fumaça do Devstral (28/10/2026, 16:31 a 17:06, US$ 0,97)

`runs/fumaca-devstral`, dados sem workspaces em [dados/fumaca-devstral/](dados/fumaca-devstral/). Mesmas 3 tarefas e configuração da fumaça do DeepSeek (§3), em paralelo com a coleta do DeepSeek já em andamento. 6 células, 0 perdidas, **5 resolvidas** (DeepSeek: 4).

| tarefa | braço | resultado | turnos | parada | ocultos | cache | US$ |
|---|---|---|---:|---|---|---:|---:|
| tomlkit-0003 | single-agent | resolveu | 91 | `tests_pass` | 1/1 | 98 % | 0,265 |
| tomlkit-0003 | orchestration | resolveu | 54 | `concluiu` | 1/1 | 87 % | 0,098 |
| sqlite-utils-0003 | single-agent | resolveu | 56 | `tests_pass` | 12/12 | 97 % | 0,091 |
| sqlite-utils-0003 | orchestration | resolveu | 65 | `concluiu` | 12/12 | 86 % | 0,133 |
| peewee-0002 | single-agent | **resolveu** | 108 | `tests_pass` | 6/6 | 98 % | 0,133 |
| peewee-0002 | orchestration | não | 120 | `budget: max_turns` | 2/6 | 71 % | 0,253 |

Saúde: 513 de 513 chamadas BYOK, todas servidas pela Mistral; 0 tokens de raciocínio; 137 execuções de código do agente na caixa de areia (129 `run_python`, 8 `run_tests`), 0 recusadas, 0 estouros de tempo; detector 0 críticos, 0 avisos; cache de prompt 92,4 % (a Mistral cobra leitura em cache a 10 % do preço de entrada). Os dois únicos retornos de erro de ferramenta são a mensagem de protocolo do `replace_in_file` para trecho ambíguo (tomlkit-0003 single-agent, turnos 82 e 84). Custo por run entre US$ 0,09 e US$ 0,27; projeção dos 78 runs US$ 15–25.

## 7. Coleta do Devstral lançada (28/10/2026, 17:07)

Fumaça limpa em todos os critérios → **coleta lançada 28/10 17:07** em `runs/coleta-devstral` (78 células, mesmos parâmetros da §4, script `runs/_lancamento/fila-devstral.sh`), em paralelo com a do DeepSeek (provedores distintos; a execução de código é leve, mediana 6 s e máximo 47 s por suíte contra teto de 120 s, medido nos runs de hoje). Autor avisado de que a máquina não pode suspender; combinado que uso moderado da máquina é aceitável e que estouros de tempo em `test_run` serão auditados no fechamento como possível confundidor.

## 8. Pendente

- Fechamento de cada coleta com as sete métricas (`scripts/analyze_results.py`), auditoria de `timed_out` nas suítes, comparação com o estudo principal.
- Conferir o uso cobrado no console da Mistral contra a soma de `cost_usd` (§5).

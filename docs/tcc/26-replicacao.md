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

## 8. Coleta do Devstral fechada (28/10/2026, 17:07 a 22:48, 78/78, 0 perdidas)

Dados em [dados/coleta-devstral/](dados/coleta-devstral/) (runs sem workspaces, `collection.json`, `collection.log`, `analise-sete-metricas.{md,json}` de `scripts/analyze_results.py`, `apendice-metricas.md` de `scripts/metrics_appendix.py`, `resumo-devstral.txt` de `scripts/resumo_rodada.py`, `auditoria-saude.txt`). Dois braços na mesma coleta, mesmas sementes por repetição, manifesto v18.

### 8.1 Saúde

5.392 de 5.392 chamadas BYOK, todas servidas pela Mistral; 0 tokens de raciocínio; cache de prompt 93,8 %; detector 0 críticos e 0 avisos; 0 estouros de tempo em suíte (oráculo e agente); 0 ferramentas negadas; 78 de 78 runs admitidos pela análise, nenhum par quebrado (`auditoria-saude.txt`, `analise-sete-metricas.md`). O autor usou a máquina durante a coleta (decisão registrada na §7); sem estouro de tempo, não há confundidor a declarar.

### 8.2 Resultado

| | single-agent | orchestration |
|---|---|---|
| runs resolvidos | **28/39** | **30/39** |
| tarefas (maioria das repetições) | **9/13** | **10/13** |
| grande | 4/9 runs, 1/3 tarefas | 5/9 runs, 2/3 tarefas |
| média | 11/12 runs, 4/4 tarefas | 9/12 runs, 3/4 tarefas |
| pequena | 13/18 runs, 4/6 tarefas | 16/18 runs, 5/6 tarefas |
| cortes por orçamento | 12 | 7 |
| turnos médios | 72 | 62 |
| custo reportado pelo OpenRouter | US$ 5,46 | US$ 4,24 |

Sete métricas (`analise-sete-metricas.md`, diferença orchestration − single-agent, unidade = tarefa): resolução 9/13 × 10/13 (sinal exato, n = 5, p = 1,0); tokens, mediana 1.002.483 × 525.005 (Wilcoxon, n = 7 tarefas resolvidas por ambos, **p = 0,031**); tempo 154,5 s × 180,1 s (p = 0,69); Δ complexidade 0,028 × 0,015 (p = 1,0); consistência 8/11 × 9/11; conclusão sem corte 27/39 × 32/39; violações 0 em ambos. O orquestrado gasta cerca de metade dos tokens nas tarefas que os dois resolvem, e é a única diferença com p abaixo de 0,05.

Por tarefa (repetições 1 a 3; `auditoria-saude.txt`): o orquestrado leva sqlite-utils-0001 3/3 contra 0/3 (o single-agent entrega suíte visível verde e o oculto reprova, nas 3 repetições), pygments-0001 3/3 contra 1/3 e a grande tomlkit-0002 2/3 contra 1/3; o single-agent leva peewee-0002 2/3 contra 0/3 e tomlkit-0005 3/3 contra 1/3. tomlkit-0004 fica 0/6 e as outras sete tarefas 3/3 nos dois braços. Aprovações erradas do revisor final: 3 (peewee-0002 rep01 e rep03, tomlkit-0005 rep02), todas na classe "nenhum exemplo exercita o critério oculto". Resolvidos só pelo oráculo, com corte por orçamento: 5 (peewee-0002 single rep01, sqlite-utils-0002 single rep02, tomlkit-0002 orq rep03, tomlkit-0003 single rep01 e rep03).

Contra o estudo principal (Qwen3-Coder, rodada 4: single-agent 23/39 e 8/13, orquestrado 24/39 e 9/13): o Devstral 2 resolve mais nos dois braços e a diferença entre braços tem o mesmo sinal e o mesmo tamanho em tarefas (+1), sem significância; o padrão por faixa também se repete, com o orquestrado à frente na grande e atrás na média.

### 8.3 Custo real na Mistral

`cost_usd` dos runs do Devstral é o `upstream_inference_cost` que o OpenRouter estima assumindo leitura em cache a 10 % do preço de entrada; a Mistral cobra o Devstral 2 pelo preço cheio ou perto disso. Soma reportada US$ 9,70; preço de tabela sem desconto de cache US$ 50,70 para os mesmos tokens; o autor observou cerca de US$ 35 no console com 74 de 78 células, compatível com o preço cheio menos a franquia de US$ 10 ([dados/sondagens/mistral-byok-429-2026-10-28.txt](dados/sondagens/mistral-byok-429-2026-10-28.txt), que traz também a contraprova na DeepInfra: saldo caiu US$ 6,44 contra US$ 6,43 reportados, razão 1,00). **Na replicação Devstral, a métrica de custo em dólares usa a cobrança do console da Mistral como fonte, pendente do autor informar o valor final do mês por modelo; `cost_usd` fica registrado como estimativa do OpenRouter e a comparação em tokens (métrica 2) não é afetada.**

## 9. Coleta do DeepSeek fechada (28/10 16:11 a 29/10 06:03, 78/78, 0 perdidas)

Dados em [dados/coleta-deepseek/](dados/coleta-deepseek/) (runs sem workspaces, `collection.json`, `collection.log`, `analise-sete-metricas.{md,json}`, `apendice-metricas.md`, `resumo-deepseek-devstral.txt` com as duas coletas lado a lado, `auditoria-saude.txt`). 13 h 52 de parede, em paralelo com a do Devstral nas primeiras 5 h 41.

### 9.1 Saúde

5.777 de 5.777 chamadas BYOK, todas servidas pela DeepInfra; 0 tokens de raciocínio; cache de prompt 95,2 %; 0 estouros de tempo em suíte (oráculo e agente); 0 ferramentas negadas; 78 de 78 runs admitidos, nenhum par quebrado. Detector: 0 críticos e **1 aviso**, regra C6 (exceção silenciada introduzida, `except Exception: pass` em `sqlite_utils/db.py`) em sqlite-utils-0001 orquestrado rep03, run não resolvido, sem bloqueio; fica registrado como aviso, não como trapaça. Custo reportado pelo OpenRouter US$ 13,58, e aqui o valor é a cobrança real: a contraprova de 28/10 às 22:37 deu razão 1,00 entre a queda do saldo da DeepInfra e a soma de `cost_usd` (§8.3).

### 9.2 Resultado

| | single-agent | orchestration |
|---|---|---|
| runs resolvidos | **26/39** | **26/39** |
| tarefas (maioria das repetições) | **9/13** | **9/13** |
| grande | 3/9 runs, 1/3 tarefas | 6/9 runs, 2/3 tarefas |
| média | 9/12 runs, 3/4 tarefas | 8/12 runs, 3/4 tarefas |
| pequena | 14/18 runs, 5/6 tarefas | 12/18 runs, 4/6 tarefas |
| cortes por orçamento | 8 | 11 |
| turnos médios | 68 | 75 |
| custo (cobrança real) | US$ 8,02 | US$ 5,56 |

Sete métricas (`analise-sete-metricas.md`): resolução 9/13 × 9/13 (sinal exato, n = 3, p = 1,0); tokens, mediana 706.968 × 792.110 (Wilcoxon, n = 8, p = 0,55); tempo 391 s × 591 s (p = 0,055, orquestrado mais lento); Δ complexidade 0,031 × 0,028 (p = 0,64); consistência 8/9 × 8/9; conclusão sem corte 31/39 × 28/39; violações 0 em ambos. Nenhuma diferença significativa.

Por tarefa (`auditoria-saude.txt`): o orquestrado leva a grande tomlkit-0002 3/3 contra 0/3; o single-agent leva sqlite-utils-0001 2/3 contra 0/3 e sqlite-utils-0003 3/3 contra 2/3; peewee-0002, sqlite-utils-0002 e tomlkit-0004 ficam 0/6; as outras sete tarefas 3/3 nos dois braços. Aprovações erradas do revisor final: **7**, todas em sqlite-utils (0001 ×3, 0002 ×3, 0003 rep03), a classe "nenhum exemplo exercita o critério oculto" que a rodada 8 já tinha medido com o Qwen (7, em attrs-0001 e sqlite-utils). Resolvidos só pelo oráculo, com corte por orçamento: 5, todos no orquestrado (attrs-0001 rep01, tomlkit-0001 ×3, tomlkit-0005 rep01): o revisor do DeepSeek reprova um estado correto até o teto, e em tomlkit-0001 faz isso nas três repetições.

## 10. Síntese das três coletas

Mesmas 13 tarefas, mesmas sementes por repetição, mesmos tetos; orquestrado na configuração da rodada 4. Fontes: estudo principal `dados/coleta/` (single-agent) e `dados/coleta-r4/` (orquestrado), replicações §8 e §9.

| modelo | single-agent runs / tarefas | orchestration runs / tarefas | OR − SA | grande (runs, SA × OR) | diferença com p < 0,05 |
|---|---|---|---|---|---|
| Qwen3-Coder (DeepInfra), estudo principal + rodada 4 | 23/39, 8/13 | 24/39, 9/13 | +1 run, +1 tarefa | 4/9 × 5/9 | nenhuma |
| DeepSeek V3.2 (DeepInfra) | 26/39, 9/13 | 26/39, 9/13 | 0, 0 | 3/9 × 6/9 | nenhuma (tempo p = 0,055, orquestrado mais lento) |
| Devstral 2 (Mistral) | 28/39, 9/13 | 30/39, 10/13 | +2 runs, +1 tarefa | 4/9 × 5/9 | tokens (orquestrado ≈ metade, p = 0,031) |

Leitura: em nenhum dos três modelos a topologia muda a taxa de resolução de forma significativa; a diferença em tarefas fica entre 0 e +1 a favor do orquestrado. O único padrão que se repete nos três é a faixa grande, em que o orquestrado resolve mais runs (5/9, 6/9 e 5/9 contra 4/9, 3/9 e 4/9), com a tarefa tomlkit-0002 resolvida pelo orquestrado 3/3 no DeepSeek e 2/3 no Devstral contra 0/3 e 1/3 do single-agent. As tarefas que travam são as mesmas nos três modelos (tomlkit-0004 por orçamento, peewee-0002 e sqlite-utils-0002 no DeepSeek, sqlite-utils-0001 no single-agent do Devstral e no orquestrado do DeepSeek), e as aprovações erradas do revisor se concentram nas tarefas sem exemplo que exercite o critério oculto (sqlite-utils-0001 e 0002 nos dois modelos da replicação e no Qwen). O que muda entre modelos é o custo da topologia: no Devstral o orquestrado gasta metade dos tokens; no DeepSeek gasta o mesmo e demora mais. A métrica de custo em dólares do Devstral depende da cobrança da Mistral (§8.3).

## 11. Pendente

- Valor final de uso do Devstral no console da Mistral (autor), para a métrica de custo em dólares da §8.3; o saldo final da DeepInfra confirma a do DeepSeek (esperado ≈ US$ 30 − 13,58).
- Leitura do autor sobre a síntese (§10) e decisão sobre o que entra no texto do TCC.

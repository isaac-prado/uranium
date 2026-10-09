# E4 — Teste de fumaça pago na tarefa grande e calibração dos tetos

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 8 de outubro de 2026

Etapa E4 de [EXIGENCIAS.md](tasks/EXIGENCIAS.md): "escrever uma tarefa da faixa grande → teste de fumaça pago nela, nos dois braços → só então fixar os tetos". Autorização do autor em 08/10/2026 (decisões 12 e 17 de [09-decisoes-do-autor.md](09-decisoes-do-autor.md)). Dados brutos (manifesto, resumo, resultado, trilha de eventos e patch de cada execução, sem o workspace) em [dados/fumaca-08-10/](dados/fumaca-08-10/); saídas dos scripts em `analyze_results.md`, `analyze_collection.txt` e `collection.log` no mesmo diretório.

## 1. O que rodou

`scripts/run_collection.py --tasks tasks/tomlkit-0002 tasks/tomlkit-0001 --repetitions 1 --workers 1`, o mesmo caminho da coleta definitiva. Modelo `qwen/qwen3-coder` via DeepInfra pinado, `LLM_REQUEST_TIMEOUT=90`, tetos do piloto (`RUN_MAX_TOKENS=1200000`, `RUN_MAX_WALL_SECONDS=1800`, `RUN_MAX_TURNS=40`), semente da repetição 1, `SEMANTIC_REVIEW` ligada, `MAX_SEMANTIC_REJECTIONS=2`. Quatro células, das 19:2x às 19:36 de 08/10/2026.

## 2. Resultado por célula (`dados/fumaca-08-10/*/summary.json` e `result.json`)

| Tarefa | Faixa | Braço | Parada | Resolvida | Turnos | Chamadas | Tokens | US$ | Parede (s) | Maior prompt (tokens) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| tomlkit-0002 | grande | single-agent | `budget: max_turns (40 >= 40)` | sim | 40 | 40 | 514.378 | 0,0582 | 71,7 | 19.216 |
| tomlkit-0002 | grande | orchestration | `budget: max_turns (40 >= 40)` | sim | 40 | 43 | 395.096 | 0,0487 | 117,5 | 16.488 |
| tomlkit-0001 | pequena | single-agent | `tests_pass` | sim | 11 | 11 | 128.235 | 0,0168 | 26,5 | 15.287 |
| tomlkit-0001 | pequena | orchestration | `concluiu` | sim | 32 | 35 | 248.593 | 0,0313 | 105,6 | 11.658 |

Custo total da fumaça: US$ 0,155. Nenhuma tentativa perdida; provedor servido `DeepInfra` em 129 de 129 chamadas; `tokens_reasoning = 0` em todas; detector de trapaça limpo nas quatro.

## 3. O que a fumaça mostrou

**O teto de 40 turnos é apertado para a faixa grande, nos dois braços.** As duas execuções da `tomlkit-0002` foram cortadas em `max_turns` com a correção já no lugar (o oráculo deu `resolved = true` nas duas). Na trilha do single-agent, as 4 escritas em arquivo aconteceram cedo e os turnos 33 a 40 são leitura, busca e `run_python` de verificação: o agente nunca encerrou um turno sem chamar ferramenta, então o operador nunca rodou a suíte e o run morreu verificando. No orquestrado, o validator rodou a suíte duas vezes (verde) e o developer continuou explorando até o teto. Com 40 turnos o desfecho "resolvida" ficou dependente de o corte cair depois da escrita; com uma tarefa um pouco maior cairia antes, e o resultado seria o artefato que a E4 descreve ("nenhuma arquitetura resolve tarefa complexa").

**Tokens e tempo de parede não foram o gargalo.** Máximo observado: 514 mil tokens (43% do teto de 1,2 M) e 118 s de parede (6,5% do teto de 1.800 s). O maior prompt único foi 19.216 tokens, longe dos 64 k de contexto exigidos em [08-escolha-modelo.md](08-escolha-modelo.md).

**A instrumentação está íntegra.** `scripts/analyze_collection.py` e `scripts/analyze_results.py` dão o mesmo n, as mesmas perdas (zero) e os mesmos pares; os quatro `result.json` passam nos três portões de admissão; `scripts/context_accounting.py` reconstrói o prompt de cada chamada com discrepância 0,0% nas quatro execuções (modo exato, instrumentação completa). Não houve defeito novo; a ablação e a coleta estão liberadas pelo critério da semana 5 do [04-cronograma.md](04-cronograma.md).

**Observação lateral (não é defeito).** Na pequena, o orquestrado gastou 32 turnos de developer contra 11 do single-agent e terminou com `concluiu` em vez de `tests_pass`: o developer encerrou sem chamar ferramenta depois de o validator já ter visto a suíte verde. É comportamento do tratamento, medido pelas métricas 2 e 3, e aparece na tabela do E1 (custo fixo dos nós auxiliares: 3 chamadas de 35).

## 4. Proposta de tetos para congelar (decisão 12, G4)

Regra combinada em 08/10 (decisão 12): 2× o máximo observado na fumaça nos dois braços, nunca abaixo dos valores atuais, com um teto só fazendo o corte. Aplicada:

| Teto | Piloto | Máximo observado | 2× | Proposta | Por quê |
|---|---:|---:|---:|---:|---|
| `RUN_MAX_TURNS` | 40 | 40 (cortado) | 80 | **80** | o único teto que cortou; o máximo observado é o próprio teto, então 2× é o mínimo defensável |
| `RUN_MAX_TOKENS` | 1.200.000 | 514.378 | 1.028.756 | **2.500.000** | 2× daria menos que o atual; mas com 80 turnos o prompt cresce com o quadrado dos turnos (Σ prompt de 511 k em 40 turnos no single-agent), e 1,2 M passaria a cortar antes dos 80 turnos. O teto de tokens fica alto o bastante para o corte ser sempre por turnos, que é a unidade declarada no desenho |
| `RUN_MAX_WALL_SECONDS` | 1.800 | 118 | 236 | **1.800** | 2× ficaria abaixo do atual; a parede é dominada pela latência do provedor (p99 de 60 s por chamada × retentativas), não pelo agente, e um teto baixo vira censura por infraestrutura (BACKLOG 8) |
| `test_timeout_s` | 120 | suítes de 3 a 12 s | — | **120** | sem mudança |

Custo projetado com 80 turnos: a execução grande que hoje custa US$ 0,05 a 0,06 pode chegar a cerca de US$ 0,20 se usar os 80 turnos (custo cresce com o quadrado); 78 execuções entre US$ 3 e US$ 10, dentro do teto acordado.

**A decisão de congelar é do autor** (decisão 12). Depois de confirmada: valores vão para `.env`, `.env.example`, `src/budget.py` (defaults), `CLAUDE.md` (seção "Tetos do run", com a data) e aparecem em `budget` no manifesto de todo run; não mudam até o fim da coleta.

## 5. Fumaça B: a tarefa maior com os tetos propostos, perdida por 429 do DeepInfra

Às 19:4x de 08/10, `tomlkit-0004` (9 arquivos, a maior das três grandes) nos dois braços com `RUN_MAX_TURNS=80` e `RUN_MAX_TOKENS=2500000` (`dados/fumaca-08-10-b/`). **As duas células saíram perdidas**: três tentativas cada, todas `infra_error: RateLimitError`, com o DeepInfra devolvendo `429 — qwen/qwen3-coder is temporarily rate-limited upstream` (`provider_error_code: engine_overloaded`, `limit_source: upstream_provider_shared_pool`), o mesmo episódio de 28/09. A primeira tentativa do single-agent chegou ao turno 37 (767 mil tokens) antes do 429; as cinco seguintes morreram na primeira chamada, com 60 s de espera entre elas. Sondagem às 19:50: DeepInfra ainda em 429; **Novita deixou de servir o modelo** (404 "No allowed providers"). Provedores que servem `qwen/qwen3-coder` com todos os parâmetros exigidos em 08/10/2026 (`fitness_test.py --list-providers`, endpoint público do OpenRouter): Google (contexto 262 k, quantização não declarada, US$ 0,22/M prompt e 1,80/M saída, uptime 100%), DeepInfra (262 k, **fp4**, 0,30/1,00), Alibaba (262 k, não declarada, 0,975/4,875). Sondagem de aptidão (`dados/validacao-08-10/fitness_test_alibaba_google.txt`): **Google APTO** 5/5 e **Alibaba APTO** 5/5, ambos determinísticos.

**Dois achados para o desenho.**

1. **O crescimento de tokens é superlinear.** No single-agent da `tomlkit-0004`: 66 mil tokens acumulados no turno 7, 276 mil no 19, 588 mil no 31, 767 mil no 36 (prompt único de 36,8 mil no turno 36). Aproximando por `k·t²`, 80 turnos projetam cerca de 3,8 M tokens. **O teto de 2,5 M proposto na seção 4 cortaria antes dos 80 turnos.** Proposta revista: `RUN_MAX_TOKENS=4000000`, para o corte continuar sendo por turnos. Custo projetado de uma execução que use os 80 turnos: 3,8 M × ~US$ 0,11/M (preço efetivo medido) ≈ **US$ 0,43**; a chave atual tem limite de US$ 5 (`/auth/key`: `limit 5`, restante 4,75) e os créditos somam US$ 10 (usados 1,77). **Para a coleta de 78 execuções é preciso subir o limite da chave** (ou criar outra sem limite) antes de começar.
2. **O provedor é o ponto frágil, não o modelo nem o harness.** O DeepInfra entregou 129/129 chamadas na fumaça A e falhou em cadeia 40 minutos depois; é o pool compartilhado do OpenRouter. Três saídas: (a) trocar o pino para **Google** (apto, mais barato no prompt, que domina o custo; quantização não declarada, a registrar como limitação); (b) manter DeepInfra com chave própria do DeepInfra registrada no OpenRouter (BYOK), que tira o run do pool compartilhado, com o mesmo pino e a mesma quantização fp4; (c) manter DeepInfra e alongar a espera entre tentativas (`--retry-delay 300`, `--max-attempts 5`), aceitando perdas. Nas três, a decisão 11 é reaberta e o provedor escolhido é declarado no manifesto de toda a coleta; os dois braços sempre no mesmo provedor.

A fumaça C, na mesma tarefa com o Google e `RUN_MAX_TOKENS=4000000`, está em `dados/fumaca-08-10-c/` (seção 6).

## 6. Fumaça C: a tarefa maior no Google, com 80 turnos e 4 M tokens

Mesma `tomlkit-0004`, dois braços, `OPENROUTER_PROVIDER=Google`, `RUN_MAX_TURNS=80`, `RUN_MAX_TOKENS=4000000`, `--retry-delay 120` (`dados/fumaca-08-10-c/`). **Zero perdas: o Google atendeu 162 de 162 chamadas**, 80 turnos em cada braço, contabilidade de contexto fechando em 0,0% nos dois (modo exato, instrumentação completa).

| Braço | Parada | Resolvida | Testes ocultos | Turnos | Tokens | US$ | Parede (s) | Maior prompt |
|---|---|---|---|---:|---:|---:|---:|---:|
| single-agent | `budget: max_turns (80 >= 80)` | não | 0/7 | 80 | 2.287.280 | 0,5274 | 259 | 48.671 |
| orchestration | `budget: max_turns (80 >= 80)` | não | 5/7 | 80 | 3.706.751 | 0,8625 | 434 | 74.450 |

**O que aconteceu em cada braço.** O single-agent escreveu em 24 turnos (do 22 ao 79), nunca chamou `run_tests` (16 `run_python`) e terminou com 0 de 7 testes ocultos verdes. O orquestrado escreveu em 17 turnos, rodou `run_tests` 9 vezes, o validator rodou a suíte uma vez, e terminou com 5 de 7 ocultos verdes mas com regressão na suíte visível (`p2p` exit 1); os dois que faltam são a ida e volta exata do exemplo 0.5.0 e a quebra de linha do cabeçalho de tabela. Nenhum dos dois parou de editar antes do teto: os dois cortes são por turnos, com o teto de tokens a 57% (single-agent) e 93% (orquestrado) do limite de 4 M.

**Leitura para a E4.** A `tomlkit-0004` (9 arquivos, 178 linhas, sete testes ocultos de três comportamentos, commit de 2018) está além dos dois braços com 80 turnos. Como os dois foram medidos com o mesmo teto e o mesmo provedor, "não resolvida por ambos" é um resultado válido e pareado, não um viés entre braços; mas a E4 pede que o teto não transforme "difícil" em "impossível" de forma indistinguível. O orquestrado estava progredindo (5/7) quando foi cortado; o single-agent não. Não há execução resolvida nesta tarefa para aplicar a regra "2× o máximo observado": o máximo observado é o próprio teto.

**Custo com 80 turnos.** US$ 0,53 e 0,86 por execução cortada; a projeção da seção 5 (US$ 0,43) foi baixa porque o orquestrado reconstrói o contexto por ciclo e chegou a prompts de 74 mil tokens. Para a coleta: as 18 execuções da faixa grande (3 tarefas × 2 braços × 3 repetições) podem custar até US$ 15 se todas usarem o teto; as 60 restantes, pela fumaça A, de US$ 1 a 4. Total plausível entre US$ 8 e 20, acima do limite de US$ 5 da chave atual e dentro do teto de US$ 50 acordado.

## 7. Decisões que ficam com o autor depois das três fumaças

1. **Tetos (decisão 12, G4).** Três caminhos, todos com `RUN_MAX_WALL_SECONDS=1800` e `test_timeout_s=120`: (a) congelar **80 turnos e 4 M tokens** e aceitar que a grande mais dura pode ficar não resolvida pelos dois braços, declarando no texto que o corte é por turnos e que a `tomlkit-0004` foi cortada nos dois na fumaça; (b) subir para **120 turnos e 8 M tokens** (custo por execução grande até cerca de US$ 2, coleta até US$ 40 no pior caso, só cabe com o teto de US$ 50 inteiro e sem refazer a coleta); (c) manter 80/4 M e **trocar a `tomlkit-0004`** por uma grande mais leve, o que reabre a decisão 23 e exige nova fumaça. Recomendação: (a). O desenho mede os dois braços sob o mesmo orçamento, e "nenhum resolve a mais difícil em 80 turnos" é um achado, desde que o orçamento esteja declarado e seja o mesmo para os dois.
2. **Provedor (decisão 11).** O Google atendeu 162/162 chamadas com prompts de até 74 mil tokens e latência compatível (434 s de parede em 82 chamadas); o DeepInfra falhou em cadeia duas vezes em dez dias. Recomendação: **pinar o Google** para a coleta inteira, registrar no manifesto, declarar a quantização como não informada pelo endpoint e manter DeepInfra (fp4) como reserva só para o caso de o Google sair do ar, com a leva marcada. Preço por 1 M tokens: Google 0,22 (prompt) e 1,80 (saída); DeepInfra 0,30 e 1,00; o custo é dominado pelo prompt.
3. **Limite da chave.** Subir de US$ 5 para ao menos US$ 25 antes da coleta.
4. **Ablação do refinador (decisões 7 e 16)** continua pendente e pode rodar na mesma leva.

## 8. Fumaça D (09/10/2026): 120 turnos e 8 M tokens no Google

Decisão do autor de 09/10: a `tomlkit-0004` tem de ser resolvida; os tetos sobem em rodadas até um braço resolver. Rodada com `RUN_MAX_TURNS=120`, `RUN_MAX_TOKENS=8000000`, Google (`dados/fumaca-09-10-d/`). Zero perdas.

| Braço | Parada | Resolvida | Testes ocultos | Regressão (`p2p`) | Turnos | Tokens | US$ | Parede (s) | Maior prompt |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| single-agent | `budget: max_turns (120 >= 120)` | não | 5/7 | exit 1 | 120 | 5.994.735 | 1,3732 | 654 | 91.114 |
| orchestration | `budget: max_turns (120 >= 120)` | não | 5/7 | exit 1 | 120 | 3.255.936 | 0,7799 | 549 | 62.174 |

Os dois chegaram a 5 de 7 (o single-agent saiu de 0/7 com 80 turnos para 5/7 com 120) e os dois deixaram regressão na suíte visível; os dois que faltam são os mesmos da fumaça C. O custo do single-agent dobrou e meio em relação a 80 turnos (US$ 0,53 → 1,37), porque o prompt chega a 91 mil tokens por chamada. Saldo da chave depois desta rodada: US$ 1,23 de 5. **A próxima rodada (160 turnos ou mais) custa mais que o saldo**; fica para depois da recarga, e a decisão 24 (enunciado íntegro ao developer) entra antes dela, porque muda o que o orquestrado recebe e pode mudar o resultado nesta mesma tarefa.

## 9. Checagem da decisão 24 e o 429 também no Google (09/10/2026)

Primeira tentativa da checagem (só o braço orquestrado, `tomlkit-0004`, 120 turnos, Google, manifesto v4 com `developer_input = enunciado+intent`): **perdida no turno 18** por `429 — qwen/qwen3-coder is temporarily rate-limited upstream`, com `provider_name: Google`, `limit_source: upstream_provider_shared_pool` (`runs/fumaca-09-10-e/orchestration-attempt01-perdido`, US$ 0,04). É a mesma mensagem que o DeepInfra devolveu em 28/09 e 08/10. **O gargalo não é o provedor: é o pool compartilhado do OpenRouter para este modelo**, que limita todos os usuários sem chave própria, em qualquer provedor. O próprio erro aponta a saída ("add your own key to accumulate your rate limits"): registrar uma chave do provedor (Google Vertex ou DeepInfra) nas integrações do OpenRouter (BYOK). O pino continua o mesmo, o manifesto registra `is_byok`, e o run sai do pool compartilhado. Sem isso, a coleta de 78 execuções vai acumular perdas e reexecuções a cada pico de uso do pool, e 120 turnos com prompts de 60 a 90 mil tokens são exatamente o perfil que o pool corta.

Recomendação para a coleta: **BYOK no provedor pinado** (decisão 11 ganha esse requisito), mais `--retry-delay 300` e `--max-attempts 5` em `run_collection.py`, porque a espera de 60 a 120 s não cobre a janela de rate limit observada.

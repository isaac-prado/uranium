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

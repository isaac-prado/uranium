# Escolha do modelo e do provedor para a coleta paga

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 19 de setembro de 2026

Todos os preços, contextos, provedores, quantizações e uptimes deste documento foram consultados **ao vivo em 19/09/2026** na API pública do OpenRouter (`https://openrouter.ai/api/v1/models` e `https://openrouter.ai/api/v1/models/{autor}/{slug}/endpoints`), sem chave e sem nenhuma chamada de inferência paga. A data de consulta está repetida no cabeçalho de cada tabela. Nenhum número vem de `docs/dossie-metodologico.html`. Os números do piloto vêm de `docs/tcc/dados/runs-11-09/*/result.json` e dos `events.jsonl` correspondentes.

## 1. Por que esta decisão importa e o que ela trava

O desenho do E1 fixa o modelo como constante, não como variável. Os dois braços compartilham a mesma `LLMConfig` ([src/config.py:51-70](../../src/config.py#L51-L70)), e o teste de paridade falha se qualquer campo divergir entre eles ([docs/tcc/01-inventario.md](01-inventario.md), linha 135). Modelo e provedor entram no manifesto de cada execução e na proveniência de cada `result.json`. Trocar de modelo no meio da coleta invalida o pareamento: as 72 execuções deixam de ser comparáveis entre si, e o Wilcoxon pareado sobre custo em tokens, que é a métrica primária inferencial ([docs/tcc/03-metricas.md](03-metricas.md), linha 17), perde a base.

O que esta decisão trava, na ordem do cronograma:

- **G4 e E4.** Os tetos de turnos, tokens e tempo de parede ([src/budget.py](../../src/budget.py)) serão calibrados na primeira tarefa da faixa grande e congelados. A calibração é específica do modelo: um modelo que produz raciocínio ou que precisa de mais turnos muda todos os três tetos. Escolher o modelo depois de congelar os tetos inverte a ordem obrigatória da E4 ([docs/tcc/tasks/EXIGENCIAS.md](tasks/EXIGENCIAS.md), E4).
- **A contabilidade de contexto do E1.** A decomposição do prompt cobrado foi fechada com `tokens_reasoning = 0` em todas as execuções, e a seção 6 de [06-contabilidade-contexto.md](06-contabilidade-contexto.md) registra que a conta **não foi testada com modelos que produzem raciocínio**. Um modelo com raciocínio ligado exige refazer a validação do script de contabilidade antes de qualquer coleta.
- **O orçamento.** O saldo é de US$ 8,64 e o teto acordado é de US$ 50, reservado para refazer a coleta inteira uma vez ([04-cronograma.md](04-cronograma.md), seção 4). A diferença de preço entre os candidatos que passam nos requisitos vai de US$ 0,59 a US$ 20,88 pelas mesmas 91 execuções (tabela da seção 5). Alguns candidatos plausíveis estouram o saldo sozinhos.
- **A janela de coleta.** A coleta definitiva é a semana de 19/10 a 25/10 e a defesa é em 23/11/2026. O endpoint pinado precisa existir nas duas datas.

Depois de iniciada a coleta, esta decisão não pode ser revista. Por isso ela é tomada agora, antes do teste de fumaça.

## 2. Requisitos, com a origem no código

### R1. Provedor pinável que honre `temperature`, `seed`, `max_tokens`, `tools` e `tool_choice`

`provider_routing()` monta `{"only": [provedor], "allow_fallbacks": false, "require_parameters": true, "data_collection": "deny"}` ([src/config.py:72-85](../../src/config.py#L72-L85)), e `_validate` recusa a configuração se `allow_fallbacks` for verdadeiro ou se `require_parameters` for falso ([src/config.py:151-157](../../src/config.py#L151-L157)). Com `require_parameters: true`, o OpenRouter só roteia para endpoints que suportem **todos** os parâmetros enviados; se nenhum suportar, devolve 404 `No endpoints found that can handle the requested parameters`, sem dizer qual parâmetro faltou ([src/config.py:180-186](../../src/config.py#L180-L186), comentário que documenta o diagnóstico real). A lista exigida está codificada em `PARAMETROS_EXIGIDOS = ("tools", "seed", "temperature", "max_tokens")` ([scripts/fitness_test.py:63](../../scripts/fitness_test.py#L63)), e `listar_provedores` lê `supported_parameters` de cada endpoint para marcar quem serve ([scripts/fitness_test.py:66-93](../../scripts/fitness_test.py#L66-L93)). `seed` vai no corpo via `extra_body` ([src/config.py:247-251](../../src/config.py#L247-L251)); provedor sem `seed` derruba o pino com 404.

**Consequência verificada em 19/09/2026:** nenhum endpoint da Anthropic no OpenRouter lista `seed`. Nenhum endpoint da família `openai/gpt-5.x` lista `temperature`. Os dois grupos estão fora por construção, não por opinião (seção 3).

### R2. Tool calling nativo e estável, sem `parallel_tool_calls`

O agente é um laço de sete ferramentas ligadas por `bind_tools`: `list_files`, `read_file`, `search_code`, `write_file`, `replace_in_file`, `run_python`, `run_tests` ([src/tools/__init__.py:31-34](../../src/tools/__init__.py#L31-L34), esquemas em [src/tools/__init__.py:40-79](../../src/tools/__init__.py#L40-L79)). O prompt de sistema nomeia as sete e prescreve o método ([src/prompts.py:30-57](../../src/prompts.py#L30-L57)). Os papéis auxiliares do braço orquestrado usam saída estruturada pelo **mesmo** mecanismo, `function_calling` ([src/structured_llm.py:34](../../src/structured_llm.py#L34) e [src/structured_llm.py:55-66](../../src/structured_llm.py#L55-L66)), sem reparo de JSON: não conformar sobe como `StructuredOutputError` e consome orçamento ([src/structured_llm.py:114-117](../../src/structured_llm.py#L114-L117)). `parallel_tool_calls`, que o `with_structured_output` acrescenta sozinho, é removido do payload porque quase nenhum provedor fora da OpenAI o implementa e, com `require_parameters: true`, ele derrubava o braço orquestrado em 100% das tentativas no piloto ([src/config.py:191-198](../../src/config.py#L191-L198)). Pelo mesmo motivo, `max_completion_tokens` é revertido para `max_tokens` ([src/config.py:187-189](../../src/config.py#L187-L189)).

### R3. Contexto útil de pelo menos 64k tokens, com folga para a faixa grande

Medido nas quatro execuções instrumentadas de 11/09: o último prompt vai de 15.248 a 21.999 tokens e o prompt cobrado por execução vai de 263.524 a 456.799 tokens, em 26 a 41 chamadas ([06-contabilidade-contexto.md](06-contabilidade-contexto.md), seção 2, e `cost` de cada `result.json`). Isso é em tarefa **pequena**, de um arquivo. A saída de `read_file` é 36,0% a 41,7% do prompt cobrado (seção 3 do mesmo documento). A faixa grande é definida como 3 ou mais arquivos-fonte e 80 ou mais linhas de patch ([07-e3-1-mineracao.md](07-e3-1-mineracao.md), seção 1; a seção 5 com os candidatos concretos ainda está pendente, então o tamanho exato das tarefas grandes é **não verificado**). Projetando 2,5 vezes o volume de leitura, o último prompt chega a 45k a 55k tokens e o prompt cobrado a cerca de 880k. Daí o piso de 64k de contexto útil, com folga. O teto de saída é 8.192 tokens ([src/config.py:59](../../src/config.py#L59)), então `max_completion_tokens` do endpoint precisa ser pelo menos isso.

### R4. Custo por execução compatível com o orçamento

Fumaça 4 execuções, ablação 10, coleta 72, reexecuções cerca de 5, total cerca de 91; saldo US$ 8,64; teto US$ 50 reservado para refazer a coleta inteira, mais 72 execuções ([04-cronograma.md](04-cronograma.md), seção 4). O custo vem do campo `usage.cost` nativo do OpenRouter, não de estimativa ([src/config.py:249](../../src/config.py#L249) e [src/config.py:299](../../src/config.py#L299)).

### R5. Reasoning tokens

`extract_call_metrics` já lê `completion_tokens_details.reasoning_tokens` ([src/config.py:297](../../src/config.py#L297)), então raciocínio seria **contado**. O problema não é medir, é comparar: a decomposição do prompt do E1 foi validada com raciocínio zero e a seção 6 de [06-contabilidade-contexto.md](06-contabilidade-contexto.md) declara a limitação. Raciocínio também muda a métrica primária inferencial (tokens) e a secundária (tempo).

### R6. Estabilidade do provedor

`max_retries = 6`, e o comentário registra a causa: um 429 `engine_overloaded` do pool compartilhado matou um run inteiro com o padrão 2 do LangChain ([src/config.py:61-67](../../src/config.py#L61-L67)). O inventário confirma 3 execuções perdidas de 42 por erro de provedor ou formato, entre elas um `RateLimitError` e dois erros 429 ([01-inventario.md](01-inventario.md), R9, linha 298). Uma execução perdida quebra o par, e o mecanismo de reexecução com a mesma semente ainda é o item 6 da Fase 5.

### R7. Determinismo com `temperature = 0` e `seed`

`temperature = 0.0` e `seed` fixo ([src/config.py:57-58](../../src/config.py#L57-L58); `LLM_SEED=20260820` no `.env.example`, `20260821` nos manifestos do piloto). A documentação do OpenRouter é explícita: "Determinism is not guaranteed for some models" (consultado em 19/09/2026 em `https://openrouter.ai/docs/api-reference/parameters`). Promessa não é medida; quem mede é `relatar`, contando assinaturas distintas de argumentos em N sondagens idênticas ([scripts/fitness_test.py:154](../../scripts/fitness_test.py#L154) e [scripts/fitness_test.py:180](../../scripts/fitness_test.py#L180)). Divergência não reprova o candidato, mas obriga a declarar a variabilidade ([scripts/fitness_test.py:184-185](../../scripts/fitness_test.py#L184-L185)).

### R8. Pesos abertos contra modelo fechado

Não é preconceito, é consequência de R1 e R6. Pesos abertos dão vários provedores para o mesmo modelo, e o OpenRouter publica a **quantização** de cada endpoint, que é um parâmetro declarável no TCC. Modelo fechado tem provedor único ou quase, o que torna o pino trivial, mas a quantização vem como `unknown` e não há como declarar em que precisão o modelo rodou. Verificado ao vivo em 19/09/2026: Anthropic não expõe `seed` em nenhum endpoint; OpenAI expõe `seed` mas a família GPT-5.x não expõe `temperature`; Google expõe `seed`, `temperature`, `tools` e `max_tokens` nos endpoints Gemini.

### R9. Valor de manter o modelo do piloto

O piloto rodou `qwen/qwen3-coder` servido por `DeepInfra`, com `seed = 20260821`, em todas as execuções de 11/09 (`manifest.json` e `provenance` dos quatro `result.json`). Nas 38 execuções da branch anterior, 853 de 853 chamadas foram atendidas pelo provedor pinado ([01-inventario.md](01-inventario.md), linha 117): o pino é prova empírica, não promessa. Todo o custo medido, todo o perfil de tokens, a validação do script de contabilidade de contexto e a estimativa dos tetos foram feitos com esse par. Trocar zera essa calibração e obriga a refazer, no mínimo, a medição de custo por execução e a calibração dos tetos da E4.

## 3. Exclusões por construção, antes da matriz

Consultado em 19/09/2026 em `https://openrouter.ai/api/v1/models` (447 modelos) e nos `/endpoints` de cada família.

| Grupo | O que falta | Efeito com `require_parameters: true` |
|---|---|---|
| `anthropic/claude-*` (haiku 4.5, sonnet 4.6, opus 4.x, fable 5.x), todos os endpoints (Anthropic, Bedrock, Azure, Google) | `seed` | 404 em toda chamada. Reprova R1 e R7 |
| `openai/gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5.1`, `gpt-5.2`, `gpt-5.4-mini`, `gpt-5.x-codex` | `temperature` (e `max_tokens` nos endpoints Azure e nos `codex`) | 404 em toda chamada. Reprova R1 |
| `google/gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro` | nada; param suportado | Campo `expiration_date = 2026-10-20` na API. Expira **durante** a semana da coleta (19/10 a 25/10) e antes da defesa. Reprova R6 |
| Qualquer modelo `:free` | tier gratuito | Recusado em `_validate` ([src/config.py:143-150](../../src/config.py#L143-L150)) |
| `z-ai/glm-4.5`, `glm-5-turbo`, `glm-5.3-flashx`, `minimax/minimax-01`, `qwen/qwen-2.5-coder-32b-instruct`, todos os `:batch` de peso aberto | `seed` ou `tools` | Reprova R1 |

Os três fechados de referência de custo médio pedidos ficam, portanto, reduzidos a um só que passa em R1: a família Gemini. Claude Haiku 4.5 e GPT-5-mini estão fora do estudo por falta de parâmetro, não por preço. Isso é um resultado, não uma limitação da busca: o desenho exige `seed` e `temperature`, e os dois maiores fornecedores fechados não os oferecem juntos pelo OpenRouter hoje.

## 4. Matriz de candidatos

Dados de `/api/v1/models/{modelo}/endpoints`, consultados em **19/09/2026**. "Apto" significa que o endpoint lista `tools`, `seed`, `temperature` e `max_tokens`, isto é, exatamente o critério de [scripts/fitness_test.py:63](../../scripts/fitness_test.py#L63). Preços em US$ por milhão de tokens. "Cache" é o campo `input_cache_read` do endpoint; "n/d" significa que o endpoint não publica preço de leitura em cache, ou que o OpenRouter não reportou o uptime da janela. Uptime é `uptime_last_30m` e `uptime_last_1d` no instante da consulta, e oscila; os valores servem para ordenar, não como medida estável.

| Modelo | Provedor apto | Entrada | Saída | Cache | Quantização | Contexto | Saída máx. | Uptime 30m / 1d | Raciocínio |
|---|---|---|---|---|---|---|---|---|---|
| qwen/qwen3-coder | **DeepInfra** (piloto) | 0,300 | 1,000 | 0,100 | fp4 | 262.144 | 65.536 | 95,5% / 96,65% | não tem |
| qwen/qwen3-coder | Google (Vertex) | 0,220 | 1,800 | n/d | unknown | 262.144 | 65.536 | 100% / 99,97% | não tem |
| qwen/qwen3-coder | Novita | 0,380 | 1,550 | n/d | fp8 | 262.144 | 65.536 | 91,4% / 95,39% | não tem |
| qwen/qwen3-coder | Alibaba | 0,975 | 4,875 | n/d | unknown | 262.144 | 65.536 | n/d / 100% | não tem |
| qwen/qwen3-coder-next | **Parasail** | 0,120 | 0,800 | 0,070 | bf16 | 262.144 | 235.929 | 99,8% / 99,98% | não tem |
| qwen/qwen3-coder-next | Novita | 0,200 | 1,500 | n/d | fp8 | 262.144 | 65.536 | 99,9% / 99,42% | não tem |
| qwen/qwen3-coder-flash | Alibaba | 0,195 | 0,975 | 0,039 | unknown | 1.000.000 | 65.536 | 100% / 100% | não tem |
| qwen/qwen3-coder-30b-a3b-instruct | Novita | 0,070 | 0,270 | n/d | fp8 | 160.000 | 32.768 | 100% / 98,91% | não tem |
| deepseek/deepseek-v3.2 | GMICloud | 0,209 | 0,310 | 0,022 | fp8 | 163.840 | 147.456 | 99,9% / 99,52% | híbrido |
| deepseek/deepseek-v3.2 | DeepInfra | 0,260 | 0,380 | 0,130 | fp4 | 163.840 | 16.384 | 100% / 99,97% | híbrido |
| deepseek/deepseek-v4-flash | OpenInference | 0,050 | 0,140 | 0,014 | fp8 | 1.048.576 | 393.216 | 100% / 99,93% | sim |
| deepseek/deepseek-v4-flash | DeepInfra | 0,090 | 0,180 | 0,018 | fp8 | 1.048.576 | 65.536 | 99,4% / 99,71% | sim |
| moonshotai/kimi-k2-0905 | Novita (único apto) | 0,600 | 2,500 | n/d | fp8 | 262.144 | 98.304 | 100% / 100% | não tem |
| moonshotai/kimi-k2.5 | AtlasCloud | 0,490 | 2,500 | 0,200 | int4 | 262.144 | 235.929 | 100% / 97,53% | sim |
| z-ai/glm-4.7 | Google (Vertex) | 0,600 | 2,200 | n/d | unknown | 200.000 | 128.000 | 100% / 99,97% | sim |
| z-ai/glm-4.7 | DeepInfra | 0,400 | 1,750 | 0,080 | fp4 | 202.752 | 131.072 | **62,3%** / 97,84% | sim |
| z-ai/glm-4.7-flash | Cloudflare | 0,061 | 0,400 | n/d | unknown | 131.072 | 117.964 | 99,1% / 99,25% | sim |
| minimax/minimax-m2.5 | AtlasCloud | 0,295 | 1,200 | 0,060 | fp8 | 196.608 | 176.947 | 100% / 99,8% | sim |
| minimax/minimax-m2.5 | Novita | 0,300 | 1,200 | 0,030 | fp8 | 204.800 | 131.100 | n/d / 99,85% | sim |
| openai/gpt-oss-120b | DeepInfra (bf16) | 0,037 | 0,170 | n/d | bf16 | 131.072 | 117.964 | 100% / 99,96% | sim, obrigatório |
| openai/gpt-oss-120b | Groq | 0,150 | 0,600 | 0,075 | unknown | 131.072 | 65.536 | 99,9% / 99,99% | sim, obrigatório |
| mistralai/codestral-2508 | Mistral (único) | 0,300 | 0,900 | 0,030 | unknown | 256.000 | 204.800 | 99,9% / 99,86% | não tem |
| mistralai/devstral-2512 | Mistral (único) | 0,400 | 2,000 | 0,040 | unknown | 262.144 | 209.715 | n/d / 100% | não tem |
| google/gemini-3.1-flash-lite | Google AI Studio | 0,125 | 0,750 | 0,012 | unknown | 1.048.576 | 65.536 | 100% / 99,98% | sim |

Observações que a tabela não cabe:

- **`moonshotai/kimi-k2-0905` tem um único provedor apto.** Dos endpoints listados, só Novita expõe `seed`. Provedor único num modelo de pesos abertos é o pior dos dois mundos: sem alternativa se cair, e sem o argumento de reprodutibilidade do fornecedor oficial.
- **`z-ai/glm-4.7` na DeepInfra estava em 62,3% de uptime nos 30 minutos anteriores à consulta** (19/09/2026), com 97,84% em 24h. O endpoint Z.AI oficial não expõe `seed`.
- **`openai/gpt-oss-120b` tem 24 endpoints**, 14 deles aptos, com quantizações bf16, fp8, fp4 e fp16 a preços parecidos. Isso é ótimo para preço e péssimo para a declaração de precisão: o mesmo modelo, no mesmo preço, em precisões diferentes.
- **`mistralai/codestral-2508` e `devstral-2512` têm provedor único** (o próprio Mistral), com `quantization: unknown`. São de pesos abertos mas servidos como se fossem fechados.
- **`qwen/qwen3-coder` na DeepInfra aparece hoje como `fp4`.** Qual era a quantização do endpoint durante o piloto de 11/09 é **não verificado**: o campo não é registrado no manifesto nem nos eventos, e o OpenRouter não publica histórico. Esta é uma lacuna de proveniência do piloto, e a correção é registrar a quantização no manifesto antes da coleta.

## 5. Projeção de custo

**Base de projeção, medida (não estimada).** As quatro execuções de 11/09 (`cost` de cada `result.json`):

| Execução | Chamadas | Prompt cobrado | Saída | Custo real |
|---|---|---|---|---|
| orquestração · sqlite-utils-0001 | 41 | 456.799 | 11.022 | US$ 0,05987 |
| orquestração · tomlkit-0001 | 36 | 332.249 | 6.652 | US$ 0,04258 |
| agente único · sqlite-utils-0001 | 26 | 263.524 | 4.102 | US$ 0,03255 |
| agente único · tomlkit-0001 | 40 | 356.834 | 7.089 | US$ 0,04482 |
| **média** | 35,75 | **352.352** | **7.216** | **US$ 0,04496** |

**Descoberta que muda toda a projeção: 96% do prompt do piloto foi cobrado como leitura em cache.** Ao preço de tabela da DeepInfra hoje (0,30 de entrada, 1,00 de saída), a execução média custaria US$ 0,1129. Ela custou US$ 0,0450. A diferença só fecha com o campo `input_cache_read` de US$ 0,10 por milhão do endpoint DeepInfra: resolvendo para a fração de prompt cobrada em cache, dá 0,965 / 0,959 / 0,960 / 0,971 nas quatro execuções (cálculo sobre `tokens_prompt`, `tokens_completion` e `cost_usd` de cada `result.json`, com os preços consultados em 19/09/2026). A primeira chamada de cada execução confirma o preço cheio: 2.022 tokens de prompt e 61 de saída custaram exatamente US$ 0,0006676, que é 2.022 × 0,30/10⁶ + 61 × 1,00/10⁶ (`events.jsonl` da execução `single-agent-tomlkit-0001-r01`).

Isso era esperado pela estrutura do agente: o prompt cresce por acréscimo, então o prefixo é idêntico entre chamadas consecutivas e o cache do provedor o pega quase inteiro. **Mas é uma propriedade do endpoint, não do modelo.** Um endpoint sem preço de cache cobra os mesmos tokens 2,5 vezes mais caro. Por isso as duas colunas abaixo.

**Projeção, preços de 19/09/2026.** Perfil médio, 352.352 tokens de prompt e 7.216 de saída por execução. "Com cache" aplica 96% do prompt ao preço `input_cache_read` do endpoint, que é o comportamento medido na DeepInfra e **hipótese não verificada** nos demais. "Sem cache" aplica o preço cheio a todo o prompt, e é o limite superior seguro.

| Modelo · provedor | Execução, com cache | Execução, sem cache | 91 execuções, com cache | 91 sem cache | 163 execuções (pior caso), com cache | 163 sem cache |
|---|---|---|---|---|---|---|
| qwen/qwen3-coder · DeepInfra | **US$ 0,0453** | 0,1129 | **4,12** | 10,28 | 7,38 | 18,41 |
| qwen/qwen3-coder · Google | 0,0905 | 0,0905 | 8,24 | 8,24 | 14,75 | 14,75 |
| qwen/qwen3-coder · Novita | 0,1451 | 0,1451 | 13,20 | 13,20 | 23,65 | 23,65 |
| qwen/qwen3-coder-next · Parasail | **0,0311** | 0,0481 | **2,83** | 4,37 | 5,08 | 7,83 |
| qwen/qwen3-coder-next · Novita | 0,0813 | 0,0813 | 7,40 | 7,40 | 13,25 | 13,25 |
| qwen/qwen3-coder-flash · Alibaba | 0,0230 | 0,0757 | 2,09 | 6,89 | 3,75 | 12,35 |
| qwen/qwen3-coder-30b-a3b · Novita | 0,0266 | 0,0266 | 2,42 | 2,42 | 4,34 | 4,34 |
| deepseek/deepseek-v3.2 · GMICloud | 0,0125 | 0,0758 | 1,14 | 6,90 | 2,03 | 12,36 |
| deepseek/deepseek-v3.2 · DeepInfra | 0,0504 | 0,0944 | 4,58 | 8,59 | 8,21 | 15,38 |
| deepseek/deepseek-v4-flash · OpenInference | 0,0065 | 0,0186 | 0,59 | 1,70 | 1,05 | 3,04 |
| moonshotai/kimi-k2-0905 · Novita | 0,2295 | 0,2295 | **20,88** | 20,88 | 37,40 | 37,40 |
| moonshotai/kimi-k2.5 · AtlasCloud | 0,0926 | 0,1907 | 8,43 | 17,35 | 15,09 | 31,08 |
| z-ai/glm-4.7 · Google | 0,2273 | 0,2273 | 20,68 | 20,68 | 37,05 | 37,05 |
| z-ai/glm-4.7 · DeepInfra | 0,0453 | 0,1536 | 4,12 | 13,97 | 7,39 | 25,03 |
| z-ai/glm-4.7-flash · Cloudflare | 0,0242 | 0,0242 | 2,20 | 2,20 | 3,95 | 3,95 |
| minimax/minimax-m2.5 · AtlasCloud | 0,0331 | 0,1126 | 3,01 | 10,25 | 5,40 | 18,35 |
| openai/gpt-oss-120b · DeepInfra bf16 | 0,0143 | 0,0143 | 1,30 | 1,30 | 2,32 | 2,32 |
| openai/gpt-oss-120b · Groq | 0,0318 | 0,0572 | 2,89 | 5,20 | 5,19 | 9,32 |
| mistralai/codestral-2508 · Mistral | 0,0209 | 0,1122 | 1,90 | 10,21 | 3,40 | 18,29 |
| mistralai/devstral-2512 · Mistral | 0,0336 | 0,1554 | 3,06 | 14,14 | 5,48 | 25,33 |
| google/gemini-3.1-flash-lite · AI Studio | 0,0114 | 0,0495 | 1,04 | 4,50 | 1,86 | 8,06 |

A projeção de US$ 0,0453 por execução para o par do piloto reproduz o custo medido de US$ 0,0450 com erro de 0,7%, o que valida o modelo de custo. Nos candidatos com raciocínio, todas as colunas **subestimam**: os tokens de raciocínio são cobrados como saída e não estão no perfil medido, que tem raciocínio zero.

**Leitura do orçamento.** Contra o saldo de US$ 8,64: passam com folga, na coluna "sem cache", que é a conservadora, `qwen3-coder-next` na Parasail (4,37), `qwen3-coder-30b-a3b` na Novita (2,42), `deepseek-v4-flash` (1,70), `glm-4.7-flash` (2,20), `gpt-oss-120b` na DeepInfra (1,30), `gemini-3.1-flash-lite` (4,50), `gpt-oss-120b` na Groq (5,20). O par do piloto passa na coluna com cache (4,12) e **estoura o saldo** na coluna sem cache (10,28), continuando bem dentro do teto de US$ 50. Reprovam contra o saldo em qualquer coluna: `kimi-k2-0905` (20,88) e `glm-4.7` na Google (20,68).

**Tarefa grande.** Projetando 2,5 vezes o perfil médio, 880.000 tokens de prompt e 18.000 de saída, dá 898.000 tokens totais por execução. O teto de tokens registrado nos manifestos do piloto é 1.200.000, então uma tarefa grande cabe, mas com folga de 25%. Custo por execução grande: qwen3-coder na DeepInfra US$ 0,1130 com cache e US$ 0,2820 sem; qwen3-coder-next na Parasail US$ 0,0778 e US$ 0,1200. Esse é o número que a E4 vai calibrar; nenhuma das duas escolhas quebra o orçamento mesmo se as 12 tarefas fossem todas grandes.

## 6. Riscos por candidato

| Candidato | Raciocínio | Quantização | Deprecação até 23/11/2026 | Instabilidade | Determinismo |
|---|---|---|---|---|---|
| qwen/qwen3-coder · DeepInfra | Nenhum. `reasoning` não está em `supported_parameters`; `tokens_reasoning = 0` nas 4 execuções. Risco zero em R5 | fp4 hoje. Quantização mais agressiva da lista. A do piloto é não verificada | Sem `expiration_date` na API. Modelo criado em 22/07/2025, 14 meses de vida. Endpoint DeepInfra existir em novembro: **não verificado** | Pior uptime entre as opções sérias: 95,5% em 30m, 96,65% em 24h. Histórico de 429 e `engine_overloaded` no piloto | Não medido com N alto. Sondagem do piloto passou, mas o laudo formal de `fitness_test.py` não está registrado em documento |
| qwen/qwen3-coder-next · Parasail | Nenhum. Sem `reasoning` | **bf16**, a melhor da lista. Sem perda por quantização a declarar | Criado em 03/02/2026, 7 meses. Sem `expiration_date` | 99,8% em 30m, 99,98% em 24h | Não medido. Modelo MoE de 3B ativos: possível mais variabilidade de trajetória |
| qwen/qwen3-coder-flash · Alibaba | Nenhum | unknown | Sem `expiration_date` | 100% / 100% | Não medido. Provedor único |
| deepseek/deepseek-v3.2 · GMICloud | **Híbrido.** `reasoning` suportado; comportamento padrão sem enviar o parâmetro é não verificado. Quebra a premissa do E1 até prova em contrário | fp8 | Sem `expiration_date` | 99,9% / 99,52% | Não medido |
| deepseek/deepseek-v4-flash | **Sim.** O mais barato da lista, mas raciocínio muda a métrica primária | fp8 na maioria, fp4 na AtlasCloud | Criado em 2026. Sem `expiration_date` | 99,9%+ na maioria dos endpoints | Não medido |
| moonshotai/kimi-k2-0905 · Novita | Nenhum | fp8 | Criado em 04/09/2025. Sem `expiration_date` | 100% / 100%, mas **provedor único apto**: se Novita tirar o `seed`, o modelo sai do estudo no meio | Não medido |
| moonshotai/kimi-k2.5 · AtlasCloud | **Sim** | **int4**, a mais agressiva da lista | Sem `expiration_date` | 100% / 97,53% | Não medido |
| z-ai/glm-4.7 · DeepInfra | **Sim** | fp4 | Sem `expiration_date` | **62,3% em 30m.** Inaceitável para coleta sequencial de 72 execuções | Não medido |
| z-ai/glm-4.7 · Google | **Sim** | unknown | Sem `expiration_date` | 100% / 99,97% | Custo estoura o saldo (US$ 20,68) |
| minimax/minimax-m2.5 | **Sim** | fp8 | Criado em 12/02/2026 | 100% / 99,8% | Não medido |
| openai/gpt-oss-120b | **Sim, e obrigatório.** É um modelo de raciocínio nativo com `reasoning_effort`; `effort: "none"` funcionar é não verificado | bf16, fp8, fp4 e fp16 pelo mesmo preço em provedores diferentes. Declarar a precisão exige pinar o provedor certo, e o preço não distingue | Criado em 05/08/2025 | 100% / 99,96% na DeepInfra bf16 | Não medido |
| mistralai/codestral-2508 e devstral-2512 | Nenhum | unknown, provedor único | Sem `expiration_date` | 99,9% / 99,86% | Não medido. `default_parameters.temperature = 0.3`, ou seja, o modelo não é desenhado para temperatura 0 |
| google/gemini-3.1-flash-lite | **Sim** | unknown | Sem `expiration_date`, mas a geração anterior (2.5 Flash Lite) expira em **20/10/2026**, durante a semana da coleta. A cadência de deprecação do Google é a mais rápida da lista | 100% / 99,98% no AI Studio; um dos endpoints Google estava em 11,7% em 30m na consulta | Não medido |

**Sobre desligar o raciocínio.** O OpenRouter aceita `reasoning: {"enabled": false}` ou `reasoning: {"effort": "none"}`, e `reasoning: {"exclude": true}` é suportado por todos os modelos mas só esconde o raciocínio da resposta, sem deixar de gerá-lo nem de cobrá-lo (consultado em 19/09/2026 em `https://openrouter.ai/docs/use-cases/reasoning-tokens`). Modelos com raciocínio obrigatório rejeitam `effort: "none"`. Nenhum dos candidatos traz o marcador `mandatory` na API hoje, mas isso não é prova de que desligar funciona em cada endpoint. Na prática, usar um modelo com raciocínio exigiria: (a) acrescentar `"reasoning": {"enabled": False}` ao `extra_body` de [src/config.py:247-251](../../src/config.py#L247-L251), o que é mudança de código e de manifesto; (b) confirmar com `require_parameters: true` que o endpoint aceita o parâmetro; (c) revalidar a contabilidade de contexto do E1, que hoje assume raciocínio zero. São três trabalhos a mais, pagos em tempo de cronograma, para chegar ao comportamento que os modelos sem raciocínio já dão de graça.

## 7. Recomendação

**Principal: `qwen/qwen3-coder`, provedor pinado `DeepInfra`. Reserva: `qwen/qwen3-coder-next`, provedor pinado `Parasail`.**

A recomendação é manter. O argumento decisivo não é preço nem benchmark, é que este projeto não tem mais um ciclo de calibração no cronograma. Faltam nove semanas e meia para a defesa, o gargalo declarado é escrever dez enunciados de tarefa, e a coleta cabe numa única semana, a de 19 a 25 de outubro. O par `qwen3-coder` mais DeepInfra é o único da lista com perfil de consumo medido em execução real deste harness: 24 a 41 chamadas por execução, 263k a 457k tokens de prompt cobrado, último prompt de 15k a 22k, raciocínio zero, e um custo real de US$ 0,0450 por execução que a projeção reproduz com 0,7% de erro. Tudo o mais na lista é projeção sobre um perfil que foi medido com outro modelo. Trocar por qualquer candidato obriga a refazer a medição de custo, refazer a calibração dos tetos da E4 e, nos candidatos com raciocínio, refazer também a validação do script de contabilidade de contexto. O ganho seria de poucos dólares num orçamento em que dinheiro não é a restrição.

Contra manter, pesam três coisas, e nenhuma é fatal. A primeira é o uptime: 95,5% em 30 minutos e 96,65% em 24 horas, o pior entre as opções sérias, coerente com as 3 execuções perdidas de 42 no piloto. A mitigação já está no código, `max_retries = 6`, e a segunda mitigação, reexecutar o run perdido com a mesma semente (portão G5), foi entregue em 19/09/2026 como E5 item 2 (`src/arms/pilot.py`, `run_pilot.py --reexecutar`; ver [07-e5-2-reexecucao.md](07-e5-2-reexecucao.md)). A segunda é a quantização fp4, hoje a mais agressiva entre os endpoints do modelo; a resposta honesta é declarar fp4 no texto do TCC, registrar o campo no manifesto antes da coleta, e reconhecer que a quantização do piloto é não verificada. A terceira é a idade do modelo, 14 meses, com risco real de o endpoint sumir antes de novembro; contra isso não existe garantia, só a reserva.

A reserva é `qwen3-coder-next` na Parasail porque ela é a troca que custa menos. Mesma família e mesmo tokenizador, então o perfil de tokens tende a transferir; sem raciocínio, então a contabilidade do E1 continua válida sem revalidação; 262k de contexto e 235k de saída máxima, então nenhum limite novo; bf16, o que na verdade **melhora** a declaração de quantização em relação ao fp4 atual; 99,98% de uptime em 24 horas; e US$ 4,37 pelas 91 execuções mesmo na coluna sem cache, o que cabe no saldo sem depender da hipótese de cache. O que se perde ao acionar a reserva é concreto e deve ser dito no texto: o custo por execução e os tetos da E4 precisam ser remedidos na fumaça, e os quatro `result.json` de 11/09 deixam de servir como piloto do modelo final, virando piloto de instrumentação apenas.

Se os dois reprovarem no teste de aptidão, a terceira opção é `qwen/qwen3-coder-flash` na Alibaba: mesma família, sem raciocínio, 100% de uptime nas duas janelas, US$ 6,89 pelas 91 execuções sem cache. O defeito é provedor único e quantização `unknown`.

Modelos com raciocínio não são reserva. Não porque sejam piores, mas porque cada um deles transforma a escolha de modelo numa etapa de pesquisa adicional (desligar, confirmar, revalidar a contabilidade) que o cronograma não comporta. Se o autor decidir que quer um modelo com raciocínio, isso vira um experimento próprio, com custo de tempo, e a decisão sobe para ele.

## 8. Protocolo do teste pago de aptidão

Este é o único gasto autorizado antes do teste de fumaça. Rode na raiz do repositório, com `OPENROUTER_API_KEY` no `.env`.

**Passo 1, custo zero: confirmar os provedores aptos hoje.** Nenhuma chamada de inferência ([scripts/fitness_test.py:71](../../scripts/fitness_test.py#L71)).

```
.venv/bin/python scripts/fitness_test.py --list-providers qwen/qwen3-coder
.venv/bin/python scripts/fitness_test.py --list-providers qwen/qwen3-coder-next
```

Espere `APTO DeepInfra` na primeira e `APTO Parasail` na segunda. Se `DeepInfra` sumir da primeira lista, pare e releia a seção 7: a reserva vira principal.

**Passo 2, pago: sondar o principal.**

```
.venv/bin/python scripts/fitness_test.py --model qwen/qwen3-coder --provider DeepInfra -n 10
```

**Passo 3, pago: sondar a reserva.**

```
.venv/bin/python scripts/fitness_test.py --model qwen/qwen3-coder-next --provider Parasail -n 10
```

`-n 10` em vez do padrão 5 porque o critério de determinismo conta assinaturas distintas ([scripts/fitness_test.py:154](../../scripts/fitness_test.py#L154)) e 5 amostras não distinguem ruído raro de divergência sistemática. O teto de saída fica no padrão de 512 tokens ([scripts/fitness_test.py:197-199](../../scripts/fitness_test.py#L197-L199)), suficiente para uma tool call.

**Custo estimado do teste.** O prompt de sondagem mais o esquema de uma ferramenta dão da ordem de 300 tokens de entrada, e a resposta é uma tool call de algumas dezenas de tokens ([scripts/fitness_test.py:38-44](../../scripts/fitness_test.py#L38-L44) e [scripts/fitness_test.py:96-111](../../scripts/fitness_test.py#L96-L111)). Aos preços de 19/09/2026, 10 sondagens custam cerca de US$ 0,0014 no principal (300 × 0,30/10⁶ + 50 × 1,00/10⁶, dez vezes) e cerca de US$ 0,0008 na reserva. **Os dois testes somados ficam abaixo de US$ 0,01**, menos de 0,2% do saldo. O laudo imprime o custo real somado ([scripts/fitness_test.py:167](../../scripts/fitness_test.py#L167)); anote-o.

**Critérios numéricos de aprovação**, todos lidos direto do laudo ([scripts/fitness_test.py:173-186](../../scripts/fitness_test.py#L173-L186)):

| Critério | Exigência | Como o laudo mostra |
|---|---|---|
| Conformidade de tool calling | 10/10 chamaram `search_code` **e** 10/10 com argumentos exatos | `1. tool calling 10/10` e `argumentos exatos 10/10` |
| Pino de provedor | 100%: o dicionário de provedores servidos tem uma única chave, igual ao pinado | `2. provedor servido {'DeepInfra': 10}` |
| Veredito | `APTO para os dois braços`, exit code 0 | linha `VEREDITO` |
| Determinismo | 1 assinatura em 10 é o esperado. Até 2 assinaturas é tolerável, e obriga a declarar a variabilidade no TCC. 3 ou mais reprova para efeito prático | `3. determinismo N assinatura(s) distinta(s) em 10` |

Conformidade e pino são eliminatórios pelo código: `apto = pino_ok and conformidade_ok` ([scripts/fitness_test.py:182](../../scripts/fitness_test.py#L182)). Determinismo não reprova sozinho, mas 3 ou mais assinaturas numa tarefa de sondagem trivial prevê divergência grande na tarefa real, o que obrigaria a aumentar o número de repetições por tarefa, o que o orçamento de tempo da semana 6 não comporta.

**O que fazer se reprovar:**

- **Reprova por pino** (aparece outro provedor, ou `(desconhecido)`): não troque de modelo ainda. `(desconhecido)` significa que o campo `provider` não voltou na resposta, o que é falha do gancho de [src/config.py:201-216](../../src/config.py#L201-L216) contra a versão instalada do `langchain-openai`, não do provedor. Rode `.venv/bin/python -m pytest tests/test_config.py -q` primeiro. Provedor **diferente** do pinado com `allow_fallbacks: false` seria falha do OpenRouter e precisa ser reportada, não contornada.
- **Reprova por conformidade** (não chamou a ferramenta, ou argumentos errados): o candidato está fora. Não ajuste o prompt de sondagem para ele passar; a sondagem é deliberadamente simples e um modelo que erra nela erra as sete ferramentas reais.
- **Erro 404 em todas as sondagens**: o endpoint perdeu um parâmetro exigido. Volte ao passo 1 e releia a lista; o 404 não diz qual parâmetro faltou ([src/config.py:180-186](../../src/config.py#L180-L186)).
- **Erro 429 ou `engine_overloaded` intermitente**: não é reprovação de conformidade, é o risco R6 se manifestando antes da coleta. Repita o teste em outro horário. Se repetir, promova a reserva.
- **Principal reprova e reserva passa**: promova a reserva, e registre no texto que a calibração de custo e os tetos precisam ser remedidos na fumaça.
- **Os dois reprovam**: rode o passo 1 e o passo 3 com `qwen/qwen3-coder-flash` e `Alibaba`. Se também reprovar, a decisão sobe para o autor, porque a próxima camada de candidatos tem raciocínio e muda o desenho.

Depois de aprovado, grave `OPENROUTER_MODEL_NAME` e `OPENROUTER_PROVIDER` no `.env` e **não mude mais**. Acrescente a quantização do endpoint ao que o manifesto registra, antes do teste de fumaça: hoje ela não está em `LLMConfig.as_manifest()` ([src/config.py:87-89](../../src/config.py#L87-L89)) e é um dado de proveniência que o piloto perdeu.

## 9. Decisões que só o autor pode tomar

1. **Aceitar fp4 como quantização declarada**, ou pagar o custo de trocar para o endpoint bf16 da reserva. É uma escolha entre preservar a calibração e poder escrever "bf16, sem perda por quantização" no texto.
2. **Aceitar o risco de o endpoint DeepInfra sumir antes de 23/11/2026.** Ninguém pode verificar isso. A pergunta prática é se vale rodar o teste de aptidão da reserva agora, por menos de um centavo, para ter o caminho pronto. A recomendação deste documento é que vale.
3. **Confirmar se o custo em dólares entra no texto ou só o custo em tokens.** A métrica primária inferencial é tokens, e dólares aparecem junto ([03-metricas.md](03-metricas.md), linha 17). Se dólares forem reportados, o efeito do cache de prompt do provedor precisa ser explicado no texto, porque 96% do custo do piloto depende dele e ele não é propriedade do modelo.
4. **Decidir se um modelo com raciocínio vira objeto de estudo.** Hoje a resposta deste documento é não, por cronograma. Se virar, é uma etapa nova com custo de tempo, não uma troca de variável de ambiente.
5. **Autorizar o gasto do passo 2 e do passo 3 da seção 8**, abaixo de US$ 0,01 somados.

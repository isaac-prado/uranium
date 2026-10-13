# Coleta definitiva, etapa 1: a faixa grande (12/10/2026)

Dados: `dados/coleta/<tarefa>/<braço>/rep0k/attempt01/` (`result.json`, `summary.json`, `patch.diff`, `events.jsonl`, `manifest.json`), `dados/coleta/collection-etapa1-grandes.json` e `collection-grandes.log`. Análise de registro: `scripts/analyze_results.py --markdown dados/coleta`. Configuração congelada (decisão 12): 120 turnos, 8 M tokens, 3.600 s; orquestrado com memória de trabalho e ciclos de 40 turnos (decisões 8 e 25); `qwen/qwen3-coder` no DeepInfra com chave própria, manifesto v7. 18 runs, **zero perdas**, 69 minutos (21:09 a 22:18), US$ 4,31 no total (soma de `cost.cost_usd`), `byok_calls == llm_calls` em todos.

## 1. Resultado por run

Ocultos = testes ocultos passados / total; regressão = falhas na suíte visível com o patch de teste aplicado (`oracle.regression.failed`); ΔMI e ΔCC = variação de manutenibilidade e de complexidade média do código alterado (`quality`); ciclos = turnos do developer em cada ciclo; checagens = suíte (ok/falhas) em cada passagem pelo validador; revisão = veredito do revisor semântico quando a suíte estava verde.

### tomlkit-0002 — "Support adding with dotted key" (oculto: `test_add_dotted_key`)

| rep | braço | resolvida | ocultos | regressão | turnos | tokens | US$ | parede | arquivos / linhas do patch | ΔMI | ΔCC | parada | ciclos · checagens · revisão |
|---|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---|---|
| 1 | single-agent | não | 0/1 | 37 | 120 | 3.265 k | 0,350 | 295 s | 3 / 186 | −0,19 | +0,03 | corte por turnos | — |
| 1 | orchestration | não | 0/1 | 1 | 120 | 1.918 k | 0,222 | 295 s | 2 / 50 | −0,59 | +0,04 | corte por turnos | 40·25·40·15 · 743/0 ×4 · reprovada ×4 |
| 2 | single-agent | **sim** | 1/1 | 0 | 89 | 2.349 k | 0,264 | 271 s | 3 / 230 | −10,08 | +2,72 | suíte verde | — |
| 2 | orchestration | **sim** | 1/1 | 0 | 120 | 1.535 k | 0,178 | 200 s | 2 / 49 | −0,68 | +0,04 | corte por turnos, correção no lugar | 37·40·40·3 · 743/0 ×4 · reprovada ×4 |
| 3 | single-agent | não | 0/1 | 0 | 120 | 4.450 k | 0,481 | 306 s | 2 / 1.599 | +49,50 | −0,95 | corte por turnos | — |
| 3 | orchestration | não | 0/1 | 428 | 120 | 2.373 k | 0,272 | 301 s | 3 / 750 | +5,87 | −0,02 | corte por turnos | 40·40·40 · 262/481, 313/430, 316/427 · — |

### tomlkit-0003 — "Ensure dict compliance for containers" (oculto: `test_repr`)

| rep | braço | resolvida | ocultos | regressão | turnos | tokens | US$ | parede | arquivos / linhas | ΔMI | ΔCC | parada | ciclos · checagens · revisão |
|---|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---|---|
| 1 | single-agent | **sim** | 1/1 | 0 | 42 | 600 k | 0,068 | 113 s | 2 / 29 | 0,00 | 0,00 | suíte verde | — |
| 1 | orchestration | **sim** | 1/1 | 0 | 21 | 180 k | 0,025 | 72 s | 1 / 13 | 0,00 | 0,00 | concluiu | 21 · 547/0 · aprovada |
| 2 | single-agent | **sim** | 1/1 | 0 | 80 | 1.928 k | 0,218 | 230 s | 1 / 22 | 0,00 | 0,00 | suíte verde | — |
| 2 | orchestration | **sim** | 1/1 | 0 | 31 | 290 k | 0,037 | 77 s | 2 / 26 | 0,00 | 0,00 | concluiu | 31 · 547/0 · aprovada |
| 3 | single-agent | **sim** | 1/1 | 0 | 20 | 141 k | 0,018 | 34 s | 1 / 13 | 0,00 | 0,00 | suíte verde | — |
| 3 | orchestration | **sim** | 1/1 | 0 | 61 | 544 k | 0,068 | 129 s | 2 / 26 | 0,00 | 0,00 | concluiu | 27·34 · 547/0 ×2 · reprovada ×2 (teto semântico) |

### tomlkit-0004 — "Add support for dotted keys" (7 ocultos, todos sobre `tests/examples/0.5.0.toml`)

| rep | braço | resolvida | ocultos | regressão | turnos | tokens | US$ | parede | arquivos / linhas | ΔMI | ΔCC | parada | ciclos · checagens · revisão |
|---|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---|---|
| 1 | single-agent | não | 0/7 | 9 | 120 | 5.211 k | 0,559 | 381 s | 2 / 97 | −1,41 | +0,16 | corte por turnos | — |
| 1 | orchestration | não | 0/7 | 94 | 120 | 1.774 k | 0,207 | 207 s | 1 / 1.158 | −0,81 | −0,82 | corte por turnos | 40·40·40 · 53/110, 71/92, 71/92 · — |
| 2 | single-agent | não | 0/7 | 9 | 120 | 3.914 k | 0,421 | 277 s | 2 / 218 | −5,72 | +1,10 | corte por turnos | — |
| 2 | orchestration | não | 0/7 | 121 | 120 | 2.506 k | 0,288 | 250 s | 4 / 2.130 | −6,25 | −0,81 | corte por turnos | 40·40·40 · 0/0, 18/145, 44/119 · — (4 avisos C6: exceção silenciada) |
| 3 | single-agent | não | **5/7** | 2 | 102 | 3.814 k | 0,413 | 235 s | 1 / 82 | −1,63 | +0,36 | suíte verde (parou sozinho) | — |
| 3 | orchestration | não | 0/7 | 9 | 120 | 1.924 k | 0,227 | 339 s | 1 / 243 | −5,64 | +0,63 | corte por turnos | 40·40·40 · 110/53, 161/2, 161/2 · — |

## 2. O que a faixa grande mostra

**Resolução.** Por tarefa, mediana das repetições: single-agent 1/3, orchestration 1/3 (`analyze_results`). Por run: single-agent 5/9, orchestration 5/9. A `tomlkit-0003` foi resolvida nas seis células; a `tomlkit-0002` nas duas células da repetição 2 e em nenhuma outra; a `tomlkit-0004` em nenhuma das seis, com o melhor resultado parcial no single-agent da repetição 3 (5/7). Nenhuma diferença de resolução entre os braços na faixa grande.

**Custo onde os dois resolveram.** Na `tomlkit-0003` (três pares resolvidos) o orquestrado gastou menos tokens em dois pares (180 k contra 600 k; 290 k contra 1.928 k) e mais no terceiro (544 k contra 141 k); mediana 291 k contra 600 k. No par resolvido da `tomlkit-0002`, 1.535 k contra 2.349 k. Em todas as nove duplas, resolvidas ou não, o orquestrado gastou menos tokens que o single-agent, exceto na `tomlkit-0003` rep. 3. O efeito vem dos ciclos de 40 turnos: o maior prompt do orquestrado fica em torno de 25 k tokens, enquanto o do single-agent cresce até 90 k.

**Regressão e tamanho do patch.** As falhas grandes aparecem nos dois braços quando a tarefa escapa: single-agent com 37 regressões (0002 rep. 1) e um patch de 1.599 linhas (0002 rep. 3); orquestrado com 428 (0002 rep. 3), 94 e 121 regressões e patches de 1.158 e 2.130 linhas (0004). Os quatro avisos do detector (C6, exceção silenciada) estão num único run orquestrado (0004 rep. 2). Nos runs resolvidos os patches são pequenos (13 a 49 linhas no orquestrado, 13 a 230 no single-agent) e a complexidade não muda.

**O revisor semântico, lido pela telemetria nova.** Na `tomlkit-0002` o revisor reprovou todas as oito passagens com a suíte verde das repetições 1 e 2, sempre apontando os mesmos critérios (`doc.add` / `table.add` com chave pontilhada, acesso como tabela aninhada). Na repetição 2 **o teste oculto já passava** e o run foi cortado por turnos com a correção no lugar: as quatro reprovações foram falsos negativos de um revisor que julga pelo diff e não executa nada, e custaram ao orquestrado 83 turnos a mais que os 37 em que a correção ficou pronta. Na `tomlkit-0003` rep. 3 o revisor reprovou duas vezes um patch que o oráculo aprovou, e o run fechou pelo teto semântico. Na `tomlkit-0004` o revisor nunca rodou nos runs orquestrados: nenhuma checagem chegou verde, porque o developer quebrou a suíte visível em todos os ciclos. Para a Discussão: o revisor é consistente e específico, mas a precisão dele contra o oráculo é baixa nesta faixa, e um falso negativo tem custo em turnos.

**Checagens por ciclo.** Com 40 turnos por ciclo, todos os runs orquestrados cortados por turnos passaram três ou quatro vezes pelo validador, com memória de trabalho e veredito ou relatório de falha no prompt da reentrada. Nos três runs da `tomlkit-0004` os pontos de checagem viram a suíte piorar ou estagnar (53/110 → 71/92 → 71/92; 0/0 → 18/145 → 44/119; 110/53 → 161/2 → 161/2): o developer recebeu a lista de testes falhando e não convergiu em 120 turnos.

**Censura.** Nenhum corte por tokens (máx. 5,2 M de 8 M) nem por parede (máx. 381 s de 3.600 s). O único corte foi por turnos, nos dois braços. Os tetos não censuraram nada que o modelo estivesse prestes a resolver, exceto possivelmente a `tomlkit-0004` rep. 3 do single-agent, que parou sozinho em 5/7 com a suíte visível verde: o critério de parada "suíte verde e houve mudança" foi satisfeito por uma implementação parcial, como nas fumaças.

## 3. Comparação qualitativa do código gerado (para o texto)

- **`tomlkit-0003` (as seis resolvem):** os dois braços convergem para o mesmo tipo de mudança, 1 a 2 arquivos, 13 a 29 linhas, sem efeito em MI ou CC. O orquestrado chega mais rápido em duas repetições (21 e 31 turnos contra 42 e 80) e mais devagar na terceira (61 contra 20), onde gastou um ciclo a mais por causa do revisor.
- **`tomlkit-0002` (resolvida uma vez por braço):** o single-agent resolve com 230 linhas em 3 arquivos e piora MI em 10 pontos e CC em 2,7; o orquestrado resolve com 49 linhas em 2 arquivos e quase não mexe nas métricas. Nas repetições em que escapa, o single-agent reescreve (1.599 linhas) e o orquestrado também (750 linhas, 428 regressões).
- **`tomlkit-0004` (ninguém resolve):** o single-agent produz patches menores (82 a 218 linhas) com 2 a 9 regressões e chega a 5/7; o orquestrado produz patches de 243 a 2.130 linhas com 9 a 121 regressões e 0/7. Nesta tarefa o single-agent gera código melhor, e o orquestrado, com três checagens de suíte vermelha por run, não converge.

Os patches estão em `dados/coleta/<tarefa>/<braço>/rep0k/attempt01/patch.diff` para leitura lado a lado.

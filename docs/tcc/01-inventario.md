# 01 — Inventário e auditoria do repositório Uranium (Fase 1)

Documento produzido em 17/09/2026 sobre o commit `99b0ed8` da branch `develop`, seguindo `docs/tcc/PROMPT_AUDITORIA.md`. Fase somente leitura: nenhuma linha fora de `docs/tcc/` foi alterada.

Convenções. Toda afirmação sobre o repositório traz `arquivo:linha`. Todo número traz o arquivo de origem. Quando um número citado em documento anterior não tem arquivo bruto que o sustente, ele aparece marcado como **sem dado bruto**. "Braço A" e "braço B" nunca são usados; os braços são `single-agent` e `orchestration`.

---

## 0. Fontes de dados brutos localizadas

O repositório versionado não contém nenhuma execução: `runs/` está no `.gitignore` ([.gitignore:13](../../.gitignore#L13)) e `output/` está vazio. As execuções foram encontradas em duas fontes fora da árvore de trabalho:

| Fonte | Conteúdo | Período | Arquivos por execução | Veredito do harness |
|---|---|---|---|---|
| Branch `runs-17-09-2026`, commit `2b3dd43` ("testes do notebook"), clonada em área temporária | 38 execuções em `runs/{pilot-01,pilot-02,calib-a2-300k,pilot-03,sonda-80turnos,variancia,variancia-02,variancia-03}` | 24/08 a 27/08/2026 | `manifest.json`, `events.jsonl`, `summary.json`, `patch.diff`, `workspace/` | **Nenhuma tem `result.json`.** O único desfecho gravado é `is_valid`, que é auto-relato do pipeline, não o oráculo |
| Cópia local em `C:\Users\isaac\Documents\uranium\runs\` | 4 execuções (rep01 de cada braço em `tomlkit-0001` e `sqlite-utils-0001`) | 11/09/2026 | os mesmos, **mais `result.json`** | Todas `resolved: false` |

Total: 42 execuções, custo somado de US$ 1,3458 (soma de `summary.json.totals.cost_usd` das 42). A tabela por rodada está na seção 1.7, risco R1.

Consequência imediata para o restante deste inventário: os números do dossiê ([docs/dossie-metodologico.html](../dossie-metodologico.html)) sobre turnos, tokens e custo **são reproduzíveis** a partir dos `summary.json` da branch; os números sobre "resolveu" **não são**, porque não existe `result.json` para nenhuma das 38 execuções. Detalhe na seção 1.7.

---

## 1.1 Rastreabilidade das sete perguntas da orientadora

| # | Pergunta | Onde está a evidência | Trecho literal (resumido) | Situação |
|---|---|---|---|---|
| 1 | Qual é o problema/pergunta de pesquisa? | [docs/modelagem-do-sistema.html:469-472](../modelagem-do-sistema.html) | "A pergunta do estudo é se decompor o trabalho em papéis especializados […] produz resultado melhor que um agente único fazendo tudo — e a que custo." | Existe em prosa, em documento HTML. **Não existe formulação única de hipótese (H0/H1) em nenhum arquivo**; ver contradição C3 abaixo |
| 2 | Qual é o objetivo do TCC? | [docs/modelagem-do-sistema.html:463-465](../modelagem-do-sistema.html); TFG p. 6 (`docs/tcc/fontes/TFG_ISAAC_DO_PRADO_ALMEIDA.pdf`) | "O Uranium não é um gerador de código. É um aparato experimental que coloca duas topologias de agente para resolver a mesma tarefa […] e mede a diferença." TFG: "investigar de que forma o paradigma ES 3.0 […] modifica o processo de desenvolvimento […] em comparação ao paradigma ES 2.0" | O objetivo do TFG (p. 6) fala em ES 2.0 versus ES 3.0 com cerca de cinco desenvolvedores; o repositório fala em topologia single-agent versus orchestration. A ponte entre os dois (homologia estrutural) só existe em `docs/tcc/PROMPT_AUDITORIA.md:18`. **Não encontrei o objetivo reescrito em nenhum `.md` versionado** |
| 3 | O que está sendo comparado? | [src/arms/runner.py:229-236](../../src/arms/runner.py#L229-L236) (`_compilar`: "É o ÚNICO ponto em que os braços divergem"); [src/arms/runner.py:35](../../src/arms/runner.py#L35) (`CHAVES_QUE_PODEM_DIFERIR`); [src/arms/driver.py:1-17](../../src/arms/driver.py#L1-L17); [src/arms/single_agent.py:1-14](../../src/arms/single_agent.py#L1-L14); [src/graph.py:51-64](../../src/graph.py#L51-L64) | "Escolhe o grafo. É o ÚNICO ponto em que os braços divergem." | Evidência forte no código e no teste de paridade ([tests/test_arm_parity.py](../../tests/test_arm_parity.py)). A hierarquia de desfechos (decisões 1 a 3 do prompt) **não está escrita em lugar nenhum além do prompt de auditoria** |
| 4 | Quais dados/tarefas estão sendo utilizados? | [src/seeds.py:161-162](../../src/seeds.py#L161-L162) (três repositórios-semente); [BACKLOG.md:76-80](../../BACKLOG.md#L76-L80) (tabela de LOC, licença, suíte); `tasks/tomlkit-0001/`, `tasks/sqlite-utils-0001/`; `mined-v1/*.json` | — | 2 tarefas prontas de 12; 54 candidatos aceitos em `mined-v1/` (contagem nesta auditoria: 24 tomlkit + 22 peewee + 8 sqlite-utils). O dossiê diz 53 ([dossie-metodologico.html:266](../dossie-metodologico.html)) |
| 5 | Quais métricas são empregadas, e por quê? | [harness/evaluate.py:115-141](../../harness/evaluate.py#L115-L141) (composição do `result.json`); [harness/oracle.py:42-50](../../harness/oracle.py#L42-L50) (`resolved`); [harness/quality.py:1-8](../../harness/quality.py#L1-L8) ("Sempre como DELTA"); [docs/modelagem-do-sistema.html:1195-1201](../modelagem-do-sistema.html) (por que o Índice de Autonomia foi removido) | "Índice de Autonomia […] removidos: com os dois braços rodando sem qualquer intervenção humana, o índice daria o valor máximo para ambos" | O "o quê" está no código (seção 1.2). O "por quê" está espalhado em docstrings e no HTML; **não há documento de métricas com justificativa por dimensão**. É o que a Fase 3 produz |
| 6 | O que já foi feito e quais são os resultados preliminares? | [dossie-metodologico.html:343-419](../dossie-metodologico.html) e [:494-614](../dossie-metodologico.html); [BACKLOG.md:7-43](../../BACKLOG.md#L7-L43); dados brutos da seção 0 | "Oito rodadas pagas produziram oito defeitos de instrumentação e zero evidência sobre a hipótese" | Parcialmente rastreável: turnos, tokens, custo e o episódio do prompt são reproduzíveis dos `summary.json` e `events.jsonl` (seção 1.7, R1). Os desfechos "resolveu X/5" **não têm `result.json`**. A lista dos "oito defeitos" não está enumerada em nenhum arquivo; reconstruí 11 candidatos pelo histórico de commits (seção 1.7, R1) |
| 7 | O que ainda falta fazer? | [BACKLOG.md:120-152](../../BACKLOG.md#L120-L152); [dossie-metodologico.html:422-490](../dossie-metodologico.html) | "Escrever os dez enunciados restantes […] manual e insubstituível · é o caminho crítico do projeto" | Existe, em ordem de dependência, sem datas nem custo por item. É o que a Fase 4 produz |

### Contradições entre fontes que a orientadora pode encontrar

| # | Contradição | Evidência |
|---|---|---|
| C1 | Teto de tokens: `BACKLOG.md:25` diz 400k; o código e o `.env.example` dizem 1.200.000 | [BACKLOG.md:25](../../BACKLOG.md#L25) × [src/budget.py:29](../../src/budget.py#L29), [.env.example:47](../../.env.example#L47). Os manifestos das rodadas `variancia*` e de 11/09 registram 1.200.000 |
| C2 | Hipótese direcional versus neutra | Direcional: [BACKLOG.md:21](../../BACKLOG.md#L21) e [dossie-metodologico.html:347](../dossie-metodologico.html) ("direção que favorece a hipótese"). Neutra: [modelagem-do-sistema.html:469-471](../modelagem-do-sistema.html) e `docs/tcc/PROMPT_AUDITORIA.md:22`. Não há H0/H1 escrita |
| C3 | Repetições: 3 na coleta planejada, 5 nas rodadas relatadas, 1 no default do código | [BACKLOG.md:32](../../BACKLOG.md#L32); [dossie-metodologico.html:501](../dossie-metodologico.html); [scripts/run_pilot.py:31](../../scripts/run_pilot.py#L31) |
| C4 | Regra C2 do detector descrita de duas formas | [dossie-metodologico.html:312](../dossie-metodologico.html) ("teste removido ou esvaziado") × [modelagem-do-sistema.html:1149](../modelagem-do-sistema.html) e o código ([harness/cheat.py:162-178](../../harness/cheat.py#L162-L178): opções do pytest alteradas). **O código é o segundo**; o dossiê está errado |
| C5 | O README descreve uma arquitetura superada (Developer "gera artefatos", Validator "valida artefatos") e cita `scripts/run_pipeline.py`, que não existe | [README.md:19-20](../../README.md#L19-L20), [README.md:145](../../README.md#L145) × [src/agents/validator.py:51](../../src/agents/validator.py#L51) (roda pytest) |
| C6 | LangSmith removido no código, ainda anunciado em `pyproject.toml:4`, `src/agents/README.md:54` e `projeto.md` | [README.md:161](../../README.md#L161), [src/config.py:30-36](../../src/config.py#L30-L36) × [pyproject.toml:4](../../pyproject.toml#L4) |
| C7 | O TFG (p. 6) promete "aproximadamente cinco desenvolvedores" e instrumentação com LangSmith; o repositório não tem nenhum dos dois | TFG p. 6 × [src/config.py:30-36](../../src/config.py#L30-L36) |
| C8 | Contagens do dossiê que não batem com o disco hoje: 53 candidatos (disco: 54 aceitos), 322 testes (coleta de hoje: 324), crédito consumido US$ 1,06 (soma dos 42 `summary.json`: US$ 1,3458) | [dossie-metodologico.html:264-269](../dossie-metodologico.html) × `mined-v1/*.json`, `uv run pytest --collect-only -q`, seção 0 |

O TFG entregue à Nota 1 tem apenas Resumo, Introdução e Referencial Teórico escritos (p. 5 a 10). As seções 3 a 5 (p. 10 a 13) ainda são o texto-modelo do template da UNIFEI. Nenhuma das sete perguntas é respondida nele.

---

## 1.2 Inventário de métricas coletadas hoje

Uma linha por métrica que chega ao `result.json` ([harness/schema/result.schema.json](../../harness/schema/result.schema.json)). "Dimensão" é a dimensão do TFG que a métrica serve (corretude, eficiência/custo, qualidade, autonomia, integridade/rastreabilidade); nenhuma pergunta de pesquisa formal existe para amarrar (ver 1.1, pergunta 1).

| Métrica (caminho no JSON) | Definição operacional | Origem na telemetria | Calcula | Teste que cobre | Dimensão |
|---|---|---|---|---|---|
| `resolved` | Todos os testes ocultos passam **e** a suíte não regride **e** o detector não acusa sinal crítico | oráculo + detector sobre `workspace/` | [harness/evaluate.py:115](../../harness/evaluate.py#L115); [harness/oracle.py:42-50](../../harness/oracle.py#L42-L50); [harness/cheat.py:66-68](../../harness/cheat.py#L66-L68) | [tests/test_harness.py:313-314](../../tests/test_harness.py#L313-L314); [tests/test_test_patch.py:112-142](../../tests/test_test_patch.py#L112-L142) | corretude (primária descritiva) |
| `resolved_blocked_by_cheat` | Oráculo aprovaria, detector reprovou | idem | [harness/evaluate.py:127](../../harness/evaluate.py#L127) | **nenhum teste referencia o campo** (só o portão 4 de `validate_task.py:134`) | integridade (modo de falha) |
| `oracle.f2p_total`, `oracle.f2p_passed` | Nº de node ids declarados em `fail_to_pass` e quantos passaram | stdout do pytest oculto | [harness/oracle.py:146-149](../../harness/oracle.py#L146-L149) | [tests/test_test_patch.py:124](../../tests/test_test_patch.py#L124) | corretude |
| `oracle.p2p.*`, `oracle.regression.*` | Suíte em `pass_to_pass` e em `suite_targets`, com `--ignore=tests/_uranium_hidden` | pytest | [harness/oracle.py:139-144](../../harness/oracle.py#L139-L144) | [tests/test_test_patch.py:125,143](../../tests/test_test_patch.py#L125) | corretude (regressão) |
| `oracle.*.network_isolated` | `unshare -rn` disponível e usado na chamada | sonda em cada `run_pytest` | [harness/pytest_runner.py:62-69,135,157](../../harness/pytest_runner.py#L135) | [tests/test_harness.py:83-85](../../tests/test_harness.py#L83-L85) (disponibilidade, não o campo) | integridade |
| `cheat.clean`, `cheat.critical_count`, `cheat.warning_count`, `cheat.signals[]` | Regras C1 a C7; só `critical` suja | diff + AST antes/depois | [harness/cheat.py:296-313](../../harness/cheat.py#L296-L313); regras em [:148-268](../../harness/cheat.py#L148-L268) | [tests/test_harness.py:160-230](../../tests/test_harness.py#L160-L230); C2 e C5 **sem teste unitário** (C5 só via patch plantado) | integridade |
| `quality.mi_before/after/delta` | Média do Índice de Manutenibilidade (radon, arquivo inteiro) dos `.py` tocados, base × atual | `git show uranium-base:` × arquivo | [harness/quality.py:54-61,95-107](../../harness/quality.py#L54-L61) | [tests/test_harness.py:266-269](../../tests/test_harness.py#L266-L269) (só caso vazio) | qualidade — **saturado em 0,0; ver 1.3 e R3** |
| `quality.cc_mean_before/after/delta` | Média das complexidades ciclomáticas dos blocos do arquivo, média entre arquivos | idem | [harness/quality.py:64-74,104-108](../../harness/quality.py#L64-L74) | **nenhum** | qualidade |
| `quality.files_analyzed` | `.py` tocados que existem nos dois lados | `changed_files` | [harness/quality.py:94-101](../../harness/quality.py#L94-L101) | [tests/test_harness.py:269](../../tests/test_harness.py#L269) | qualidade |
| `cost.tokens_prompt/completion/reasoning/total` | Soma sobre todos os eventos do valor nativo de `usage` do OpenRouter | `events.jsonl.tokens_*` ← [src/config.py:295-298](../../src/config.py#L295-L298) | [harness/cost.py:30-33](../../harness/cost.py#L30-L33) | [tests/test_harness.py:101-105](../../tests/test_harness.py#L101-L105); [tests/test_telemetry.py:140-161](../../tests/test_telemetry.py#L140-L161) | eficiência (primária inferencial) |
| `cost.cost_usd` | Soma de `usage.cost` nativo, 8 casas | `events.jsonl.cost_usd` ← [src/config.py:299](../../src/config.py#L299) | [harness/cost.py:34](../../harness/cost.py#L34) | [tests/test_config.py:243](../../tests/test_config.py#L243) | eficiência (custo) |
| `cost.llm_calls`, `cost.tool_calls` | Contagem de eventos `llm_call` e `tool_call` | `event_type` | [harness/cost.py:35-36](../../harness/cost.py#L35-L36) | [tests/test_harness.py:104](../../tests/test_harness.py#L104) | eficiência — `tool_calls` **subconta**, ver 1.5 |
| `cost.wall_seconds` | `max(elapsed_ms)/1000` | `elapsed_ms` | [harness/cost.py:37-39](../../harness/cost.py#L37-L39) | [tests/test_harness.py:105](../../tests/test_harness.py#L105) | eficiência |
| `process.turns` | `max(turn)`; um turno = uma chamada de LLM do agente que escreve código | `turn` ← `next_turn()` em [src/arms/single_agent.py:73](../../src/arms/single_agent.py#L73) e [src/agents/developer.py:77](../../src/agents/developer.py#L77) | [harness/cost.py:62](../../harness/cost.py#L62) | [tests/test_harness.py:109](../../tests/test_harness.py#L109) | eficiência — assimetria com `llm_calls`, ver 1.4 |
| `process.test_runs` | Eventos `test_run` (driver ou validator; `run_tests` do agente **não** conta aqui) | `event_type` | [harness/cost.py:63](../../harness/cost.py#L63) | [tests/test_harness.py:109](../../tests/test_harness.py#L109) | autonomia (candidata) |
| `process.tool_denials` | Eventos com `tool_denied` verdadeiro (recusa da guarda de caminho) | `tool_denied` ← [src/tools/__init__.py:104](../../src/tools/__init__.py#L104) | [harness/cost.py:64](../../harness/cost.py#L64) | [tests/test_harness.py:110](../../tests/test_harness.py#L110) | autonomia/integridade (candidata) |
| `process.errors` | Eventos `error` | [src/telemetry.py:290-295](../../src/telemetry.py#L290-L295) | [harness/cost.py:65](../../harness/cost.py#L65) | nenhum no harness | autonomia (candidata) |
| `process.circuit_breaks` | Eventos `circuit_break` | [src/runtime.py:156-161](../../src/runtime.py#L156-L161) | [harness/cost.py:66](../../harness/cost.py#L66) | nenhum no harness | autonomia (candidata) |
| `process.self_recoveries` | Transições falha→verde entre eventos `test_run` consecutivos | `payload.green` | [harness/cost.py:43-56](../../harness/cost.py#L43-L56) | [tests/test_harness.py:120-124](../../tests/test_harness.py#L120-L124) | autonomia |
| `process.stop_reason` | `payload.stop_reason` do último `run_end` | [src/telemetry.py:305-309](../../src/telemetry.py#L305-L309) | [harness/cost.py:60,68](../../harness/cost.py#L60) | [tests/test_harness.py:111,128](../../tests/test_harness.py#L111) | autonomia (candidata) |
| `provenance.model`, `provider_requested`, `providers_served`, `llm_seed`, `topology` | Do manifesto; `providers_served` é o conjunto dos provedores que de fato atenderam | `manifest.json` + `provider_served` dos eventos | [harness/evaluate.py:134-138](../../harness/evaluate.py#L134-L138); [harness/cost.py:72-74](../../harness/cost.py#L72-L74) | [tests/test_harness.py:113-118](../../tests/test_harness.py#L113-L118) | rastreabilidade |
| `diff.files_changed`, `insertions`, `deletions`, `changed_files` | `git diff --numstat` (só rastreados) e `--name-only` ∪ não rastreados | git do workspace | [harness/gitutil.py:22-43](../../harness/gitutil.py#L22-L43) | [tests/test_harness.py:317](../../tests/test_harness.py#L317) | descritiva |

Dois artefatos paralelos existem e não são o harness: `summary.json` ([src/arms/runner.py:203-221](../../src/arms/runner.py#L203-L221)), cujo `is_valid` é auto-relato do pipeline, e o relatório do piloto ([src/arms/pilot.py:42-49](../../src/arms/pilot.py#L42-L49)). A confusão entre `is_valid` e `resolved` é o risco R1.

---

## 1.3 Divergência entre o prometido (TFG, Nota 1) e o implementado

O TFG promete, na p. 6, medir "produtividade, autonomia, qualidade dos artefatos, rastreabilidade e custo", e na p. 10 (§2.8) cita "Maintainability Index, Cyclomatic Complexity e Mutation Score".

| Item prometido | Situação | Evidência |
|---|---|---|
| Maintainability Index | **Parcialmente implementado, mas inoperante nos dados.** É calculado ([harness/quality.py:54-61](../../harness/quality.py#L54-L61)), porém sobre o arquivo inteiro. Nos 4 `result.json` existentes, `mi_before = mi_after = 0.0` em todos. Reproduzi com radon sobre os arquivos tocados: `tomlkit/parser.py` (1.294 linhas) e `sqlite_utils/db.py` (5.239 linhas) têm MI saturado em 0 pela fórmula do radon (volume de Halstead 5.783 e 15.044; MI bruto 2,4 e −185,8). O delta 0,0 lê-se como "sem mudança" e significa "escala saturada". Nenhum teste verifica valor de MI | `result.json` das 4 execuções de 11/09; [harness/quality.py:59](../../harness/quality.py#L59) |
| Cyclomatic Complexity | **Implementado** como média das complexidades dos blocos do arquivo, média entre arquivos, delta contra a base. Sem teste. Valores observados nos 4 resultados: deltas de +0,024 a +0,097 | [harness/quality.py:64-74](../../harness/quality.py#L64-L74); `result.json` de 11/09 |
| Mutation Score | **Ausente.** Não há dependência, código, campo no schema nem menção fora de `docs/tcc/PROMPT_AUDITORIA.md`. Os agentes não escrevem testes na suíte: `tests/**` é área protegida com escrita recusada ([src/prompts.py:52](../../src/prompts.py#L52); [src/workspace.py:197-204](../../src/workspace.py#L197-L204); [harness/taskspec.py:15-19](../../harness/taskspec.py#L15-L19)) e o `test_generator` devolve só um plano em JSON, sem chamada de escrita ([src/agents/test_generator.py:26-59](../../src/agents/test_generator.py#L26-L59)). Recomendação vai para a Fase 3 | `pyproject.toml:7-25` sem `mutmut`/`cosmic-ray` |
| Produtividade | **Parcial, redefinida.** Sem desenvolvedores humanos, "produtividade" só pode ser eficiência do sistema: turnos, tokens, custo, tempo de parede ([harness/cost.py:28-40](../../harness/cost.py#L28-L40)). Não há métrica de tempo humano nem de throughput | — |
| Autonomia | **Não operacionalizada.** O Índice de Autonomia e a taxonomia L0–L4 foram removidos por serem constantes entre os braços ([docs/modelagem-do-sistema.html:1195-1201](../modelagem-do-sistema.html)). Proposta abaixo | — |
| Qualidade dos artefatos | **Parcial:** `resolved` (funcional), deltas de MI e CC (estrutural, com MI inoperante). `coverage_percent` existe e nunca é chamada ([harness/quality.py:113-149](../../harness/quality.py#L113-L149)) | — |
| Rastreabilidade | **Instrumentada, não operacionalizada como métrica.** JSONL de 25 campos obrigatórios validado contra JSON Schema ([harness/schema/event.schema.json](../../harness/schema/event.schema.json); [src/telemetry.py:178-204](../../src/telemetry.py#L178-L204)); provedor atendido por chamada; manifesto por run. Proposta abaixo | — |
| Custo | **Implementado** com valor nativo do provedor, não estimativa ([src/config.py:245-250,299](../../src/config.py#L245-L250)); reagregado de forma independente pelo harness ([harness/cost.py:1-7](../../harness/cost.py#L1-L7)) | — |
| Estudo com ~5 desenvolvedores; LangSmith; DSR | **Movidos ou removidos.** Participantes humanos: trabalhos futuros, por variância (decisão do prompt). LangSmith: removido deliberadamente ([README.md:161](../../README.md#L161)). DSR: não há menção no repositório | — |

### Proposta de definição operacional para autonomia

Todos os campos abaixo já são coletados. A proposta é descritiva; nenhum deles vira desfecho inferencial.

| Nome no texto | Definição | Campos | Observação metodológica |
|---|---|---|---|
| Conclusão autônoma | A execução terminou por critério próprio do sistema (`tests_pass` ou `concluiu`) e não por corte externo (`budget:*`, `error:*`) | `process.stop_reason`, `process.circuit_breaks` | Proporção por braço, X/N. É o que resta de "autonomia" quando nenhum humano intervém |
| Recuperações próprias | Nº de transições falha→verde da suíte sem input externo | `process.self_recoveries` | No `single-agent` a suíte é rodada pelo driver, que devolve stderr cru ([src/arms/driver.py:74-107](../../src/arms/driver.py#L74-L107)); no `orchestration`, pelo validator. O "input externo" é determinístico e idêntico em conteúdo bruto, mas o **texto da mensagem difere** (ver 1.4, folga F1). Declarar |
| Tentativas contra a fronteira | Nº de chamadas de ferramenta recusadas pela guarda de caminho | `process.tool_denials` | Recusa é valor de retorno, não exceção ([src/tools/__init__.py:104](../../src/tools/__init__.py#L104)); a tentativa é o sinal. Observado: 2 recusas no `orchestration` em `sqlite-utils-0001` rep01 de 11/09, 0 nas outras três |
| Verificações espontâneas | Nº de vezes que o agente rodou a suíte por iniciativa própria (`run_tests` como `tool_call`), separado das rodadas do driver/validator (`test_run`) | eventos `tool_call` com `tool_name = run_tests` × eventos `test_run` | Hoje o harness soma só `test_runs` ([harness/cost.py:63](../../harness/cost.py#L63)); a separação exige ler `events.jsonl` |

### Proposta de definição operacional para rastreabilidade

| Nome no texto | Definição | Campos | Observação |
|---|---|---|---|
| Proveniência verificada | Proporção de chamadas de LLM atendidas pelo provedor pinado | `provider_served == provider_requested` por evento `llm_call`; agregado em `provenance.providers_served` | Nas 38 execuções da branch: 853 de 853 chamadas atendidas por DeepInfra (contagem sobre `events.jsonl`). É prova de que o pino funciona |
| Trilha completa | Toda ação do sistema tem evento com `seq`, `ts`, `node`, `agent_role`, `turn` e hash dos argumentos, validado contra o schema | os 25 campos de [event.schema.json](../../harness/schema/event.schema.json) | `agent_role` é o campo que materializa a variável independente no dado bruto: nulo no `single-agent`, preenchido no `orchestration` ([src/arms/single_agent.py:67](../../src/arms/single_agent.py#L67)) |
| Atribuição por papel | Fração de tokens por `agent_role` no braço `orchestration` | `tokens_total` agrupado por `agent_role` | Reproduzi: os nós fora do developer custaram 3.977 a 4.600 tokens por execução na rodada `variancia-03` (mediana 4.403), contra totais de 166 mil a 492 mil. Confirma o "4.400" do dossiê ([dossie-metodologico.html:587](../dossie-metodologico.html)) |
| Reexecutabilidade | O `manifest.json` permite reexecutar o run: modelo, provedor, semente derivada, tetos, política do driver | [src/arms/runner.py:70-88](../../src/arms/runner.py#L70-L88) | Cinco parâmetros que afetam o braço `orchestration` **não** estão no manifesto (1.4, folga F9) |

---

## 1.4 Auditoria de paridade

Classificação: **(a)** identidade literal testada; **(b)** comparado por semelhança ou tolerância; **(c)** não comparado por nenhum teste; **(d)** diferente por desenho (é a topologia), com indicação de se a diferença **vaza** para o agente que escreve código.

Os três mecanismos de verificação existentes: comparação do manifesto com lista de chaves que podem diferir ([tests/test_arm_parity.py:56-67](../../tests/test_arm_parity.py#L56-L67); [src/arms/runner.py:35](../../src/arms/runner.py#L35)); comparação de dois `RunContext` reais ([tests/test_arm_parity.py:102-152](../../tests/test_arm_parity.py#L102-L152)); identidade literal do prompt de sistema ([tests/test_arm_parity.py:177-185](../../tests/test_arm_parity.py#L177-L185)). Tudo que está fora desses três não é comparado.

### Blindado por identidade literal (a)

| Item | Onde vive | Teste |
|---|---|---|
| Prompt de sistema `AGENT_SYSTEM_PROMPT`, mesma origem de objeto | [src/prompts.py:30-57](../../src/prompts.py#L30-L57); [src/arms/single_agent.py:33](../../src/arms/single_agent.py#L33); [src/agents/developer.py:24](../../src/agents/developer.py#L24) | [tests/test_arm_parity.py:178,184-185](../../tests/test_arm_parity.py#L178) |
| Configuração de LLM inteira: modelo, provedor, `temperature=0`, semente derivada, `max_tokens=8192`, `timeout_s=300`, `max_retries=6`, `allow_fallbacks=False`, `require_parameters=True`, `data_collection=deny` | [src/config.py:51-70](../../src/config.py#L51-L70) | [tests/test_arm_parity.py:77-83](../../tests/test_arm_parity.py#L77-L83) |
| Cliente construído da configuração resolvida, não do ambiente | [src/runtime.py:74-82](../../src/runtime.py#L74-L82) | [tests/test_arm_parity.py:330-368](../../tests/test_arm_parity.py#L330-L368) |
| Orçamento (`max_tokens`, `max_wall_seconds`, `max_turns`) no manifesto e em runtime | [src/budget.py:29-31](../../src/budget.py#L29-L31) | [tests/test_arm_parity.py:85-87,147-148](../../tests/test_arm_parity.py#L85-L87) |
| Conjunto de ferramentas, schemas de argumentos, descrições | [src/tools/__init__.py:31-34,40-78,165-201](../../src/tools/__init__.py#L165-L201) | [tests/test_arm_parity.py:127-145](../../tests/test_arm_parity.py#L127-L145) |
| `test_timeout_s` | [src/arms/runner.py:85](../../src/arms/runner.py#L85) | [tests/test_arm_parity.py:150-152](../../tests/test_arm_parity.py#L150-L152) |
| Semente pareada por repetição, distinta entre repetições | [src/arms/runner.py:38-50,127](../../src/arms/runner.py#L38-L50) | [tests/test_arm_parity.py:214-233](../../tests/test_arm_parity.py#L214-L233) |
| Mensagem de diff vazio `DIFF_VAZIO` | [src/feedback.py](../../src/feedback.py); [src/arms/driver.py:89](../../src/arms/driver.py#L89); [src/agents/developer.py:49](../../src/agents/developer.py#L49) | [tests/test_arm_parity.py:429-447](../../tests/test_arm_parity.py#L429-L447) |
| Executor único de tool calls; nós auxiliares passam pela telemetria e pelo orçamento | [src/runtime.py:163-202](../../src/runtime.py#L163-L202); [src/runtime.py:132-154](../../src/runtime.py#L132-L154) | [tests/test_arm_parity.py:380-389,301-318](../../tests/test_arm_parity.py#L380-L389) (o primeiro por inspeção de código-fonte, proxy sintático) |

### Folgas encontradas: comparado por semelhança (b), não comparado (c), ou diferente por desenho com vazamento (d)

Ordenadas pelo impacto sobre a métrica primária inferencial (tokens).

| # | Item | single-agent | orchestration | Classe | Evidência |
|---|---|---|---|---|---|
| F1 | **Texto da mensagem "a suíte falhou"** | `"A suíte falhou.\n\n{saida}"` via `suite_falhou` | `"A suíte falhou na tentativa anterior. Saída do pytest:"` + `stdout_tail`, **sem usar `suite_falhou`** | **(c)** divergência literal confirmada | [src/feedback.py:26-28](../../src/feedback.py#L26-L28); [src/arms/driver.py:105](../../src/arms/driver.py#L105); [src/agents/developer.py:38-43](../../src/agents/developer.py#L38-L43). Mesma classe do defeito que motivou `src/feedback.py`; só `DIFF_VAZIO` migrou |
| F2 | **Truncamento do feedback de pytest** | últimos 4.000 caracteres (`stderr_chars`) | `stdout_tail` inteiro, já limitado a 8.000 pela ferramenta; estratégia cabeça 2/3 + cauda 1/3 | **(c)** 4.000 vs 8.000 | [src/arms/driver.py:44,96-98](../../src/arms/driver.py#L96-L98); [src/tools/exec.py:149](../../src/tools/exec.py#L149); [src/tools/base.py:17,54-66](../../src/tools/base.py#L17). `stderr_chars` está dentro de `driver_policy`, chave **autorizada a diferir** pelo teste de paridade ([src/arms/runner.py:35](../../src/arms/runner.py#L35)) |
| F3 | **Política de janela de contexto** | lista de mensagens persistente no `RunContext`, cresce por todo o run | lista reconstruída do zero a cada entrada no nó `developer`; histórico da rodada anterior descartado | **(c)**, não é consequência necessária da topologia | [src/runtime.py:47](../../src/runtime.py#L47); [src/arms/single_agent.py:58](../../src/arms/single_agent.py#L58) × [src/agents/developer.py:61-64](../../src/agents/developer.py#L61-L64). Afeta diretamente o crescimento quadrático de tokens que o dossiê discute |
| F4 | **Enunciado entregue ao agente que escreve código** | intent-esqueleto com o `statement.md` cru em `goal` | intent reescrita pelo `intent_refiner` (contexto, fases, critérios de aceitação gerados por LLM), possivelmente enriquecida por `clarification` | **(d), vaza.** O manifesto declara `statement` idêntico, mas o developer vê outro texto | [src/arms/runner.py:173-177](../../src/arms/runner.py#L173-L177); [src/arms/single_agent.py:38](../../src/arms/single_agent.py#L38) × [src/agents/intent_refiner.py:49-64](../../src/agents/intent_refiner.py#L49-L64); [src/agents/developer.py:31-34](../../src/agents/developer.py#L31-L34). É a hipótese da ablação (Fase 5, item 3). Nada registra o tamanho da primeira mensagem humana em cada braço |
| F5 | **Teto de ciclos de retry** | ilimitado até o orçamento | `MAX_VALIDATION_ITERATIONS = 2`: no máximo duas invocações do developer | **(c)** critério de parada distinto, fora do manifesto | [src/arms/single_agent.py:120-121](../../src/arms/single_agent.py#L120-L121) × [src/graph.py:28-31](../../src/graph.py#L28-L31); [src/config.py:41](../../src/config.py#L41) |
| F6 | **Gate semântico de parada** | verde e houve mudança | verde, houve mudança **e** revisão semântica por LLM não rebaixou | **(d), vaza** (decide se o developer roda de novo). Ligado por `SEMANTIC_REVIEW`, que **não está no `.env.example` nem no manifesto** | [src/arms/driver.py:86-94](../../src/arms/driver.py#L86-L94) × [src/agents/validator.py:40-44,74](../../src/agents/validator.py#L74) |
| F7 | **Turno não é teto equalizado de chamadas de LLM** | 1 turno = 1 chamada | 1 turno = 1 chamada do developer; `intent_refiner`, `clarification`, `validator`, `test_generator` consomem tokens sem consumir turno | **(d)**, declarável; nenhum teste documenta | [src/runtime.py:132-154](../../src/runtime.py#L132-L154) não chama `next_turn()`; [src/budget.py:61-63](../../src/budget.py#L61-L63) |
| F8 | Mensagem "Arquivos já modificados: …" | não existe | existe | **(c)** | [src/agents/developer.py:50-51](../../src/agents/developer.py#L50-L51) |
| F9 | **Parâmetros que afetam só o `orchestration` e não vão ao manifesto** | — | `MAX_VALIDATION_ITERATIONS`, `MAX_CLARIFICATION_ITERATIONS`, `SEMANTIC_REVIEW`, `STRUCTURED_OUTPUT_METHOD`, `STRUCTURED_OUTPUT_RETRIES` | **(c)**. Dois runs com valores diferentes produzem manifestos idênticos | [src/config.py:40-41](../../src/config.py#L40-L41); [src/agents/validator.py:42](../../src/agents/validator.py#L42); [src/structured_llm.py:63,71](../../src/structured_llm.py#L63); manifesto em [src/arms/runner.py:70-88](../../src/arms/runner.py#L70-L88) |
| F10 | Ordem das ferramentas no `bind_tools` | idêntica por construção comum | idem | **(c)** o teste usa `set` e ordena por nome | [tests/test_arm_parity.py:129-139](../../tests/test_arm_parity.py#L129-L139); [src/tools/__init__.py:165-211](../../src/tools/__init__.py#L165-L211) |
| F11 | Constantes compartilhadas fora do manifesto: `MAX_TOOL_CALLS_POR_TURNO=8`, `DEFAULT_SNIPPET_TIMEOUT_S=60`, `MAX_READ_CHARS=20.000`, `MAX_READ_LINES=400`, `MAX_SEARCH_RESULTS=50`, `MAX_TOOL_OUTPUT_CHARS=8.000`, `max_results=200`, `recursion_limit` | iguais por serem constantes de módulo | idem | **(c)** idênticos hoje, sem teste que os fixe nem registro no manifesto | [src/runtime.py:27](../../src/runtime.py#L27); [src/tools/exec.py:187](../../src/tools/exec.py#L187); [src/tools/base.py:14-17](../../src/tools/base.py#L14-L17); [src/tools/fs.py:41](../../src/tools/fs.py#L41); [src/arms/runner.py:193](../../src/arms/runner.py#L193) |
| F12 | Executor comum verificado por inspeção de código-fonte, e testes de erro rodam só com contexto `orchestration` | — | — | **(b)** proxy sintático; `ctx_minimo` é sempre `orchestration` | [tests/test_arm_parity.py:380-389](../../tests/test_arm_parity.py#L380-L389); [tests/conftest.py:176](../../tests/conftest.py#L176) |
| F13 | Teste do manifesto itera só as chaves do `single-agent` | — | — | fragilidade latente: chave exclusiva do `orchestration` passaria | [tests/test_arm_parity.py:61](../../tests/test_arm_parity.py#L61) |

Leitura para o texto: F1, F2, F3 e F8 são corrigíveis sem tocar na topologia e afetam a métrica primária. F4, F5, F6 e F7 são a topologia, mas hoje **não estão declaradas em nenhum documento nem no manifesto**, o que é o mesmo tipo de silêncio que deixou passar a divergência de prompt. F9 é a lacuna de registro mais concreta. Nenhuma correção foi feita nesta fase.

---

## 1.5 Auditoria de instrumentação

Ponto único de medição para as sete ferramentas: `record.bytes_read = len(result.encode("utf-8"))` em [src/tools/__init__.py:113](../../src/tools/__init__.py#L113), dentro do wrapper `_instrument` ([:84-121](../../src/tools/__init__.py#L84-L121)). A string medida é byte a byte a que vira `ToolMessage` em [src/runtime.py:192,200](../../src/runtime.py#L192). A medição acontece **depois** de todo truncamento (limites em [src/tools/base.py:14-17](../../src/tools/base.py#L14-L17), aplicados em `fs.py` e `exec.py` antes do `return`). O commit `3820b1d` (27/08/2026 00:23 −03:00) tornou a medição incondicional; antes só `read_file`, `search_code` e `list_files` mediam.

| Ferramenta | Caminho de sucesso medido | Caminhos de recusa/erro medidos | Escapes | Teste de `bytes_read` |
|---|---|---|---|---|
| `list_files` | sim | recusa e "nenhum arquivo" sim | — | sucesso: [tests/test_tools.py:405,418](../../tests/test_tools.py#L405) |
| `read_file` | sim, pós-truncamento (400 linhas / 20.000 chars) | recusa, inexistente, diretório, binário, `start_line` além do fim: sim | `OSError` em `read_bytes()` ([src/tools/fs.py:75](../../src/tools/fs.py#L75)) cai na exceção genérica, `bytes_read = 0` | [tests/test_tools.py:252-258,406](../../tests/test_tools.py#L252-L258) |
| `search_code` | sim, pós-limite de 50 | recusa, regex inválida, sem ocorrências: sim | — | [tests/test_tools.py:407](../../tests/test_tools.py#L407) |
| `write_file` | sim; `bytes_written = len(content)` | recusas: sim, `bytes_written = 0` | — | [tests/test_tools.py:409,420-429](../../tests/test_tools.py#L420-L429) |
| `replace_in_file` | sim | recusas: sim. **Erros** (inexistente, `old == new`, zero ou múltiplas ocorrências) contabilizam `bytes_written = len(new_text)` sem nada ter sido escrito | `bytes_written` espúrio: [src/tools/__init__.py:114-116](../../src/tools/__init__.py#L114-L116) só condiciona a `not denied` | [tests/test_tools.py:410-411](../../tests/test_tools.py#L410-L411) (só sucesso) |
| `run_python` | sim, pós-truncamento 8.000 | recusa (prefixo `RECUSADO:`) sim; **timeout** sim, mas com `denied=False`, `error=None`, `exit_code=None` (indistinguível na telemetria) | falha em `write_text` do trecho cai na exceção genérica | [tests/test_tools.py:408](../../tests/test_tools.py#L408) (só sucesso) |
| `run_tests` | sim (verde, vermelho, timeout) | — | `SeedRepoError` (venv ausente, [src/seeds.py:106-109](../../src/seeds.py#L106-L109)) cai na exceção genérica | **ausente** do dicionário de [tests/test_tools.py:405-412](../../tests/test_tools.py#L405-L412), apesar de ser o motivo declarado do commit; só `duration_ms` é testado ([:277-279](../../tests/test_tools.py#L277-L279)) |

### Caminhos em que texto entra no contexto do modelo sem medição

| # | Caminho | Evidência | Efeito |
|---|---|---|---|
| E1 | Exceção não tratada dentro da ferramenta | [src/tools/__init__.py:97-101](../../src/tools/__init__.py#L97-L101): `emit(record)` antes da linha 113 | evento `tool_call` com `bytes_read = 0`, texto de erro entregue ao modelo |
| E2 | Ferramenta desconhecida | [src/runtime.py:185-189](../../src/runtime.py#L185-L189) | **nenhum evento**; `cost.tool_calls` subconta |
| E3 | Argumento inválido (validação pydantic antes do wrapper) | [src/runtime.py:191-199](../../src/runtime.py#L191-L199) | evento `error`, **nenhum `tool_call`**; texto devolvido não medido |
| E4 | Tool calls além da oitava no mesmo turno | [src/runtime.py:183](../../src/runtime.py#L183) | descartadas em silêncio, sem `ToolMessage` de resposta |
| E5 | Mensagens humanas de protocolo (tarefa inicial, feedback de pytest de até 4.000 ou 8.000 caracteres) | [src/arms/single_agent.py:63,103](../../src/arms/single_agent.py#L103); [src/agents/developer.py:63](../../src/agents/developer.py#L63) | maior injeção de contexto não instrumentada, e é exatamente onde os braços divergem (1.4, F1 e F2) |

Ressalvas: `bytes_read` conta bytes UTF-8, não tokens; `tool_exit_code` é sempre nulo em `tool_call` porque nada preenche `ToolCallRecord.exit_code` ([src/tools/base.py:31](../../src/tools/base.py#L31)); `payload` é objeto livre no schema ([event.schema.json:163-165](../../harness/schema/event.schema.json)), então um `tool_call` sem `bytes_read` valida. O evento `llm_call` guarda `tool_calls_requested` ([src/telemetry.py:250](../../src/telemetry.py#L250)), que permite reconciliar E2 e E3 a posteriori.

**Verificação nos dados.** As 38 execuções da branch são todas anteriores ao commit `3820b1d` (a última, `variancia-03`, terminou às 03:17 UTC de 27/08; o commit é das 03:23 UTC). Nelas, `run_python` (100 chamadas), `run_tests` (23) e `replace_in_file` (13) registram `bytes_read = 0` em todas as chamadas da rodada `variancia-03`. Nas 4 execuções de 11/09, todas as ferramentas registram `bytes_read > 0`, inclusive recusas. Consequência: a "reanálise do crescimento de contexto com dados já coletados, custo zero" (Fase 5, item 4) **só é possível sobre as 4 execuções de 11/09**; as rodadas de variância não podem ser reanalisadas e precisariam ser refeitas.

---

## 1.6 Dívida do "vibe coding"

Grafo de imports construído por AST a partir de `main.py`, `scripts/*.py`, `harness/evaluate.py` e `tests/*.py`. Todo módulo de `src/`, `harness/` e `scripts/` é alcançado por algum ponto de entrada dos braços, exceto os listados. Nada foi removido.

| Caminho | O que é (por leitura) | Alcançado por braço | Alcançado por teste | Classificação | Justificativa |
|---|---|---|---|---|---|
| `main.py` | Hello-world LangGraph com efeito colateral no import ([main.py:21](../../main.py#L21)) | não | não | **remover** | sem relação com o experimento |
| `test.py` | Invoca `build_graph()` sem `run_id`; quebra em [src/runtime.py:113-114](../../src/runtime.py#L113-L114); pede "CRUD em Node.js" | não | não | **remover** | quebrado e fora de escopo |
| `src/export.py` | Grava `output/latest` a partir de chave `artifacts`, que não existe mais no estado ([src/state.py:19-62](../../src/state.py#L19-L62)) | não | [tests/test_export.py:6](../../tests/test_export.py#L6) | **remover** (com o teste) | resíduo da POC de artefatos em texto |
| `src/metrics.py` | `self_recoveries` e `process_metrics`, duplicatas de [harness/cost.py:43,59](../../harness/cost.py#L43) | não | [tests/test_telemetry.py:11](../../tests/test_telemetry.py#L11) | **decidir** | o harness declara a duplicação como proposital ([harness/cost.py:1-7](../../harness/cost.py#L1-L7)), mas nenhum teste faz o cross-check entre as duas versões |
| `src/schemas/intent_agent.py` | Literal JSON de exemplo salvo como `.py` | não | não | **remover** | órfão |
| `src/agents/intent_refiner/cases.json` | Esqueleto JSON com `"..."`; o diretório colide com o módulo `intent_refiner.py` | não | não | **remover** | nenhuma referência |
| `src/agents/tfg1.md` | **arquivo vazio, 0 bytes** | não | não | **remover** | não é fonte de nada |
| `src/agents/README.md` | Descreve LangSmith, `src/tracing.py` (inexistente) e Developer que devolve `artifacts` | não | não | **decidir** | contradiz o código; reescrever ou apagar |
| `projeto.md` | Tutorial da POC inicial: grafo de um nó, LLM global, LangSmith | não | não | **decidir** | histórico; se ficar, cabeçalho "superado por docs/modelagem-do-sistema.html" |
| `.agents/skills/multi-agent-orchestration/*`, `skills-lock.json` | Pacote de skill de terceiro (`qodex-ai/ai-agent-skills`, [skills-lock.json:5-6](../../skills-lock.json#L5-L6)); exemplos genéricos de CrewAI/AutoGen; nenhum import de `src/` | não | não | **decidir** | material de terceiro no repositório do TCC; se ficar, declarar proveniência e licença |
| `mined-v1/*.json` | Dado de mineração congelado (90 candidatos, 54 aceitos) | não (o emissor lê `mined/`, que é gitignored: [scripts/emit_task.py:145](../../scripts/emit_task.py#L145), [.gitignore:15](../../.gitignore#L15)) | não | **manter e documentar** | é dado de pesquisa; falta um README dizendo que é o conjunto v1 e como foi gerado |
| `harness/quality.py:113-149` `coverage_percent` | Cobertura de linha e ramo | nunca chamada | não | **decidir** | única razão de `coverage>=7.0.0` em `pyproject.toml:24`; a ajuda do CLI promete "radon/coverage" e não mede cobertura ([harness/evaluate.py:160](../../harness/evaluate.py#L160); [scripts/validate_task.py:143](../../scripts/validate_task.py#L143)) |
| `harness/gitutil.py:58` `stash_agent_changes` | Stash de mudanças do agente | não | não | **remover** | sem referência |
| `src/state.py:70,76,88` `parse_clarifications`, `parse_validation`, `parse_test_plan` | Parsers de estado | não | não | **remover** | sem referência |
| `src/tools/base.py:69` `Timer` | Cronômetro | não | não | **remover** | sem referência |
| `src/schemas/__init__.py:3-23` | Reexportações e `__all__` | ninguém usa `from src.schemas import` | — | **manter** | inofensivo |
| `src/arms/pilot.py`, `src/feedback.py`, `src/agents/clarification.py` | Verificados: **estão vivos** ([scripts/run_pilot.py:23](../../scripts/run_pilot.py#L23); [src/arms/driver.py:25](../../src/arms/driver.py#L25); [src/graph.py:5,46,57](../../src/graph.py#L46)) | sim | pilot e feedback sim; a função `clarification` **nunca é executada por teste**, só o roteamento ([tests/test_graph_flow.py:22-25](../../tests/test_graph_flow.py#L22-L25)) | **manter e documentar** | `clarification` é alcançável em produção se o `intent_refiner` devolver `is_ready = false` ([src/graph.py:14-18](../../src/graph.py#L14-L18)); nunca observado nas 42 execuções |

---

## 1.7 Riscos à validade, por gravidade

Critério de ordenação: primeiro o que pode produzir número plausível e errado no texto final; depois o que impede a coleta; depois o que só enfraquece a explicação.

### R1 — Os desfechos "resolveu" das rodadas piloto não têm veredito do harness

Nenhuma das 38 execuções da branch tem `result.json`. O único desfecho gravado é `summary.json.is_valid`, que é a autoavaliação do pipeline ([src/arms/runner.py:212](../../src/arms/runner.py#L212)): no `single-agent`, "a suíte visível ficou verde e houve mudança" ([src/arms/driver.py:86-94](../../src/arms/driver.py#L86-L94)); no `orchestration`, o mesmo mais a revisão semântica ([src/agents/validator.py:74](../../src/agents/validator.py#L74)). A suíte visível **não contém o teste oculto**. Na única rodada com os dois valores (11/09/2026), auto-relato e harness discordam em 3 de 4 execuções:

| Execução (11/09) | `stop_reason` | `is_valid` | `resolved` | Por quê |
|---|---|---|---|---|
| single-agent · tomlkit-0001 | `budget: max_turns (40 >= 40)` | false | false | 40 turnos sem parar de chamar ferramenta; `test_runs = 0`; o driver nunca chegou a rodar a suíte |
| orchestration · tomlkit-0001 | `concluiu` | **true** | **false** | f2p 0/1 |
| single-agent · sqlite-utils-0001 | `tests_pass` | **true** | **false** | f2p 1/5 |
| orchestration · sqlite-utils-0001 | `concluiu` | **true** | **false** | f2p 5/5, mas p2p regrediu 1 teste (`test_transform_in_transaction_allowed_with_foreign_keys_off`) |

Fonte: `result.json` e `summary.json` das quatro execuções em `C:\Users\isaac\Documents\uranium\runs\`.

Efeito sobre o dossiê. As afirmações "5/5", "2/5", "4/4", "14 de 14" ([dossie-metodologico.html:508-509,550-552,352](../dossie-metodologico.html)) coincidem com `is_valid` da branch em duas das três (variancia-03: 4/4 e 5/5; variancia-02 single-agent: 5/5), **mas não na terceira**: em `variancia-02` o `orchestration` tem `is_valid` 3/5, e o dossiê diz 2/5. Se o 2/5 veio de um `result.json` que se perdeu, não há como saber. Todas essas frações ficam **sem dado bruto** e não podem ser citadas como `resolved` no texto. Os agregados de turnos, tokens e custo, ao contrário, **batem exatamente** com os `summary.json` (tabela abaixo).

Tabela consolidada das 42 execuções (fonte: `summary.json` e `manifest.json`; `resolved` só onde há `result.json`):

| rodada | data (UTC) | braço | tarefa | n | teto tokens/turnos | is_valid (auto-relato) | resolved (harness) | turnos mediana | tokens mediana | US$ total | paradas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-01 | 2026-08-24 02:10 | single-agent | tomlkit-0001 | 1 | 120.000/25 | 1/1 | sem result.json | 10 | 138.370 | 0,0253 | tests_pass×1 |
| pilot-01 | 2026-08-24 02:11 | orchestration | tomlkit-0001 | 1 | 120.000/25 | 0/1 | sem result.json | 0 | 0 | 0,0000 | error: StructuredOutputError×1 |
| pilot-02 | 2026-08-24 02:44 | single-agent | tomlkit-0001 | 1 | 120.000/20 | 0/1 | sem result.json | 9 | 120.486 | 0,0164 | budget: max_tokens×1 |
| pilot-02 | 2026-08-24 02:45 | orchestration | tomlkit-0001 | 1 | 120.000/20 | 1/1 | sem result.json | 13 | 129.163 | 0,0182 | concluiu×1 |
| calib-a2-300k | 2026-08-24 02:48 | single-agent | tomlkit-0001 | 1 | 300.000/40 | 1/1 | sem result.json | 29 | 227.350 | 0,0307 | tests_pass×1 |
| pilot-03 | 2026-08-27 00:23 | single-agent | tomlkit-0001 | 1 | 400.000/40 | 1/1 | sem result.json | 14 | 219.439 | 0,0272 | tests_pass×1 |
| pilot-03 | 2026-08-27 00:24 | orchestration | tomlkit-0001 | 1 | 400.000/40 | 0/1 | sem result.json | 22 | 413.856 | 0,0506 | budget: max_tokens×1 |
| sonda-80turnos | 2026-08-27 01:20 | orchestration | tomlkit-0001 | 1 | 3.000.000/80 | 1/1 | sem result.json | 40 | 464.825 | 0,0581 | concluiu×1 |
| variancia | 2026-08-27 00:31 | single-agent | tomlkit-0001 | 5 | 1.200.000/40 | 5/5 | sem result.json | 14 | 214.987 | 0,1573 | tests_pass×5 |
| variancia | 2026-08-27 00:31 | orchestration | tomlkit-0001 | 5 | 1.200.000/40 | 2/5 | sem result.json | 18 | 67.955 | 0,0783 | concluiu×4; error: ValidationError×1 |
| variancia-02 | 2026-08-27 00:47 | single-agent | tomlkit-0001 | 5 | 1.200.000/40 | 5/5 | sem result.json | 15 | 123.743 | 0,1001 | tests_pass×5 |
| variancia-02 | 2026-08-27 00:48 | orchestration | tomlkit-0001 | 5 | 1.200.000/40 | 3/5 | sem result.json | 40 | 525.195 | 0,2858 | concluiu×3; budget: max_turns×2 |
| variancia-03 | 2026-08-27 02:56 | single-agent | tomlkit-0001 | 5 | 1.200.000/40 | 4/5 | sem result.json | 24 | 124.837 | 0,1121 | error: RateLimitError×1; tests_pass×4 |
| variancia-03 | 2026-08-27 03:03 | orchestration | tomlkit-0001 | 5 | 1.200.000/40 | 5/5 | sem result.json | 24 | 318.315 | 0,2060 | concluiu×5 |
| coleta-11-09 | 2026-09-11 11:29 | single-agent | sqlite-utils-0001, tomlkit-0001 | 2 | 1.200.000/40 | 1/2 | **0/2** | 33 | 315.774 | 0,0774 | tests_pass×1; budget: max_turns×1 |
| coleta-11-09 | 2026-09-11 11:32 | orchestration | sqlite-utils-0001, tomlkit-0001 | 2 | 1.200.000/40 | 2/2 | **0/2** | 35,5 | 403.361 | 0,1025 | concluiu×2 |

O que o dado bruto **confirma** do episódio do prompt (seção 03 do dossiê): a rodada `variancia-02` foi executada antes do commit `3ec3565` (prompt único, 26/08 23:13 −03:00 = 27/08 02:13 UTC) e a `variancia-03` depois. Recontei dos `events.jsonl`: chamadas de ferramenta após a primeira escrita no `single-agent` de `variancia-02` = 4, 4, 4, 4, 4; no `orchestration` = 2, 8, 6, 32, 21. Mediana de turnos do `orchestration` caiu de 40 para 24. Tokens dos nós fora do developer em `variancia-03`: 3.977 a 4.600 por execução. Chamadas de `read_file` em `variancia-03`: 22 no `single-agent` e 34 no `orchestration`. Os bytes lidos por `read_file` que recontei (86.728 e 168.637) **não coincidem** com os do dossiê (90.487 e 182.866); a definição do numerador usada lá não está documentada. Tudo isso é resultado sobre **turnos, tokens e mecanismo**, não sobre `resolved`.

Os "oito defeitos de instrumentação" não estão enumerados em nenhum arquivo. Pelo histórico de commits com prefixo `fix` entre 20/08 e 17/09, os candidatos são 16: `d23217b` (max_tokens), `31a3546` (parallel_tool_calls), `274e0a4` (nós fora da telemetria e do orçamento), `9748a81` (diff vazio não é sucesso), `ee817d7`, `c11a9cf` (interpretador do repo-semente), `805cd7b` (piloto herdava tetos próprios), `3cad221` (turnos viram o orçamento), `4ab2978` (executor unificado e aviso de diff vazio), `851d2dd`, `356a27c` (erro transitório do provedor), `3b23e75` (run_id é um run), `3ec3565` (prompt único), `3820b1d` (medição de saída), `3be9d7c` (avaliar duas vezes dá o mesmo veredito), `0b81a15` (cópia descartável). A Fase 2 precisa escolher e nomear os oito, ou mudar o número.

### R2 — Índice de Manutenibilidade saturado em zero

Detalhado em 1.3. `mi_delta = 0.0` em 100% dos resultados existentes é artefato de escala, não achado. Publicado como "a manutenibilidade não mudou", seria número plausível e errado. Evidência: 4 `result.json` de 11/09; reprodução com radon nos arquivos do workspace (MI bruto 2,4 para `parser.py` e −185,8 para `db.py`, ambos saturando em 0 na escala 0–100 do radon).

### R3 — Folgas de paridade que afetam tokens (1.4, F1 a F3)

O texto do feedback, o corte em 4.000 versus 8.000 caracteres e a política de janela de contexto (acumular tudo versus reconstruir a cada ciclo) não são topologia e alteram diretamente `tokens_prompt`, o desfecho primário inferencial. O crescimento quadrático que o dossiê atribui à orquestração é parcialmente atribuível a F3. Nenhum teste as fixa; nenhum documento as declara.

### R4 — `pass_to_pass` contaminado pelos testes `fail_to_pass` na forma `test_patch`

Nas tarefas por patch do upstream, `apply_test_patch` insere os testes novos em `tests/` ([harness/oracle.py:69-97](../../harness/oracle.py#L69-L97)) e `pass_to_pass = ["tests/"]` os inclui ([tasks/sqlite-utils-0001/task.json](../../tasks/sqlite-utils-0001/task.json); [harness/oracle.py:139-144](../../harness/oracle.py#L139-L144)). Sempre que f2p falha, p2p e regressão "falham" com os mesmos node ids. Exemplo real: `single-agent` · `sqlite-utils-0001` de 11/09 mostra `p2p.failed = 4`, e os 4 são exatamente os f2p que falharam. Não muda `resolved` (exige todos), mas qualquer tabela que reporte "regrediu N testes" ou distinga "resolveu mas regrediu" de "não resolveu" sai errada. O `--ignore=tests/_uranium_hidden` só protege a forma de arquivo oculto.

### R5 — Estratificação por dificuldade não é executável como decidida

Decisão 4 do prompt exige 12 tarefas estratificadas pelo tamanho do patch. Regra atual: baixa = 1 arquivo e menos de 30 linhas; média = até 3 arquivos; alta = 4 ou mais ([scripts/mine_tasks.py:83-90](../../scripts/mine_tasks.py#L83-L90)). Nos 90 candidatos minerados, 54 aceitos: 35 baixa, 18 média, **1 alta** (`mined-v1/*.json`). O emissor alterna faixas ([scripts/emit_task.py:160-168](../../scripts/emit_task.py#L160-L168)), mas não há de onde tirar tarefas altas. Além disso, `faixa` é gravada no `task.json` ([scripts/emit_task.py:109](../../scripts/emit_task.py#L109)) e **ignorada** por `TaskSpec` ([harness/taskspec.py:22-49](../../harness/taskspec.py#L22-L49)), então não chega ao `result.json`; `tasks/tomlkit-0001/task.json` nem tem o campo. A análise estratificada exigiria juntar manualmente.

### R6 — Tetos mudaram entre rodadas; rodadas não são comparáveis entre si

Sequência observada nos manifestos: 120k tokens/25 turnos, 120k/20, 300k/40, 400k/40, 1,2M/40, 3M/80 e de novo 1,2M/40. O `BACKLOG.md:25` ainda registra 400k. Qualquer agregação que misture rodadas mede o teto, como o próprio backlog reconhece para o piloto ([BACKLOG.md:18-23](../../BACKLOG.md#L18-L23)). Só `variancia`, `variancia-02`, `variancia-03` e a rodada de 11/09 compartilham 1,2M/40, e as três primeiras diferem entre si pelo prompt (antes/depois de `3ec3565`).

### R7 — Contagem de chamadas de ferramenta subestimada e instrumentação retroativa impossível

1.5, E2 a E4: ferramenta desconhecida, argumento inválido e chamadas além da oitava não geram evento `tool_call`. `cost.tool_calls` e a razão "tool calls por turno" do dossiê ([dossie-metodologico.html:584](../dossie-metodologico.html)) são pisos. E as 38 execuções antigas não têm tamanho de saída para `run_python`, `run_tests` e `replace_in_file`, então a análise de crescimento de contexto só pode usar as 4 de 11/09 ou dados novos.

### R8 — Parâmetros que mudam o braço `orchestration` sem deixar rastro

1.4, F9. `SEMANTIC_REVIEW` liga uma chamada de LLM e muda `is_valid`; não está no `.env.example` nem no manifesto. Duas coletas com valores diferentes seriam indistinguíveis pelo dado.

### R9 — Perda de execuções por erro de provedor quebra o pareamento

Na branch: 1 `RateLimitError` em `variancia-03` (single-agent rep01), 1 `ValidationError` em `variancia` (orchestration rep04), 1 `StructuredOutputError` em `pilot-01`, 2 erros 429 em `sonda-80turnos`. O par da repetição perdida não existe, e não há mecanismo de reexecução com a mesma semente (Fase 5, item 6). O dossiê diz "duas execuções perdidas para `engine_overloaded`" ([dossie-metodologico.html:488](../dossie-metodologico.html)); encontrei uma perda por 429 nas rodadas de variância.

### R10 — Isolamento de rede degrada em silêncio

Se `unshare` faltar ou falhar, o pytest roda com rede e `network_isolated: false` fica só registrado; nada recusa o resultado ([harness/pytest_runner.py:62-69,135](../../harness/pytest_runner.py#L62-L69)). Nos 4 resultados existentes o campo é `true` em todas as chamadas. Risco baixo hoje, alto se a coleta rodar em outra máquina.

### R11 — Discrepâncias menores que confundiriam um leitor atento

`diff.files_changed` conta só arquivos rastreados e `diff.changed_files` inclui não rastreados ([harness/gitutil.py:22-43](../../harness/gitutil.py#L22-L43)): `orchestration` · `sqlite-utils-0001` de 11/09 mostra `files_changed = 1` com dois nomes na lista (o agente criou `teste_transform.py` na raiz do repositório, fora da área protegida). `summary.json` de uma execução cortada por orçamento pode trazer `changed_files = []` enquanto o harness vê o diff ([src/arms/runner.py:213](../../src/arms/runner.py#L213) lê o estado do grafo, que não foi atualizado). `is_valid = true` com `stop_reason = budget: max_turns` em `variancia-02` rep04. Faixa de custo por execução observada: US$ 0,0037 a 0,1013; o dossiê diz 0,015 a 0,057.

### R12 — Reprodutibilidade da semente é best-effort

Já declarado no dossiê ([dossie-metodologico.html:731-733](../dossie-metodologico.html)). Confirmado nos dados: mesma tarefa, mesma semente (20260821), `single-agent`: 10, 9, 29, 14, 15, 14, 40 turnos em rodadas distintas. Limitação a declarar, não defeito.

---

## O que esta fase não conseguiu verificar

- Se algum `result.json` das rodadas de variância existiu e se perdeu, ou se nunca foi gerado. O relatório do piloto ([src/arms/pilot.py:70,107](../../src/arms/pilot.py#L70)) chama o harness, mas não encontrei `pilot.json` em nenhuma das duas fontes.
- A origem exata dos números de bytes lidos do dossiê (90.487 e 182.866).
- O conteúdo do `.env` real da máquina de coleta (não versionado; não lido).
- O PDF do dossiê citado no prompt não está em `docs/tcc/fontes/`; usei `docs/dossie-metodologico.html`, que é a fonte do PDF.

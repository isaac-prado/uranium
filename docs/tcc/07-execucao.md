# Execução das exigências E2 a E5

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · iniciado em 19 de setembro de 2026
Registro por item, no formato pedido em [EXIGENCIAS.md](tasks/EXIGENCIAS.md): diff resumido, teste que prova que funciona, e o que mudou em `docs/tcc/`. Escopo pré-aprovado pelo autor em 19/09/2026: E2, E3 itens 1 a 3, E5 itens 2, 4 e 5, esqueleto do `CLAUDE.md`. Branch `exigencias-e2-e5`, um commit por item. Nada aqui gasta crédito. E4, a implementação do E3.3 e os tetos ficam para decisão do autor.

Proibições respeitadas em todos os itens: detector de trapaça, oráculo, guarda de caminho e pino de provedor intocados.

---

## E2 — Equalizar o que não é arquitetura, e declarar o que é

Corrige F1, F2 e F8 (docs/tcc/01-inventario.md, seção 1.4) com teste de igualdade literal; registra F9 e F11 no manifesto; corrige as fragilidades de teste F13 e F10; declara F3 como parte da variável independente, sem corrigi-la.

### Diff resumido por arquivo

| Arquivo | O que mudou |
|---|---|
| [src/feedback.py](../../src/feedback.py) | Nova função `feedback_de_falha(report: TestReport) -> str`, que chama `suite_falhou(report.stdout_tail)`. É o ponto único de onde sai o texto "a suíte falhou" nos dois braços. `suite_falhou` continua existindo — o driver a usa também no modo de ablação `sumariza_falhas`. |
| [src/arms/driver.py](../../src/arms/driver.py) | `DriverPolicy` perde o campo `stderr_chars` (era o corte próprio de 4.000 caracteres, F2). `apos_turno` chama `feedback_de_falha(report)` no caminho normal, e só compõe texto próprio (via `suite_falhou`) no modo de ablação `sumariza_falhas`, que resume em vez de truncar. Docstrings da classe e do campo atualizadas para declarar que o truncamento passa a ser só o da ferramenta (`MAX_TOOL_OUTPUT_CHARS`, comum aos dois braços). |
| [src/agents/developer.py](../../src/agents/developer.py) | `_build_prompt`: o ramo "suíte falhou" passa a usar `feedback_de_falha(report)` em vez de montar `"A suíte falhou na tentativa anterior. Saída do pytest:" + report.stdout_tail` (F1/F2). O ramo `elif alterados: partes += [..., f"Arquivos já modificados: ..."]` foi removido inteiro (F8): com suíte verde e houve mudança, o developer recebe só a tarefa. |
| [src/graph.py](../../src/graph.py) | `route_after_intent_refiner`/`route_after_validator` passam a ler `config.MAX_CLARIFICATION_ITERATIONS`/`config.MAX_VALIDATION_ITERATIONS` como atributo do módulo `src.config` (import `from src import config`), em vez de `from src.config import X`. Sem essa mudança, o manifesto (que precisa ler o mesmo valor que o grafo usa de verdade) e o grafo teriam duas cópias independentes da constante, capazes de divergir sob `monkeypatch` — o comportamento não mudou, só a forma de ler. |
| [src/arms/runner.py](../../src/arms/runner.py) | `CHAVES_QUE_PODEM_DIFERIR` ganha `orchestration_policy`. `RunSpec` ganha o campo `orchestration_policy: dict \| None`, resolvido em `build_run_spec` por `_orchestration_policy()` (só para `arm == "orchestration"`, `None` para `single-agent`) com os cinco parâmetros de F9. Nova chave `shared_limits` no manifesto (função `_shared_limits`), com as oito constantes de F11, idêntica nos dois braços — inclui `list_files_max_results`, lido por introspecção do default de `src.tools.fs.list_files` para não duplicar o número, e `recursion_limit`, calculado por `_recursion_limit(max_turns)`, a mesma função agora usada em `run_arm` para invocar o grafo (antes era `max(8, spec.budget.max_turns * 4)` inline, um único lugar depois da mudança). `MANIFEST_VERSION` sobe de 1 para 2. |
| [.env.example](../../.env.example) | `SEMANTIC_REVIEW=true` documentado na seção "Workflow (braço orchestration)", com comentário de uma linha e referência à folga F9. |
| [tests/test_arm_parity.py](../../tests/test_arm_parity.py) | Ver testes novos abaixo. `test_so_a_topologia_difere` passa a iterar a união das chaves dos dois manifestos, não só as do single-agent (F13). `test_politica_vai_inteira_para_o_manifesto` perde `stderr_chars` do conjunto esperado. |
| [tests/test_arm_single_agent.py](../../tests/test_arm_single_agent.py) | `test_trunca_pelo_fim` (testava o corte próprio do driver) virou `test_nao_trunca_de_novo_por_conta_propria` (prova que o driver NÃO corta de novo o que a ferramenta já truncou). |

### Testes novos

Em `tests/test_arm_parity.py`:

- `TestManifesto.test_so_o_b_tem_politica_de_orchestration` — espelho de `test_so_o_a2_tem_politica_de_driver` para `orchestration_policy`.
- `TestManifestoRegistraOQueAfetaOOrchestration.test_shared_limits_e_igual_ao_valor_efetivo_dos_modulos` — `shared_limits` do manifesto bate com as constantes lidas direto dos módulos (`src.runtime`, `src.tools.base`, `src.tools.exec`).
- `TestManifestoRegistraOQueAfetaOOrchestration.test_mudar_max_validation_iterations_muda_o_manifesto`
- `TestManifestoRegistraOQueAfetaOOrchestration.test_mudar_max_clarification_iterations_muda_o_manifesto`
- `TestManifestoRegistraOQueAfetaOOrchestration.test_mudar_semantic_review_muda_o_manifesto`
- `TestManifestoRegistraOQueAfetaOOrchestration.test_mudar_structured_output_method_muda_o_manifesto`
- `TestManifestoRegistraOQueAfetaOOrchestration.test_mudar_structured_output_retries_muda_o_manifesto` — as cinco acima provam F9: mudar qualquer um dos cinco parâmetros (via `monkeypatch.setattr` no módulo `src.config` para os dois lidos no import, via `monkeypatch.setenv` para os três lidos do ambiente a cada chamada) muda `orchestration_policy` no manifesto.
- `TestManifestoRegistraOQueAfetaOOrchestration.test_manifest_version_subiu`
- `TestRuntimeIdentico.test_mesma_ordem_de_ferramentas` — F10: a ORDEM dos nomes de ferramenta é idêntica nos dois braços, não só o conjunto.
- `TestFeedbackDeProtocolo.test_mensagem_de_suite_falhou_e_a_mesma_byte_a_byte` (parametrizado: stdout curto e stdout acima de 8.000 caracteres) — F1/F2: o feedback do driver e o trecho embutido no prompt do developer são a mesma string, byte a byte, para o mesmo `TestReport` vermelho.
- `TestFeedbackDeProtocolo.test_verde_sem_mudanca_os_dois_dao_diff_vazio` — cenário "verde sem mudança": os dois terminam em `DIFF_VAZIO`.
- `TestMensagensDeProtocoloSaoUnicas.test_verde_com_mudanca_o_developer_recebe_so_a_tarefa` — F8: com suíte verde e houve mudança, o prompt do developer é exatamente `"Tarefa:\n" + intent_json`, sem `DIFF_VAZIO` nem "Arquivos já modificados".
- `TestMensagensDeProtocoloSaoUnicas.test_nenhuma_string_de_protocolo_fora_do_feedback` — nenhum dos textos que já divergiram uma vez ("A suíte falhou", "Saída do pytest", "Arquivos já modificados") pode voltar a existir como string solta em `developer.py`/`driver.py`.
- `TestMensagensDeProtocoloSaoUnicas.test_funcoes_publicas_de_feedback_conhecidas` — canário: se uma mensagem de protocolo nova entrar em `src/feedback.py`, este teste lembra de blindá-la também.

Em `tests/test_arm_single_agent.py`:

- `TestDriverDeterministico.test_nao_trunca_de_novo_por_conta_propria` — substitui o teste anterior de truncamento próprio; prova que o driver repassa `report.stdout_tail` sem cortar de novo.

### Resultado da suíte completa

```
.venv/bin/python -m pytest -q
2 failed, 440 passed in 95.66s (0:01:35)
```

As duas falhas são `tests/test_seed_repos.py::TestSuiteVerdeNoPontoDePartida::test_roda_inteira_e_passa[peewee]` e `tests/test_seed_repos.py::test_peewee_sem_alvo_declarado_coletaria_quase_nada`, ambas por ambiente: o `venv` do repo-semente `peewee` nesta máquina não coleta teste nenhum (`exit_code=5`, "nenhum teste coletado"), não por regressão. Confirmado rodando a mesma suíte com `git stash` (código anterior a este item): as mesmas duas falham, com o mesmo `exit_code=5`, antes de qualquer mudança do E2. Não são falha introduzida por este item, e corrigir o `venv` do peewee está fora do escopo de E2 (é infraestrutura de repo-semente, não paridade entre braços). `tests/test_arm_parity.py` sozinho: 52 passed.

### Declaração da política de contexto (F3)

**Não corrigida de propósito.** O braço `orchestration` reconstrói a lista de mensagens do `developer` do zero a cada entrada no nó — `mensagens: list[BaseMessage] = [SystemMessage(...), HumanMessage(...)]` em [src/agents/developer.py:60-63](../../src/agents/developer.py#L60-L63), sem herdar nada da chamada anterior ao mesmo nó. O braço `single-agent` faz o oposto: mantém uma única lista viva, `RunContext.conversation` ([src/runtime.py:47](../../src/runtime.py#L47)), que os dois nós do grafo (`single_agent`, `driver`) só acrescentam — nunca recriam — via `mensagens = ctx.conversation` em [src/arms/single_agent.py:58](../../src/arms/single_agent.py#L58) e `ctx.conversation.append(...)` em [src/arms/single_agent.py:105](../../src/arms/single_agent.py#L105).

Essa diferença é a estratégia de limpeza e reinjeção de contexto que Rangel (2025) apresenta, no CodeAir, como vantagem do paradigma ES 3.0 sobre um agente único que arrasta o histórico inteiro: **Rangel, G. A. (2025). CodeAir: A multi-agent orchestration framework for AI-assisted software development. *SSRN Electronic Journal*.** (referência extraída de `docs/tcc/fontes/TFG_ISAAC_DO_PRADO_ALMEIDA.pdf`, seção de referências, via `pdftotext`).

**Revista em 09/10/2026 (decisão 8): ver "Memória de trabalho do developer" abaixo; o que segue é o registro de 19/09.** Por isso ela é tratada como parte da variável independente (a topologia), não como defeito a equalizar — ao contrário de F1, F2 e F8, que eram descuido de implementação e não tinham nenhuma justificativa de desenho. O preço dessa reconstrução por ciclo é justamente o que a métrica 2 do estudo (custo computacional, `cost.tokens_total`/`cost.cost_usd`/`cost.llm_calls`, [docs/tcc/03-metricas.md:17](../03-metricas.md#L17)) precisa capturar: reconstruir o contexto do zero a cada ciclo de validação custa tokens que o `single-agent`, ao só acrescentar à conversa existente, não paga da mesma forma — e é exatamente essa troca (contexto limpo vs. contexto caro) que o estudo mede, não uma assimetria a remover.


## Índice dos demais itens (19/09/2026)

Cada item tem relatório próprio, no formato do EXIGENCIAS (diff resumido, teste que prova, impacto em docs), e um commit na branch `exigencias-e2-e5`.

| Item | Relatório | Commit | Resultado em uma linha |
|---|---|---|---|
| E1 (fechamento) | [06-contabilidade-contexto.md](06-contabilidade-contexto.md) | `59b0a91` | instrumentação `prompt_bytes` e script de contabilidade commitados |
| E2 | seção acima | `bc76693` | feedback idêntico nos dois braços, manifesto v2 com `orchestration_policy` e `shared_limits`, F3 declarada |
| E3 item 1 | [07-e3-1-mineracao.md](07-e3-1-mineracao.md) | `2a53466` | cinco repositórios (pygments e tqdm novos): 3 grandes, 2 médias, 55 pequenas verificadas por execução |
| E3 item 2 | [07-e3-2-faixa.md](07-e3-2-faixa.md) | `d47abda` | `faixa` do `task.json` ao `result.json`, schema v2 |
| E3 item 3 | [07-e3-3-breaking-change.md](07-e3-3-breaking-change.md) | `d7f0e8c` | relatório; recomendação de não implementar agora; seis decisões do autor |
| E5 item 1 (parcial) | [CLAUDE.md](../../CLAUDE.md) | `947a91d` | invariantes registradas; tetos marcados como não congelados até o E4 |
| E5 item 2 | [07-e5-2-reexecucao.md](07-e5-2-reexecucao.md) | `47ebeff` | reexecução com a mesma semente, `attempt` no manifesto, marca `PERDIDO` recusada pelo avaliador |
| E5 item 4 | [07-e5-4-analise.md](07-e5-4-analise.md) | `2ca5f58` | sete métricas com sinal e Wilcoxon exatos; portão G7 rodado sobre os 4 runs de 11/09 (versionados em `dados/runs-11-09/`) |
| E5 item 5 | [07-e5-5-docs.md](07-e5-5-docs.md) | `0156989` | README, projeto.md e src/agents/README.md sem arquitetura superada nem LangSmith |
| Escolha do modelo | [08-escolha-modelo.md](08-escolha-modelo.md) | `48f7490` | manter qwen3-coder na DeepInfra; reserva qwen3-coder-next na Parasail; protocolo do teste de aptidão |

Suíte do projeto ao fim do dia: 511 testes passando (`.venv/bin/python -m pytest -q`, relatório do E3.1).

### O que não foi feito, e por quê

- **E3 item 3 (implementação)** e **E4**: proibidos sem aprovação do autor.
- **E5 item 3** (validar as 12 tarefas): depende das tarefas escritas.
- **Tetos** no `CLAUDE.md`: dependem do E4.
- **Faixas grande e média com 4 tarefas cada**: a mineração verificada encontrou 3 grandes e 2 médias em cinco repositórios. Os repositórios com maior densidade de commits multi-arquivo (click, jinja, marshmallow, attrs) usam layout `src/` que o harness não instala; suportar isso (em `src/workspace.py` e `src/tools/exec.py`) é a alavanca mais barata para ampliar as faixas escassas e fica como item para decisão.

### Decisões que ficaram com o autor

1. Quais 12 tarefas, dado que grande e média não chegam a 4 cada (lista de candidatas em [07-e3-1-mineracao.md](07-e3-1-mineracao.md)); se vale ampliar a verificação (`--max-verificar-por-faixa`, `--desde`) ou suportar layout `src/`.
2. Implementar ou não a exclusão à la SWE-bench do E3.3, e as seis decisões listadas lá.
3. Definição de "resolvida por ambos" e tratamento de `stop_reason` nulo (E5.4).
4. Igualar `MAX_VALIDATION_ITERATIONS` ao critério do single-agent ou declarar como desenho (05-stack.md, seção 5).
5. Modelo e provedor (08-escolha-modelo.md) e a ordem para rodar o teste pago de aptidão.
6. Tetos (E4), depois de uma tarefa grande escrita e do teste de fumaça.

---

## Reconciliação com a `develop` (08/10/2026)

Entre 19/09 e 08/10 duas linhas de trabalho avançaram em paralelo: esta branch (`exigencias-e2-e5`, 13 commits de 19/09, nunca enviada) e a `develop` no GitHub (6 commits de 28/09, feitos em outra máquina: `598a61c`, `e863546`, `848661f`, `7068a55`, `f4c01a9`, `c2046fd`). As duas resolviam problemas em comum de formas diferentes. O merge da `develop` nesta branch teve conflito em cinco arquivos; a regra de resolução foi: **decisão de desenho tomada pelo autor em 28/09 entra; mecanismo já coberto por teste de paridade em 19/09 fica.**

### O que entrou da `develop`

- `ProviderError`, `is_provider_error`, `is_fatal_provider_error` e `root_provider_error` em `src/config.py`; `invoke_structured_raw` não retenta falha de provedor (o orquestrado tolerava 3 × 7 tentativas contra 7).
- `stop_reason` de run morto com prefixo `infra_error:` ou `interrupted:` e campo `lost` no `summary.json` (`src/arms/runner.py`, `LOST_PREFIXES`, `stop_reason_for`). Ctrl+C passa pelo `finally` e grava resumo.
- Coleta definitiva retomável: `src/arms/collection.py`, `scripts/run_collection.py`, regra única de tentativa válida em `harness/attempts.py`, análise operacional em `harness/analysis.py` + `scripts/analyze_collection.py`, com testes próprios.
- D6: o laço developer ↔ validator só termina por orçamento; `MAX_VALIDATION_ITERATIONS` deixa de existir e `MAX_SEMANTIC_REJECTIONS = 2` cobre só a reprovação semântica (`src/graph.py`, `src/agents/validator.py`, `src/state.py`, `.env.example`).
- D4: o developer recebe `issues`, `missing_criteria` e `suggestions` do revisor quando ele reprova com a suíte verde.
- `LLM_REQUEST_TIMEOUT` padrão 90 s; `BACKLOG.md` seções 6 a 8; `tests/fakes.py::erro_http`.

### O que ficou desta branch, e por quê

| Conflito | Resolução |
|---|---|
| `src/agents/developer.py` | Feedback de suíte vermelha vem de `src.feedback.feedback_de_falha` (E2), não de `DeterministicDriver().apos_turno` (develop): mesma paridade literal, mas a mensagem fica num módulo só e o nó de um braço não importa o operador do outro. Sem corte próprio de 4.000 caracteres: vale o da ferramenta, 8.000, premissa F2 aprovada em 19/09. "Arquivos já modificados" continua removido (F8). A moldura do parecer do revisor (D4) foi para `src/feedback.py::revisao_reprovada`, porque nenhum braço pode ter texto próprio de feedback (`CLAUDE.md`). |
| `src/graph.py` | Lógica de D6 da develop, lendo `config.MAX_SEMANTIC_REJECTIONS` como atributo do módulo (E2), para o manifesto e o grafo nunca lerem cópias diferentes. |
| `src/arms/runner.py` | Manifesto v3: `orchestration_policy` (E2) ganha `max_semantic_rejections` no lugar de `max_validation_iterations`; as chaves `structured_output` e `orchestration` que a develop acrescentou foram descartadas porque já estavam dentro de `orchestration_policy`. `shared_limits` e `attempt` mantidos. |
| `tests/test_pilot.py` | Os dois conjuntos de teste ficaram. O run perdido simulado passou a ser um 429 real (`erro_http(429)`), porque com a regra nova um `RuntimeError` genérico não é perda. |
| `README.md` | Listagem de `scripts/` com os dois conjuntos. |

### Regra única de perda (E5.2 e G5 depois do merge)

Perda = `lost: true` no `summary.json`, isto é, `stop_reason` em `infra_error:` ou `interrupted:`. `src/arms/pilot.py::detectar_perdidos` passou a usar essa regra (antes era qualquer `error:`), a mesma de `harness/attempts.py`. Corte por orçamento não é perda. Erro que não é de provedor (`error: ...`) **não é perda**: é bug do harness e hoje, na coleta, conta como run válido que não resolveu; o que fazer com ele é a decisão 14 de [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

### Testes

- Adaptados: `test_mudar_max_semantic_rejections_muda_o_manifesto` (era `max_validation_iterations`), `test_manifest_version_subiu` (3), `test_funcoes_publicas_de_feedback_conhecidas` (inclui `revisao_reprovada`), `test_feedback_de_suite_vermelha_e_literalmente_o_mesmo` (sem exigir corte de 4.000), `TestDeveloperRecebeARevisao` (sem "Arquivos já modificados", F8), `TestReexecucaoDeRunPerdido` e `TestCorteDeOrcamentoNaoEhPerda` (perda = 429/interrupção; `error:` do harness não é perda).
- Resultado da suíte completa após o merge: ver o commit do merge (`git log -1`).

### Impacto em docs

- [09-decisoes-do-autor.md](09-decisoes-do-autor.md): novo, com todas as decisões pendentes e as já tomadas.
- `CLAUDE.md`: regra de perda e teto do laço atualizados.
- A decisão 4 da lista de 19/09 (igualar `MAX_VALIDATION_ITERATIONS` ou declarar) está **resolvida** pela D6 de 28/09: igualada. [05-stack.md](05-stack.md) seção 5 e [01-inventario.md](01-inventario.md) F5 ficam como registro histórico.
- O `.env` desta máquina ainda tem `LLM_REQUEST_TIMEOUT=300` e precisa ser alinhado ao `.env.example` (90) quando a decisão 11 for tomada; `MAX_VALIDATION_ITERATIONS` no `.env`, se existir, passa a ser ignorado.

---

## Suporte a "src layout" nos repositórios-semente (08/10/2026, decisão 1(b))

A mineração ampliada de 08/10 (`mined-v3/`) esgotou o pré-filtro de média e grande nos cinco repositórios atuais. Os repositórios com maior densidade de candidato grande/média (jinja, marshmallow, attrs, click) têm o pacote em `src/<nome>/`, que um clone limpo não importa. O autor aprovou a opção (b) da decisão 1 ([09-decisoes-do-autor.md](09-decisoes-do-autor.md)).

### Mecanismo

`SeedRepoSpec.pythonpath` (`src/seeds.py`) declara os diretórios do workspace que precisam estar em `sys.path`. `scripts/setup_mirror.py` grava no venv do repositório um `uranium_src_layout.pth` (função pura `pth_line`) que, na partida de qualquer interpretador daquele venv, insere `<cwd>/<dir>` em `sys.path` se o diretório existir. Como todo ponto do harness que roda Python no workspace usa `cwd` = raiz do workspace e o interpretador do venv do repo (ferramentas do agente em `src/tools/exec.py`, avaliador em `harness/pytest_runner.py`, `validate_task.py`, `mine_tasks.py`), os dois braços e o oráculo passam a enxergar o mesmo pacote sem `pip install` por run, sem variável de ambiente e **sem tocar oráculo, avaliador, prompts, ferramentas ou guarda de caminho**. O `task.json` ganha o campo informativo `pythonpath`.

### Repositórios

| Repositório | `source_dir` | Suíte no HEAD (clone limpo, `setup_mirror.py --check`, 08/10) | Observação |
|---|---|---|---|
| jinja | `src/jinja2` | 911 passed, 3,7 s | `markupsafe` é dependência de runtime, pinada no venv |
| marshmallow | `src/marshmallow` | 1190 passed, 2,8 s | `norecursedirs` do pyproject continua valendo |
| attrs | `src/attr,src/attrs` | 1395 passed, 10 skipped, 1 xfailed, 12,7 s | lista explícita de arquivos: fora `tests/test_packaging.py` (exige metadados de pacote instalado) e `tests/test_forward_references.py` (o `conftest.py` do upstream o ignora abaixo do Python 3.14) |
| click | — | **adiado** | sem o `-m "not stress"` do `addopts` upstream (zerado por `-o addopts=` nos dois braços) a suíte passa de 10 min; `tests/test_deprecations.py` exige metadados de pacote. Resolver pede argumentos de pytest por repositório no oráculo, intocável sem aprovação |

### Testes

`tests/test_seed_repos.py::TestSrcLayout`: declaração dos três repos; os antigos sem `pythonpath`; a linha do `.pth` só insere diretório que existe (executada de verdade sob `tmp_path`); o venv de cada um tem o `.pth`; `run_python` (o mesmo caminho do agente) importa o pacote de dentro do workspace. `TestCatalogo` e `PISO_DE_COLETA` atualizados; `test_roda_inteira_e_passa` roda nos oito repositórios.

### Impacto em docs

- [09-decisoes-do-autor.md](09-decisoes-do-autor.md), decisão 1: (b) escolhida em 08/10; click pendente.
- `CLAUDE.md`: convenção do `.pth` registrada.


---

## E4 — Fumaça paga na tarefa grande (08/10/2026)

Relatório em [07-e4-fumaca.md](07-e4-fumaca.md): 4 células (`tomlkit-0002` grande e `tomlkit-0001` pequena × 2 braços), todas resolvidas, 0 perdidas, US$ 0,155; a grande foi cortada em `max_turns` nos dois braços com a correção no lugar. Instrumentação íntegra (duas análises concordam, contabilidade de contexto 0,0%). Fumaça B (DeepInfra, tomlkit-0004): perdida por 429 em cadeia; Novita saiu do modelo; Google e Alibaba aptos. Fumaça C (Google, 80 turnos, 4 M): zero perdas, tomlkit-0004 não resolvida por nenhum braço, cortada por turnos nos dois. Proposta: 80 turnos, 4 M tokens, 1.800 s, provedor Google. G6 verde (13 tarefas validadas, [10-tarefas.md](10-tarefas.md)); G4 e provedor aguardam o autor (seção 7 do relatório).

**Reversão (09/10/2026, à noite).** A checagem paga não mostrou melhora (0/7 contra 5/7, [07-e4-fumaca.md](07-e4-fumaca.md) seção 10) e o autor decidiu reverter: "faz mais sentido para o protótipo em si". `git revert` do commit `1ad6a07`, mantendo a correção de `tests/test_harness.py::TestFaixa`; `MANIFEST_VERSION` 5 para nenhum manifesto novo se confundir com os da checagem (v4). O developer recebe só a intent; a invariante foi reescrita no `CLAUDE.md`.


---

## Custo com chave própria do provedor (09/10/2026)

**Diff resumido.** `src/config.py: extract_call_metrics` lê `usage.is_byok` e `usage.cost_details.upstream_inference_cost`; `cost_usd` passa a ser o total pago (taxa do OpenRouter + custo do provedor quando BYOK; sem BYOK, só `usage.cost`, para não contar duas vezes). `LLMCallMetrics` ganha `cost_openrouter_usd`, `cost_upstream_usd` e `is_byok`. `src/telemetry.py` grava os três no `payload` do `llm_call` (esquema de evento inalterado). `harness/cost.py: aggregate_cost` acrescenta `byok_calls` ao `cost` do `result.json`; na coleta tem de ser igual a `llm_calls`.

**Teste que prova.** `tests/test_config.py::TestCustoComChavePropria` (BYOK soma os dois; sem BYOK não soma o upstream; resposta sem o campo deixa `is_byok` indefinido). Suíte: 592 passando.

**Impacto em docs.** Decisão 11 final em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md` (regra de custo e BYOK). Sem isso, a métrica de custo em dólares da coleta sairia zero.


---

## Memória de trabalho do developer (09/10/2026, decisão 8 revista)

**Por quê.** A reconstrução do contexto a cada ciclo (F3) fazia o developer do orquestrado voltar ao nó sem saber o que tinha feito: na fumaça D ele submeteu com a suíte verde, foi reprovado pelo revisor semântico, voltou sem memória e quebrou 29 testes ([07-e4-fumaca.md](07-e4-fumaca.md) seções 8 e 11, `dados/fumaca-09-10-d/` e `-f/`). O autor decidiu que o developer "tem que ter tudo nas mãos", sem acúmulo de transcrição: a orquestração cura o que volta.

**Diff resumido.**
- `src/feedback.py`: `memoria_de_trabalho(ciclos, diff)` e `MEMORIA_DIFF_MAX_CHARS = 20_000` (mesmo recorte do revisor). Só títulos são do harness; o conteúdo é o registro do próprio developer e o diff dele.
- `src/agents/developer.py`: `_registro_do_ciclo` monta, da própria conversa do ciclo, o registro determinístico (arquivos lidos, buscas, arquivos escritos, execuções de `run_python`, suítes com a primeira linha do resultado, turnos, motivo de parada, nota final). O prompt de reentrada é `Tarefa` → memória → feedback (ordem do single-agent: histórico antes da mensagem do driver). No primeiro ciclo o prompt é idêntico ao anterior. O registro é gravado sempre (evento `memory`), mesmo com a política desligada.
- `src/config.py`: `DEVELOPER_MEMORY` (`ledger` | `none`, validado no import); `src/state.py`: `developer_memory`; `src/arms/runner.py`: `orchestration_policy.developer_memory` e `developer_memory_diff_max_chars`, estado inicial com `developer_memory: []`, `MANIFEST_VERSION = 6`.
- Telemetria (`src/telemetry.py`, `harness/schema/event.schema.json`): eventos `intent` (o que o refinador entregou), `validation` (veredito do revisor, com `issues` e `missing_criteria`) e `memory`. Até aqui a telemetria não dizia por que o revisor reprovou um patch verde.
- `.env.example` e `.env`: `DEVELOPER_MEMORY=ledger`.

**Teste que prova.** `tests/test_nodes.py::TestDeveloperMemoriaDeTrabalho` (primeiro ciclo sem memória; registro determinístico e evento `memory`; segundo ciclo recebe memória e diff; memória antes do feedback; `none` reproduz 19/09), `::TestValidatorExecuta::test_veredito_do_revisor_vai_a_telemetria`, `::TestGrafoPontaAPonta` (eventos `intent` e `memory` no run inteiro), `tests/test_arm_parity.py::test_mudar_developer_memory_muda_o_manifesto`, `::test_manifest_version_subiu` (6), `::test_memoria_de_trabalho_so_tem_moldura`, canário de `src/feedback.py` atualizado; `tests/test_intent_refiner.py` ajustado ao evento novo. Suíte: 600 passando.

**Impacto em docs.** Decisão 8 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md) (decidida, com as opções e as palavras do autor); `CLAUDE.md` (invariante de F3 substituído pela memória de trabalho); [00-guia-etapas.md](00-guia-etapas.md) (nota de revisão). Para o texto: Método › Tratamentos descreve a memória como parte do tratamento orquestrado e deixa de citar a "limpeza e reinjeção de contexto" como traço do protótipo; Ameaças à validade registra que a política foi definida depois de fumaças de calibração e antes da coleta, e que as fumaças A a F rodaram com `developer_memory = none`.


---

## Teto de turnos por ciclo do developer (09/10/2026, decisão 25)

**Por quê.** Na fumaça G ([07-e4-fumaca.md](07-e4-fumaca.md) seção 12) o developer gastou os 120 turnos num só ciclo; a memória de trabalho (decisão 8) nunca entrou no prompt e o veredito do revisor, correto, chegou com o orçamento esgotado.

**Diff resumido.** `src/config.py`: `DEVELOPER_CYCLE_MAX_TURNS` (40; 0 desliga). `src/agents/developer.py`: ao bater o teto do ciclo, sai com `stop_reason = "cycle: max_turns_per_cycle (n >= teto)"`, sem `circuit_break`; a contagem de turnos do run continua no `BudgetTracker`. `src/agents/validator.py`: a reprovação semântica só incrementa `semantic_rejections` quando o developer submeteu por decisão própria (`stop_reason` não começa em `cycle:`). `src/graph.py`: documentação da rota (`cycle:` volta ao developer como qualquer rodada não válida). `src/arms/runner.py`: `final_stop_reason` (um `cycle:` final vira `concluiu`), chave `orchestration_policy.developer_cycle_max_turns`, `MANIFEST_VERSION = 7`. `.env.example` e `.env`: `DEVELOPER_CYCLE_MAX_TURNS=40`.

**Teste que prova.** `tests/test_nodes.py::TestDeveloperTetoPorCiclo` (volta no teto sem circuit break; 0 desliga; orçamento total prevalece; contagem do run continua), `::TestValidatorExecuta::test_reprovacao_no_ponto_de_checagem_nao_conta_para_o_teto`, `::TestRoteamento::test_teto_do_ciclo_nao_e_orcamento_e_volta_ao_developer`, `::TestGrafoPontaAPonta::test_ciclos_com_memoria_ate_resolver` (dois ciclos, memória e aviso de diff vazio no segundo prompt, run fecha pela validação), `tests/test_arm_parity.py::test_mudar_developer_cycle_max_turns_muda_o_manifesto`, `::test_stop_reason_final_nunca_e_cycle`, `::test_manifest_version_subiu` (7). Suíte: 609 passando.

**Impacto em docs.** Decisão 25 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md`. Para o texto: Método › Tratamentos (o orquestrado passa pelo validador a cada 40 turnos; o single-agent passa pela suíte sempre que para de agir); Ameaças à validade (parâmetro definido depois das fumaças A a G e antes da coleta).


---

## G4 — Tetos congelados (12/10/2026, decisão 12)

**Diff resumido.** `src/budget.py` (padrões 8.000.000 tokens, 3.600 s, 120 turnos, com a justificativa no comentário), `.env.example` e `.env` (mesmos valores), `CLAUDE.md` (seção "Tetos do run" passa de "NÃO CONGELADOS" aos valores e à data). Os parâmetros do orquestrado já estavam gravados (`DEVELOPER_MEMORY=ledger`, `DEVELOPER_CYCLE_MAX_TURNS=40`, `MAX_SEMANTIC_REJECTIONS=2`).

**Teste que prova.** `tests/test_telemetry.py` (`RunBudget.from_env` lê o ambiente; manifesto serializável) e `tests/test_arm_parity.py::test_orcamento_identico` (mesmo orçamento nos dois braços). A suíte inteira continua verde. Os números vêm de [07-e4-fumaca.md](07-e4-fumaca.md), seções 6 a 13, e de `dados/fumaca-*`.

**Impacto em docs.** Decisão 12 final em [09-decisoes-do-autor.md](09-decisoes-do-autor.md). Para o texto: Método › Procedimento (tetos, regra de calibração e as oito fumaças que a sustentam); Ameaças à validade (a tarefa grande `tomlkit-0004` não foi resolvida em nenhuma fumaça por nenhum braço; o teto de parede foi subido depois de um corte por latência do provedor, antes da coleta).


---

## Coleta definitiva — etapa 1, faixa grande (iniciada em 12/10/2026, 21:09)

**Comando.** `scripts/run_collection.py --tasks tasks/tomlkit-0002 tasks/tomlkit-0003 tasks/tomlkit-0004 --repetitions 3 --out runs/coleta --workers 1 --retry-delay 300 --max-attempts 5`, com o `.env` nos valores congelados (decisão 12) e `OPENROUTER_PROVIDER=DeepInfra` com chave própria. Manifesto da primeira célula (`runs/coleta/tomlkit-0002/single-agent/rep01/attempt01/manifest.json`): versão 7, orçamento 120 turnos / 8.000.000 tokens / 3.600 s, modelo `qwen/qwen3-coder`, provedor DeepInfra, semente da repetição 1 = 20260821.

**Ordem.** Repetição → tarefa → braço (`plan_cells`), single-agent primeiro no par. 18 células. As 10 tarefas médias e pequenas entram em seguida no mesmo diretório (coleta retomável por célula). Decisões 13 e 14 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

**Motivo da ordem.** O autor pediu a comparação do código gerado nas grandes antes de tudo. As repetições do desenho são a forma legítima de obter esse código; repetir fora da coleta até obter resolução seria escolher o resultado.

**Comparação do código gerado (a produzir ao fim da etapa).** Por célula e repetição: `patch.diff`, ocultos passados por teste (`oracle.f2p.failing_node_ids`), regressão visível, `quality` (MI e CC do código alterado), custo e turnos, e no orquestrado os eventos `validation` e `memory`. Relatório a escrever em `docs/tcc/11-coleta-grandes.md` com os dados versionados em `docs/tcc/dados/coleta/`.


---

## Coleta definitiva — etapa 2 e fechamento (12 e 13/10/2026)

**Execução.** Etapa 2 (`scripts/run_collection.py --repetitions 3 --out runs/coleta --workers 1 --retry-delay 300 --max-attempts 5`, todas as tarefas; as 18 células da etapa 1 já estavam concluídas e foram puladas) iniciada em 12/10 às 22:19. **A máquina reiniciou em 12/10 às 23:53** (`uptime -s`), matando o processo durante `sqlite-utils-0003/single-agent/rep01/attempt01` (146 eventos, US$ 0,08, sem `summary.json`). Retomada em 13/10 às 08:17 com o mesmo comando: pela regra única de `harness/attempts.py`, tentativa sem resumo é perdida, e a célula rodou como `attempt02` com a mesma semente (decisão 14 aplicada; `lost_attempts = 1`). Fechamento em 13/10 às 15:31: 78 de 78 células, 0 perdidas (`dados/coleta/collection.json`).

**Resultados.** [12-coleta-resultados.md](12-coleta-resultados.md). Análises salvas em `dados/coleta/analise-sete-metricas.{md,json}`, `analise-operacional.md`, `contabilidade-contexto.{md,json}`.

**Impacto em docs.** Resultados (as sete métricas), Discussão (revisor sem execução; custo do histórico persistente; faixa média), Ameaças à validade (interrupção por reinício, tratada pela regra de perda).


---

## Ablação do refinador e refinador v2 (14/10/2026, decisões 7/16 e 28)

**Diff resumido.** Ablação: `src/config.py: DEVELOPER_INPUT` (`intent` | `enunciado+intent`), `src/agents/developer.py::_build_prompt` (ramo da ablação: enunciado íntegro + "Intenção estruturada:" + intent), `src/arms/collection.py::plan_cells(arms=...)` e `scripts/run_collection.py --arms`, manifesto v8 (`orchestration_policy.developer_input`). Refinador v2: `src/config.py: INTENT_REFINER` (`v1` | `v2`), `src/agents/intent_refiner.py: SYSTEM_PROMPT_V2` e `_versao()`, `src/schemas/intent.py: StructuredIntentV2, V2_KEYS, intent_as_text`, `src/state.py::parse_intent` (reconhece v2), developer e validador usam `intent_as_text`, manifesto v9 (`orchestration_policy.intent_refiner`). `.env.example` e `CLAUDE.md` atualizados.

**Teste que prova.** `tests/test_collection.py::TestPlano` (um braço só; braço desconhecido recusado), `tests/test_nodes.py::TestDeveloperEntradaDaAblacao` (padrão só intent; ablação entrega o enunciado byte a byte como o driver), `tests/test_intent_v2.py` (markdown literal; v1 segue JSON; `parse_intent`; escolha de prompt e schema; developer e revisor recebem o mesmo texto), `tests/test_arm_parity.py` (manifesto 9, chaves `developer_input` e `intent_refiner`). Suíte: 627 passando.

**Impacto em docs.** Decisões 7/16 (ablação em curso), 27 (pendente) e 28 (decidida) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [15-refinador-analise.md](15-refinador-analise.md); `CLAUDE.md` (prompts: refinador v2 aprovado por escrito, coleta própria). Para o texto: Método › Tratamentos ganha o braço de ablação e o braço com refinador v2 como variantes do orquestrado, cada um com manifesto próprio; Discussão compara os três orquestrados contra o mesmo single-agent.


---

## Rodada 2: tarefas reconstruídas, revisor que executa, nota de ciclo (14/10/2026, decisões 27 e 29)

**Diff resumido.** `harness/taskspec.py` e `src/workspace.py` (`visible_deselect`), `src/tools/exec.py::run_pytest` (`--deselect` por node id, nos dois braços), `src/arms/runner.py` (`RunSpec.visible_deselect`, manifesto com a lista, chaves `review_execution` e `cycle_note`, `MANIFEST_VERSION = 10`), `src/arms/collection.py` (repassa da tarefa), `scripts/validate_task.py` (quinto portão com o runner do agente), `tasks/{pygments-0001,sqlite-utils-0002,tomlkit-0004}/task.json` (`visible_deselect` + motivo), `src/config.py` (`REVIEW_EXECUTION`, `CYCLE_NOTE`), `src/agents/validator.py` (`_executar_reproducao`, saídas no prompt e no evento `validation`), `src/agents/developer.py` (nota de ciclo), `src/feedback.py::NOTA_DE_CICLO`, `.env.example`, `CLAUDE.md`.

**Teste que prova.** `tests/test_rodada2.py` (task.json carrega a lista; `run_pytest` deseleciona e a suíte visível perde exatamente o teste; as três tarefas declaram lista e motivo; manifesto leva a lista igual nos dois braços; revisor `off` não executa, `on` executa só blocos Python e leva a saída ao prompt e ao evento; intent v1 não executa; nota de ciclo `on` pede sem ferramentas e entra na memória, `off` não pede, orçamento esgotado não pede; chaves novas mudam o manifesto; `NOTA_DE_CICLO` no canário de `src/feedback.py`). `scripts/validate_task.py` nas três tarefas com os cinco portões: ver `dados/coleta-r2/validate_task_r2.txt`. Suíte: 641 passando.

**Impacto em docs.** Decisões 27 e 29 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [14-tres-tarefas-decisao.md](14-tres-tarefas-decisao.md); `CLAUDE.md` (quinto portão e `visible_deselect`; políticas da rodada 2). Para o texto: Método › Tarefas (quinto portão e a correção das três), Método › Tratamentos (orquestrado da rodada 2 como variante com três componentes novos, cada um com chave no manifesto), Ameaças à validade (instrumento corrigido depois da rodada 1, com as células antigas versionadas).

---

## Correção do rootdir do pytest e schema v2 tolerante (14/10/2026, decisão 30)

**Diff resumido.** `src/tools/exec.py::run_pytest` (`--rootdir .`: sem isso o pytest sobe até o `pyproject.toml` do uranium, os node ids ganham o prefixo `runs/.../workspace/` e o `--deselect` da decisão 27 não casa), `src/arms/runner.py::_shared_limits` (`pytest_rootdir: "workspace"`), `src/schemas/intent.py::StructuredIntentV2._achatar_listas` (lista de listas e itens vazios em `reproduction`/`expected_outputs`/`constraints`/`open_questions`). Commit `4f4f80e`.

**Teste que prova.** `tests/test_rodada2.py::TestVisibleDeselect::test_deselect_vale_com_pyproject_acima_do_workspace` (workspace sob diretório com pyproject; a suíte perde exatamente o teste) e `test_manifesto_registra_o_rootdir`; `tests/test_intent_v2.py::TestSchemaV2::test_listas_aninhadas_e_vazias_sao_achatadas` e `test_item_que_nao_e_texto_continua_invalido`. Suíte: 645 verdes. Verificação no workspace real do run OR-v2 do pygments: suíte inteira `passed=5294 failed=0` com o golden deselecionado.

**Dados.** Rodada 2 interrompida às 16:45 com 19 células; pygments-0001 (rep01, rep02), sqlite-utils-0002 (rep01, rep02 em andamento) e tomlkit-0004 (rep01) movidas para `runs/coleta-r2-descartados/` (README), mais tomlkit-0003 rep01 (`error: StructuredOutputError`, 0 turnos). Fila retomada às 17:00. Ablação e v2 versionados em `dados/ablacao-refinador/` e `dados/refinador-v2/`.

**Impacto em docs.** [16-ablacao-e-v2.md](16-ablacao-e-v2.md) (novo); decisões 7, 16, 28 (resultado), 30 e 31 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md` (rootdir no quinto portão).

---

## Rodada 2: execução e fechamento (14/10/2026, decisões 27 e 29)

**Execução.** Orquestrado: `INTENT_REFINER=v2 REVIEW_EXECUTION=on CYCLE_NOTE=on DEVELOPER_INPUT=intent scripts/run_collection.py --arms orchestration --repetitions 3 --out runs/coleta-r2 --workers 1 --retry-delay 300 --max-attempts 5`, 14/10 14:23 a 16:45 (19 células) e, após a correção do rootdir (decisão 30), 16:50 a 21:00 (25 células, 5 refeitas). Single-agent nas três reconstruídas (`--arms single-agent --tasks tasks/pygments-0001 tasks/sqlite-utils-0002 tasks/tomlkit-0004`), 21:00 a 22:16. 48 células, 0 perdidas, 0 erros do harness depois da correção. `collection.json` mesclado das duas chamadas (`collection-orchestration.json` + `collection-single-agent.json`), sem chamada paga. Custo: OR US$ 4,72 (39 runs), SA US$ 3,81 (9 runs).

**Resultados.** [17-rodada-2.md](17-rodada-2.md). Análises em `dados/coleta-r2/analise-sete-metricas.{md,json}`, `apendice-metricas.md`, `analise-operacional.md`; raiz pareada `runs/coleta-r2-analise/` (OR da rodada 2 + SA da rodada 2 nas três reconstruídas e da coleta principal nas outras dez). Resumo: OR 23/39 runs (antes 17/39), SA pareado 23/39; por tarefa 7 × 8 (p = 0,69); negações 39 → 3; tempo até a solução pior para o OR (p = 0,125).

**Impacto em docs.** Resultados (rodada 2 ao lado da coleta principal), Discussão (sqlite-utils-0002: suíte verde cedo demais no single-agent; custo de parede do revisor que executa; faixa média), Ameaças à validade (single-agent pareado híbrido; 14 runs anteriores ao rootdir; oráculo do pygments mais estrito que o enunciado). Decisões 27 e 29 com resultado em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

---

## Rodada 3: revisor coerente e sem teto de reprovações (14/10/2026, decisão 32)

**Diff resumido.** `src/config.py` (`REVIEW_STRICT` on|off, padrão off; `MAX_SEMANTIC_REJECTIONS` aceita 0 = sem teto), `src/agents/validator.py` (com strict, revisão aprovada com `missing_criteria` é rebaixada a reprovada; `strict_coerced` no evento `validation`), `src/graph.py::route_after_validator` (teto 0 nunca encerra por reprovação), `src/arms/runner.py` (`orchestration_policy.review_strict`, manifesto v11), `.env.example`, `CLAUDE.md`.

**Teste que prova.** `tests/test_rodada2.py::TestRodada3RevisorCoerenteESemTeto` (rebaixa aprovação com critério faltando e conta a reprovação; não toca aprovação limpa nem reprovação; off reproduz a rodada 2; teto 0 nunca encerra; manifesto registra), `tests/test_arm_parity.py` (versão 11).

**Execução.** `INTENT_REFINER=v2 REVIEW_EXECUTION=on CYCLE_NOTE=on REVIEW_STRICT=on MAX_SEMANTIC_REJECTIONS=0 scripts/run_collection.py --arms orchestration --repetitions 3 --out runs/coleta-r3 --workers 1 --retry-delay 300 --max-attempts 5`, sementes da coleta principal. Single-agent de comparação: o mesmo pareado da rodada 2 (`runs/coleta-r2-analise/*/single-agent`).

**Impacto em docs.** Decisões 32 e 33 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); resultados em 18-rodada-3 (a escrever).

---

## Rodada 3: fechamento (15/10/2026, decisão 32)

**Execução.** 14/10 23:3x a 15/10 05:0x, 39 células, 0 perdidas, 0 erros do harness. Custo US$ 5,58, 41,1 M tokens (`dados/coleta-r3`). Raiz pareada `runs/coleta-r3-analise/` (orquestrado r3 + mesmo single-agent da rodada 2).

**Resultados.** [18-rodada-3.md](18-rodada-3.md): 19/39 (rodada 2: 23/39); 98 revisões, 76 reprovações, 58 de 221 blocos de reprodução quebrados por execução isolada; 7 aprovações com oráculo vermelho. Análises em `dados/coleta-r3/analise-sete-metricas.{md,json}` e `apendice-metricas.md`.

**Impacto em docs.** Resultados (três rodadas lado a lado, rodada 2 como configuração final), Discussão (revisor como gargalo nos dois sentidos; teto de reprovações como proteção contra falso negativo), decisão 34 pendente em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

---

## Rodada 4: planejador de sub-tarefas e execução acumulada (15/10/2026, decisões 33 e 34)

**Diff resumido.** `src/agents/planner.py` (nó novo: exploração só-leitura com teto de turnos, chamada estruturada `Plan`, fallback para plano de uma sub-tarefa, replanejamento que acrescenta sub-tarefas), `src/schemas/plan.py` (`Subtask`, `Plan`, `sanear`, estados), `src/agents/developer.py` (`_subtarefa`, `_revisao_da_subtarefa`, sub-tarefa no registro do ciclo), `src/agents/validator.py` (`SYSTEM_PROMPT_SUBTAREFA`, `_avancar_plano`, `_proxima_subtarefa`, `_executar_reproducao` com índices e modo `cumulative`), `src/feedback.py` (`subtarefa_atual`, `plano_em_andamento`, `SUBTAREFA_CONCLUIDA_NAO`, cabeçalho opcional em `revisao_reprovada`), `src/graph.py` (nó e rotas), `src/runtime.py` (ferramentas por papel: `bound_llm(tools=[...])`, `executar_tool_calls(permitidas=...)`), `src/telemetry.py` e `harness/schema/event.schema.json` (evento `plan`), `src/state.py`, `src/config.py` (`PLANNER`, `PLANNER_MAX_TURNS`, `PLANNER_MAX_SUBTASKS`, `PLANNER_MAX_REPLANS`, `SUBTASK_MAX_CYCLES`, `REVIEW_EXECUTION=cumulative`), `src/arms/runner.py` (política, manifesto v12, estado inicial).

**Teste que prova.** `tests/test_planner.py` (16 testes: schema e saneamento; planejador explora só com leitura e recusa escrita, teto de exploração, fallback, replanejamento; developer recebe a sub-tarefa com critérios e blocos copiados e o parecer; validador avança o plano, adia, replaneja uma vez, aprovação final encerra; execução acumulada; rotas e manifesto). Canário do feedback atualizado em `tests/test_arm_parity.py`.

**Execução.** Fumaça nas três tarefas grandes (1 repetição) antes dos 39 runs: `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=off scripts/run_collection.py --arms orchestration ...`.

**Fumaça (15/10/2026, `runs/fumaca-planejador`).** Primeira tentativa: a chamada estruturada devolveu `Plan()` vazio em 12 tokens; corrigido em `f01291c` (plano pedido em JSON na própria conversa; `subtasks` exige ao menos 1 item; `Replan` pode vir vazio). Segunda tentativa: tomlkit-0004 não resolvida, 0/7 (rodada 2: 5/7 em duas repetições); o planejador gastou 13 turnos e entregou 6 sub-tarefas coerentes (3 apontando `tomlkit/items.py`, que nenhum run anterior tocou), mas o developer ficou 82 turnos na sub-tarefa 1 (parsing de chaves pontilhadas), escreveu arquivos de depuração em `tomlkit/` no primeiro ciclo e quebrou 53 testes no segundo; sub-tarefa adiada, orçamento acabou na sub-tarefa 2. tomlkit-0002 interrompida no turno 11 por `infra_error: AuthenticationError 401 "API key expired"` (chave do OpenRouter expirada; `collection.log`); tomlkit-0003 não rodou. Retomada pendente de chave nova.

**Fumaça retomada (15/10/2026 10:12, chave nova do OpenRouter `sk-or-v1-45a...5e4`, BYOK confirmado).** tomlkit-0002 **resolvida** em 102 turnos (rodada 2: 1/3): plano de 5 sub-tarefas em 12 turnos de exploração (`api.py`+`items.py`, `container.py`, serialização, exemplos, regressão); sub-tarefa 1 feita no ciclo 1 (21 turnos), sub-tarefa 2 levou dois ciclos, revisão final aprovada no ciclo 3; US$ 0,14. tomlkit-0003 **resolvida** em 41 turnos (13 do planejador + 28 do developer), revisão final aprovada no primeiro ciclo com o plano ainda aberto; US$ 0,06. Com tomlkit-0004 0/7, a fumaça fecha 2/3 (rodada 2 nessas três, repetição 1: 2/3 também). Critério combinado com o autor atendido (0003 continua resolvendo, 0002 não piorou): rodada 4 lançada às 10:5x, `runs/coleta-r4`, 39 runs. Dados da fumaça em `dados/fumaca-planejador/`.

---

## Rodada 4: fechamento (15/10/2026, decisão 33)

**Execução.** 10:43 a 19:32, 39 células, 0 perdidas (1 tentativa perdida por provedor, refeita), US$ 5,67, 37,9 M tokens, 7,8 h de parede (`dados/coleta-r4`). Raiz pareada `runs/coleta-r4-analise/` (orquestrado r4 + mesmo single-agent da rodada 2).

**Resultados.** [20-rodada-4.md](20-rodada-4.md): 24/39 runs e 9/13 tarefas (SA 23/39 e 8/13; p = 1,0), grande 5/9, pygments 3/3, tomlkit-0002 2/3; tokens por run 2× a rodada 2; 3 cortes por parede atribuídos à latência do provedor (26 a 46 s por chamada entre 16:31 e 18:53); 13 de 186 sub-tarefas feitas, revisão de sub-tarefa reprova 84 %; 3 aprovações finais com oráculo vermelho. Análises em `dados/coleta-r4/analise-sete-metricas.{md,json}` e `apendice-metricas.md`.

**Impacto em docs.** Resultados (quatro rodadas lado a lado; rodada 4 como melhor resolução, rodada 2 como melhor custo), Discussão (o que o planejador entrega de fato: exploração e primeira fatia; esteira de sub-tarefas pouco usada; custo em tokens e parede), Ameaças à validade (latência do provedor; variância entre rodadas de uma repetição por tarefa), decisão 35 pendente em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

---

## Rodada 5: verificação determinística, trechos do planejador e planejador enxuto (15/10/2026, decisões 35 a 38)

**Diff resumido.** `src/verificacao.py` (novo: `normalizar`, `saida_contem`, `comparar_saidas`; estados `encontrada`, `nao_encontrada`, `nao_verificavel`), `src/agents/validator.py` (`_verificar_subtarefa`, `_esperadas_apontadas`, `_comparar_esperadas`, `REGRA_COMPARACAO` e `system_prompt_revisao`, modo `strict`, reaproveitamento da execução da revisão final na sub-tarefa; evento `validation` com `comparisons`, `deterministic`, `basis`), `src/agents/planner.py` (prompt com `{maximo}` e regras novas, `expected` no pedido do plano, `_guardar_leituras`, `plan.trechos`, `trechos_chars` no evento), `src/agents/developer.py` (`_trechos_da_subtarefa`; saídas esperadas apontadas no prompt), `src/feedback.py` (`COMPARACAO_DE_SAIDAS`, `comparacao_de_saidas`, `subtarefa_atual` com `esperadas` e `trechos`), `src/schemas/plan.py` (`Subtask.expected`, `sanear(n_esperadas=...)`, `caminho_normalizado`), `src/schemas/intent.py` (`_desescapar_quebras`; markdown com blocos e saídas numerados), `src/config.py` (`SUBTASK_CHECK`, `REVIEW_COMPARE`, `PLANNER_CONTEXT_MAX_CHARS`), `src/arms/runner.py` (manifesto v13, três chaves novas em `orchestration_policy`), `scripts/calibrar_comparacao.py` (novo), `.env.example`, `CLAUDE.md`.

**Teste que prova.** `tests/test_verificacao.py` (13 testes: normalização; `\n` escrito; reticências; o que vem depois de `#`; linhas não comparáveis; pedaço mínimo; bloco que não compilou; erro de execução não é "não verificável"); `tests/test_planner.py` (+11: sub-tarefa feita sem consultar o modelo e reaproveitando a execução da revisão final; saída ausente segura a sub-tarefa e o developer recebe a comparação; palavra do developer vale, teto do ciclo não; sem mudança não há feita; `advisory` leva comparação e regra ao revisor; `off` reproduz a rodada 4; `strict` reprova sozinho e consulta o revisor quando nada verificável falta; trechos guardados, entregues e cortados pelo teto; prompt do planejador com o teto e `expected`; saneamento de `expected`; manifesto); `tests/test_intent_v2.py` (+1 desescape; markdown numerado); `tests/test_arm_parity.py` (manifesto 13; canário do feedback com os três nomes novos). Suíte: 694 passando.

**Calibração offline.** `scripts/calibrar_comparacao.py` sobre as rodadas 2 a 4 (`dados/coleta-r5/calibracao-offline.txt`): a comparação como barreira dura derrubaria 4 dos 24 runs resolvidos da rodada 4; por isso `REVIEW_COMPARE=advisory` (decisão 35). Leituras do planejador e releituras do developer na rodada 4: `dados/coleta-r5/leituras-planejador-r4.txt` (decisão 37).

**Execução.** Fumaça nas três grandes (`runs/fumaca-r5`, 1 repetição, ordem tomlkit-0003, 0002, 0004; critério combinado: 0003 continua resolvendo e 0002 não piora), depois os 39 runs: `INTENT_REFINER=v2 REVIEW_EXECUTION=cumulative CYCLE_NOTE=on PLANNER=on PLANNER_MAX_TURNS=8 PLANNER_MAX_SUBTASKS=3 SUBTASK_CHECK=deterministic REVIEW_COMPARE=advisory PLANNER_CONTEXT_MAX_CHARS=16000 MAX_SEMANTIC_REJECTIONS=2 REVIEW_STRICT=off DEVELOPER_INPUT=intent scripts/run_collection.py --arms orchestration --repetitions 3 --out runs/coleta-r5 --workers 1 --retry-delay 300 --max-attempts 5`, sementes da coleta principal. Single-agent de comparação: o pareado da rodada 2 (`runs/coleta-r2-analise/*/single-agent`).

**Impacto em docs.** Decisões 35 a 38 e registro em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [21-rodada-5.md](21-rodada-5.md) (configuração e calibração; resultados a preencher no fechamento); `CLAUDE.md`; `.env.example`.

**Fumaça (15/10/2026, `runs/fumaca-r5`, dados em `dados/fumaca-r5/`).** tomlkit-0003 resolvida em 21 turnos (US$ 0,042; rodada 4: 41 turnos), tomlkit-0002 resolvida em 44 turnos (US$ 0,069; rodada 4: 102), tomlkit-0004 0/7 em 120 turnos (US$ 0,285), com os três estados do veredito determinístico e o avanço do plano registrados nos eventos ([21-rodada-5.md](21-rodada-5.md), §4). Rodada 5 lançada às 23:4x de 15/10 (`runs/coleta-r5`, 39 runs).

**Falsa partida e decisão 39 (16/10/2026).** Rodada lançada às 23:4x de 15/10 e parada às 00:2x de 16/10 no 5º run: a comparação exigia saídas esperadas que descrevem o comportamento atual e o developer desfazia a correção certa (attrs-0001). Correção: o planejador executa os blocos de reprodução no workspace intocado e as saídas esperadas já produzidas pelo código original saem de `expected` e de toda comparação (`src/agents/planner.py::_saidas_ja_produzidas`, `src/schemas/plan.py::sanear(excluir_esperadas)`, `src/agents/validator.py::_saidas_na_base`, linha nova em `src/feedback.py::comparacao_de_saidas`; manifesto v14, `orchestration_policy.expected_outputs_base_filter`). Testes: `tests/test_planner.py::TestSaidasQueOCodigoOriginalJaProduz` (+2; fixtures com saída esperada que muda com a correção). Runs apartados em `runs/coleta-r5-descartados/` (README); rodada relançada do zero em `runs/coleta-r5`.

**Fechamento da rodada 5 (16/10/2026).** Relançada 00:5x (manifesto v14); queda de energia às 06:29 com 29 células fechadas, célula em andamento refeita com a mesma semente (attempt02), coleta retomada 08:0x e fechada 10:4x; 39 células, US$ 5,61, 42,1 M tokens, 3,4 h. Resultado em [21-rodada-5.md](21-rodada-5.md) §5: 18/39 runs e 6/13 tarefas (rodada 4: 24/39 e 9/13), 7 aprovações finais com oráculo vermelho, 33 das 37 sub-tarefas feitas pela palavra do developer. Análises em `dados/coleta-r5/analise-sete-metricas.{md,json}` e `apendice-metricas.md`; raiz pareada `runs/coleta-r5-analise/`.

**Impacto em docs.** Resultados (cinco rodadas lado a lado; rodada 5 como resultado negativo informativo: a verificação determinística depende de saídas esperadas literais, raras nos enunciados; a regra "não verificável não reprova" deslocou o erro do revisor para aprovações indevidas), Discussão, Ameaças à validade (variância de uma repetição por tarefa entre rodadas), decisão pendente do autor sobre configuração final e segundo modelo em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

---

## Rodada 6: veredito híbrido, revisor sem leniência e bloco que não compila fora da evidência (16/10/2026, decisões 40 a 42)

**Diff resumido.** `src/agents/validator.py` (`SUBTASK_CHECK=hybrid` em `_verificar_subtarefa`, que devolve veredito None quando nada é verificável, e `_revisar_subtarefa_pelo_modelo`, a revisão de sub-tarefa da rodada 4 extraída de `_avancar_plano` e usada pelos modos `llm` e `hybrid`, com `basis="revisao_do_modelo"` no segundo; `system_prompt_revisao` só acrescenta `REGRA_COMPARACAO` em `advisory` e `strict`; `_blocos_que_nao_compilam` e `BLOCO_NAO_COMPILA` em `_executar_reproducao`, com o bloco que não compila fora da cadeia acumulada e marcado `executado=False, nao_compila=True`), `src/config.py` (`SUBTASK_CHECK` ganha `hybrid`, `REVIEW_COMPARE` ganha `neutral`, `REPRODUCTION_COMPILE_CHECK`), `src/arms/runner.py` (manifesto v15, `orchestration_policy.reproduction_compile_check`), `.env.example`, `CLAUDE.md`.

**Teste que prova.** `tests/test_planner.py::TestRodada6` (+6: híbrido decide pela comparação sem o modelo quando há saída verificável; sem saída verificável consulta o revisor de sub-tarefa, a palavra do developer não fecha, "feita" pelo modelo avança, aprovação com critério faltando não fecha; suíte vermelha não consulta o modelo; `neutral` leva as linhas sem a regra e `REVIEW_STRICT=on` rebaixa a aprovação contraditória; bloco que não compila sai da cadeia, é rotulado e a comparação o ignora, com o comportamento da rodada 5 reproduzido com a chave em `off`; manifesto), `tests/test_arm_parity.py` e `tests/test_rodada2.py` (manifesto 15). Suíte: ver fechamento.

**Execução.** Fumaça em `runs/fumaca-r6` (tomlkit-0003, tomlkit-0001, sqlite-utils-0003; 1 repetição), depois os 39 runs em `runs/coleta-r6` com o comando registrado em [22-rodada-6.md](22-rodada-6.md) §1. Single-agent de comparação: o pareado da rodada 2.

**Impacto em docs.** Decisões 40 a 42 e registro em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [22-rodada-6.md](22-rodada-6.md); [21-rodada-5.md](21-rodada-5.md) §5.3 (decisão do autor); `CLAUDE.md`; `.env.example`.

**Fumaça 1 (16/10/2026 14:05 a 14:26, `runs/fumaca-r6`, dados em `dados/fumaca-r6/`, US$ 0,63): critério não atendido.** tomlkit-0003 0/1 em 120 turnos (bloco de reprodução corrompido pelo refinador; o revisor citou o rótulo "não compila" como motivo em 8 de 8 reprovações e o developer reverteu a correção certa, idêntica à da rodada 5), tomlkit-0001 resolvida em 38, sqlite-utils-0003 0/12 (9 "NÃO encontrada" falsos por revisão: saídas apontadas por sub-tarefa sem bloco e por blocos de shell). Correções em `src/agents/validator.py` (`_evidencias`: bloco não executado fora dos prompts de revisão; `neutral` só com linhas encontrada / NÃO encontrada; `_comparar_esperadas` por sub-tarefa) e `src/verificacao.py` (bloco do conjunto que não rodou → saída que falta é não verificável); decisão 43 (correção do executor, para o autor confirmar); +2 testes em `TestRodada6`; suíte 704 passando. Detalhe em [22-rodada-6.md](22-rodada-6.md) §3.1.

**Fumaça 2 (14:32 a 14:54, `runs/fumaca-r6b`, dados em `dados/fumaca-r6b/`, US$ 0,42): 3 de 3 resolvidas.** tomlkit-0003 em 20 turnos, tomlkit-0001 em 27, sqlite-utils-0003 12/12 no corte de orçamento (CLI corrigida no ciclo 4; a comparação seguiu dizendo "saída 5 NÃO encontrada" porque nenhum bloco da sub-tarefa exercita a CLI: limitação residual registrada em §3.2). Rodada 6 lançada às 14:55 em `runs/coleta-r6`.

**Fechamento da rodada 6 (16/10/2026 18:45).** 39 células, 0 perdidas; o fechamento do VSCode às 16:31 matou o processo com 15 células fechadas, a célula em andamento (peewee-0002 rep02) ficou sem `summary.json` e foi refeita como attempt02 com a mesma semente, coleta retomada desacoplada do editor. Resultado em [22-rodada-6.md](22-rodada-6.md) §5: **19/39 runs e 6/13 tarefas** (rodada 5: 18/39 e 6/13; rodada 4: 24/39 e 9/13; SA 23/39 e 8/13; p = 0,69), grande 4/9, média 4/12, pequena 11/18; US$ 5,97, 46,3 M tokens, 1,30 M tokens por run (o dobro da rodada 5), 16 cortes por orçamento; 4 aprovações finais erradas (rodada 5: 7), 3 coerções, 91 vereditos de sub-tarefa (37 comparação, 24 revisão do modelo, 30 suíte vermelha). Análises em `dados/coleta-r6/analise-sete-metricas.{md,json}` e `apendice-metricas.md`; raiz pareada `runs/coleta-r6-analise/`.

**Impacto em docs.** Resultados (seis rodadas lado a lado; rodada 4 como configuração final do orquestrado; rodadas 5 e 6 como resultados negativos: saídas esperadas do enunciado não são oráculo literal, e o freio ao developer custa turnos sem devolver resolução), Discussão, Ameaças à validade (variância entre rodadas com uma repetição por tarefa; imprecisão literal dos enunciados), decisões pendentes do autor (configuração final, segundo modelo, confirmação da 43) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

---

## Rodada 7: teto de um ciclo por sub-tarefa, blocos que não compilam fora da evidência e blocos de linha de comando executados (22/10/2026, decisão 44)

**Diff resumido.** `src/config.py` (`REPRODUCTION_SHELL`), `src/agents/validator.py` (`_comando_shell`: reconhece bloco de reprodução em linha de comando, com ou sem `$ `, só Python do venv da tarefa ou script de console instalado nele, sem operadores de shell; `_executar_comandos`: roda cada comando como processo no workspace com a guarda de arquivo protegido do `run_python`; `_executar_reproducao` trata o bloco de comando como executado, `shell: true`, fora da cadeia acumulada), `src/arms/runner.py` (manifesto v16, `orchestration_policy.reproduction_shell`), `.env.example`, `CLAUDE.md`. `SUBTASK_MAX_CYCLES=1` e `REPRODUCTION_COMPILE_CHECK=on` são chaves já existentes.

**Teste que prova.** `tests/test_planner.py::TestRodada7` (+4: reconhecimento só de programas do venv e sem operadores, inclusive `;` dentro de aspas; bloco de comando roda fora da cadeia e entra na comparação, com a rodada 6 reproduzida com a chave em `off`; comando que falha registra `exit` sem derrubar; manifesto), `tests/test_arm_parity.py` e `tests/test_rodada2.py` (manifesto 16). Suíte: ver fechamento.

**Execução.** Autor: "PODE IR!" (22/10/2026). Fumaça em `runs/fumaca-r7` das 19:42 às 19:57 (US$ 0,44; [dados/fumaca-r7/](dados/fumaca-r7/)): 1 de 3 resolvida (tomlkit-0003 em 44 turnos), mas os três mecanismos confirmados nos eventos: sub-tarefas 4 e 5 da peewee-0002 adiadas após um ciclo e 3 de 6 ocultos passando (habitual 0 de 6); bloco de CLI da sqlite-utils-0003 executado como processo (`shell: true`) com a saída na revisão; bloco que não compila fora da evidência na tomlkit-0003; `tokens_cached` em 88,6 a 94,3 %. Detalhe em [23-rodada-7.md](23-rodada-7.md) §3. Coleta de 39 runs lançada às 19:58 em `runs/coleta-r7`, desacoplada do editor. **Fechada às 22:26 (2 h 28): 23/39 runs e 9/13 tarefas, igual à rodada 4 em tarefas (24/39, 9/13); grande 4/9 (rodada 4: 5/9), média 6/12, pequena 13/18; US$ 4,37; 10 cortes; 6 aprovações erradas; cache gravado 90,7 %. Não atinge o critério de decisiva; a regra da decisão 45 aponta a rodada 4 para a replicação, pendente do autor.** Dados em [dados/coleta-r7/](dados/coleta-r7/); leitura em [23-rodada-7.md](23-rodada-7.md) §4. Dois runs morreram com 502 da DeepInfra devolvido no corpo de uma resposta 200 (`ValueError` do LangChain) e saíram como `error:` em vez de perda: `src/config.py::openrouter_error_body` passa a reconhecer esse corpo em `is_provider_error` e `is_fatal_provider_error` (teste `tests/test_structured_llm.py::TestFalhaDeInfraestrutura::test_erro_do_provedor_no_corpo_da_resposta_200_e_infra`); reclassificação e reexecução dos dois pendentes do autor. `scripts/resumo_rodada.py` novo (desfechos, cortes, aprovações erradas e mecanismos por coleta). Achado para o autor: em peewee-0002 rep02 um `exec_test.py` criado por código em `run_python` fez a guarda recusar 16 execuções do developer e 28 do validador até o fim do run, porque `git checkout` não remove arquivo novo ([23-rodada-7.md](23-rodada-7.md) §4.4; guarda intocável, correção pendente).

**Impacto em docs.** Decisões 44 e 45 e registro em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [23-rodada-7.md](23-rodada-7.md); [22-rodada-6.md](22-rodada-6.md) §5.3 (decisão do autor); [08-escolha-modelo.md](08-escolha-modelo.md) §10 e §10.1; `CLAUDE.md`; `.env.example`.

## Telemetria: tokens em cache por chamada (22/10/2026, decisão 46)

**Motivo.** A pergunta do autor "estamos rodando com ou sem cache?" só tinha resposta por inferência: a fração do prompt cobrada como leitura em cache era deduzida do custo pago contra o preço de tabela ([08-escolha-modelo.md](08-escolha-modelo.md) §10). O OpenRouter devolve o número em `usage.prompt_tokens_details.cached_tokens`, no mesmo objeto de onde já saem `is_byok` e `cost_details`. O autor aprovou por escrito gravar o campo ("Com certeza vale a pena executar agora a gravação dos tokens em cache no llm_call").

**Diff resumido.** `src/config.py: LLMCallMetrics.tokens_cached` e `extract_call_metrics` lendo `prompt_tokens_details.cached_tokens` (zero quando ausente); `src/telemetry.py`: `payload.tokens_cached` em cada `llm_call` (envelope do evento inalterado, `harness/schema/event.schema.json` não muda), `Totals.tokens_cached` acumulado dos `llm_call` (vai ao `summary.json` e ao `run_end`), `aggregate_cost` com `tokens_cached`; `harness/cost.py: aggregate_cost` idem (reimplementação independente do avaliador), `cost.tokens_cached` no `result.json` e em `harness/schema/result.schema.json` (opcional, para não invalidar os `result.json` anteriores). Scripts novos: `scripts/cache_probe.py` (duas chamadas com o mesmo prefixo no provedor pinado, imprime o `usage` cru) e `scripts/cache_fraction.py` (fração gravada e fração inferida por coleta). Nenhum prompt, ferramenta, teto ou chave de manifesto muda: os dois braços continuam idênticos, e o campo é só observação.

**Teste que prova.** `tests/test_config.py::TestTokensEmCache` (+2: lê `cached_tokens`; ausência, `prompt_tokens_details` sem o campo ou nulo dão zero), `tests/test_telemetry.py` (payload e totais com `tokens_cached`; reagregação do arquivo bate com os totais), `tests/test_harness.py::TestAgregacao::test_custo` (soma só dos `llm_call`, lida do payload). Suíte: 710 testes passando.

**Sonda paga (US$ 0,0023).** `scripts/cache_probe.py` no `qwen/qwen3-coder` pinado na DeepInfra, 22/10/2026 ([dados/sondagens/cache-deepinfra-2026-10-22.txt](dados/sondagens/cache-deepinfra-2026-10-22.txt)): 1ª chamada 5.695 tokens de prompt, `cached_tokens: 0`, custo igual ao preço cheio; 2ª chamada com o mesmo prefixo, 5.696 de prompt e `cached_tokens: 5.664`, custo igual a 32 tokens a US$ 0,30/M mais 5.664 a US$ 0,10/M. O campo chega, a extração lê, e o preço de leitura em cache da DeepInfra é confirmado pelo custo cobrado.

**Fração em cache das coletas anteriores (inferida, porque o campo não existia).** `scripts/cache_fraction.py` sobre os eventos ([dados/sondagens/fracao-cache-por-coleta-2026-10-22.txt](dados/sondagens/fracao-cache-por-coleta-2026-10-22.txt)): single-agent pareado 95,4 %, orquestrado rodada 6 92,4 %, rodada 5 91,5 %, rodada 4 82,5 %. O orquestrado aproveita menos cache porque cada troca de nó e cada ciclo do developer (memória de trabalho e sub-tarefa atualizadas) muda o prefixo; o single-agent só acrescenta. Leitura e consequência para a projeção da replicação em [08-escolha-modelo.md](08-escolha-modelo.md) §10.2.

**Impacto em docs.** Decisão 46 e registro em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [08-escolha-modelo.md](08-escolha-modelo.md) §10.2; [23-rodada-7.md](23-rodada-7.md) §2 (a rodada 7 é a primeira coleta com o campo gravado); `CLAUDE.md`.

## Guarda da execução: arquivo protegido novo é apagado ao recusar (22/10/2026, decisão 47)

**Diff resumido.** `src/tools/exec.py`: `reverter_protegidos(ws, antes)` (rastreado → `git checkout`; não rastreado → apagado; devolve só o que a execução acrescentou em relação à foto `antes`) e `run_python` fotografa `ws.protected_touched()` antes de rodar o trecho; `src/agents/validator.py::_executar_comandos` usa o mesmo helper no lugar da cópia local do `git checkout`. Guarda de caminho (`DEFAULT_PROTECTED_GLOBS`, `src/workspace.py`) inalterada; mensagem `RECUSADO` inalterada. Os dois braços compartilham `run_python`, então a mudança é simétrica.

**Teste que prova.** `tests/test_tools.py::TestGuardaDaExecucaoRestauraArquivoNovo` (+3: arquivo novo `rascunho_test.py` apagado e a execução seguinte aceita; `tests/test_items.py` alterado por código volta ao commit-base; comando do validador com a mesma guarda). Guardas existentes (`test_nodes`, `test_oracle_contract`, `TestRodada7`) continuam passando.

**Motivo.** peewee-0002 rep02 da rodada 7: `exec_test.py` criado por código em `run_python`; 16 execuções do developer e 28 do validador recusadas até o fim ([23-rodada-7.md](23-rodada-7.md) §4.4). Decisão 47 em [09-decisoes-do-autor.md](09-decisoes-do-autor.md).

## Rodada 8: blocos de reprodução consertados pelo enunciado e saída esperada amarrada ao bloco (22/10/2026, decisão 48)

**Diff resumido.** `src/enunciado.py` (novo: `blocos`, `blocos_python`, `sem_cercas`, `compila`, `similaridade`, `bloco_mais_parecido`, `reparar_blocos`, `pares_esperados`, `esperado_do_bloco`, `comparar_bloco`); `src/config.py` (`REPRODUCTION_SOURCE` intent|statement, `BLOCK_EXPECTED` off|statement); `src/agents/validator.py` (`_executar_reproducao` conserta os blocos pelo `raw_request` antes da checagem de compilação e, por bloco executado, grava `fonte`, `esperado_enunciado` e `comparacao_enunciado`; `_build_review_prompt` e `_build_subtask_review_prompt` acrescentam `COMPARACAO_POR_BLOCO` com as linhas por bloco); `src/feedback.py` (`COMPARACAO_POR_BLOCO`, `comparacao_por_bloco`); `src/arms/runner.py` (`MANIFEST_VERSION = 17`, chaves `reproduction_source`, `block_expected`); `.env.example`. Prompts (`src/prompts.py`) inalterados; o developer continua recebendo só a intent.

**Teste que prova.** `tests/test_enunciado.py` (+8: cerca removida; similaridade; bloco deturpado trocado pelo do enunciado, cerca sem troca, sem parecido fica; pareamento ignora "Saída hoje"; comparação linha a linha; enunciados reais de tomlkit-0002, tomlkit-0003, attrs-0001 e sqlite-utils-0003), `tests/test_planner.py::TestRodada8` (+3: bloco que não compilava roda com o texto do enunciado e ganha `fonte`/`comparacao_enunciado`; revisor final e de sub-tarefa recebem as linhas por bloco, sem regra, e nada com a chave em `off`; manifesto 17), `tests/test_arm_parity.py` e `tests/test_rodada2.py` (manifesto 17).

**Execução.** Só fumaças, por decisão do autor (saldo da DeepInfra ≈ US$ 4,7): `runs/fumaca-r8`, 7 tarefas × 1 repetição mais a 2ª repetição da tomlkit-0002, lançadas em 22/10/2026 às 23:29 e fechadas às 23:51 (US$ 0,82): **5 de 8 resolvidas, 3 cortes por orçamento, 0 aprovações erradas** (as mesmas 7 tarefas na rodada 7: 13/21, 5 aprovações erradas, 4 cortes); o revisor citou as linhas esperadas em 9 de 14 reprovações e só aprovou com todas encontradas; nenhuma cópia precisou de conserto nos 8 runs. Leitura e tabela em [24-rodada-8.md](24-rodada-8.md) §3; dados em [dados/fumaca-r8/](dados/fumaca-r8/). Os 39 runs aguardam crédito (saldo ≈ US$ 3,9).

**Impacto em docs.** Decisão 48 e registro em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [24-rodada-8.md](24-rodada-8.md) (novo); `CLAUDE.md`; `.env.example`.

## Rodada 8: comparação por exemplo do enunciado e modo guardado `strict` (23/10/2026, decisão 48, complemento)

**Diff resumido.** `src/enunciado.py`: `exemplo_do_bloco` (bloco da intent → exemplo Python do enunciado de que é cópia ou pedaço, por parecença ou contenção, entre todos os exemplos), `esperado_do_exemplo`, `anotar_comparacoes` (agrega os blocos de um mesmo exemplo e grava `exemplo`, `blocos_do_exemplo`, `esperado_enunciado`, `comparacao_enunciado` na última execução do exemplo), `execucao_terminou_bem` (`exit≠0`, `RECUSADO`, `TIMEOUT` → "não verificável"); `src/agents/validator.py`: `_executar_reproducao` chama `anotar_comparacoes` após o laço; `_linhas_nao_encontradas` e o rebaixamento em `BLOCK_EXPECTED=strict` ao lado da coerção do `REVIEW_STRICT` (`strict_coerced`); `src/feedback.py::comparacao_por_bloco` escreve "exemplo k do enunciado (blocos a a b)"; `src/config.py`: modo `strict` em `BLOCK_EXPECTED_MODES`. `scripts/calibrar_por_exemplo.py` (novo). Manifesto continua v17 (mesmas chaves; o valor `strict` é registrado em `block_expected`).

**Teste que prova.** `tests/test_enunciado.py::TestExemploFatiado` (+3: pedaços de um exemplo comparados juntos; bloco de exemplo sem saída esperada não é pareado; execução com `exit=1` ou `RECUSADO` vira não verificável), `tests/test_planner.py::TestRodada8Strict` (+3: aprovação contra linha NÃO encontrada é rebaixada com as linhas como motivo e `strict_coerced`; com todas encontradas a aprovação fica; em `statement` a linha só informa). Suíte completa verde.

**Calibração.** [24-rodada-8.md](24-rodada-8.md) §5: em 164 runs gravados a barreira derrubaria 0 resolvidos, pegaria 2 aprovações erradas e deixaria escapar 15, que nenhum exemplo do enunciado exercita.

**Impacto em docs.** [24-rodada-8.md](24-rodada-8.md) §2, §3 e §5; decisão 48 (complemento) e registro em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md`; `.env.example`.

## Rodada 8: fumaça em `strict` e lançamento dos 39 runs (23/10/2026, decisão 48)

**O que rodou.** Fumaça de 2 células em `BLOCK_EXPECTED=strict` (`runs/fumaca-r8-strict`, US$ 0,36, dados em [dados/fumaca-r8-strict/](dados/fumaca-r8-strict/)): sqlite-utils-0003 resolvida (12/12, 0 regressões), tomlkit-0002 orçamento com o teste oculto passando e 2 módulos de teste sem importar (developer reescreveu `api.py` com `write_file`). A comparação por exemplo do enunciado apareceu nos eventos e nas reprovações; `strict_coerced` não disparou. Com isso, os 39 runs foram lançados às 08:06 em `runs/coleta-r8` (manifesto v17, `block_expected: strict`).

**Diff resumido.** Só código de medição: `scripts/subtarefa_suite_vermelha.py` (novo; conta, por coleta, sub-tarefas aprovadas com a suíte visível vermelha, porque em `SUBTASK_CHECK=llm` o revisor de sub-tarefa não recebe o resultado da suíte). Nenhuma mudança em `src/`.

**Teste que prova.** Suíte completa verde (732) antes do lançamento; o manifesto do primeiro run confere a política.

**Impacto em docs.** [24-rodada-8.md](24-rodada-8.md) §3.1 e §4; decisão 48 (decidido em 23/10) e registro (fumaça `strict`, lançamento) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md`.

## Decisão 49: workspace só com o commit-base, caixa de areia e regra C8 (27/10/2026)

**Diff resumido.** `src/workspace.py`: `materialize` troca `git clone --shared` + `checkout` por `git init` + `fetch --depth 1 file://<espelho> <commit-base>` (`uploadpack.allowAnySHA1InWant`) + `checkout --detach FETCH_HEAD`; constante `WORKSPACE_HISTORY`. `src/tools/exec.py`: `SANDBOX`, `sandbox_mode`, `_prefixos_do_python`, `envolver_na_caixa` (argv do bubblewrap), `executar_isolado` (usado por `run_pytest` e `run_python`); `src/agents/validator.py::_executar_comandos` passa a usar `executar_isolado`. `harness/cheat.py`: `mirror_for`, `_c8_codigo_do_futuro`, `detect(..., mirror=, base_commit=)`; `harness/evaluate.py` passa o espelho e o commit-base. `src/arms/runner.py`: manifesto v18, `shared_limits.workspace_history` e `shared_limits.sandbox`. `scripts/varredura_vazamento_git.py` (novo). Testes que aplicavam a correção upstream com `git checkout <fix> -- arquivo` passam a lê-la do espelho (`tests/test_test_patch.py`, `tests/test_harness.py`).

**Teste que prova.** `tests/test_workspace.py::TestIsolamentoDoHistorico` (6: um commit alcançável, só a tag base, sem remoto/alternates, `master` inexistente, só o branch do run), `tests/test_tools.py::TestCaixaDeAreia` (7: não enxerga `src/`, espelho nem caches; sem rede; escrita no workspace persiste; suíte roda na caixa; desligar só por variável e vai ao manifesto; sem `bwrap` falha alto; prefixos do Python), `tests/test_harness.py::TestC8CodigoDoFuturo` (6), F11 em `tests/test_arm_parity.py` com as chaves novas; pinos do manifesto em 18. Suíte completa: 751.

**Dados.** [dados/sondagens/vazamento-git-2026-10-27.txt](dados/sondagens/vazamento-git-2026-10-27.txt): 426 workspaces varridos, 23 com sinal, leitura em [25-vazamento-historico-git.md](25-vazamento-historico-git.md) §2.

**Impacto em docs.** [25-vazamento-historico-git.md](25-vazamento-historico-git.md) (novo); decisão 49 e registro em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md`; `.env.example`.

## Rodada 8 fechada (27/10/2026)

**O que rodou.** 39 células em `runs/coleta-r8` (14 em 23/10, 25 na retomada de 27/10, 0 perdidas): 20/39 runs, 7/13 tarefas; grande 6/9; US$ 4,95; `strict_coerced` 0 em 84 revisões finais; 7 aprovações erradas, todas em tarefas sem saída esperada pareada no enunciado. Não decisiva: a rodada 4 segue como configuração do orquestrado na replicação (decisão 45).

**Diff resumido.** Só dados e documentação: `docs/tcc/dados/coleta-r8/` (runs sem workspaces, sete métricas, apêndice, `resumo-rodadas-4-7-8.txt`), re-varredura de vazamento da rodada anexada a `dados/sondagens/vazamento-git-2026-10-27.txt` (tomlkit-0004 rep03 também copiou `items.py` do `master`: 5ª cópia, não resolvida). Nenhuma mudança em `src/`.

**Teste que prova.** Suíte completa verde na árvore principal após a mesclagem da decisão 49 (751).

**Impacto em docs.** [24-rodada-8.md](24-rodada-8.md) §4 e §4.1; registro 48 (resultado) e 45 (configuração) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); [25-vazamento-historico-git.md](25-vazamento-historico-git.md) §1 e §2; `CLAUDE.md`.

## Replicação: sondagem de aptidão e fumaça do DeepSeek (27/10/2026, decisão 45)

**O que rodou.** `scripts/fitness_test.py` para os dois modelos (apto, apto; raciocínio 0) e a fumaça do DeepSeek V3.2 na DeepInfra (`runs/fumaca-deepseek`: 3 tarefas × 2 braços, orquestrado na configuração da rodada 4, manifesto v18): 4/6, US$ 1,43, 521/521 BYOK, primeira coleta com a caixa de areia e o workspace só no commit-base (125 execuções, 0 recusas, 0 erros).

**Diff resumido.** Só dados e documentação: [26-replicacao.md](26-replicacao.md) (novo), `docs/tcc/dados/fumaca-deepseek/`, `docs/tcc/dados/sondagens/aptidao-replicacao-2026-10-27.txt`. Nenhuma mudança em `src/`.

**Teste que prova.** Suíte completa verde (751); os manifestos da fumaça registram `workspace_history: commit-base-only`, `sandbox: bwrap`, `model: deepseek/deepseek-v3.2`, `provider: DeepInfra`.

**Impacto em docs.** [26-replicacao.md](26-replicacao.md); registro 45 (aptidão e fumaça DeepSeek) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md`.


---

## Replicação: coleta do DeepSeek lançada e Devstral bloqueado na Mistral (28/10/2026, decisão 45)

**Diff resumido.** Só documentação e dados. Sonda direta no OpenRouter antes do lançamento ([dados/sondagens/mistral-byok-429-2026-10-28.txt](dados/sondagens/mistral-byok-429-2026-10-28.txt)): DeepSeek V3.2 na DeepInfra com `is_byok: true` e `reasoning_tokens: 0`; Devstral 2 na Mistral com a chave BYOK registrada, mas 429 `Rate limit exceeded` código 1300 em 4 de 4 chamadas. Coleta do DeepSeek lançada 28/10 16:11 em `runs/coleta-deepseek` (78 células, `--workers 1 --retry-delay 300 --max-attempts 5`, orquestrado da rodada 4). Scripts de lançamento recriados em `runs/_lancamento/` (pasta ignorada pelo git; o scratchpad da sessão foi apagado duas vezes e levou os anteriores).

**Teste que prova.** Suíte completa verde antes do commit (`runs/_lancamento/suite-2026-10-28.log`, fora do git); o manifesto do primeiro run registra `manifest_version 18`, `model: deepseek/deepseek-v3.2`, `provider: DeepInfra`, `sandbox: bwrap`, `workspace_history: commit-base-only`, orçamento 120/8M/3600.

**Impacto em docs.** [26-replicacao.md](26-replicacao.md) §4 a §6; registro 45 (lançamento DeepSeek; Mistral bloqueada) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md` (estado em 28/10). Pendente do autor: ativar pay-as-you-go na Mistral (crédito pré-pago não muda a faixa de limites, segundo a central de ajuda da Mistral), depois sonda, fumaça e 78 runs do Devstral.



---

## Replicação: fumaça do Devstral e lançamento dos 78 runs (28/10/2026, decisão 45)

**Diff resumido.** Só documentação e dados. Autor ativou o pay-as-you-go na Mistral (o Devstral 2 não existe no plano gratuito; crédito pré-pago não muda a faixa de limites) e a sonda respondeu BYOK às 16:31. Fumaça `runs/fumaca-devstral` (16:31 a 17:06, US$ 0,97): 6 células, 0 perdidas, 5 resolvidas, 513/513 BYOK servidas pela Mistral, 137 execuções na caixa de areia sem recusa nem estouro, detector 0/0, cache 92,4 %; dados sem workspaces em [dados/fumaca-devstral/](dados/fumaca-devstral/). Coleta do Devstral lançada 17:07 em `runs/coleta-devstral` (78 células), em paralelo com a do DeepSeek (5 células prontas às 17:07, 4 resolvidas).

**Teste que prova.** Nenhum código mudou desde a suíte verde das 16:35 (751, `runs/_lancamento/suite-2026-10-28.log`); a suíte não foi rodada de novo para não disputar CPU com as duas coletas. Os `result.json` da fumaça trazem `byok_calls == llm_calls`, `cheat.clean`, `oracle.*.network_isolated` e `timed_out: false` em todas as execuções.

**Impacto em docs.** [26-replicacao.md](26-replicacao.md) §5 a §8; registro 45 (fumaça e lançamento Devstral) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md` (estado em 28/10).



---

## Replicação: coleta do Devstral fechada (28/10/2026, decisão 45)

**Diff resumido.** Só documentação e dados. `runs/coleta-devstral` fechada às 22:48 (5 h 40 desde o lançamento), 78/78, 0 perdidas; dados sem workspaces, análise das sete métricas, apêndice, resumo e auditoria em [dados/coleta-devstral/](dados/coleta-devstral/). Resultado: single-agent 28/39 runs e 9/13 tarefas, orquestrado 30/39 e 10/13; tokens do orquestrado cerca da metade nas tarefas resolvidas por ambos (p = 0,031), demais métricas sem diferença; 3 aprovações erradas; 5 resolvidos só pelo oráculo. Cobrança real da Mistral ≈ 4 a 5× o `cost_usd` reportado (contraprova na DeepInfra: razão 1,00).

**Teste que prova.** Nenhum código mudou desde a suíte verde das 16:35 (751); `analise-sete-metricas.md` admite 78 de 78 runs sem par quebrado; `auditoria-saude.txt` registra 5.392/5.392 BYOK, detector 0/0, 0 estouros de tempo.

**Impacto em docs.** [26-replicacao.md](26-replicacao.md) §8 e §9; registro 45 (resultado Devstral) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md`. Pendente do autor: valor final de uso do Devstral no console da Mistral.



---

## Replicação: coleta do DeepSeek fechada e síntese das três coletas (29/10/2026, decisão 45)

**Diff resumido.** Só documentação e dados. `runs/coleta-deepseek` fechada às 06:03 de 29/10 (13 h 52), 78/78, 0 perdidas; dados sem workspaces, análise das sete métricas, apêndice, resumo das duas replicações e auditoria em [dados/coleta-deepseek/](dados/coleta-deepseek/). Resultado: 26/39 runs e 9/13 tarefas nos dois braços; nenhuma métrica com p < 0,05; 7 aprovações erradas, todas em sqlite-utils; 5 resolvidos só pelo oráculo, todos no orquestrado; 1 aviso C6 do detector em run não resolvido. Síntese das três coletas em [26-replicacao.md](26-replicacao.md) §10.

**Teste que prova.** Nenhum código mudou desde a suíte verde das 16:35 de 28/10 (751); `analise-sete-metricas.md` admite 78 de 78 runs; `auditoria-saude.txt` registra 5.777/5.777 BYOK, 0 estouros de tempo, detector 0 críticos e 1 aviso.

**Impacto em docs.** [26-replicacao.md](26-replicacao.md) §9 a §11; registro 45 (resultado DeepSeek e síntese) em [09-decisoes-do-autor.md](09-decisoes-do-autor.md); `CLAUDE.md`. Pendente do autor: valor final do Devstral no console da Mistral e leitura da síntese.

---

## Replicação: tarefas piso e teto nas seis células e correção da síntese (29/10/2026, decisão 45)

**Diff resumido.** Só documentação e dados. O autor perguntou se "as tarefas que travam são as mesmas" nos três modelos e se isso indicaria erro padrão do harness em vez de teste válido. A frase da síntese dizia que sim e estava forte demais. Tabela por tarefa das seis células (3 modelos × 2 braços, 234 runs) em [dados/coleta-deepseek/por-tarefa-tres-modelos.txt](dados/coleta-deepseek/por-tarefa-tres-modelos.txt): 4 tarefas teto (18/18), 1 piso (tomlkit-0004, 0/18), 8 discriminam; tomlkit-0005 e sqlite-utils-0002 vão de 0/6 num modelo a 6/6 noutro; peewee-0002 é 0/9 no orquestrado dos três modelos e 4/9 no single-agent. Para a tomlkit-0004, o arquivo lista os testes ocultos que falham em cada um dos 18 runs e a reprodução do oráculo no run DeepSeek single-agent rep02 (6/7): o serializador do agente duplica o último caractere dos valores de chave pontilhada, erro que o bloco 5 do enunciado detecta.

**Teste que prova.** Suíte completa de 29/10 (`runs/_lancamento/suite-2026-10-29.log`); a tarefa continua validada pelos quatro portões com duas referências ([dados/validacao-08-10/validate_task_final.txt](dados/validacao-08-10/validate_task_final.txt), l.103-133); o enunciado em `tasks/tomlkit-0004/statement.md` descreve os sete comportamentos cobrados e as cinco linhas que o patch de teste acrescenta a `tests/examples/0.5.0.toml`.

**Impacto em docs.** [26-replicacao.md](26-replicacao.md) §10: frase corrigida e parágrafo "Validade das tarefas como teste".

---

## Relatório científico consolidado e revisão de código do harness final (29/10/2026)

**Diff resumido.** Só documentação e dados. [27-relatorio-cientifico.md](27-relatorio-cientifico.md): resumo, pergunta e hierarquia de desfechos a priori, método, construção do instrumento (fumaças A a H, rodadas 1 a 8, 16 defeitos corrigidos, replicação), resultados das três coletas com análise agregada run a run (117 pares, McNemar exato) e por tarefa×modelo, tabela teto/piso, validação de dez proposições (a priori × emergentes), análise de poder por simulação, ameaças à validade, contribuições, melhorias e prompt para redação externa. Arquivos de origem novos: [dados/coleta-deepseek/agregado-tres-modelos.txt](dados/coleta-deepseek/agregado-tres-modelos.txt) (script ad hoc sobre os 234 `result.json`; Qwen com o single-agent pareado de `dados/coleta` + `dados/coleta-r2`), [dados/revisao-codigo-2026-10-29.md](dados/revisao-codigo-2026-10-29.md) (14 achados da revisão estática `xhigh` de `src/`, `harness/` e scripts de análise, nenhum altera resultado coletado, nada corrigido por serem intocáveis). [dados/coleta-deepseek/por-tarefa-tres-modelos.txt](dados/coleta-deepseek/por-tarefa-tres-modelos.txt) regenerado com o single-agent pareado (antes usava os 39 runs originais de `dados/coleta`, que nas três tarefas reconstruídas não são comparáveis à rodada 4): pygments-0001 Qwen-SA 3/3 → 2/3, sqlite-utils-0002 1/3 → 0/3; teto, piso e as oito tarefas que discriminam não mudam.

**Teste que prova.** Suíte completa verde às 10:xx de 29/10 (`runs/_lancamento/suite-2026-10-29.log`, 751 passed); nenhum código mudou depois. Varredura da chave da API em 322 `patch.diff` e nos `events.jsonl` das cinco raízes de coleta: 0 ocorrências.

**Impacto em docs.** Documento novo 27; nenhum documento anterior alterado. Pendências do autor listadas em 27 §8.

---

## Análise exploratória do orquestrado e scripts de análise versionados (30/10/2026)

**Diff resumido.** Só documentação, dados derivados e scripts de análise. [28-exploratorio-orquestrado.md](28-exploratorio-orquestrado.md): análise pós-hoc declarada, a pedido do autor, dos pontos em que o orquestrado se destaca (custo da carga inteira 29% menor em dólares nos 117 pares, Wilcoxon pareado p = 0,031 em dólares e p < 0,001 em tokens; pior caso 2,9 M contra 8,1 M tokens; tomlkit-0002 7/9 contra 2/9 nos três modelos, com o single-agent quebrando de 5 a 91 testes e nunca chegando à suíte verde; 8 dos 15 pares vencidos pelo orquestrado passam por reprovação do revisor com suíte verde seguida de reescrita; IC 95% da diferença pareada −6,1 a +11,3 pontos), dos pontos em que perde (10 patches certos nunca aprovados pelo revisor e 40% a 55% dos turnos gastos depois do verde [corrigido em 04/11/2026 para 21% a 41%: a conta somava os turnos do planejador]; peewee-0002 com seis sub-tarefas seriais de até 40 turnos em 120, 0/9 e 0/24 nas rodadas; aprovações erradas 13 iguais às falsas conclusões do single-agent 14) e quatro hipóteses pré-registráveis (H1 a H4). Fonte: `dados/coleta-deepseek/exploratorio-orquestrado.txt`, saída de `scripts/exploratorio_orquestrado.py`. Os scripts que geraram `agregado-tres-modelos.txt` e `por-tarefa-tres-modelos.txt` (até então só no scratchpad da sessão) foram versionados em `scripts/agregado_tres_modelos.py` e `scripts/por_tarefa_tres_modelos.py`; o primeiro reproduz o arquivo versionado byte a byte fora de linhas em branco, o segundo reproduz a tabela (a nota final do oráculo foi acrescentada à mão em 29/10).

**Correção de leitura.** A faixa grande "a favor do orquestrado nos três modelos" (27 Resumo, §4.2, §5 P10, §7 e §9) é uma única tarefa: tomlkit-0003 é teto e tomlkit-0004 é piso, logo os 7 pares discordantes da faixa são todos da tomlkit-0002. Frases ajustadas em 27 com a ressalva e ponteiro para 28; a faixa média, por sua vez, tem 4 dos 7 pares discordantes na peewee-0002.

**Teste que prova.** Suíte completa em `runs/_lancamento/suite-2026-10-30.log` (ver resultado no commit); nenhum arquivo de `src/`, `harness/` ou `tests/` mudou. Os três scripts rodam da raiz sem argumentos e leem só arquivos versionados ou de `runs/coleta-deepseek` e `runs/coleta-devstral`.

**Impacto em docs.** Documento novo 28; 27 com seis frases ajustadas (ressalva "uma tarefa" e ponteiros para 28); `26-replicacao.md` já nomeava a tomlkit-0002 em §10 e não mudou.

---

## Pacote de redação para o assistente externo (03/11/2026)

**Diff resumido.** Só documentação. [29-pacote-redacao.md](29-pacote-redacao.md): o autor decidiu redigir o texto final com o Perplexity, que já contém a revisão bibliográfica. O pacote reúne, sem número novo, tudo o que o assistente precisa: instruções (nenhum número fora dos arquivos, fonte entre colchetes, significância só onde há), vocabulário fixo, fatos do desenho, modelos e por quê, cronograma, as sete métricas e o processo por modelo, custo da carga inteira, tarefa a tarefa, anatomia da tomlkit-0002, mecanismos, integridade, hipóteses P1 a P10 com veredito, afirmações A1 a A10, hipóteses H1 a H8, estrutura dos capítulos que faltam (o `texto/desenvolvimento.tex` de 16/10 precisa de atualização), nove prompts na ordem e a lista de conferência que o executor aplica quando o texto voltar. Página de resultados para a orientadora publicada em 30/10 (artefato privado, versão 3) com o mesmo conteúdo em tabelas.

**Teste que prova.** Nenhum código mudou; suíte rodada antes do commit (ver log em `runs/_lancamento/`).

**Impacto em docs.** Documento novo 29; nenhum anterior alterado.

---

## Calibração offline da hipótese H4 e README atualizado (04/11/2026)

**Diff resumido.** Só documentação, dados derivados, um script de análise e o README. [30-calibracao-h4.md](30-calibracao-h4.md): simulação, sobre os eventos gravados dos 117 runs orquestrados das coletas finais, de cinco regras de parada alternativas para o revisor final (`scripts/calibracao_h4.py`, saída em `dados/coleta-deepseek/calibracao-h4-offline.txt`). Como o diff de cada ciclo não é gravado, o desfecho no ponto de aprovação simulado só é conhecido quando nenhuma escrita ocorreu depois dele; os demais entram como incertos nos dois limites. Resultado: a forma forte de H4 (cortar metade dos turnos após o verde sem aumentar aprovações erradas) é refutada; a única regra segura (aprovar patch inalterado após reprovação com verde) poupa 6% dos turnos com no máximo 2 resoluções em risco. A causa principal das reprovações com suíte verde é bloco de reprodução que não compila: 58 das 136 citam `SyntaxError`, em 16 runs (15 resolvidos), com 885 turnos gastos depois da primeira delas; o `REPRODUCTION_COMPILE_CHECK` das rodadas 6 a 8 resolve isso (tomlkit-0001 e tomlkit-0003 na rodada 8: 0 reprovações, 29 a 47 turnos, contra 2 a 7 reprovações e 81 a 120 turnos na rodada 4), mas a configuração da rodada 4 usada na replicação o tem desligado. H4 reformulada em 28 §3 com ponteiro para 30. README reescrito para o estado final (planejador no grafo, cinco repositórios e 13 tarefas, oráculo, detector, caixa de areia, scripts de análise, documentos 26 a 30).

**Teste que prova.** Suíte completa em `runs/_lancamento/suite-2026-11-04.log` (751 passed); nenhum arquivo de `src/`, `harness/` ou `tests/` mudou. O script roda da raiz sem argumentos.

**Impacto em docs.** Documento novo 30; 28 §3 (H4) com o veredito e o ponteiro; README; 29 inalterado (a hipótese H4 do pacote passa a remeter a 30 na próxima revisão do texto).

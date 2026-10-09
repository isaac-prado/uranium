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


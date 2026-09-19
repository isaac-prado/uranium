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

Por isso ela é tratada como parte da variável independente (a topologia), não como defeito a equalizar — ao contrário de F1, F2 e F8, que eram descuido de implementação e não tinham nenhuma justificativa de desenho. O preço dessa reconstrução por ciclo é justamente o que a métrica 2 do estudo (custo computacional, `cost.tokens_total`/`cost.cost_usd`/`cost.llm_calls`, [docs/tcc/03-metricas.md:17](../03-metricas.md#L17)) precisa capturar: reconstruir o contexto do zero a cada ciclo de validação custa tokens que o `single-agent`, ao só acrescentar à conversa existente, não paga da mesma forma — e é exatamente essa troca (contexto limpo vs. contexto caro) que o estudo mede, não uma assimetria a remover.


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

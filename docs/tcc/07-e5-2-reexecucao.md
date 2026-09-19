# E5 item 2 — Reexecução de run perdido por erro de provedor

Antes: quando um run inteiro morria por erro do provedor (429, `engine_overloaded`, timeout, formato — `max_retries` de `LLMConfig`, [src/config.py:67](../../src/config.py#L67), já tolera erro transitório POR CHAMADA, mas não cobre o run inteiro morrendo), o `summary.json` saía com `stop_reason` iniciado em `error:` e o par ficava quebrado — a repetição *k* de um braço sem contraparte na *k* do outro. Foram 3 perdas em 42 execuções no piloto. Não havia mecanismo para refazer só o run perdido preservando a semente.

## Critério de "perdido"

Implementado em `_diagnostico_do_attempt` ([src/arms/pilot.py:203](../../src/arms/pilot.py#L203)), aplicado ao attempt de maior número de cada (task_id, arm, repetition):

- `summary.json` ausente, ilegível ou sem a chave `stop_reason` → morte abrupta;
- `events.jsonl` sem nenhum evento `run_end` → morte abrupta (defesa extra: `run_arm` só grava `summary.json` **depois** de `telemetry.run_end`, [src/arms/runner.py:301](../../src/arms/runner.py#L301), então isso só dispara se o processo morrer exatamente entre as duas escritas);
- `stop_reason` começando em `"error:"` → erro de provedor/execução.

Um corte por orçamento (`stop_reason` começando em `"budget:"`) **não** é perdido — é resultado do experimento (é o que a métrica 6, autonomia, mede) e não é reexecutado. Coberto por `TestCorteDeOrcamentoNaoEhPerda.test_run_cortado_por_orcamento_nao_e_perdido`.

## Como a semente é preservada

`seed_for_repetition(base_seed, repetition)` ([src/arms/runner.py:111](../../src/arms/runner.py#L111)) depende só do índice da repetição, nunca do braço nem de quantas vezes ela já foi tentada. `build_run_spec` ([src/arms/runner.py:182-228](../../src/arms/runner.py#L182-L228)) recebeu um parâmetro novo, `attempt` (padrão 1, validado ≥ 1 em [src/arms/runner.py:210](../../src/arms/runner.py#L210)), que entra em `RunSpec` ([src/arms/runner.py:156](../../src/arms/runner.py#L156)) e no manifesto ([src/arms/runner.py:167](../../src/arms/runner.py#L167)) — mas nunca participa do cálculo da semente ([src/arms/runner.py:222](../../src/arms/runner.py#L222), onde `llm=replace(base_llm, seed=seed_for_repetition(...))` não recebe `attempt`). A reexecução chama `build_run_spec` passando a mesma `repetition` do run perdido e `attempt = attempt_perdido + 1`; a semente sai idêntica por construção, não por coincidência de teste.

Como a perda pode acontecer num braço só, `attempt` pode divergir entre os dois lados de um par sem violar o desenho experimental. Por isso `attempt` entrou em `CHAVES_QUE_PODEM_DIFERIR` ([src/arms/runner.py:48-60](../../src/arms/runner.py#L48-L60)), com comentário explicando o porquê, e `tests/test_arm_parity.py::TestTentativaDeReexecucao.test_attempt_pode_divergir_entre_bracos_sem_violar_a_paridade` prova que dois `RunSpec` com `attempt` diferente têm `manifest()["llm"]` (logo `seed`) idêntico.

## Diff resumido por arquivo

| Arquivo | O que mudou |
|---|---|
| [src/arms/runner.py](../../src/arms/runner.py) | `RunSpec` ganha `attempt: int = 1`, gravado no manifesto. `build_run_spec` ganha o parâmetro `attempt` (padrão 1, recusa `< 1` com a mesma mensagem de estilo de `repetition`). `run_arm` grava `attempt` também no `summary.json`. `CHAVES_QUE_PODEM_DIFERIR` ganha `"attempt"`, com o comentário de que a semente não é afetada. |
| [src/arms/pilot.py](../../src/arms/pilot.py) | Núcleo do item. `MAX_TENTATIVAS_REEXECUCAO = 3` (teto padrão). `PilotOutcome` ganha o campo `attempt` (padrão 1). Novidades: `RunPerdido` (dataclass com o que se sabe de uma perda), `_perda_por_stop_reason`, `_tem_run_end`, `_diagnostico_do_attempt` (critério de perda), `detectar_perdidos(out_dir)` (varre `out_dir` por `manifest.json`, agrupa por (task_id, arm, repetition) e devolve o attempt mais recente perdido de cada grupo), `marcar_perdido(run_dir, motivo)` (grava um arquivo `PERDIDO` de texto; se achar um `result.json` espúrio no diretório perdido, renomeia para `result.json.perdido`) e `reexecutar_perdidos(out_dir, ...)` (para cada perdido: se já esgotou `max_tentativas`, só marca; senão refaz com `build_run_spec(..., attempt=attempt+1)`, marca o diretório antigo como substituído, e se a nova tentativa também morrer e já bater o teto, marca a nova também). |
| [scripts/run_pilot.py](../../scripts/run_pilot.py) | Opção `--reexecutar` (não roda o piloto normal: varre `--out` e refaz só os perdidos), `--tasks-dir` (raiz das tarefas para resolver `task_id → TaskSpec` durante a reexecução, padrão `tasks/`) e `--max-tentativas` (padrão `MAX_TENTATIVAS_REEXECUCAO`). Reaproveita `format_report`/`load_llm_config`/`RunBudget` já existentes; nenhum código de avaliação ou execução novo neste arquivo, só orquestração de CLI. |
| [tests/test_arm_parity.py](../../tests/test_arm_parity.py) | `TestTentativaDeReexecucao`: `attempt` default 1 e presente no manifesto; `attempt` diferente entre duas chamadas de `build_run_spec` não muda `llm.seed`; dois specs de braços diferentes com `attempt` diferente não violam `test_so_a_topologia_difere` (a prova pedida pelo plano); `attempt=0` é recusado. |
| [tests/test_pilot.py](../../tests/test_pilot.py) | `TestReexecucaoDeRunPerdido` (com mirror do tomlkit, `run_arm` de verdade): detecta o perdido pelo `stop_reason` de erro; reexecuta com a mesma semente, `run_id` novo e `attempt=2`; avalia o substituto quando pedido; o diretório antigo fica marcado e intacto (`summary.json`/`manifest.json` continuam lá); o perdido já marcado não reaparece numa nova varredura; um `result.json` espúrio no diretório perdido é neutralizado (renomeado). `TestCorteDeOrcamentoNaoEhPerda` (sem mirror, manifestos sintéticos): corte por orçamento não é perdido; run concluído normalmente não é perdido; morte abrupta sem `summary.json` é perdida; morte abrupta sem `run_end` é perdida; teto de tentativas esgotado declara o par perdido de vez sem tentar de novo. |

Nenhum prompt, detector de trapaça, oráculo, guarda de caminho ou pino de provedor foi tocado.

## Como o autor usa isso na coleta

```
uv run python scripts/run_pilot.py --out runs/pilot --reexecutar
```

Varre `runs/pilot` (ou a raiz que for passada em `--out`) atrás de runs perdidos, refaz cada um com a mesma semente e imprime a mesma tabela comparativa do piloto normal (`format_report`). Sobrepor modelo/provedor/orçamento funciona com as mesmas flags do modo normal (`--model`, `--provider`, `--max-turns`, etc.); `--max-tentativas N` muda o teto padrão de 3; `--tasks-dir` só importa se as tarefas não estiverem em `tasks/`.

## Por que um run perdido não pode entrar duas vezes na análise

`scripts/analyze_results.py` (não tocado neste item) só lê `result.json` — `find_results` faz `rglob("result.json")` a partir das raízes dadas ([scripts/analyze_results.py:204-221](../../scripts/analyze_results.py#L204-L221)). Confirmado por leitura: nenhum outro arquivo do run (`summary.json`, `manifest.json`, `events.jsonl`) é considerado pela análise.

Um run perdido, pela via normal, nunca chega a ter `result.json`: tanto `run_pilot` quanto `reexecutar_perdidos` só chamam o avaliador (`harness.evaluate.evaluate_run`) quando `erro is None`, e além disso descobri, testando (`tests/test_pilot.py::TestReexecucaoDeRunPerdido::test_avalia_o_substituto_quando_pedido`), que `evaluate_run` **devolve** o resultado mas não grava nada em disco — quem grava é `harness/evaluate.py:main()`, a CLI (`python -m harness.evaluate`), não a função. Ou seja: o `result.json` de um run só existe se alguém rodar essa CLI manualmente sobre o diretório do run.

Isso cria um risco residual que não está sob controle de código: nada em `harness/evaluate.py` (fora do escopo deste item) sabe que um diretório é `PERDIDO` — `evaluate_run` só exige que `workspace/.git` exista, e ele existe mesmo num run perdido (o workspace é materializado por `run_arm` antes de qualquer chamada de rede). Se alguém rodar `python -m harness.evaluate --run-dir <diretório perdido> --task ...` na mão, um `result.json` é gerado ali, e a repetição substituída entraria na análise ao lado do substituto — dobrando a amostra daquele (task, arm) na mediana de `agregar()` em `scripts/analyze_results.py`.

Duas camadas de mitigação, dentro do que este item pode tocar:

1. **Convenção operacional, documentada aqui**: nunca rodar `harness.evaluate` sobre um diretório que contenha o arquivo `PERDIDO`. `find runs -name PERDIDO` lista todos de uma vez.
2. **Neutralização retroativa em `marcar_perdido`** ([src/arms/pilot.py:283](../../src/arms/pilot.py#L283)): se, ao marcar um diretório como perdido, já existir um `result.json` nele (avaliação manual feita antes da marca), ele é renomeado para `result.json.perdido` — fora do padrão que `find_results` varre. Testado em `test_result_json_espurio_no_diretorio_perdido_e_neutralizado`.

O que este item **não** cobre: alguém avaliar manualmente um diretório perdido **depois** de já estar marcado, ignorando a marca. Não há gancho em `harness/evaluate.py` (fora do escopo) para recusar isso; fica registrado como risco residual, não como pendência de código.

## Testes

Escopo do item (`tests/test_pilot.py tests/test_arm_parity.py`):

```
72 passed in 21.69s
```

Suíte inteira (`.venv/bin/python -m pytest -q`):

```
471 passed in 109.94s (0:01:49)
```

Não observei as duas falhas de `tests/test_seed_repos.py` (`peewee` coletando zero testes) relatadas em itens anteriores — a suíte inteira passou 471/471 nesta máquina, neste momento. Não investiguei se o ambiente do `peewee` foi corrigido por outro agente (mexe em `scripts/setup_mirror.py`/`src/seeds.py`, fora do meu escopo); registro só o que observei.

## Decisões e dúvidas para o autor

- **Onde morou o mecanismo**: em `src/arms/pilot.py`, não num script novo. O piloto já é, pelo próprio texto do módulo, "o formato de coleta em miniatura" — é ele quem hoje roda os dois braços × repetições × avaliação (as "42 execuções" citadas na exigência vieram dele), e `--reexecutar` em `scripts/run_pilot.py` reaproveita toda a infraestrutura de CLI já existente. Se a coleta definitiva das 12 tarefas vier a ganhar um script dedicado depois, `detectar_perdidos`/`marcar_perdido`/`reexecutar_perdidos` são reaproveitáveis como estão — dependem só do conteúdo de `manifest.json`/`summary.json`/`events.jsonl`, não do layout de diretório de quem os grava.
- **Teto de tentativas = 3**: não é um número do estudo (que o plano proíbe inventar), é o teto do MECANISMO de reexecução, escolhido para bater com o padrão pedido em "E5 item 2" e G5. Ajustável por `--max-tentativas` sem mexer em código.
- **`reexecutar_perdidos` não decide sozinho quando rodar**: é uma função pura de reexecução, chamada por comando explícito do autor (`--reexecutar`). Não há automação que rode sozinha depois de uma coleta — decisão deliberada para não gastar crédito sem supervisão.
- **Dúvida em aberto**: se a coleta definitiva vier a ser feita por um shell script/loop externo a este repositório (não visto por mim), esse script precisa saber pular diretórios marcados `PERDIDO` antes de invocar `harness.evaluate` em lote — a convenção está documentada aqui, mas não há como este item garantir que um script futuro, fora do meu escopo de edição, vá respeitá-la.

### Complemento (orquestrador)

O risco residual apontado acima foi fechado: a CLI `python -m harness.evaluate` recusa um diretório que contenha a marca `PERDIDO` e não grava `result.json` ([harness/evaluate.py](../../harness/evaluate.py), início de `main`). Teste: `tests/test_harness.py::TestRunPerdidoNaoEhAvaliado`. O oráculo, o detector e a guarda não foram tocados; a checagem fica antes de qualquer avaliação.

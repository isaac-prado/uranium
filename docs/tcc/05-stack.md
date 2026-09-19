# Verificação do stack (E0)

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 18 de setembro de 2026
Etapa E0 de [EXIGENCIAS.md](tasks/EXIGENCIAS.md). Somente leitura. Base: commit `99b0ed8` da branch `develop`. Toda contagem sobre dados vem de arquivo de execução com o caminho ao lado; nenhum número vem do dossiê HTML.

## 1. O LangGraph ainda é usado?

**Sim, nos dois braços, e como grafo de verdade.** Cada braço é um `StateGraph` do LangGraph com nós, arestas fixas e arestas condicionais, compilado para `CompiledStateGraph`. O ponto único em que os braços divergem é a função que escolhe qual grafo compilar: [src/arms/runner.py:229-238](../../src/arms/runner.py#L229-L238). Tudo antes (workspace, orçamento, ferramentas, telemetria, LLM) e tudo depois (manifesto, `summary.json`, avaliação) é comum.

Verifiquei a estrutura executando `get_graph()` sobre os dois grafos compilados nesta sessão, sem chamada de LLM. O resultado bate com o código de montagem.

### Braço `orchestration` — [src/graph.py:43-66](../../src/graph.py#L43-L66)

| # | Aresta | Tipo | Regra de roteamento |
|---|---|---|---|
| 1 | `START → intent_refiner` | fixa | [graph.py:51](../../src/graph.py#L51) |
| 2 | `intent_refiner → developer` | condicional | intent pronta (`is_ready`) **ou** 3 rodadas de esclarecimento atingidas ([graph.py:12-18](../../src/graph.py#L12-L18)) |
| 3 | `intent_refiner → clarification` | condicional | intent não pronta e menos de 3 rodadas |
| 4 | `clarification → intent_refiner` | fixa | [graph.py:57](../../src/graph.py#L57); é o laço de esclarecimento |
| 5 | `developer → validator` | fixa | [graph.py:58](../../src/graph.py#L58) |
| 6 | `validator → test_generator` | condicional | orçamento estourado **ou** suíte válida **ou** 2 rodadas de validação atingidas ([graph.py:19-32](../../src/graph.py#L19-L32)) |
| 7 | `validator → developer` | condicional | suíte inválida e menos de 2 rodadas; é o laço de correção |
| 8 | `test_generator → END` | fixa | [graph.py:64](../../src/graph.py#L64) |

Cinco nós de trabalho: `intent_refiner`, `clarification`, `developer`, `validator`, `test_generator` ([graph.py:45-49](../../src/graph.py#L45-L49)). Quatro deles fazem uma chamada de LLM com saída estruturada por execução do nó ([src/agents/intent_refiner.py:48-55](../../src/agents/intent_refiner.py#L48-L55); [clarification.py:42-43](../../src/agents/clarification.py#L42-L43); [validator.py:52-60](../../src/agents/validator.py#L52-L60); [test_generator.py:49](../../src/agents/test_generator.py#L49)). O `developer` é o único que roda um laço de chamadas com ferramentas ([developer.py:70-90](../../src/agents/developer.py#L70-L90)).

### Braço `single-agent` — [src/arms/single_agent.py:123-134](../../src/arms/single_agent.py#L123-L134)

| # | Aresta | Tipo | Regra de roteamento |
|---|---|---|---|
| 1 | `START → single_agent` | fixa | [single_agent.py:126](../../src/arms/single_agent.py#L126) |
| 2 | `single_agent → single_agent` | condicional | o agente pediu ferramenta neste turno ([single_agent.py:114-118](../../src/arms/single_agent.py#L114-L118)) |
| 3 | `single_agent → driver` | condicional | o agente não pediu ferramenta: parou de agir |
| 4 | `single_agent → END` | condicional | orçamento estourado |
| 5 | `driver → END` | condicional | suíte verde ([single_agent.py:120-121](../../src/arms/single_agent.py#L120-L121)) |
| 6 | `driver → single_agent` | condicional | suíte vermelha: o driver devolve o stderr cru e o agente volta |

Dois nós: `single_agent` (uma chamada de LLM por turno, com ferramentas) e `driver` (nenhuma chamada de LLM; roda a suíte, [single_agent.py:92-112](../../src/arms/single_agent.py#L92-L112)).

### O que o LangGraph faz e o que não faz aqui

- **Faz:** executa os nós na ordem ditada pelas arestas, aplica as funções de roteamento condicional, mantém o estado compartilhado (`WorkflowState`, um `TypedDict` em [src/state.py](../../src/state.py)) e impõe um limite de recursão derivado do teto de turnos ([runner.py:192-193](../../src/arms/runner.py#L192-L193)).
- **Não faz:** não há checkpointer, persistência, execução paralela de nós, interrupção humana nem subgrafos. O LangGraph é usado como motor de máquina de estados, e só isso. Não encontrei evidência de uso de qualquer recurso do LangGraph além de `StateGraph`, `START`, `END`, `add_node`, `add_edge`, `add_conditional_edges` e `compile` (imports em [graph.py:3](../../src/graph.py#L3) e [single_agent.py:22](../../src/arms/single_agent.py#L22)).
- **Nem "degenerou" nem é ornamental.** Os laços de esclarecimento e de correção são arestas condicionais reais, exercitadas por teste ([tests/test_graph_flow.py:18-50](../../tests/test_graph_flow.py#L18-L50)). O teste de estrutura, porém, só confere que os cinco nós existem ([test_graph_flow.py:53-61](../../tests/test_graph_flow.py#L53-L61)); **nenhum teste verifica as arestas**. Se alguém removesse uma aresta condicional, a suíte não perceberia.
- Há uma prova de conceito morta com LangGraph em [main.py:1-22](../../main.py#L1-L22) (grafo de um nó que imprime "Olá"). Não é alcançada por nenhum caminho do estudo (inventário 1.6).

## 2. Versões

| Pacote | Declarado em `pyproject.toml` | Travado em `uv.lock` | Instalado em `.venv` |
|---|---|---|---|
| `langgraph` | `>=1.2.0` ([pyproject.toml:9](../../pyproject.toml#L9)) | 1.2.0 | 1.2.0 |
| `langgraph-checkpoint` | — (transitiva) | 4.1.0 | 4.1.0 |
| `langgraph-prebuilt` | — (transitiva) | 1.1.0 | 1.1.0 |
| `langgraph-sdk` | — (transitiva) | 0.3.14 | 0.3.14 |
| `langchain-openai` | `>=1.2.1` ([pyproject.toml:8](../../pyproject.toml#L8)) | 1.2.1 | 1.2.1 |
| `langchain-core` | — (transitiva) | 1.4.0 | 1.4.0 |
| `langchain` (metapacote) | **não declarado** | **não está no lock** | **não instalado** |
| `langsmith` | **não declarado** | 0.8.5, dependência de `langchain-core` | 0.8.5 |
| Python | `>=3.12` ([pyproject.toml:6](../../pyproject.toml#L6)) | — | 3.12.14 |

Instalado e travado coincidem em todos os pacotes (saída de `uv pip list` nesta sessão). O repositório não usa o metapacote `langchain`; usa só `langchain-core` (mensagens, ferramentas) e `langchain-openai` (cliente do OpenRouter, [src/config.py:18](../../src/config.py#L18)).

## 3. O LangSmith

**Removido do código; presente como dependência transitiva; desligado à força.**

- Nenhum módulo importa `langsmith` nem usa `@traceable`. Isso é verificado por teste que varre `src/` e `harness/` ([tests/test_observabilidade.py:23-29](../../tests/test_observabilidade.py#L23-L29)), e outro teste confirma que não é dependência declarada ([test_observabilidade.py:31-34](../../tests/test_observabilidade.py#L31-L34)).
- O pacote continua instalado porque `langchain-core` depende dele (`uv.lock`). Por isso [src/config.py:22-36](../../src/config.py#L22-L36) sobrescreve quatro variáveis de ambiente (`LANGSMITH_TRACING`, `LANGCHAIN_TRACING_V2`, `LANGCHAIN_TRACING`, `LANGSMITH_OTEL_ENABLED`) para `"false"` no momento do import, para que nenhuma variável perdida no ambiente reative o envio de spans durante uma coleta.
- O arquivo `src/tracing.py`, que a documentação antiga cita, **não existe**.

### Onde ainda é anunciado

| Local | O que diz | Situação |
|---|---|---|
| [pyproject.toml:4](../../pyproject.toml#L4) | descrição do pacote: "com LangGraph e LangSmith" | superado |
| [src/agents/README.md:54](../../src/agents/README.md#L54) | "Funções decoradas com `@traceable` (LangSmith) via `src/tracing.py`" | superado; arquivo inexistente |
| [src/agents/README.md:75](../../src/agents/README.md#L75) | frase para o TCC "com observabilidade via LangSmith" | superado |
| [projeto.md:8](../../projeto.md#L8), [projeto.md:272-274](../../projeto.md#L272-L274), [projeto.md:308](../../projeto.md#L308) | lista LangSmith no stack e descreve o que "você verá no LangSmith" | superado (tutorial da POC) |
| [src/telemetry.py:5](../../src/telemetry.py#L5) | "o LangSmith fica só como apoio de depuração" | impreciso: está desligado incondicionalmente, não fica como apoio |
| [README.md:161-165](../../README.md#L161-L165) | declara a remoção e o motivo | **correto** |
| [docs/modelagem-do-sistema.html:1047-1060](../modelagem-do-sistema.html) | seção "por que o LangSmith saiu" | **correto** |
| TFG (Nota 1), resumo e p. 2 | "instrumentado com LangSmith" | precisa da declaração abaixo |

### Parágrafo de declaração para o texto do TCC

> A proposta original previa instrumentar o Uranium com o LangSmith, serviço de rastreamento remoto do ecossistema LangChain. Durante o desenvolvimento, ele foi substituído por telemetria própria: cada execução grava, em arquivo local, um evento por linha para cada chamada ao modelo, cada uso de ferramenta, cada execução da suíte de testes e cada decisão de parada, em um envelope de 25 campos validado contra um esquema formal. A substituição foi uma decisão metodológica, por quatro razões. Primeira, o rastreamento remoto coloca um serviço externo, com latência variável e possibilidade de falha, dentro do caminho que mede tempo e custo; a telemetria local não depende de rede. Segunda, o custo em dólares e a contagem de tokens passam a vir do valor nativo devolvido pelo provedor a cada chamada, e não de estimativa feita por terceiro. Terceira, o envelope registra em cada evento o papel do agente que o gerou, o que materializa a variável independente do estudo no dado bruto: o campo fica vazio no braço de agente único e preenchido no braço orquestrado. Quarta, os arquivos de eventos são lidos por um avaliador independente, que recalcula custo e processo sem confiar no relato do sistema avaliado. O LangSmith continua instalado como dependência indireta da biblioteca, e o código o desativa de forma incondicional para que nenhuma configuração de ambiente o reative durante a coleta.

## 4. Documentação que descreve arquitetura superada

Classe: texto no repositório que descreve componentes, papéis ou arquivos que não existem mais ou que fazem outra coisa. Listado, não corrigido.

| Local | O que descreve | O que existe hoje |
|---|---|---|
| [README.md:12](../../README.md#L12) | diagrama de arquitetura só do braço orquestrado | dois braços; o `single-agent` não aparece no diagrama (aparece só na seção "Os dois braços", [README.md:111-118](../../README.md#L111-L118)) |
| [README.md:15-21](../../README.md#L15-L21) | "Developer: gera artefatos de desenvolvimento"; "Validator: valida artefatos vs critérios"; "Clarification: respostas simuladas na POC" | o developer edita um repositório real por ferramentas e o artefato é o diff do workspace ([src/agents/developer.py:1-8](../../src/agents/developer.py#L1-L8)); o validador roda a suíte e só rebaixa por revisão ([validator.py:1-13](../../src/agents/validator.py#L1-L13)); não há mais "POC" |
| [README.md:130-146](../../README.md#L130-L146) | árvore de diretórios | omite `src/arms/`, `src/budget.py`, `src/runtime.py`, `src/telemetry.py`, `src/prompts.py`, `src/structured_llm.py`, `src/workspace.py`, todo `harness/`, e os scripts `run_arm.py`, `run_pilot.py`, `mine_tasks.py`, `emit_task.py`, `validate_task.py` |
| [README.md:145](../../README.md#L145) | `scripts/run_pipeline.py  # CLI` | **não existe**; a CLI é `scripts/run_arm.py` (usada corretamente em [README.md:90-98](../../README.md#L90-L98)) |
| [src/agents/README.md](../../src/agents/README.md) inteiro | pipeline que devolve `artifacts`; `src/tracing.py`; exemplo "Criar CRUD de Cliente"; LangSmith | `artifacts` não é campo do estado ([src/state.py](../../src/state.py)); `src/tracing.py` não existe; a entrada é um enunciado de manutenção sobre repositório real |
| [projeto.md](../../projeto.md) inteiro | "Arquitetura Inicial da POC": grafo de um nó, modelo global, `test.py`, LangSmith | histórico da primeira semana; nada descreve o estudo atual |
| [test.py:1-15](../../test.py#L1-L15) | invoca o grafo com pedido de "CRUD em javascript com node" | o grafo hoje exige workspace, tarefa e contexto de execução; o script não representa o uso |
| [main.py](../../main.py) | grafo "Olá" | prova de conceito sem uso |
| [pyproject.toml:4](../../pyproject.toml#L4) | "Pipeline multi-agente ... com LangGraph e LangSmith" | dois braços, sem LangSmith |
| [src/telemetry.py:5](../../src/telemetry.py#L5) | LangSmith "como apoio de depuração" | desligado incondicionalmente |
| `src/agents/tfg1.md` | arquivo de 0 bytes | vazio |

Não encontrei evidência de arquitetura superada em `docs/modelagem-do-sistema.html` nem em `BACKLOG.md`: ambos descrevem os dois braços e o harness como estão. Não encontrei referência a `run_pipeline.py` fora de [README.md:145](../../README.md#L145).

## 5. Assimetrias estruturais do braço orquestrado

Para cada uma: o que é, onde está, se a topologia a exige ou se foi escolha de implementação, e o que declarar. Cruza com as folgas F5, F6 e F7 do inventário ([01-inventario.md](01-inventario.md), seção 1.4).

| Assimetria | Onde | Natureza | Consequência observável | O que declarar |
|---|---|---|---|---|
| **Teto de esclarecimento**, `MAX_CLARIFICATION_ITERATIONS = 3` | [src/config.py:40](../../src/config.py#L40); laço em [graph.py:12-18](../../src/graph.py#L12-L18); contador em [intent_refiner.py:57-59](../../src/agents/intent_refiner.py#L57-L59) | **Escolha de implementação.** O laço de esclarecimento existe só no braço orquestrado (a topologia o cria), mas o valor 3 é arbitrário e só evita laço infinito | Cada rodada gasta duas chamadas de LLM sem consumir turno e reescreve o enunciado (folga F4) | O valor no manifesto e no texto; a hipótese de que o enunciado reescrito muda o que o developer vê é a da ablação (E1 testa direto) |
| **Teto de correção**, `MAX_VALIDATION_ITERATIONS = 2` | [src/config.py:41](../../src/config.py#L41); [graph.py:30-31](../../src/graph.py#L30-L31) | **Escolha de implementação.** O single-agent itera até o orçamento ([single_agent.py:120-121](../../src/arms/single_agent.py#L120-L121)); nada na topologia orquestrada obriga a parar em duas rodadas. É critério de parada distinto entre braços | O braço orquestrado encerra com `concluiu` e suíte vermelha: 3 dos 16 runs orquestrados da branch `runs-17-09-2026` (contagem sobre `summary.json`, [01-inventario.md](01-inventario.md), seção 1.7, tabela de R1) | Ou igualar ao critério do single-agent (iterar até o orçamento) ou declarar como parte do desenho e registrar no manifesto. Decisão sua; a E2 trata do manifesto |
| **Gate semântico**, `SEMANTIC_REVIEW` (padrão ligado) | [validator.py:40-42](../../src/agents/validator.py#L40-L42), [:52-60](../../src/agents/validator.py#L52-L60), [:74](../../src/agents/validator.py#L74) | **Escolha de implementação.** Uma chamada de LLM extra a cada validação verde, que só pode rebaixar o veredito. Não está no `.env.example` nem no manifesto (folga F6); nada impede uma coleta com e outra sem, com manifestos idênticos | Gasta tokens e pode mandar o developer de volta mesmo com suíte verde | Registrar no manifesto (E2). Decidir se fica ligado; se ficar, é papel adicional do braço e entra na descrição da topologia |
| **Turno conta só o developer** | `next_turn()` só em [developer.py:77](../../src/agents/developer.py#L77) e [single_agent.py:73](../../src/arms/single_agent.py#L73) ([budget.py:61-63](../../src/budget.py#L61-L63)); chamadas estruturadas passam por [runtime.py:132-154](../../src/runtime.py#L132-L154), que emite o evento e conta tokens, mas não turno | **Misto.** Que existam chamadas fora do developer é consequência da topologia (os papéis auxiliares só existem no braço orquestrado). Que essas chamadas não consumam turno é escolha de implementação: o teto de 40 turnos limita só o developer, enquanto tokens e tempo limitam o sistema inteiro | Nos 4 runs de 11/09 (`result.json` em `runs/`), o orquestrado fez 41 chamadas em 38 turnos e 36 em 33; o single-agent, 26 em 26 e 40 em 40 | Declarar que "turno" é unidade do agente que escreve código e que a comparação de esforço usa chamadas ao modelo, como já fixado na métrica 2 de [03-metricas.md](03-metricas.md) |
| **Reconstrução do contexto a cada ciclo** (folga F3) | [developer.py:61-64](../../src/agents/developer.py#L61-L64) × [single_agent.py:58-64](../../src/arms/single_agent.py#L58-L64) | Fora do escopo desta etapa: a E2 a declara como parte da variável independente | — | Ver E2 |

Síntese: das quatro assimetrias pedidas, **nenhuma é consequência necessária da topologia em seu valor atual**. A topologia cria os laços e os papéis; os tetos, o gate e a regra de contagem de turno são escolhas que podem ser igualadas, registradas ou declaradas, e hoje não estão registradas no manifesto.

---

Não encontrei evidência para: uso de checkpointer, `Send`, subgrafos ou interrupção humana no LangGraph; teste que verifique as arestas do grafo; referência a `run_pipeline.py` fora do `README.md`; arquivo `src/tracing.py`.

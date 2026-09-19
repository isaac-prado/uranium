## E5 item 5 — Corrigir a documentação que descreve arquitetura superada

Exigência: "Corrigir a documentação que descreve arquitetura superada (lista da E0)" ([EXIGENCIAS.md](tasks/EXIGENCIAS.md), E5 item 5). A lista é [05-stack.md](05-stack.md), seção 3 (onde o LangSmith ainda é anunciado) e seção 4 (documentação que descreve arquitetura superada). Escopo desta tarefa: só documentação (`README.md`, `projeto.md`, `src/agents/README.md`, `pyproject.toml` — texto descritivo, não dependências); código em `src/`, `scripts/`, `tests/` e `docs/tcc/07-*.md` ficaram intocados de propósito, porque outras frentes da E5 mexem neles em paralelo.

### Diff resumido

| arquivo | mudou |
|---|---|
| `README.md` | tabela de papéis do braço orchestration, árvore de `src/`/`scripts/`, nova seção "Documentação do estudo" |
| `src/agents/README.md` | diagrama, tabela de agentes, parágrafo de observabilidade, exemplo de fluxo de dados, frase de fechamento para o TCC |
| `projeto.md` | aviso no topo, sem alterar o corpo do documento |
| `pyproject.toml` | `description` (texto; dependências não tocadas) |

### Seção 3 do 05-stack.md — onde o LangSmith ainda era anunciado

| Local (05-stack.md, seção 3) | O que dizia | Correção | Situação |
|---|---|---|---|
| `pyproject.toml:4` | descrição do pacote: "com LangGraph e LangSmith" | `description` trocada para "Estudo comparativo de Engenharia de Software 3.0: pipeline multi-agente (LangGraph) contra agente único, com telemetria própria em JSONL" | **corrigido** |
| `src/agents/README.md:54` | "Funções decoradas com `@traceable` (LangSmith) via `src/tracing.py`" | reescrito: telemetria JSONL própria (`src/telemetry.py`), envelope validado por `harness/schema/event.schema.json`, `agent_role` por evento, tracing remoto desligado por `src/config.py` | **corrigido** — [src/agents/README.md:54](../../src/agents/README.md#L54) |
| `src/agents/README.md:75` | frase para o TCC "com observabilidade via LangSmith" | trocada por "com telemetria própria em JSONL (o LangSmith foi removido; ver docs/tcc/05-stack.md)" | **corrigido** — [src/agents/README.md:75](../../src/agents/README.md#L75) |
| `projeto.md:8`, `projeto.md:272-274`, `projeto.md:308` | lista LangSmith no stack da POC; "o que você verá no LangSmith" | **não linha a linha.** Adicionado aviso no topo do arquivo classificando-o como registro histórico da primeira semana, superado pelo estudo atual, com link para `README.md` e `05-stack.md`. O corpo (inclusive as três menções a LangSmith) foi mantido verbatim | **parcialmente corrigido**, ver justificativa abaixo |
| `src/telemetry.py:5` | "o LangSmith fica só como apoio de depuração" | — | **não corrigido**: arquivo de código, fora do escopo desta tarefa (só documentação) |
| `README.md:161-165` | declara a remoção e o motivo | — | já estava correto; nenhuma mudança necessária |
| `docs/modelagem-do-sistema.html:1047-1060` | seção "por que o LangSmith saiu" | — | já estava correto; também fora do escopo (`.html`, não `.md`, e a instrução só cobre `docs/*.md` fora de `docs/tcc`) |
| TFG (Nota 1), resumo e p. 2 | "instrumentado com LangSmith" | — | **não corrigido**: é `docs/tcc/fontes/TFG_ISAAC_DO_PRADO_ALMEIDA.pdf`, PDF do trabalho já entregue/avaliado, não um arquivo de documentação do repositório para editar. O parágrafo de declaração para usar no texto do TCC já está redigido em [05-stack.md](05-stack.md), seção 3 |

### Seção 4 do 05-stack.md — documentação que descreve arquitetura superada

| Local (05-stack.md, seção 4) | O que descrevia | Correção | Situação |
|---|---|---|---|
| `README.md:12` | diagrama só do braço orquestrado, sem o single-agent | adicionada frase logo abaixo do diagrama dizendo que é o grafo do braço `orchestration` e apontando para a seção "Os dois braços" | **corrigido** — [README.md:15-17](../../README.md#L15-L17) |
| `README.md:15-21` | "Developer: gera artefatos de desenvolvimento"; "Validator: valida artefatos vs critérios"; "Clarification: respostas simuladas na POC" | tabela reescrita com o comportamento real: Developer edita o repositório por ferramentas (o artefato é o diff do workspace); Validator roda a suíte e só pode rebaixar por revisão; removida a palavra "POC" da linha do Clarification | **corrigido** — [README.md:19-25](../../README.md#L19-L25) |
| `README.md:130-146` | árvore de diretórios sem `src/arms/`, `src/budget.py`, `src/runtime.py`, `src/telemetry.py`, `src/prompts.py`, `src/structured_llm.py`, `harness/`, e os scripts `run_arm.py`, `run_pilot.py`, `mine_tasks.py`, `emit_task.py`, `validate_task.py` | árvore reescrita com os itens confirmados por `ls src/` e `ls scripts/`; `src/workspace.py` já estava presente (não precisou de correção) | **corrigido** — [README.md:136-163](../../README.md#L136-L163) |
| `README.md:145` | `scripts/run_pipeline.py  # CLI` (não existe) | linha removida; a árvore agora lista os nove scripts reais, com uma linha de docstring cada, confirmada lendo o topo de cada arquivo | **corrigido** — [README.md:153-162](../../README.md#L153-L162) |
| `src/agents/README.md` inteiro | pipeline que devolve `artifacts`; `src/tracing.py`; exemplo "Criar CRUD de Cliente"; LangSmith | tabela de agentes com as chaves reais do `WorkflowState` (`changed_files`, `diff_stat`, `dev_summary`, `test_report`); diagrama com os rótulos corrigidos; exemplo de fluxo de dados trocado para os campos reais do estado, sem inventar um caso concreto (não há exemplo de tarefa real neste arquivo para citar); observabilidade e frase de fechamento sem LangSmith | **corrigido** — ver seção anterior e [src/agents/README.md](../../src/agents/README.md) |
| `projeto.md` inteiro | "Arquitetura Inicial da POC": grafo de um nó, modelo global, `test.py`, LangSmith | aviso no topo classificando o documento como histórico (primeira semana), com link para o estado atual; o corpo (código da POC, exemplo "Criar CRUD de Cliente", `test.py`, LangSmith) foi mantido, porque é relato fiel do que existia naquele momento, não uma alegação falsa sobre o presente | **parcialmente corrigido**, ver justificativa abaixo |
| `test.py:1-15` | invoca o grafo com "CRUD em javascript com node"; não representa o uso atual (grafo exige workspace, tarefa, contexto de execução) | — | **não corrigido**: é um script executável na raiz do repositório, não um arquivo de documentação da lista permitida para esta tarefa |
| `main.py` | grafo "Olá", prova de conceito sem uso | — | **não corrigido**: mesmo motivo — arquivo de código, fora da lista de arquivos que esta tarefa pode tocar |
| `pyproject.toml:4` | "Pipeline multi-agente ... com LangGraph e LangSmith" | ver tabela da seção 3 acima | **corrigido** |
| `src/telemetry.py:5` | LangSmith "como apoio de depuração" | — | **não corrigido**: arquivo de código |
| `src/agents/tfg1.md` | arquivo de 0 bytes, vazio | — | **não corrigido**: não está na lista de arquivos permitidos (só `src/agents/README.md` dentro de `src/agents/`); o E0 só registra que está vazio, não descreve nada de errado para reescrever, e apagar ou preencher um arquivo de conteúdo desconhecido não é uma correção de texto |

O E0 também registrou, na seção 4, que não encontrou arquitetura superada em `docs/modelagem-do-sistema.html` nem em `BACKLOG.md`. Conferido de novo nesta etapa por leitura de `BACKLOG.md` inteiro: nenhuma menção a papéis inexistentes, a `run_pipeline.py` ou a LangSmith — nenhuma mudança necessária. `docs/*.md` fora de `docs/tcc` está vazio (só existe o `.html`), então não há outro arquivo dessa categoria para corrigir.

### Por que `projeto.md` recebeu um aviso, e não uma reescrita

A instrução desta tarefa é "não reescrever os documentos do zero: corrigir o que está errado, apagar o que descreve o que não existe, manter o estilo. Nada de inventar recurso que não exista." O `projeto.md` inteiro é um tutorial datado da primeira semana do projeto (POC de um nó, `IntentRefinerAgent`) — o próprio E0 o descreve como "histórico da primeira semana; nada descreve o estudo atual". Reescrever o código de exemplo, o fluxo do LangSmith ou o exemplo "Criar CRUD de Cliente" para refletir o estado atual destruiria o valor do documento como registro do ponto de partida, sem tornar nenhuma frase mais correta — ele nunca afirmou descrever o presente, só passou a ficar desatualizado com o tempo. A correção aplicada foi declarar isso explicitamente no topo do arquivo, com link para onde está o estado atual (`README.md`, `docs/tcc/05-stack.md`, `docs/tcc/00-guia-etapas.md`), o que resolve a contradição C5 do inventário sem apagar histórico.

### Seção nova no README

Adicionada a seção "Documentação do estudo" ao final do `README.md`, apontando para [docs/tcc/00-guia-etapas.md](00-guia-etapas.md) (a metodologia, etapa por etapa) e [docs/tcc/01-inventario.md](01-inventario.md) (o inventário de fato sobre o repositório), como pedido.

### O que ficou de fora, por decisão de escopo (não de esquecimento)

Todo item marcado "não corrigido" acima é arquivo de **código** (`src/telemetry.py`, `test.py`, `main.py`, `src/agents/tfg1.md`) ou **fonte externa já entregue** (o PDF do TFG) — nenhum está na lista de arquivos que esta tarefa tem permissão de tocar (`README.md`, `projeto.md`, `src/agents/README.md`, `BACKLOG.md`, `docs/*.md` fora de `docs/tcc`, e texto descritivo de `pyproject.toml`). Corrigi-los é trabalho de outra frente da E5 (a que mexe em `src/`) ou do próprio autor (o PDF entregue).

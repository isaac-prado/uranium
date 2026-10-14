# Uranium: invariantes do experimento

Este repositório é o instrumento de um TCC que compara duas topologias de agentes de IA corrigindo bugs: `single-agent` (agente único com operador determinístico) e `orchestration` (papéis orquestrados por um grafo LangGraph). A alegação causal do estudo depende de os dois braços serem idênticos em tudo, exceto na topologia. O que está listado aqui é proposital. Não "otimize", "simplifique" nem "modernize" nada desta lista sem o autor pedir por escrito.

Fonte de verdade sobre o desenho: `docs/tcc/00-guia-etapas.md`, `docs/tcc/01-inventario.md`, `docs/tcc/03-metricas.md`, `docs/tcc/tasks/EXIGENCIAS.md`. Decisões pendentes e tomadas, com data: `docs/tcc/09-decisoes-do-autor.md`. Não cite `docs/dossie-metodologico.html` como fonte de número.

## Intocáveis sem aprovação do autor

- Detector de trapaça (`harness/cheat.py`), oráculo (`harness/oracle.py`), guarda de caminho (`src/seeds.py` `DEFAULT_PROTECTED_GLOBS` e `src/workspace.py`), pino de provedor (`src/config.py`: `provider_routing`, `_validate`, `OpenRouterChat`).
- Prompts (`src/prompts.py`). Os dois braços usam o mesmo prompt de sistema e o mesmo conjunto de ferramentas na mesma ordem.
- O refinador de intent tem duas versões (`INTENT_REFINER`, `orchestration_policy.intent_refiner`, manifesto v9): `v1` é o prompt do TFG, que resume, e é o da coleta principal de 12-13/10/2026; `v2` enriquece (reprodução, saídas esperadas e restrições copiadas literalmente, critérios verificáveis), aprovado por escrito pelo autor em 14/10/2026 (decisão 28) e roda em coleta própria, nunca misturado com a principal. Intent v2 entra no prompt do developer e do revisor como markdown (`src/schemas/intent.py::intent_as_text`); v1 continua JSON.
- Mensagens de protocolo ao agente vivem só em `src/feedback.py`. Nenhum braço pode ter texto próprio de feedback; `tests/test_arm_parity.py` falha se houver.
- O developer do orquestrado volta ao nó com a **memória de trabalho** (decisão 8 revista em 09/10/2026): registro determinístico dos ciclos anteriores (arquivos lidos, buscas, escritas, suítes, nota final) e o diff atual, montados por `src/feedback.py::memoria_de_trabalho` sem chamada extra ao modelo. Política `DEVELOPER_MEMORY` (`ledger` na coleta; `none` reproduz a reconstrução do zero de 19/09, folga F3), registrada em `orchestration_policy.developer_memory`. Não passar a transcrição inteira (seria o histórico do single-agent) nem acrescentar síntese do harness. A memória vale só dentro do run: nada atravessa tarefas ou repetições.
- O developer do orquestrado volta ao validador a cada `DEVELOPER_CYCLE_MAX_TURNS` turnos (decisão 25 de 09/10/2026; `orchestration_policy.developer_cycle_max_turns`). `stop_reason` `cycle:` não é orçamento nem fim de run; a reprovação semântica num ponto de checagem não conta para `MAX_SEMANTIC_REJECTIONS`. O critério de parada continua "suíte verde ou orçamento" nos dois braços.
- O developer do orquestrado recebe só a intent do `intent_refiner`, nunca o enunciado cru (decisão 24 revertida em 09/10/2026: é o protótipo do TFG; o confundidor D3 é declarado e medido pela ablação). `DEVELOPER_INPUT=enunciado+intent` existe **só para o braço de ablação do refinador** (decisões 7 e 16, 14/10/2026; `orchestration_policy.developer_input`, manifesto v8) e nunca entra na coleta principal.

## Paridade e manifesto

- `tests/test_arm_parity.py` é o teste que sustenta o estudo. Qualquer chave nova no manifesto que divirja entre braços precisa estar em `CHAVES_QUE_PODEM_DIFERIR` (`src/arms/runner.py`) com justificativa, ou o teste falha de propósito.
- Tudo que muda o comportamento de um braço vai ao manifesto (`orchestration_policy`, `shared_limits`, `budget`, `llm`, `driver_policy`). Dois runs com configuração diferente nunca podem produzir manifestos idênticos.
- A repetição k de um braço e a k do outro rodam com a mesma semente (`seed_for_repetition`). Reexecução de run perdido preserva a semente.
- Constantes de ferramenta (`src/tools/base.py`, `src/tools/exec.py`, `src/runtime.py`) são compartilhadas e registradas em `shared_limits`. Mudar uma delas muda os dois braços e invalida comparação com coletas anteriores.
- Critério de parada igual nos dois braços: suíte verde ou orçamento. O orquestrado tem um teto só para a reprovação da revisão semântica (`MAX_SEMANTIC_REJECTIONS`, em `orchestration_policy`); não existe mais `MAX_VALIDATION_ITERATIONS` (decisão do autor de 28/09/2026, BACKLOG 7.2 D6).
- Repositórios com pacote em `src/<nome>/` (jinja, marshmallow, attrs) importam pelo `uranium_src_layout.pth` que `scripts/setup_mirror.py` grava no venv do repo a partir de `SeedRepoSpec.pythonpath`. Vale igualmente para ferramentas do agente, oráculo, validação e mineração, porque todos rodam com `cwd` na raiz do workspace. Não instalar pacote no venv nem passar `PYTHONPATH` por fora: seria um segundo mecanismo que pode divergir.
- Run perdido tem uma definição só: `lost: true` no `summary.json`, isto é, `stop_reason` em `infra_error:` (provedor) ou `interrupted:` (Ctrl+C), `src/arms/runner.py: LOST_PREFIXES`. É lida por `harness/attempts.py` (coleta e análise) e `src/arms/pilot.py`. Corte por orçamento não é perda; `error:` de outra origem é bug do harness, não perda. Perdido é reexecutado com a mesma semente e `attempt + 1`.

## Faixas das tarefas (congeladas em 08/10/2026, decisão 22 de `docs/tcc/09-decisoes-do-autor.md`)

Função pura `calcular_faixa` em `scripts/mine_tasks.py`, sobre o patch de referência do upstream: "arquivo-fonte" é `.py` dentro do `source_dir` do repositório (arquivo apagado não conta); "linhas" é o total de linhas alteradas nesses arquivos; "teste novo/modificado" é a contagem de funções `def test_` adicionadas/alteradas no diff dos testes. Checadas nesta ordem:

- **Grande:** 3 ou mais arquivos-fonte, 80 ou mais linhas, mais testes novos que modificados (e ao menos um novo), e assunto do commit que não começa por `fix`/`bug`. Funcionalidade nova com teste escrito pelo projeto: exige planejar antes de escrever.
- **Média:** 3 a 7 arquivos-fonte e 40 a 400 linhas. "Módulo" é o arquivo `.py`; não se exige mais de um diretório (a versão de 19/09 exigia, e esvaziava a faixa em pacote plano).
- **Pequena:** 1 ou 2 arquivos-fonte e 10 a 50 linhas; ou 3 ou mais arquivos com menos de 40 linhas (pequena por tamanho, com `motivo_faixa` registrado).
- **Fora:** o resto; registrado com o motivo, nunca verificado por execução.

A faixa é gravada no `task.json`, atravessa até o `result.json` e é eixo da análise. Toda tarefa, em qualquer faixa, só entra se for verificada por execução (suíte verde no commit-base, teste oculto vermelho na base e verde com a referência) e passar nos quatro portões de `scripts/validate_task.py` com duas soluções de referência. Mudar uma faixa depois da coleta começar invalida a estratificação.

## Tetos do run (congelados em 12/10/2026, decisão 12 de `docs/tcc/09-decisoes-do-autor.md`)

`RUN_MAX_TURNS=120`, `RUN_MAX_TOKENS=8000000`, `RUN_MAX_WALL_SECONDS=3600`, `test_timeout_s=120`; no orquestrado, `DEVELOPER_MEMORY=ledger`, `DEVELOPER_CYCLE_MAX_TURNS=40`, `MAX_SEMANTIC_REJECTIONS=2`. Padrões em `src/budget.py` e `.env.example`; calibrados nas fumaças A a H da `tomlkit-0004` (`docs/tcc/07-e4-fumaca.md`, seção 13). Turnos são o orçamento; tokens e parede são rede de segurança (nenhum corte por tokens em oito runs a 120 turnos ou mais; o único corte por parede foi latência do provedor). Não mudam até o fim da coleta; mudar qualquer um invalida a comparação com os runs já coletados.

## Regras de trabalho

- Nada de execução paga (chave `OPENROUTER_API_KEY`) sem os portões offline de `docs/tcc/04-cronograma.md` verdes e sem o autor pedir.
- A coleta roda com chave própria do provedor registrada no OpenRouter (BYOK, decisão 11 final de 09/10/2026), fallback para o pool compartilhado desligado. `cost_usd` de cada chamada é o total pago (taxa do OpenRouter + `upstream_inference_cost` quando `is_byok`); `result.json` traz `byok_calls`, que na coleta tem de ser igual a `llm_calls`.
- Nenhum número em documento sem o arquivo de origem ao lado. Não inventar.
- Agentes não escrevem testes na suíte dos repositórios-semente; a área de testes é protegida.
- Rodar a suíte com `.venv/bin/python -m pytest -q` (ou `uv run pytest`). Ela deve ficar verde antes de qualquer commit.
- Commits em português, no estilo conventional commits do histórico.
- Etapas E2 a E5 têm registro em `docs/tcc/07-execucao.md`: diff resumido, teste que prova, impacto em docs.

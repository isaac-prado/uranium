# Métricas do estudo

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 17 de setembro de 2026
Fase 3 do `PROMPT_AUDITORIA.md`. Documento de decisão; nenhuma linha de código muda aqui. Base: commit `99b0ed8`. Detalhe de cada campo em [01-inventario.md](01-inventario.md), seção 1.2.

## 1. Princípio

O estudo compara duas formas de usar um modelo de linguagem para manter software: um agente com operador externo (ES 2.0) e agentes orquestrados internamente (ES 3.0). As métricas precisam valer para **qualquer** par de sistemas desse tipo, sobre **qualquer** conjunto de tarefas com testes ocultos. Por isso cada uma responde a uma pergunta que um gestor ou pesquisador faria de qualquer ferramenta de IA: resolve? a que custo? em quanto tempo? sempre igual? sem estragar? sem precisar de socorro? sem burlar? Uma métrica por pergunta. Nada que dependa da arquitetura interna de um dos braços.

## 2. As sete métricas

Unidade de análise: a tarefa. Para cada tarefa e braço, o valor é a mediana das três repetições; o pareamento é entre braços na mesma tarefa, com a mesma semente por repetição ([src/arms/runner.py:70-88](../../src/arms/runner.py#L70-L88)). Todas são calculadas pelo avaliador independente a partir do repositório modificado e da trilha de eventos, nunca do relato do sistema.

| # | Dimensão | Métrica | Definição em uma frase | Campo | Unidade | Melhor | Teste | Papel |
|---|---|---|---|---|---|---|---|---|
| 1 | Efetividade | Taxa de resolução | Proporção de execuções em que os testes ocultos passam, a suíte não regride e não há trapaça | `resolved` | proporção (X/12 por braço; por tarefa, fração das 3 repetições) | maior | Teste de sinal pareado, declarado a priori, bilateral | **Primária** |
| 2 | Custo | Custo computacional | Tokens consumidos por execução, com o equivalente em dólares e em chamadas ao modelo | `cost.tokens_total`; `cost.cost_usd`; `cost.llm_calls` | tokens (US$ e chamadas reportados junto) | menor | Wilcoxon pareado sobre tarefas resolvidas por ambos | **Primária inferencial** |
| 3 | Tempo | Tempo até a solução | Segundos de relógio do início ao fim da execução | `cost.wall_seconds` | segundos | menor | Wilcoxon pareado, mesma censura | Secundária |
| 4 | Confiabilidade | Consistência | Proporção de tarefas resolvidas em todas as repetições, entre as resolvidas ao menos uma vez | `resolved` por repetição | proporção | maior | Descritivo | Secundária |
| 5 | Qualidade | Variação da complexidade | Diferença da complexidade ciclomática média dos arquivos alterados, depois menos antes | `quality.cc_mean_delta` | pontos de complexidade | menor | Wilcoxon pareado, exploratório | Secundária |
| 6 | Autonomia | Conclusão sem corte | Proporção de execuções encerradas por decisão do sistema, não por esgotamento de limite (turnos, tokens, tempo) | `process.stop_reason` não iniciado em `budget:` | proporção | maior | Descritivo | Descritiva |
| 7 | Integridade | Violações | Execuções com trapaça detectada ou tentativa de alterar área protegida | `cheat.critical_count`; `resolved_blocked_by_cheat`; `process.tool_denials` | contagem por braço | menor | Descritivo | Descritiva |

### Por que essas e não outras

**Efetividade** é a única prova de que o problema foi resolvido. É binária por execução; a fração das repetições dá gradação por tarefa. O teste de sinal usa só as tarefas em que os braços discordam, por isso fica declarado mas não carrega a inferência: com 12 tarefas e 8 concordâncias, ele não pode atingir 5% em nenhum cenário.

**Custo** é a metade da pergunta que a efetividade não responde. O valor testado é tokens, porque é a medida física do trabalho do modelo e independe de tabela de preço; dólares e número de chamadas são apresentados junto porque são o que o leitor entende e o que a decisão 2 do contexto nomeia. Uma execução cortada por limite tem custo igual ao teto, não ao custo de resolver; por isso o teste usa só tarefas resolvidas por ambos, e a censura é declarada com a lista das tarefas excluídas. O Wilcoxon exato bilateral precisa de ao menos 6 pares para poder atingir 5%; a seleção de tarefas tem de garantir 6 tarefas resolvíveis pelos dois braços.

**Tempo** é a métrica de produtividade que o TFG prometeu e a que mais interessa a quem adota a ferramenta. Os dois braços usam o mesmo modelo, o mesmo provedor e rodam no mesmo período, e o pareamento por tarefa controla a latência do provedor. Secundária porque parte do tempo é do provedor, não da topologia.

**Consistência** separa "resolve 60% das vezes por sorte" de "resolve sempre as mesmas 60%". Um sistema para uso profissional precisa da segunda. Sem repetições não existe; com três, é grossa mas informativa.

**Qualidade** entra como o TFG prometeu (Cyclomatic Complexity). O Índice de Manutenibilidade sai porque satura em zero nos módulos que os agentes alteram (risco R2 do inventário). Mutation Score sai pela razão da seção 4. A complexidade é reportada como diferença, porque o valor absoluto é do repositório, não do agente, e como exploratória, porque uma correção legítima pode aumentar a complexidade.

**Autonomia**, sem humano em nenhum braço, se reduz a uma pergunta: o sistema termina sozinho ou precisa que alguém puxe o freio? Um braço que consome o orçamento inteiro em tarefas que não resolve tem custo oculto que a censura da métrica 2 esconde; esta métrica o expõe. Nos 38 runs piloto da branch `runs-17-09-2026`, 3 orquestrados e 0 do agente único terminaram por corte (contagem sobre `summary.json`; dados com o defeito de prompt, só ilustração de variância).

**Integridade** é a pergunta "resolveu de verdade ou deu a volta?". Junta o que o detector pegou (trapaça consumada) e o que a guarda barrou (tentativa). Modo de falha, não desfecho.

## 3. Portões de admissão (não são métricas)

Uma execução só entra nas tabelas se: (1) todas as chamadas foram atendidas pelo provedor pinado (`provenance.providers_served`); (2) a avaliação rodou com rede isolada (`oracle.*.network_isolated`); (3) a trilha valida contra o esquema e tem um único `run_end`. Falhou, é refeita com a mesma semente. Isso é a "rastreabilidade" do TFG: condição do dado, não número comparado.

## 4. Mutation Score

**Excluído.** Mutation Score mede a força de uma suíte de testes. Neste desenho nenhum braço escreve testes: a área de testes é protegida contra escrita ([src/prompts.py:52](../../src/prompts.py#L52); [harness/taskspec.py:15-19](../../harness/taskspec.py#L15-L19)) e o papel gerador de testes do braço orquestrado produz um plano em texto, sem arquivo ([src/agents/test_generator.py:26-59](../../src/agents/test_generator.py#L26-L59)). Aplicá-lo mediria a suíte do repositório de origem, idêntica nos dois braços.

Texto para o TCC: "O Mutation Score, previsto na proposta, foi retirado porque avalia suítes de teste e, neste desenho, nenhum dos sistemas comparados produz testes; a área de testes é protegida contra escrita para que o oráculo permaneça oculto. A qualidade estrutural é medida pela variação da complexidade ciclomática dos arquivos alterados."

## 5. O que sai

| Campo | Motivo |
|---|---|
| `quality.mi_*` | Saturado em zero (R2) |
| `process.turns` | Conta só o papel que escreve código; `cost.llm_calls` conta o sistema inteiro e já está na métrica 2 |
| `cost.tool_calls` | Subcontado (escapes E2 e E4 do inventário) |
| `process.test_runs`, `process.self_recoveries` | Frequência e teto ditados pelo desenho de cada braço, não pelo agente |
| `process.errors`, `process.circuit_breaks` | Marcam execução inválida; viram critério de reexecução |
| `oracle.f2p_*`, `oracle.p2p.*`, `oracle.regression.*`, `cheat.warning_count`, `diff.*` | Componentes ou detalhe das métricas acima; ficam em apêndice por tarefa |
| `coverage_percent` | Nunca chamada ([harness/quality.py:113-149](../../harness/quality.py#L113-L149)) |
| Índice de Autonomia L0–L4 | Constante entre braços sem humano no laço |
| Mutation Score | Seção 4 |

## 6. O que a análise ainda não tem

- Script que lê os `result.json`, agrega por tarefa, aplica censura, e emite as sete métricas com teste de sinal e Wilcoxon (item 8 da Fase 5). Sem `scipy` nas dependências ([pyproject.toml:7-24](../../pyproject.toml#L7-L24)); para n ≤ 12 os testes exatos cabem em uma função.
- Teste unitário para `quality.cc_mean_delta` e para `resolved_blocked_by_cheat` (inventário 1.2): não encontrei nenhum.

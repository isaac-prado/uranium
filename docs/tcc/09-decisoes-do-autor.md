# Decisões do autor antes dos testes finais

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 8 de outubro de 2026

Este documento reúne **toda** decisão que ainda está com o autor antes da fumaça paga (E4) e da coleta definitiva, e também as que já foram tomadas e precisam ir para o texto do TCC. Para cada uma: o que está em jogo, as opções, o que cada opção muda no resultado, uma recomendação e **onde a decisão entra no texto** (seção de Método, de Ameaças à validade ou Apêndice). O campo "Decisão" fica em branco até o autor preencher; depois de preenchido, a data entra ao lado e o item não é reaberto.

Fontes: [04-cronograma.md](04-cronograma.md), [07-execucao.md](07-execucao.md), [07-e3-1-mineracao.md](07-e3-1-mineracao.md), [07-e3-3-breaking-change.md](07-e3-3-breaking-change.md), [07-e5-4-analise.md](07-e5-4-analise.md), [08-escolha-modelo.md](08-escolha-modelo.md), [BACKLOG.md](../../BACKLOG.md) seções 6 a 8, e o código citado ao lado de cada item. Nenhum número vem do dossiê HTML.

## Estrutura do texto do TCC que estas decisões alimentam

| Seção do TCC | Decisões que entram nela |
|---|---|
| Método › Materiais (repositórios e tarefas) | 1, 2, 3 |
| Método › Tratamentos (os dois braços) | 4 a 10 |
| Método › Procedimento (modelo, provedor, tetos, coleta) | 11 a 17 |
| Método › Análise | 18 a 20 |
| Ameaças à validade | 2, 7, 9, 14, 15 |
| Apêndice (manifesto, registro datado das decisões) | todas, na tabela final |

---

## Bloco 1 — Materiais: as 12 tarefas

### Decisão 1. Composição das 12 tarefas por faixa

**Situação.** A exigência E3 pede 4 tarefas por faixa. A mineração verificada por execução ([07-e3-1-mineracao.md](07-e3-1-mineracao.md), seções 4 e 5) achou: pequena 55 aceitas, média **2** (ambas peewee: `ab1266aa`, `08b28d14`), grande **3** (todas tomlkit: `0561e5de`, `b29cdf0c`, `eedcdb25`). Hoje só existem 2 diretórios em `tasks/` (`sqlite-utils-0001`, `tomlkit-0001`).

**Opções.**

- (a) **Ampliar a verificação nos cinco repositórios atuais**: `--max-verificar-por-faixa` acima de 30 e `--desde` para alcançar commits mais antigos. Custo zero em crédito; tempo de máquina (97 a 185 s por candidato no peewee). Pode render as 2 médias e 1 grande que faltam, sem garantia.
- (b) **Suportar layout `src/<pacote>/` no harness** (`src/workspace.py`, `src/tools/exec.py`) e minerar click, jinja, marshmallow e attrs: 24 + 9 + 8 + 11 candidatos grandes no pré-filtro. Custo: mudança em dois módulos compartilhados, testes, espelhos novos, remineração. Muda `shared_limits`? Não; muda a materialização do workspace, igual para os dois braços.
- (c) **Aceitar o desenho desigual** e declarar: por exemplo 6 pequenas + 2 médias + 3 grandes (11) ou 7 + 2 + 3 (12). A estratificação por faixa deixa de ser balanceada.

**Impacto.** A inferência primária (Wilcoxon sobre custo) exige ao menos 6 tarefas resolvidas pelos dois braços ([03-metricas.md](03-metricas.md), seção 2); as pequenas garantem isso. A faixa grande é o que a E4 e a hipótese do multiagente precisam: menos de 4 grandes enfraquece a leitura "o orquestrado ajuda quando a tarefa exige planejamento", mas não invalida a comparação pareada. Cada tarefa escrita custa cerca de 1,5 dia útil do autor ([04-cronograma.md](04-cronograma.md), caminho crítico).

**Recomendação.** (a) imediatamente, em segundo plano, com teto de um dia de máquina; (b) só se (a) não fechar 4 médias e 4 grandes, porque muda código compartilhado e exige rodar a paridade de novo; (c) como plano de contingência declarado, nunca abaixo de 11 tarefas.

**Onde entra.** Método › Materiais: tabela das 12 tarefas com repositório, commit, faixa, arquivos, linhas; critério das faixas ([07-e3-1-mineracao.md](07-e3-1-mineracao.md), seção 1). Se (c): parágrafo de limitação.

**Decisão:** ______ (data: ______)

### Decisão 2. Mudança de comportamento e exclusão à la SWE-bench (E3.3)

**Situação.** [07-e3-3-breaking-change.md](07-e3-3-breaking-change.md) mostra que o oráculo julga a mudança de comportamento quando o commit de correção atualiza todos os testes afetados (o minerador já verifica isso), mas o **laço do agente** não consegue terminar nela: os dois braços só param com a suíte antiga verde, e o agente não pode tocar em `tests/`. Recomendação do relatório: não implementar a exclusão agora; manter o passo 2 do minerador como portão (alternativa A) e reportar quantos candidatos grandes foram rejeitados por dano colateral.

**As seis sub-decisões (seção 5 do relatório).**

1. Autorizar ou não a alteração do oráculo (`harness/oracle.py`), que implica enfraquecer a verificação de regressão sobre a suíte inteira.
2. Significado de "resolvido" na faixa grande: forte (suíte inteira verde) ou restrito (conjunto que a referência mantém verde).
3. Política de amostragem: A (excluir por execução, custo zero), B (só commits que acrescentam testes), C (aceitar e declarar) ou a exclusão à la SWE-bench.
4. Se o laço do agente pode mudar. Leitura do relatório: não; a saída é evitar a tarefa, não adaptar o laço.
5. Se o risco R4 do inventário (node ids de `fail_to_pass` contados dentro de `p2p`) é corrigido junto ou separado.
6. Subir `RESULT_SCHEMA_VERSION` de 2 para 3 caso a exclusão entre.

**Impacto.** Com A, `resolved` conserva o significado forte e a ameaça à validade some; o custo é poder não fechar 4 grandes (ligado à decisão 1). Com a exclusão, a faixa grande ganha candidatos, mas a taxa de resolução vira limite superior nessas tarefas e o texto precisa do parágrafo de três frases da seção 4 do relatório.

**Recomendação.** A, sem tocar no oráculo (sub-decisões 1 = não, 2 = forte, 3 = A, 4 = não, 5 = separado, declarado no texto, 6 = não). Reabrir só se a decisão 1 falhar na opção (a).

**Onde entra.** Método › Materiais (critério de aceitação de candidato por execução); Ameaças à validade (parágrafo sobre mudança de comportamento e R4).

**Decisão:** ______ (data: ______)

### Decisão 3. Segunda solução de referência em todas as 12 tarefas

**Situação.** O portão 3 de [scripts/validate_task.py](../../scripts/validate_task.py) exige **ao menos duas** referências por tarefa ("prova que o oráculo não é travado numa forma"). Escrever o `alternative.patch` é trabalho manual do autor e é a parte mais cara do caminho crítico.

**Opções.** (a) Manter duas referências em todas; (b) exigir duas só nas faixas pequena e média e aceitar uma na grande, declarando; (c) relaxar o portão para uma referência em todas.

**Impacto.** A segunda referência é o que mostra que o oráculo não aceita só a forma do upstream. Sem ela, a validade do oráculo numa tarefa fica apoiada só no commit original. Em tempo: (a) custa cerca de metade do 1,5 dia por tarefa.

**Recomendação.** (a) se o cronograma da decisão 22 fechar; senão (b), com a lista das tarefas de referência única declarada no texto.

**Onde entra.** Método › Materiais (validação das tarefas, os quatro portões); Apêndice (saída de `validate_task.py` por tarefa).

**Decisão:** ______ (data: ______)

---

## Bloco 2 — Tratamentos: o desenho do braço `orchestration`

As decisões 4 a 6 **já foram tomadas pelo autor em 28/09/2026** (commits `f4c01a9`, `c2046fd`, `7068a55` na `develop`) e integradas à branch de trabalho em 08/10/2026 ([07-execucao.md](07-execucao.md), seção "Reconciliação"). Aparecem aqui para confirmação e para o texto.

### Decisão 4. Teto do laço developer ↔ validator (D6)

**Tomada em 28/09.** Suíte vermelha e diff vazio voltam ao developer até o orçamento acabar, como o driver do single-agent. O único teto próprio é `MAX_SEMANTIC_REJECTIONS = 2`, reprovações da revisão semântica sobre código verde, caso que não existe no outro braço. Vai ao manifesto em `orchestration_policy.max_semantic_rejections`. Resolve a decisão 4 da lista de 19/09 e a folga F5 do inventário.

**Onde entra.** Método › Tratamentos: "critério de parada idêntico nos dois braços: verde ou orçamento; o orquestrado tem um teto adicional só para a reprovação semântica, com o valor no manifesto".

**Decisão (confirmar):** ______ (data: ______)

### Decisão 5. Texto e truncamento do feedback do pytest (D7 / F1 / F2)

**Duas correções independentes chegaram ao mesmo problema.** A de 19/09 (E2) usa uma função única em `src/feedback.py` e nenhum corte além do da ferramenta (8.000 caracteres, cabeça 2/3 + cauda 1/3, `MAX_TOOL_OUTPUT_CHARS`), premissa aprovada pelo autor em 19/09. A de 28/09 (develop) fazia o developer chamar o driver do single-agent, com corte de 4.000 caracteres pela cauda. **Na reconciliação de 08/10 ficou a de 19/09**: ambas dão paridade literal; a de 19/09 é a premissa já aprovada, mantém a mensagem num módulo só e evita que o nó de um braço importe o operador do outro. O teste de identidade byte a byte cobre stdout curto e stdout acima de 8.000 caracteres.

**Onde entra.** Método › Tratamentos (feedback de execução idêntico; tamanho do truncamento declarado).

**Decisão (confirmar):** ______ (data: ______)

### Decisão 6. Motivo da reprovação semântica repassado ao developer (D4)

**Tomada em 28/09.** Com a suíte verde e o revisor reprovando, o developer recebe `issues`, `missing_criteria` e `suggestions` do próprio revisor. Na reconciliação, a moldura (os três títulos) passou para `src/feedback.py`, como toda mensagem de protocolo; o conteúdo continua sendo do revisor. O aviso "Arquivos já modificados", que só este braço dava (F8), continua removido.

**Onde entra.** Método › Tratamentos (o que cada papel recebe).

**Decisão (confirmar):** ______ (data: ______)

### Decisão 7. O developer recebe a paráfrase do `intent_refiner`, não o enunciado cru (D3)

**Situação.** O single-agent recebe o enunciado literal; o developer do orquestrado recebe o JSON reescrito pelo `intent_refiner` (mais o que o `clarification` acrescentar). É compressão com perda feita pelo LLM, e é confundidor: mede a qualidade da paráfrase, não a topologia (BACKLOG 7.2, D3). O E1 mediu o tamanho da primeira mensagem em cada braço ([06-contabilidade-contexto.md](06-contabilidade-contexto.md)); a ablação do refinador está no cronograma com 10 execuções (US$ 0,30 a 0,60).

**Opções.** (a) Manter e **rodar a ablação** (5 pares: orquestrado com e sem refinador) e reportar como resultado; (b) manter e só declarar como parte do tratamento; (c) mudar: o developer recebe o enunciado cru e a intent entra como anexo (muda o tratamento antes da coleta).

**Impacto.** (a) isola a hipótese de mecanismo e custa pouco; (b) deixa um confundidor declarado dentro do efeito; (c) redefine o braço e precisa de nova rodada de paridade.

**Recomendação.** (a). Se o tempo apertar, (b) com a medida do E1 (tamanho da primeira mensagem) como evidência.

**Onde entra.** Método › Tratamentos; Resultados (ablação) ou Ameaças à validade (se (b)).

**Decisão:** ______ (data: ______)

### Decisão 8. Reconstrução do contexto a cada ciclo (D5 / F3)

**Tomada em 19/09 (E2).** Declarada como parte da variável independente, com a referência a Rangel (2025) ([07-execucao.md](07-execucao.md), "Declaração da política de contexto"). O custo em tokens dessa estratégia é o que a métrica 2 mede. Não se iguala ao histórico persistente do single-agent.

**Onde entra.** Método › Tratamentos; Discussão (custo da reinjeção de contexto).

**Decisão (confirmar):** ______ (data: ______)

### Decisão 9. `test_generator` e `clarification`: nós sem efeito sobre o desfecho (D1, D2)

**Situação.** O `test_generator` roda em todo run, produz um plano que só `export.py` lê e não afeta `resolved`. O `clarification` faz o modelo responder às próprias perguntas, até 3 voltas, sem fonte de verdade. Os dois são custo fixo por run (BACKLOG 7.3) e nenhuma fonte da literatura levantada os sustenta (BACKLOG 7.6).

**Opções.** (a) **Manter o braço como está (`orch-full`) e declarar** D1 e D2 como limitação, reportando custo e chamadas por nó a partir do `events.jsonl` (BACKLOG 7.4); (b) remover os dois nós antes da coleta (redefine o braço: a hipótese passa a ser sobre outro sistema); (c) manter `orch-full` e adicionar `orch-min` (developer + validator) como braço de ablação (mais 36 execuções, mais US$ 1,2 a 2,2 pelo custo médio do piloto).

**Impacto.** (a) preserva a hipótese do TFG e o pareamento; o custo fixo aparece no resultado e é discutido. (b) muda o objeto de estudo a seis semanas da defesa. (c) é o desenho mais informativo, mas custa uma coleta a mais e uma semana.

**Recomendação.** (a), com a tabela de custo por nó como figura da Discussão.

**Onde entra.** Método › Tratamentos (grafo nó a nó, [05-stack.md](05-stack.md)); Ameaças à validade; Discussão.

**Decisão:** ______ (data: ______)

### Decisão 10. Valores de `MAX_SEMANTIC_REJECTIONS`, `MAX_CLARIFICATION_ITERATIONS` e `SEMANTIC_REVIEW`

**Situação.** Hoje 2, 3 e `true`. Todos vão ao manifesto em `orchestration_policy` (E2). São parâmetros do tratamento; depois da fumaça não mudam.

**Recomendação.** Manter os três como estão e congelar junto com os tetos (decisão 12).

**Onde entra.** Método › Tratamentos (tabela de parâmetros do braço orquestrado, com o valor e a origem no manifesto).

**Decisão:** ______ (data: ______)

---

## Bloco 3 — Procedimento: modelo, provedor, tetos e coleta

### Decisão 11. Modelo, provedor e timeout por chamada

**Situação.** [08-escolha-modelo.md](08-escolha-modelo.md) recomenda manter `qwen/qwen3-coder` e o DeepInfra, com `qwen3-coder-next` na Parasail como reserva. Em 28/09 o DeepInfra recusou três vezes com 429 (`temporarily rate-limited upstream`), inclusive logo depois de o `fitness_test.py` passar nele; o piloto migrou ao Novita, que serve o modelo com `seed`, mas o laudo completo de aptidão (5 sondagens) no Novita não foi rodado (BACKLOG 6). O timeout por chamada caiu de 300 s para 90 s na `develop` (p99 de 60 s em 854 chamadas); o `.env` desta máquina ainda tem `LLM_REQUEST_TIMEOUT=300`.

**Opções.** (a) DeepInfra, aceitando o risco de 429 coberto pela reexecução; (b) Novita, depois do laudo completo de aptidão; (c) Parasail com `qwen3-coder-next` (modelo diferente: refaz a calibração de custo e dos tetos).

**Impacto.** O provedor é parte do tratamento: quantização, versão e implementação do `seed` variam; nunca muda dentro da coleta (`allow_fallbacks: false`), e o manifesto o registra. Trocar depois da fumaça obriga a repetir a fumaça. O timeout interage com o tempo de parede: 90 s × 7 tentativas = até 630 s numa chamada antes de o run ser cortado por `max_wall_seconds`, o que é censura por infraestrutura (BACKLOG 8).

**Recomendação.** Rodar `scripts/fitness_test.py` completo no DeepInfra **e** no Novita no mesmo dia; escolher o que passar nas 5 sondagens com menos 429; fixar `LLM_REQUEST_TIMEOUT=90` no `.env` e no manifesto; registrar a data. Reserva: o outro dos dois.

**Onde entra.** Método › Procedimento (modelo, provedor, quantização, parâmetros de amostragem, timeout, retentativas, com a data de consulta); Ameaças à validade (provedor como parte do tratamento).

**Decisão:** ______ (data: ______)

### Decisão 12. Tetos do run (E4 / G4)

**Situação.** `RUN_MAX_TOKENS=1200000`, `RUN_MAX_WALL_SECONDS=1800`, `RUN_MAX_TURNS=40` são os do piloto, calibrados em tarefa pequena. A E4 exige: escrever **uma** tarefa grande → fumaça paga nela nos dois braços → só então fixar e registrar no `CLAUDE.md` e no manifesto.

**O que decidir.** (i) Qual tarefa grande é a da fumaça (candidatas: as três tomlkit da decisão 1); (ii) a regra de calibração: por exemplo, teto de turnos e tokens = 2× o máximo observado na fumaça nos dois braços, arredondado para cima; (iii) se `test_timeout_s=120` (timeout da suíte por execução) fica, dado que o peewee agora roda em 4,3 s com `suite_targets` ordenado.

**Impacto.** Teto baixo demais transforma "não resolveu" em artefato de teto nos dois braços na faixa grande (o erro que a E4 quer evitar). Teto alto demais só custa dinheiro: o custo escala com o quadrado dos turnos pelo reenvio de contexto.

**Recomendação.** (i) `tomlkit 0561e5de` (4 arquivos, 163 linhas, 1 teste novo); (ii) 2× o máximo observado, nunca abaixo dos valores atuais; (iii) manter 120 s.

**Onde entra.** Método › Procedimento (tetos, com a justificativa da fumaça); `CLAUDE.md` (valores congelados e data).

**Decisão:** ______ (data: ______)

### Decisão 13. Repetições, ordem dos braços e paralelismo da coleta

**Situação.** O desenho tem 3 repetições por célula (12 × 2 × 3 = 72 runs). `scripts/run_collection.py` roda os dois braços de um par em sequência, single-agent sempre primeiro (BACKLOG 8 sugere alternar por repetição, uma linha em `plan_cells`), e aceita `--workers` para rodar células em paralelo por processo.

**Opções.** Repetições: 3 (como desenhado) ou 2 (48 runs, menos poder). Ordem: fixa ou alternada por repetição. Paralelismo: 1 (sequencial, pares próximos no tempo) ou 2+ (mais rápido, mais 429).

**Recomendação.** 3 repetições; alternar a ordem por repetição (implementar, uma linha e um teste); `--workers 1`.

**Onde entra.** Método › Procedimento (ordem de execução, pareamento por semente).

**Decisão:** ______ (data: ______)

### Decisão 14. O que é run perdido, e o que fazer com erro do harness

**Situação, depois da reconciliação de 08/10.** Perda tem uma definição só: `stop_reason` iniciado em `infra_error:` (provedor não atendeu: 401, 402, 403, 408, 409, 429, 5xx, rede, timeout) ou `interrupted:` (Ctrl+C), gravado como `lost: true` no `summary.json` por `src/arms/runner.py`, lido por `harness/attempts.py` (coleta e análise) e por `src/arms/pilot.py` (piloto). Run perdido é reexecutado com a mesma semente e `attempt + 1`, até 3 tentativas; par que esgota sai do denominador. 401 e 402 param a coleta. Corte por orçamento **não** é perda. O que **ainda não está decidido**: um erro que não é de provedor (`error: FileNotFoundError`, espelho ausente, bug nosso) hoje **não é perda** e, na coleta, a tentativa é avaliada como run válido que não resolveu.

**Opções.** (a) Como está: erro do harness conta como fracasso do braço (contamina o desfecho); (b) **parar a coleta** (`CollectionAborted`) em qualquer exceção que não seja de provedor, consertar e retomar: a célula fica pendente e é refeita com a mesma semente; (c) tratar como perda e reexecutar automaticamente (repete o mesmo erro três vezes).

**Recomendação.** (b): é uma mudança pequena em `src/arms/collection.py` com teste. Declarar no texto que erro de instrumentação interrompe a coleta e nunca entra no denominador.

**Onde entra.** Método › Procedimento (perda, reexecução, denominador); Ameaças à validade (seleção: tentativas perdidas por braço são reportadas por `analyze_collection.py`).

**Decisão:** ______ (data: ______)

### Decisão 15. Pontos abertos da revisão de 28/09 (BACKLOG 8)

Cada um pede sim ou não.

1. **403 como moderação de conteúdo** ("input flagged") é resposta ao conteúdo do run, não infraestrutura. Hoje 403 é perda. Opção: distinguir pelo corpo da resposta. Recomendação: manter 403 como perda e registrar o corpo; improvável com Qwen no Novita/DeepInfra.
2. **`resposta vazia (choices=None)`** hoje vira erro de schema (fracasso do orquestrado) depois de esgotar `STRUCTURED_OUTPUT_RETRIES`; no OpenRouter costuma ser 200 com erro de provedor por baixo, e o single-agent não tem esse caminho. Recomendação: classificar como `ProviderError` (perda) nos dois braços.
3. **Validar tarefas e espelhos antes de começar** (`--dry-run` carrega cada tarefa e checa o espelho e o `base_commit`). Recomendação: sim.
4. **SIGKILL/SIGTERM não passam pelo `finally`**: a tentativa fica sem resumo e conta como perdida. Recomendação: aceitar e declarar.

**Onde entra.** Método › Procedimento; Apêndice (tabela de classificação de erro por status HTTP).

**Decisão:** 1 ______ 2 ______ 3 ______ 4 ______ (data: ______)

### Decisão 16. Ablação do refinador de enunciado

Ligada à decisão 7. Cronograma: 5 pares, US$ 0,30 a 0,60, semana 5. Rodar (sim/não) e, se sim, se entra como Resultado ou Apêndice ([04-cronograma.md](04-cronograma.md), seção 6, recomenda Resultado).

**Decisão:** ______ (data: ______)

### Decisão 17. Teste de fumaça: escopo

A E4 pede a fumaça em **uma** tarefa grande (os dois braços, 1 repetição); o cronograma prevê 2 tarefas × 2 braços. Recomendação: a tarefa grande da decisão 12 **mais** uma pequena já validada (`tomlkit-0001`), 1 repetição cada, US$ 0,14 a 0,24 pelo piloto; qualquer defeito de instrumentação encontrado reabre a fumaça depois do conserto.

**Decisão:** ______ (data: ______)

---

## Bloco 4 — Análise

### Decisão 18. Definição de "resolvida por ambos" para a censura das métricas 2 e 3

**Situação.** Implementado em `scripts/analyze_results.py` ([07-e5-4-analise.md](07-e5-4-analise.md)): a tarefa é resolvida num braço quando a **maioria estrita** das repetições admitidas resolve; "por ambos" é o agregado por tarefa. A leitura dura (resolvida em todas as repetições nos dois braços) é uma linha no script e muda quais tarefas entram no Wilcoxon primário.

**Recomendação.** Manter o agregado por tarefa (não privilegia nenhum braço; a fração de repetições resolvidas é reportada ao lado) e declarar. Decidir antes da coleta, nunca depois de ver os dados.

**Onde entra.** Método › Análise (unidade de análise, censura, teste).

**Decisão:** ______ (data: ______)

### Decisão 19. `stop_reason` nulo na métrica 6

Hoje conta como "sem corte" pela definição literal, e o JSON reporta `sem_stop_reason` por braço. Recomendação: manter e, se o número for maior que zero na coleta, tratar o run como perda de instrumentação (decisão 14).

**Decisão:** ______ (data: ______)

### Decisão 20. Dois scripts de análise

**Situação.** `scripts/analyze_results.py` (19/09) emite as sete métricas do estudo, com portões de admissão e faixa ao lado de cada par; `scripts/analyze_collection.py` (28/09) lê o layout da coleta, tira o par perdido do denominador e reporta tentativas perdidas e cortes por orçamento **por braço**, que é o teste de que a reexecução não selecionou runs a favor de um lado.

**Recomendação.** Os dois, com papéis distintos: `analyze_results.py` é a análise de registro (as tabelas do TCC); `analyze_collection.py` é o relatório operacional da coleta e entra como apêndice. Verificar na fumaça que os dois concordam em `n`, perdas e pares.

**Onde entra.** Método › Análise; Apêndice.

**Decisão:** ______ (data: ______)

---

## Bloco 5 — Cronograma

### Decisão 21. Replanejar a partir de 08/10

**Situação.** O cronograma de 17/09 previa as 10 tarefas restantes escritas até 11/10, validação e fumaça de 12 a 18/10, coleta de 19 a 25/10, texto à orientadora em 09/11. Em 08/10 há 2 tarefas de 12. A folga declarada é a semana 9 (16 a 22/11).

**Opções.** (a) Deslocar validação e coleta uma semana (coleta 26/10 a 01/11) e comprimir a escrita de resultados em 10 dias; (b) manter as datas e reduzir o trabalho manual pelas decisões 1(c) e 3(b); (c) as duas coisas.

**Recomendação.** (c), com a ordem de escrita que o cronograma já sugere: primeiro as tarefas dos dois tercis inferiores (garantem a inferência), a tarefa grande da fumaça logo em seguida, as demais grandes por último.

**Decisão:** ______ (data: ______)

---

## Decisões já tomadas (para o texto, sem reabrir)

| # | Decisão | Data | Fonte |
|---|---|---|---|
| J1 | Mutation Score excluído; qualidade só por variação da complexidade ciclomática | 17/09 | [03-metricas.md](03-metricas.md), seção 4 |
| J2 | As oito rodadas pagas anteriores são material metodológico; a coleta definitiva recomeça do zero | 17/09 | [01-inventario.md](01-inventario.md) |
| J3 | Feedback do pytest: o da ferramenta, 8.000 caracteres, cabeça 2/3 + cauda 1/3, nos dois braços (F2) | 19/09 | [07-execucao.md](07-execucao.md), E2 |
| J4 | Reconstrução do contexto por ciclo (F3) é parte da variável independente, com Rangel (2025) | 19/09 | [07-execucao.md](07-execucao.md), E2 |
| J5 | Provedor pinado, sem fallback, com `require_parameters`; provedor é parte do tratamento | 19/09 e 28/09 | [08-escolha-modelo.md](08-escolha-modelo.md); BACKLOG 6 |
| J6 | Erro de provedor é perda, não fracasso; reexecução com a mesma semente; 401/402 param a coleta | 19/09 e 28/09 | [07-e5-2-reexecucao.md](07-e5-2-reexecucao.md); BACKLOG 6 |
| J7 | Laço developer ↔ validator só termina por orçamento; teto próprio só para reprovação semântica | 28/09 | BACKLOG 7.2, D6 |
| J8 | Motivo da reprovação semântica vai ao developer | 28/09 | BACKLOG 7.2, D4 |
| J9 | Timeout por chamada 90 s (p99 = 60 s em 854 chamadas), a fixar junto com o provedor | 28/09 | BACKLOG 6 |
| J10 | "Resolvida num braço" = maioria estrita das repetições admitidas; comparação sempre orchestration − single-agent | 19/09 | [07-e5-4-analise.md](07-e5-4-analise.md) |

## Registro das decisões (preencher à medida que forem tomadas)

| # | Decisão tomada | Data | Onde foi documentada |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |
| 11 | | | |
| 12 | | | |
| 13 | | | |
| 14 | | | |
| 15 | | | |
| 16 | | | |
| 17 | | | |
| 18 | | | |
| 19 | | | |
| 20 | | | |
| 21 | | | |

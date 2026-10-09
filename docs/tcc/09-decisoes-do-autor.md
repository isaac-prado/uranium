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

**Decisão (08/10/2026):** (a) ampliar a verificação nos cinco repositórios atuais, em segundo plano, com teto de um dia de máquina; (b) e (c) só se (a) não fechar 4 médias e 4 grandes.

**Resultado de (a), 08/10/2026** (`mined-v3/RELATORIO.md`, `mined-v3/mineracao.log`): a verificação ampliada (`--max-verificar-por-faixa 100`, histórico inteiro) esgotou o pré-filtro de média e grande nos cinco repositórios (peewee 4 grandes + 12 médias, pygments 3 + 20, sqlite-utils 2 + 0, tomlkit 6 + 0, tqdm 0 + 0, todos verificados) e aceitou **as mesmas 3 grandes (tomlkit) e 2 médias (peewee)** de 19/09. O limite não é o teto de verificação: nos cinco repositórios não existem outros candidatos de média/grande que passem no portão de execução. Motivo dominante: suíte não executa no commit-base (peewee 14 de 16, pygments 23 de 23; commits antigos, anteriores ao layout de testes atual). **(a) está esgotada; a decisão volta ao autor entre (b) e (c).**

**Decisão (08/10/2026, mais tarde): (b).** Suporte a src layout implementado pelo `.pth` no venv de cada repositório (ver [07-execucao.md](07-execucao.md), seção "Suporte a src layout"); jinja, marshmallow e attrs registrados e verdes no HEAD; click adiado por precisar de argumentos de pytest por repositório no oráculo (intocável sem aprovação). Mineração dos três em `mined-v3/mineracao-src-layout.log`.

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

**Decisão (08/10/2026):** alternativa A, oráculo intocado (sub-decisões: 1 não, 2 forte, 3 A, 4 não, 5 separado e declarado, 6 não). Reabrir só se a mineração ampliada não fechar 4 grandes.

### Decisão 3. Segunda solução de referência em todas as 12 tarefas

**Situação.** O portão 3 de [scripts/validate_task.py](../../scripts/validate_task.py) exige **ao menos duas** referências por tarefa ("prova que o oráculo não é travado numa forma"). Escrever o `alternative.patch` é trabalho manual do autor e é a parte mais cara do caminho crítico.

**Opções.** (a) Manter duas referências em todas; (b) exigir duas só nas faixas pequena e média e aceitar uma na grande, declarando; (c) relaxar o portão para uma referência em todas.

**Impacto.** A segunda referência é o que mostra que o oráculo não aceita só a forma do upstream. Sem ela, a validade do oráculo numa tarefa fica apoiada só no commit original. Em tempo: (a) custa cerca de metade do 1,5 dia por tarefa.

**Recomendação.** (a) se o cronograma da decisão 22 fechar; senão (b), com a lista das tarefas de referência única declarada no texto.

**Onde entra.** Método › Materiais (validação das tarefas, os quatro portões); Apêndice (saída de `validate_task.py` por tarefa).

**Decisão (08/10/2026):** (a) duas referências em todas as 12 tarefas, como o portão 3 exige.

### Decisão 22. Critério da faixa média: o que é "atravessar módulos"

**Situação (08/10/2026).** A regra implementada em 19/09 exigia 3 a 7 arquivos-fonte, 40 a 400 linhas **e dois ou mais módulos, com módulo = diretório** ([07-e3-1-mineracao.md](07-e3-1-mineracao.md), seção 1). Em pacote plano (todos os `.py` numa pasta: tomlkit, sqlite-utils, jinja, marshmallow) nenhum candidato pode ser médio por construção. Contagem de candidatos com perfil médio por arquivos e linhas mas um único diretório, nunca verificados por execução (`mined-v3/*.json`): tomlkit 24 (18 não verificados), pygments 28, marshmallow 11, sqlite-utils 6, jinja 4.

**Decisão (08/10/2026): módulo = arquivo `.py`.** A faixa média passa a ser "3 a 7 arquivos-fonte e 40 a 400 linhas de patch"; a condição de diretórios cai. A leitura é a da exigência E3 ("em torno de 5 arquivos, atravessando módulos"): em Python, módulo é o arquivo. `modulos_fonte` continua registrado como campo informativo. Consequência: reclassificar e verificar por execução os candidatos escondidos; a faixa grande não muda.

**Onde entra.** Método › Materiais (definição das faixas, com a data da mudança e o motivo).

### Decisão 23. O conjunto final de tarefas: as 13, todas válidas

**Decisão (08/10/2026): "todos os commits são válidos".** As 13 tarefas de [10-tarefas.md](10-tarefas.md) ficam no estudo: 3 grandes, 4 médias, 6 pequenas. Consequências e desfechos das pendências da seção 5 daquele documento:

- `peewee-0002` fica, com a natureza composta (seis correções num commit) declarada no texto.
- `tomlkit-0003` fica como grande; a faixa é atribuída pelo patch de referência do upstream, não pelo mínimo que o teste oculto exige, e isso vale para todas as tarefas e é declarado no método.
- Os enunciados de `sqlite-utils-0002` e `sqlite-utils-0003` ficam como estão (mostram a saída exata que o teste compara; é especificação, não solução).
- A alternativa de `tomlkit-0005` fica.
- O desenho passa de 12 para **13 tarefas**: 13 × 2 braços × 3 repetições = **78 execuções** na coleta; a estratificação 3/4/6 é declarada como desigual, com a faixa ao lado de cada par na análise. Custo estimado sobe na mesma proporção (04-cronograma.md, seção 4, ×13/12).

**Onde entra.** Método › Materiais (tabela das 13 tarefas, [10-tarefas.md](10-tarefas.md)); Método › Procedimento (78 execuções); Ameaças à validade (estratificação desigual; faixa pelo patch de referência).

### Decisão 24. O developer recebe o enunciado íntegro, com a intent do refinador como anexo

**Situação (09/10/2026).** O developer do orquestrado recebia só a intent do `intent_refiner`, 24% a 68% menor que o enunciado nas fumaças de 08/10 ([07-e4-fumaca.md](07-e4-fumaca.md)); numa reprodução sobre a `tomlkit-0004` a intent dizia "os valores são os do item 6 do relatório", item que o developer nunca via. Custo direto do refinador: 0,2% a 2% do run; custo indireto suspeito: leitura de código 1,8 a 4,4 vezes maior que no single-agent (E1 e fumaça C), compatível com o developer explorar para recuperar o que a paráfrase descartou.

**Decisão (09/10/2026, "válido, desde que melhore"):** o refinador fica (não há sentido em tirá-lo da orquestração); a primeira mensagem do developer passa a ser a mesma string que o single-agent recebe (`Tarefa:` + intent bruta com o enunciado em `goal`, `src/state.py: tarefa_bruta`) seguida de "Intenção estruturada:" com a intent do refinador. Registrado no manifesto em `orchestration_policy.developer_input = "enunciado+intent"`; manifesto v4. Teste: `tests/test_arm_parity.py::TestDeveloperRecebeOEnunciadoIntegro`. Condição do autor: medir se melhora — checagem paga na `tomlkit-0004`, 120 turnos, só o braço orquestrado, contra a fumaça D (5/7, 3,26 M tokens, US$ 0,78). A ablação do refinador (decisões 7 e 16) passa a medir o valor do anexo e fica para depois da coleta. **Resultado da checagem (09/10, [07-e4-fumaca.md](07-e4-fumaca.md) seção 10): não melhorou; 0/7 contra 5/7 da fumaça D, mais leitura e sem rodar a suíte, n = 1. A condição "desde que melhore" não foi atendida nesta execução. Reaberta: manter pelo argumento de desenho, reverter (`git revert 1ad6a07`), ou repetir a célula depois da recarga. Pendente do autor.** **Decidido em 09/10/2026: REVERTIDA.** "Reverter para só a intent faz mais sentido para o protótipo em si." O developer volta a receber só a intent do refinador, como no TFG e nas fumaças A, C e D; manifesto v5 (a forma de v3; v4 existiu só na checagem). O D3 fica declarado em Ameaças à validade e a ablação do refinador (decisões 7 e 16) é o que o mede. `tarefa_bruta`/`intent_bruta` saem junto com a reversão.

**Onde entra.** Método › Tratamentos (o que cada papel recebe; o enunciado chega íntegro aos dois braços); Ameaças à validade (D3 deixa de ser confundidor de informação; resta o anexo como diferença de topologia).

---

### Decisão 25. Teto de turnos por ciclo do developer (`DEVELOPER_CYCLE_MAX_TURNS`)

**Situação (09/10/2026, depois da fumaça G).** Com a memória de trabalho ligada (decisão 8 revista), o developer gastou os 120 turnos num único ciclo e foi cortado antes de submeter: a memória só age a partir do segundo ciclo, e o segundo ciclo só existia se o developer decidisse encerrar antes do corte. O revisor semântico, quando rodou, apontou corretamente os dois critérios que faltavam (eram dois dos testes ocultos), mas com o orçamento já esgotado ([07-e4-fumaca.md](07-e4-fumaca.md) seção 12). O autor: "o orchestration teve o corte em 120 e não conseguiu produzir nada? Ainda precisamos de uma forma para resolução."

**Mecanismo.** `DEVELOPER_CYCLE_MAX_TURNS` (padrão 40; 0 desliga). Ao atingi-lo, o developer volta ao validador com `stop_reason = cycle: ...`, que não é orçamento: o validador roda a suíte e a revisão, e o developer reentra com a memória de trabalho e o veredito, até o orçamento total (`RUN_MAX_TURNS`) ou até o validador aprovar. A reprovação semântica num ponto de checagem **não conta** para `MAX_SEMANTIC_REJECTIONS`, que fica reservado ao laço "developer diz que terminou, revisor discorda". No `result.json`, um run que termina depois de um ponto de checagem registra `concluiu`, o mesmo nome que o orquestrado já usava (`src/arms/runner.py::final_stop_reason`). Manifesto v7, chave `orchestration_policy.developer_cycle_max_turns`.

**Por que é topologia e não vantagem indevida.** É a orquestração decidindo quando checar, que é o papel dela; o single-agent tem o equivalente no driver determinístico, que roda a suíte sempre que o agente para de agir. O prompt de sistema, as ferramentas, os limites compartilhados e o critério de parada ("suíte verde ou orçamento") continuam iguais. O que muda é só com que frequência o braço orquestrado passa pelo validador.

**Impacto.** Mais chamadas de validação por run (uma suíte e uma revisão a cada 40 turnos, custo da revisão em torno de US$ 0,001). Com 120 turnos, até 3 ciclos. Definido depois de fumaças de calibração e antes da coleta; as fumaças A a G rodaram com o equivalente a 0.

**Fumaça H ([07-e4-fumaca.md](07-e4-fumaca.md) seção 13):** quatro ciclos (40/40/32/8), memória e veredito no prompt; o developer desfez a implementação para voltar ao verde depois de dois pontos de checagem vermelhos, e o revisor reprovou com motivo exato. 0/7, US$ 0,23, prompt máximo 25 k contra 71 k sem ciclos. **Decisão (09/10/2026):** implementado com 40 para a fumaça H na `tomlkit-0004` (120 turnos, DeepInfra BYOK). O valor congela junto com os tetos (decisão 12) depois da fumaça. Teste: `tests/test_nodes.py::TestDeveloperTetoPorCiclo`, `::TestGrafoPontaAPonta::test_ciclos_com_memoria_ate_resolver`, `::TestValidatorExecuta::test_reprovacao_no_ponto_de_checagem_nao_conta_para_o_teto`, `tests/test_arm_parity.py::test_mudar_developer_cycle_max_turns_muda_o_manifesto`, `::test_stop_reason_final_nunca_e_cycle`.

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

**Reaberta em 09/10/2026.** O que a reconstrução perdia: a conversa do developer (o que leu, tentou e concluiu), não o que os outros papéis lhe passam (intent, relatório da suíte, veredito), que vai pelo estado. Na fumaça D ([07-e4-fumaca.md](07-e4-fumaca.md) seção 8 e `dados/fumaca-09-10-d/`), o developer submeteu com a suíte visível verde (163/0) no turno 49, foi reprovado pelo revisor semântico, voltou sem memória e quebrou 29 testes refazendo. Na F, 146 turnos sem submeter. O inventário ([01-inventario.md](01-inventario.md), F3) já classificava a reconstrução como "não consequência necessária da topologia".

**Opções apresentadas.** (a) histórico persistente do developer dentro do run; (b) manter o reset e reinjetar só a nota final (`dev_summary`); (c) manter e declarar. Dentro de (a): transcrição completa (igual ao single-agent), registro determinístico curado pela orquestração, ou registro mais síntese escrita pelo modelo (prompt novo, uma chamada a mais por ciclo).

**Decisão (09/10/2026):** (a), na forma de **memória de trabalho com registro determinístico**. Palavras do autor: "Com certeza a A. [...] o developer tem que ter tudo nas mãos. Não um acúmulo de contexto [...] quero que a ORQUESTRAÇÃO seja feita de forma inteligente"; entre as três formas, escolheu o registro determinístico. A cada reentrada o developer recebe, depois da intent e antes do feedback, o registro dos ciclos anteriores (arquivos lidos, buscas, arquivos escritos, execuções de `run_python`, suítes com resultado, nota final) e o diff atual do workspace, truncado em 20.000 caracteres, o mesmo recorte do revisor. Nenhuma chamada extra, nenhum texto do harness além dos títulos (`src/feedback.py::memoria_de_trabalho`). Política `DEVELOPER_MEMORY=ledger` no manifesto (`orchestration_policy.developer_memory`, manifesto v6); `none` reproduz o comportamento de 19/09 e identifica as fumaças A a F. A memória vale só dentro do run; nada atravessa tarefas ou repetições. O texto deixa de atribuir ao protótipo a "limpeza e reinjeção de contexto" de Rangel (2025) como traço de desenho; o custo da memória continua medido pela métrica 2. Registro em [07-execucao.md](07-execucao.md), "Memória de trabalho do developer". **Fumaça G (09/10, [07-e4-fumaca.md](07-e4-fumaca.md) seção 12):** mecanismo gravado e verificado, mas o developer gastou os 120 turnos num só ciclo e a memória não chegou a ser usada; o revisor reprovou com motivo correto (faltavam dois critérios que são dois dos ocultos) e tarde demais. Proposta derivada: teto de turnos por ciclo do developer (`DEVELOPER_CYCLE_MAX_TURNS`) para a orquestração decidir quando checar. Aguarda o autor.

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

**Decisão (08/10/2026):** rodar `scripts/fitness_test.py` completo no DeepInfra e no Novita no mesmo dia e escolher pelo laudo (menos 429 nas 5 sondagens); `LLM_REQUEST_TIMEOUT=90`. Sondagens rodadas em 08/10/2026 ([dados/validacao-08-10/fitness_test.txt](dados/validacao-08-10/fitness_test.txt)): **DeepInfra APTO** (5/5 chamadas corretas, provedor pinado nas 5, 1 assinatura em 5, US$ 0,0005); **Novita NÃO APTO** (5 sondagens sem resposta em 10 min com timeout de 300 s; na repetição com timeout de 90 s, 2/3 corretas e 1 `APITimeoutError`). Resultado: **DeepInfra**, timeout 90 s. Reserva: repetir o laudo do Novita no dia da fumaça; se continuar reprovando, a reserva passa a ser `qwen3-coder-next` na Parasail (08-escolha-modelo.md), com nova calibração.

**Reaberta à noite de 08/10/2026** ([07-e4-fumaca.md](07-e4-fumaca.md), seção 5): o DeepInfra entrou em 429 (`engine_overloaded`, pool compartilhado) e perdeu as duas células da fumaça B; o Novita deixou de servir o modelo. Aptos em 08/10: **Google** (5/5, US$ 0,22/M prompt, quantização não declarada) e **Alibaba** (5/5, 3× mais caro). Opções: (a) pinar Google; (b) DeepInfra com chave própria (BYOK) fora do pool; (c) DeepInfra com espera longa entre tentativas. Fumaça C no Google: 162/162 chamadas atendidas, prompts de até 74 k tokens, zero perdas. **Recomendação: pinar o Google para a coleta inteira; DeepInfra (fp4) só como reserva, com a leva marcada. Decisão pendente do autor.** **Decidido em 09/10/2026: Google.** `OPENROUTER_PROVIDER=Google` no `.env`; DeepInfra (fp4) só como reserva com a leva marcada; quantização do endpoint do Google não informada, declarada como limitação. **Adendo de 09/10 à noite:** o Google também devolveu 429 do pool compartilhado do OpenRouter ([07-e4-fumaca.md](07-e4-fumaca.md), seção 9). O requisito passa a ser **chave própria do provedor registrada no OpenRouter (BYOK)** antes da coleta, em qualquer provedor escolhido; `is_byok` entra no manifesto. Pendente do autor: criar a chave no Google Vertex (ou no DeepInfra) e registrá-la em openrouter.ai/settings/integrations. **Feito em 09/10/2026: chave própria do DeepInfra registrada no OpenRouter (fallback para o pool compartilhado desligado, ZDR no padrão), US$ 25 de crédito no DeepInfra e US$ 3,78 no OpenRouter. Chamada pinada confirmou `provider: DeepInfra`, `is_byok: true`, `cost: 0` no OpenRouter e custo real em `cost_details.upstream_inference_cost`. Decisão 11 final: DeepInfra (fp4, declarado) com chave própria; `OPENROUTER_PROVIDER=DeepInfra`. A telemetria passou a somar OpenRouter + provedor em `cost_usd` e a gravar `is_byok` por chamada e `byok_calls` no `result.json`.**

### Decisão 12. Tetos do run (E4 / G4)

**Situação.** `RUN_MAX_TOKENS=1200000`, `RUN_MAX_WALL_SECONDS=1800`, `RUN_MAX_TURNS=40` são os do piloto, calibrados em tarefa pequena. A E4 exige: escrever **uma** tarefa grande → fumaça paga nela nos dois braços → só então fixar e registrar no `CLAUDE.md` e no manifesto.

**O que decidir.** (i) Qual tarefa grande é a da fumaça (candidatas: as três tomlkit da decisão 1); (ii) a regra de calibração: por exemplo, teto de turnos e tokens = 2× o máximo observado na fumaça nos dois braços, arredondado para cima; (iii) se `test_timeout_s=120` (timeout da suíte por execução) fica, dado que o peewee agora roda em 4,3 s com `suite_targets` ordenado.

**Impacto.** Teto baixo demais transforma "não resolveu" em artefato de teto nos dois braços na faixa grande (o erro que a E4 quer evitar). Teto alto demais só custa dinheiro: o custo escala com o quadrado dos turnos pelo reenvio de contexto.

**Recomendação.** (i) `tomlkit 0561e5de` (4 arquivos, 163 linhas, 1 teste novo); (ii) 2× o máximo observado, nunca abaixo dos valores atuais; (iii) manter 120 s.

**Onde entra.** Método › Procedimento (tetos, com a justificativa da fumaça); `CLAUDE.md` (valores congelados e data).

**Decisão (08/10/2026):** autorizada em 08/10/2026 ("pode rodar os testes de fumaça e os testes que quiser"): fumaça na grande `tomlkit-0002` com os tetos atuais (1.200.000 tokens, 1.800 s, 40 turnos); regra de calibração proposta e ainda a confirmar com o resultado na mão: tetos finais = 2× o máximo observado na fumaça nos dois braços, nunca abaixo dos atuais; `test_timeout_s` = 120 s.

**Resultado da fumaça (08/10/2026, [07-e4-fumaca.md](07-e4-fumaca.md)):** os dois braços resolveram a grande, mas cortados em `max_turns` com a correção já no lugar; tokens (máx. 514 k) e parede (máx. 118 s) longe dos tetos. **Proposta revista após a fumaça B (crescimento superlinear de tokens, 767 k em 36 turnos): `RUN_MAX_TURNS=80`, `RUN_MAX_TOKENS=4000000`, `RUN_MAX_WALL_SECONDS=1800`, `test_timeout_s=120`.** Congelamento pendente da palavra do autor e do limite da chave (US$ 5 hoje; a coleta pode passar disso). **Fumaça C** (Google, 80 turnos, 4 M): a `tomlkit-0004` não foi resolvida por nenhum braço, os dois cortados por turnos (single-agent 0/7, orquestrado 5/7; US$ 0,53 e 0,86). Caminhos na seção 7 de [07-e4-fumaca.md](07-e4-fumaca.md): (a) congelar 80/4 M e declarar; (b) 120/8 M; (c) trocar a tarefa. Recomendação: (a). **Decidido em 09/10/2026 pelo autor: a tarefa grande deve ser resolvida; os tetos sobem, em rodadas de fumaça na `tomlkit-0004`, até que um braço a resolva, e aí congelam.** Próxima rodada: 120 turnos e 8 M tokens, Google. O limite da chave fica em US$ 5 (decisão do autor: usar até esgotar, depois recarregar). **Rodada de 120/8 M (fumaça D, 09/10):** nenhum braço resolveu, os dois em 5/7 com regressão; US$ 1,37 e 0,78. Saldo da chave: US$ 1,23. Próxima rodada só depois da recarga e depois da decisão 24. **Rodada de 160/16 M (fumaça F, 09/10, DeepInfra com chave própria, zero perdas):** nenhum braço resolveu, os dois em **0/7** (pior que 120); único corte em todas as rodadas é `max_turns`, parede e tokens longe do teto; o orquestrado reescreveu 9 módulos e quebrou 114 testes. A premissa "subir até resolver" não se sustenta: subir piorou. **Recomendação revista: congelar 120 turnos / 8 M tokens / 1.800 s (fumaça D, melhor resultado) e aceitar que a `tomlkit-0004` pode ficar sem resolução nos dois braços** ([07-e4-fumaca.md](07-e4-fumaca.md) seção 11, caminhos a-c). Aguarda a palavra do autor.

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

**Decisão (08/10/2026):** autorizada em 08/10/2026: `tomlkit-0002` (grande) e `tomlkit-0001` (pequena), dois braços, uma repetição, pelo `scripts/run_collection.py` (o mesmo caminho da coleta definitiva), DeepInfra, timeout 90 s. Resultado em `docs/tcc/dados/fumaca-08-10/`.

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
| 1 | (a) esgotada no mesmo dia; (b) implementada: jinja, marshmallow, attrs com src layout; click adiado | 08/10/2026 | 09, Decisão 1; 07-execucao (src layout); mined-v3/ |
| 2 | alternativa A, oráculo intocado; reabrir só se faltarem grandes | 08/10/2026 | 09, Decisão 2; 07-e3-3 seção 5 |
| 3 | duas referências em todas as 12 | 08/10/2026 | 09, Decisão 3 |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | memória de trabalho do developer entre ciclos (registro determinístico + diff), `DEVELOPER_MEMORY=ledger`, manifesto v6 | 09/10/2026 | 09, Decisão 8; 07-execucao; src/feedback.py; src/agents/developer.py |
| 9 | | | |
| 10 | | | |
| 11 | DeepInfra (apto 5/5); Novita reprovou por timeout; timeout 90 s | 08/10/2026 | 09, Decisão 11; dados/validacao-08-10/fitness_test.txt; manifesto da fumaça |
| 11 (rev.) | Google para a coleta inteira; DeepInfra reserva | 09/10/2026 | 09, Decisão 11; 07-e4-fumaca seções 5-7 |
| 12 (rev.) | tetos sobem em rodadas na tomlkit-0004 até um braço resolver; chave fica em US$ 5 | 09/10/2026 | 09, Decisão 12; 07-e4-fumaca |
| 11 (final) | DeepInfra com chave própria (BYOK) confirmada `is_byok: true`; custo lido do provedor | 09/10/2026 | 09, Decisão 11; src/config.py; harness/cost.py |
| 12 | fumaça autorizada com os tetos atuais; regra 2× o máximo observado a confirmar | 08/10/2026 | 09, Decisão 12; dados/fumaca-08-10 |
| 12 (rev. 2) | 160 turnos piorou (0/7 nos dois); recomendação de congelar 120/8 M/1.800 s pendente do autor | 09/10/2026 | 09, Decisão 12; 07-e4-fumaca seção 11; dados/fumaca-09-10-f |
| 8 (fumaça) | memória ligada, 120 turnos: 0/7 nos dois, developer não ciclou; proposta de teto por ciclo pendente | 09/10/2026 | 07-e4-fumaca seção 12; dados/fumaca-09-10-g |
| 25 | teto de turnos por ciclo do developer = 40 (fumaça H); reprovação em checagem não conta para o teto semântico; manifesto v7 | 09/10/2026 | 09, Decisão 25; src/agents/developer.py; src/agents/validator.py |
| 12 (proposta) | congelar 120 turnos / 8 M / 3.600 s / ciclo 40 / memória ledger; tomlkit-0004 pode ficar sem resolução; aguarda o autor | 09/10/2026 | 07-e4-fumaca seção 13; dados/fumaca-09-10-h |
| 13 | | | |
| 14 | | | |
| 15 | | | |
| 16 | | | |
| 17 | tomlkit-0002 + tomlkit-0001, 2 braços × 1 repetição, via run_collection.py | 08/10/2026 | 09, Decisão 17; dados/fumaca-08-10 |
| 18 | | | |
| 19 | | | |
| 20 | | | |
| 21 | | | |
| 22 | faixa média: módulo = arquivo .py; condição de diretórios cai; regras congeladas no CLAUDE.md | 08/10/2026 | 09, Decisão 22; CLAUDE.md; 07-e3-1 seção 1; scripts/mine_tasks.py |
| 23 | as 13 tarefas ficam (3/4/6); 78 execuções; pendências do 10-tarefas resolvidas a favor de manter | 08/10/2026 | 09, Decisão 23; 10-tarefas seção 5 |
| 24 | implementada e REVERTIDA no mesmo dia: developer recebe só a intent (protótipo do TFG); manifesto v5; D3 declarado | 09/10/2026 | 09, Decisão 24; 07-e4-fumaca seção 10; CLAUDE.md |

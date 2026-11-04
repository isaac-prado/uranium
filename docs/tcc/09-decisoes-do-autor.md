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

### Decisão 26. Modelo fixo (`qwen/qwen3-coder`) e segundo modelo como trabalho futuro

**Situação (12/10/2026).** Depois das fumaças, o autor perguntou se "deveria haver uma troca de modelos". O modelo é o mesmo nos dois braços ([08-escolha-modelo.md](08-escolha-modelo.md), decisão 11) e é fator fixo do desenho: o estudo compara topologias, não modelos.

**Avaliação registrada.** Trocar agora (i) muda o objeto de estudo e invalida a calibração dos tetos (oito fumaças), o laudo de aptidão e as estimativas de custo; (ii) multiplica o custo: o preço efetivo observado com chave própria foi US$ 0,125 por milhão de tokens (`dados/fumaca-09-10-f` a `-h`, 24,8 M tokens por US$ 3,09), e modelos de fronteira custam uma ordem de grandeza a mais; (iii) o limite do modelo na `tomlkit-0004` é achado para a Discussão, e a comparação não depende de resolução: ocultos passados por teste, regressão, qualidade do código alterado (MI e CC, `harness/quality.py`), custo, turnos e vereditos do revisor são medidos em todo run.

**Recomendação.** Manter o modelo; replicação com um segundo modelo como trabalho futuro ou extensão se sobrar crédito depois da coleta.

**Decisão:** recomendação aceita tacitamente em 12/10/2026 (o autor não pediu a troca e autorizou o início da coleta pela faixa grande); confirmar por escrito: ______

### Decisão 27. Três tarefas com "suíte visível verde" inalcançável

**Situação (14/10/2026).** [14-tres-tarefas-decisao.md](14-tres-tarefas-decisao.md): `pygments-0001`, `sqlite-utils-0002` e `tomlkit-0004` ficam vermelhas na suíte visível com a correção de referência, porque o patch de teste modifica testes visíveis ou um arquivo dourado protegido. Opções: (a) declarar e manter; (b) excluir da análise principal; (c) reconstruir (testes modificados fora do alvo visível, quinto portão) e recoletar 18 runs; (d) substituir.

**Recomendação.** (c) quando houver crédito; (a) no texto até lá.

**Decisão (14/10/2026), palavras do autor: "Vamos seguir a proposta então, iniciar com a rodada 2 no qwen."** (c): as três tarefas ganham `visible_deselect` no `task.json` (pygments-0001: `tests/examplefiles/go/generics.go`; sqlite-utils-0002: os 6 node ids de `test_transform_sql_table_with_(no_)primary_key` que o patch de teste altera; tomlkit-0004: `tests/test_items.py::test_items_can_be_appended_to_and_removed_from_a_table`), retirados da suíte visível do agente, do driver e do validador por `--deselect`, mantidos no oráculo. `scripts/validate_task.py` ganha o quinto portão (suíte visível verde com cada referência, sem o patch de teste). As 18 células dessas tarefas são recoletadas na rodada 2, nos dois braços; as células da rodada 1 ficam versionadas. Faixas inalteradas (o patch de referência não mudou).

### Decisão 28. Refinador v2: enriquecer em vez de resumir

**Situação (14/10/2026).** [15-refinador-analise.md](15-refinador-analise.md): o refinador v1 resume por desenho (sem campo para exemplos, regra "seja objetivo", `is_ready` sempre verdadeiro, 7 de 39 intents mandando escrever testes em área protegida). Nas três tarefas em que o orquestrado zerou e o single-agent resolveu, a intent referia conteúdo que não carregava.

**Decisão (14/10/2026), palavras do autor:** "EXATAMENTE, quero que ele enriqueça, compreenda e facilite. Implemente-o." Aprovação por escrito da mudança de prompt e schema do refinador, como versão nova e política do manifesto, sem tocar a coleta principal:

- `INTENT_REFINER=v2` → `SYSTEM_PROMPT_V2` em `src/agents/intent_refiner.py`: o developer não verá o enunciado; copiar literalmente blocos de código, comandos, tabelas, valores e mensagens; critérios verificáveis por execução; plano com verificação por `run_python`; restrições do ambiente (área de testes protegida, suíte visível pode não cobrir o comportamento novo); não inventar; ambiguidades em `open_questions` com a leitura adotada; `is_ready` sempre true (o usuário não está disponível).
- `StructuredIntentV2` (`src/schemas/intent.py`): `reproduction`, `expected_outputs`, `constraints`, `open_questions` além dos campos v1; `to_markdown()`; `intent_as_text` entrega markdown para v2 e o JSON de sempre para v1. `parse_intent` reconhece a v2 pelas chaves; o estado inicial dos dois braços e o single-agent não mudam.
- Developer e revisor recebem o mesmo texto (`Tarefa:` + markdown). Manifesto v9: `orchestration_policy.intent_refiner`.
- Testes: `tests/test_intent_v2.py` (schema, parse, escolha de versão, prompts do developer e do revisor), `tests/test_arm_parity.py::test_mudar_intent_refiner_muda_o_manifesto`. Suíte: 627 passando.

**O que não entrou na 28 e virou a decisão 29:** revisor que executa e nota de ciclo (abaixo). Clarificação com fonte de verdade ou remoção do nó: pendente.

**Execução.** Coleta própria do braço orquestrado com `INTENT_REFINER=v2`, repetição 1 das 13 tarefas (≈ US$ 1,7), depois da ablação do refinador em curso; pareada por semente com a coleta principal e com a ablação.

### Decisão 29. Revisor que executa e nota de ciclo (rodada 2)

**Situação (14/10/2026).** Diagnóstico da coleta ([12-coleta-resultados.md](12-coleta-resultados.md), seção 6): o revisor semântico lê o diff sem executar e devolveu falsos negativos em 5 runs resolvidos; o developer, depois do reset do ciclo, desfaz ou reescreve em 8 runs porque a memória de trabalho carrega o que ele fez, não por quê.

**Decisão (14/10/2026), palavras do autor: "Vamos seguir a proposta então, iniciar com a rodada 2 no qwen. Força qwen!!!!"** Aprovados por escrito, como políticas do braço orquestrado da rodada 2 (manifesto v10):

- `REVIEW_EXECUTION=on`: com a suíte verde e intent v2, o validador executa cada bloco Python de `reproduction` no código atual (`run_python`, 60 s por bloco, saída truncada em 2.000 caracteres; blocos que não são Python são marcados e não executados) e entrega as saídas reais ao revisor ao lado das saídas esperadas, antes do veredito. As execuções ficam no evento `validation` (`executions`). Com intent v1 ou `off`, nada muda.
- `CYCLE_NOTE=on`: ao bater o teto do ciclo, o developer recebe `NOTA_DE_CICLO` (`src/feedback.py`) e responde sem ferramentas; a resposta entra na memória de trabalho como `nota`. A chamada conta como turno e não acontece com o orçamento esgotado.

**Rodada 2.** Orquestrado nas 13 tarefas × 3 repetições com `INTENT_REFINER=v2`, `REVIEW_EXECUTION=on`, `CYCLE_NOTE=on`, `DEVELOPER_INPUT=intent`; single-agent só nas três tarefas reconstruídas (decisão 27) × 3 repetições; as outras 30 células do single-agent vêm da rodada 1 (braço sem mudança, mesmas sementes, manifesto v7 cujas chaves novas são todas do orquestrado). 57 runs, ≈ US$ 9 a 10. Testes: `tests/test_rodada2.py`. Suíte: 641 passando.

### Decisão 30. Bug do rootdir do pytest: o `visible_deselect` não valia em `runs/` (correção do harness)

**Situação.** Os workspaces dos runs ficam em `runs/` dentro do uranium; o pytest sobe até o `pyproject.toml` do projeto, o rootdir vira a raiz do uranium e os node ids ganham o prefixo `runs/.../workspace/`. O `--deselect` da decisão 27 compara prefixo de node id e não casava nada: a suíte visível das três tarefas reconstruídas continuou contraditória nos primeiros runs da rodada 2 e no run OR-v2 do pygments. O quinto portão passou porque `scripts/validate_task.py` materializa em `/tmp`. Diagnóstico e verificação em [16-ablacao-e-v2.md](16-ablacao-e-v2.md), seção 4.

**O que foi feito (14/10/2026, commit `4f4f80e`).** `src/tools/exec.run_pytest` passa `--rootdir .`; chave `shared_limits.pytest_rootdir` no manifesto; teste que reproduz o cenário. Células afetadas da rodada 2 (pygments-0001, sqlite-utils-0002, tomlkit-0004, todas as repetições gravadas) movidas para `runs/coleta-r2-descartados/` e refeitas com a mesma semente; as 15 células das outras tarefas mantidas. Coleta principal, ablação e v2 não mudam (não tinham deselect). Oráculo intocado.

**Para o autor confirmar.** (a) manter as 15 células da rodada 2 gravadas antes da correção (única diferença para as 10 tarefas: forma do node id na saída do pytest), ou (b) refazer a rodada 2 inteira (≈ US$ 4 a mais). Recomendação: (a), com a chave do manifesto como registro.

**Decisão:** correção aplicada e registrada pelo executor em 14/10/2026; (a)/(b): ______ (data: ______)

### Decisão 31. `run_python` pode reescrever arquivos-fonte (pendente)

**Situação.** No run OR-v2 do peewee-0001, depois de um `replace_in_file` falhar por trecho inexato, o developer reescreveu `peewee.py` por `run_python` (9 694 → 550 linhas) e perdeu o run ([16-ablacao-e-v2.md](16-ablacao-e-v2.md), seção 3.2). `run_python` executa qualquer código no workspace e contorna a correspondência exata do `replace_in_file`. A ferramenta é compartilhada pelos dois braços e está congelada (`shared_limits`).

**Opções.** (a) Nada: comportamento do modelo, igual nos dois braços, fica em Discussão; (b) `run_python` com o workspace somente leitura fora de um diretório de rascunho (muda os dois braços, invalida comparação com as coletas já feitas, exige nova rodada); (c) só registrar na telemetria quando um `run_python` altera arquivos rastreados (não muda o comportamento, dá a contagem para o texto).

**Recomendação.** (a) agora, (c) se houver tempo; (b) só em trabalho futuro.

**Decisão:** ______ (data: ______)

### Decisão 32. Rodada 3: revisor coerente e fim do teto de reprovações (aprovada)

**Situação.** Dos 16 runs orquestrados não resolvidos da rodada 2 ([17-rodada-2.md](17-rodada-2.md)), 4 encerraram porque o revisor aprovou código que o oráculo reprovou (peewee-0002 5/6, sqlite-utils-0003 11/12, pygments-0001 1/2, sqlite-utils-0001 0/5) e 1 porque bateu o teto de duas reprovações no turno 24 com 96 turnos sobrando (attrs-0001 rep3, 2/3). Em 4 das 59 revisões o revisor listou `missing_criteria` e aprovou mesmo assim. Nas tarefas médias o padrão é quase-acerto: 4/6, 5/6, 11/12.

**Opções apresentadas em 14/10/2026.** (1) revisor coerente: revisão que lista critérios não cobertos não aprova (regra do harness, sem tocar prompt); (2) retirar o teto de reprovações: parada só por suíte verde ou orçamento, igual ao single-agent; (3) decomposição por critério, na versão leve (lista de pendências na memória de trabalho) ou completa (nó planejador que fatia a intent em sub-tarefas).

**Decisão do autor (14/10/2026, por escrito).** "1. Perfeito, faz muito sentido. 2. Excelente, retire-o. 3. MUITO ambicioso e interessante, vamos guardar essa carta na manga [...] Mas não vamos executar agora mesmo." Rodar só o orquestrado de novo (rodada 3), 39 runs; o single-agent não muda.

**Implementação.** `REVIEW_STRICT=on` (`src/config.py`; `src/agents/validator.py` rebaixa `is_valid` quando `missing_criteria` não está vazio e grava `strict_coerced` no evento `validation`); `MAX_SEMANTIC_REJECTIONS=0` = sem teto (`src/graph.py`); `orchestration_policy.review_strict`, manifesto v11. Rodada 3 = rodada 2 + estas duas chaves; `off`/2 reproduz a rodada 2. A opção (3) fica como decisão 33 pendente (trabalho futuro ou rodada 4 se o cronograma permitir).

### Decisão 33. Decomposição por critério no orquestrado: planejador (aprovada)

**Situação.** O protótipo do TFG fatia o tempo (ciclos de 40 turnos) e as responsabilidades (papéis), não o problema: o developer ataca todos os critérios de uma vez e, perdendo a conversa a cada ciclo, reexplora e não chega aos arquivos mais distantes nas tarefas médias e grandes ([19-balanco-e-caminhos.md](19-balanco-e-caminhos.md), §4; tomlkit-0004: nenhum run dos dois braços tocou `tomlkit/items.py`, que a referência altera). A hipótese do autor ("quebrar deveria ser melhor quanto pior o caso") é sobre fatiar o problema, e nenhuma rodada até a 3 testou isso.

**Decisão do autor (15/10/2026, por escrito).** "Podemos sim seguir com o planejador fatiando as sub-tarefas, ele precisa de atenção pois será o foco de todas e precisa de autonomia e conhecimento para saber quando fatiar e quando prosseguir. EU QUERO RODAR AS TAREFAS GRANDES COM O ORQUESTRADOR DE QUALQUER FORMA."

**Implementação (rodada 4, manifesto v12).** Nó `planner` (`src/agents/planner.py`, prompt próprio): recebe a intent v2, explora o repositório só com `list_files`/`read_file`/`search_code` por até `PLANNER_MAX_TURNS` turnos contados no orçamento, e devolve um `Plan` (`src/schemas/plan.py`): sub-tarefas com objetivo, arquivos, índices dos critérios e dos blocos de reprodução da intent, e "pronto quando". Fatiar é decisão dele (uma sub-tarefa só quando a mudança é uma). O developer recebe a sub-tarefa corrente (critérios e blocos copiados da intent pelo índice, `src/feedback.py::subtarefa_atual`) e o estado do plano; o validador, além da suíte e da revisão final, confere a sub-tarefa com os blocos dela (`SYSTEM_PROMPT_SUBTAREFA`) e avança o plano: feita → próxima; não feita → mais um ciclo até `SUBTASK_MAX_CYCLES`, depois adiada e, na segunda rodada, abandonada; plano esgotado com a tarefa aberta → replanejamento (`PLANNER_MAX_REPLANS`). Aprovação final com plano aberto encerra; reprovação final com plano aberto não conta para o teto. Execução acumulada dos blocos (decisão 34) entra junto. Rodada 4 = rodada 2 + `PLANNER=on` + `REVIEW_EXECUTION=cumulative`, teto de reprovações 2.

**Decisão:** aprovada em 15/10/2026; só o orquestrado roda (39 runs); tarefas grandes primeiro, como fumaça.

### Decisão 34. Execução acumulada dos blocos de reprodução e "não verificável" ≠ reprovado (pendente)

**Situação.** Na rodada 3 ([18-rodada-3.md](18-rodada-3.md)), 58 dos 221 blocos de reprodução executados pelo validador quebraram com `NameError`/`ImportError` porque cada bloco roda isolado, e 38 das 76 reprovações do revisor tinham um bloco quebrado; sem teto de reprovações, isso consumiu o orçamento de runs cujo código o oráculo aprovaria (peewee-0003: 11 reprovações, 8 reescritas, corte em 120). Rodada 3 fechou em 19/39 contra 23/39 da rodada 2.

**Opções.** (a) Executar os blocos acumulados: o bloco *i* roda precedido dos blocos 1..*i*−1 no mesmo namespace (correção determinística em `src/agents/validator.py::_executar_reproducao`, chave no manifesto); (b) além de (a), regra estrutural: revisão cuja reprovação se apoia só em bloco que não executou não conta como reprovação (o developer recebe o parecer, mas o run não gasta "reprovação"); (c) voltar ao teto 2 da rodada 2 e parar por aí.

**Recomendação.** (a) e manter o teto 2 enquanto o revisor não for recalibrado; (b) exige definir "se apoia só" de forma auditável. Rodada 4 só com aprovação e orçamento (≈ US$ 5,5).

**Decisão:** ______ (data: ______)

### Decisão 35. Revisão de sub-tarefa: calibrar ou substituir (pendente)

**Situação.** Na rodada 4 ([20-rodada-4.md](20-rodada-4.md)), a revisão de sub-tarefa reprovou 68 de 81 vezes; de 186 sub-tarefas, 13 foram marcadas feitas e 108 nunca começaram; 16 dos 24 runs resolvidos fecharam pela revisão final com o plano aberto. O ganho da rodada veio da exploração do planejador e da primeira fatia, não da esteira de sub-tarefas.

**Opções.** (a) Manter como está e reportar; (b) revisão de sub-tarefa só pode reprovar com motivo executável (bloco de reprodução da sub-tarefa que rodou e divergiu da saída esperada); (c) substituir a revisão de sub-tarefa por comparação determinística das saídas dos blocos com `expected_outputs` quando a intent os traz, sem LLM; (d) planejador com menos sub-tarefas (máximo 3) e primeira fatia maior.

**Recomendação.** (b) ou (c) numa rodada 5, se houver orçamento e tempo; senão (a), com o registro de que a rodada 4 mede "planejador + primeira fatia", não "esteira de sub-tarefas".

**Calibração offline (15/10/2026; `scripts/calibrar_comparacao.py` sobre `dados/coleta-r2`, `-r3` e `-r4`; saída em `dados/coleta-r5/calibracao-offline.txt`).** A comparação de texto de `src/verificacao.py`, aplicada à última revisão final de cada run sobre todas as saídas esperadas da intent, usada como barreira dura (saída verificável ausente = reprovação) derrubaria runs que o oráculo aprovou: 4 dos 24 resolvidos da rodada 4, 9 dos 23 da rodada 2, 7 dos 19 da rodada 3. Os motivos estão nos dados: saídas esperadas que descrevem o comportamento atual ("fields(Caixa[str]) falhou: TypeError", attrs-0001), prosa com o valor dentro ("O script deve imprimir '0 de 17 casos divergem'", pygments-0001 rep02), formato diferente do real (`Field(...)` no enunciado, `Attribute(...)` na saída) e blocos copiados numa linha só com `\n` escrito, que não compilam (sqlite-utils-0003 rep02). Das aprovações erradas do revisor (última revisão aprovada, oráculo vermelho), a barreira pegaria 1 das 3 da rodada 4, 3 das 5 da rodada 2 e 4 das 7 da rodada 3. Conclusão: a comparação vale como veredito da sub-tarefa e como subsídio ao revisor, não como barreira na revisão final.

**Decisão do autor (15/10/2026, por escrito), sobre os quatro itens propostos:** "Perfeitamente, a ideia é exatamente essa! Estamos muito alinhados, ir rodando testes para encontrarmos possibilidades e encontrarmos um modelo estável [...] 1. Perfeito! Acredito que teremos um ganho grande nesta etapa. 2. Exato, vamos passar ao developer as informações. 3. Sim, tem que ter. 4. Sim." Os itens viram, respectivamente, as decisões 36 (veredito determinístico da sub-tarefa), 37 (trechos do planejador ao developer), esta (comparação na revisão final) e 38 (planejador mais barato). Rodada 5 = rodada 4 + as quatro; só o orquestrado, 39 runs, mesmas sementes. O autor recarregou o provedor (US$ 18,78 em 15/10) para a fumaça e a rodada; um segundo modelo e a rodada final ficam para recarga posterior.

**Implementação desta decisão (`REVIEW_COMPARE`, manifesto v13).** `advisory` (rodada 5): com a suíte verde, o validador compara, antes do veredito, as saídas esperadas apontadas pelo plano (união de `Subtask.expected`; sem plano ou sem apontamento, todas) com a saída real dos blocos e entrega ao revisor, no prompt, uma linha por saída (encontrada, NÃO encontrada, não verificável) e a regra "uma saída não verificável não prova nada e não é motivo de reprovação" (`REGRA_COMPARACAO`, o que faltava da decisão 34). `strict`: saída verificável ausente reprova sem consultar o revisor (evento `validation` com `deterministic: true`); guardado pela calibração acima. `off` reproduz a rodada 4. O evento `validation` ganha `comparisons`.

### Decisão 36. Veredito determinístico da sub-tarefa (aprovada, rodada 5)

**Situação.** Rodada 4 ([20-rodada-4.md](20-rodada-4.md), §3): a revisão de sub-tarefa, feita pelo modelo, reprovou 68 de 81 vezes e 13 de 186 sub-tarefas foram dadas por feitas. Um "não feita" errado custa até dois ciclos (80 turnos) numa fatia pronta; um "feita" errado custa pouco, porque a revisão final e o oráculo continuam no caminho.

**Decisão (15/10/2026, item 1 da aprovação registrada na decisão 35).** `SUBTASK_CHECK=deterministic` (`src/agents/validator.py::_verificar_subtarefa`), sem chamada ao modelo: com a suíte verde e mudança no workspace, as saídas esperadas que o planejador apontou para a sub-tarefa (`Subtask.expected`, índices da lista numerada da intent) são comparadas com a saída real dos blocos dela (execução acumulada da revisão final, reaproveitada). Alguma verificável ausente → não feita, e o developer recebe a comparação linha a linha e a saída real (`src/feedback.py::comparacao_de_saidas`, sob `SUBTAREFA_CONCLUIDA_NAO`); todas encontradas → feita; nenhuma verificável (sem bloco, sem saída apontada, bloco que não compilou, texto não comparável) → vale a palavra do developer: feita se ele encerrou o ciclo por conta própria (`stop_reason == "concluiu"`), não se bateu o teto do ciclo. Suíte vermelha ou diff vazio → não feita, sem parecer (o feedback de sempre já diz o motivo). Evento `validation` com `scope=subtask`, `deterministic: true`, `basis` (`comparacao`, `palavra_do_developer`, `suite_vermelha`, `sem_mudanca`) e `comparisons`. Adiar, abandonar e replanejar seguem a decisão 33. `llm` reproduz a rodada 4.

### Decisão 37. Trechos lidos pelo planejador vão ao developer (aprovada, rodada 5)

**Situação.** Na rodada 4 o planejador leu, por tentativa, 36,7 mil caracteres em 9,1 chamadas de `read_file` e entregou ao developer só os nomes dos arquivos; o developer releu 12,0 mil caracteres em 7,4 chamadas no primeiro ciclo (`dados/coleta-r5/leituras-planejador-r4.txt`). A perda da faixa média é contexto que se perde entre papéis e entre ciclos ([19-balanco-e-caminhos.md](19-balanco-e-caminhos.md), §4).

**Decisão (15/10/2026, item 2).** O planejador guarda o que `read_file` devolveu, por arquivo (`plan.trechos`; o evento `plan` leva só `trechos_chars`); o developer recebe, dentro da sub-tarefa, os trechos dos arquivos que ela lista, na ordem dela, até `PLANNER_CONTEXT_MAX_CHARS` no total (16 000 na rodada 5; o último que não cabe é cortado com marca; 0 desliga). O prompt do planejador avisa que o que ele ler vai ao desenvolvedor. Compatível com a decisão 8: é conteúdo de um papel do braço, emoldurado por `src/feedback.py::subtarefa_atual`, não transcrição acumulada. O custo em tokens é medido pela métrica 2.

### Decisão 38. Planejador mais barato: 8 turnos, 3 sub-tarefas, primeira fatia com o núcleo (aprovada, rodada 5)

**Situação.** Rodada 4: mediana de 5 sub-tarefas por plano e 12 turnos de exploração; 108 de 186 sub-tarefas nunca começaram; a sub-tarefa "integração e regressão" que o prompt sugeria listava `tests/` em `files` e rendeu negações de escrita (10 na rodada, 6 de `write_file`).

**Decisão (15/10/2026, item 4).** `PLANNER_MAX_TURNS=8` e `PLANNER_MAX_SUBTASKS=3` na rodada 5 (o prompt do planejador lê o teto da política, `system_prompt()`); regras do prompt: a primeira sub-tarefa carrega o núcleo da mudança e as seguintes são complementos; fatiar só quando cada fatia pode ser verificada sozinha por blocos e saídas esperadas próprios; cada sub-tarefa aponta `expected`; saem a regra dos 30 turnos e a sub-tarefa de regressão. Blocos e saídas esperadas passam a sair numerados em `intent_as_text` (é por esses índices que o plano aponta), e blocos copiados numa linha só com `\n` escrito são desescapados (`StructuredIntentV2._desescapar_quebras`). Os padrões de `src/config.py` continuam 12 e 6 (rodada 4); a rodada 5 passa os valores por ambiente e o manifesto os registra.

### Decisão 39. Saída esperada que o código original já produz não verifica nada (correção do executor, rodada 5)

**Situação (16/10/2026, 00:2x).** Falsa partida da rodada 5: dos 4 primeiros runs, 3 cortados por orçamento nas tarefas médias (`runs/coleta-r5-descartados/`). O refinador v2 copia como "saídas esperadas" também as saídas **atuais** que o enunciado mostra para descrever o bug (attrs-0001: `has(Caixa[str]): False`, `fields(Caixa[str]) falhou: TypeError`; peewee-0002: `commit -> OperationalError no such savepoint`), e o planejador as apontou em `expected`. Com a decisão 36 a comparação as exigiu: na attrs-0001 o developer corrigiu, a comparação disse "não encontrada", o revisor (com a comparação no prompt) reprovou "porque `has(Caixa[str])` retorna True" e o developer **desfez a correção** (ciclos 2, 5 e 8); na peewee-0002 a sub-tarefa 1 nunca podia ficar feita. A rodada 4 sobrevivia a isso porque o revisor usava julgamento sobre as mesmas saídas.

**Correção (executor, 16/10/2026; manifesto v14, `orchestration_policy.expected_outputs_base_filter`).** Antes de explorar, o planejador executa os blocos de reprodução no workspace ainda intocado (`src/agents/planner.py::_saidas_ja_produzidas`) e toda saída esperada encontrada nessa execução é marcada como já produzida pelo código original (`plan.saidas_na_base`; `execucoes_base` no evento `plan`): sai de `expected` de toda sub-tarefa (`sanear(excluir_esperadas=...)`), não entra na comparação da sub-tarefa nem na da revisão final (`validator._saidas_na_base`), e o revisor recebe a lista "saídas esperadas que o código original já produzia, fora da comparação". O planejador também recebe a lista no cabeçalho. É a mesma lógica do oráculo (o teste oculto precisa falhar no commit-base): o que o bug já produz não discrimina correção. Quando nada resta verificável, o veredito da sub-tarefa volta à palavra do developer e a revisão final fica como na rodada 4. Os 4 runs da falsa partida foram apartados com README e a rodada relançada do zero, mesmas sementes. Testes: `tests/test_planner.py::TestSaidasQueOCodigoOriginalJaProduz`.

**Para o autor confirmar:** a correção é do instrumento (torna a decisão 36 coerente com o oráculo), aplicada e relançada pelo executor para não gastar a rodada numa falha conhecida; o autor pediu por escrito que a rodada continuasse ("NÃO, continue rodando, a prioridade é sua"), e a mensagem chegou segundos depois da parada.

**Decisão:** ______ (data: ______)

### Decisão 40. Veredito híbrido da sub-tarefa: a palavra do developer não fecha sub-tarefa (aprovada, rodada 6)

**Situação (16/10/2026, fechamento da rodada 5, [21-rodada-5.md](21-rodada-5.md) §5).** Com `SUBTASK_CHECK=deterministic`, quando nenhuma saída esperada da sub-tarefa é verificável o veredito recai na palavra do developer (`stop_reason == "concluiu"`). Nos eventos da rodada 5 isso deu "feita" em 33 de 37 vezes, sempre no mesmo ponto de checagem em que a revisão final reprovava a tarefa; em 16 dos 39 runs nenhuma comparação foi verificável. O plano se esgotava em três ciclos, o replanejamento recriava a mesma sub-tarefa e o developer seguia editando (tomlkit-0001 rep02: correção certa no ciclo 1, `parser.py` reescrito nos ciclos 4 e 5, 74 regressões). Na rodada 4 a revisão de sub-tarefa pelo modelo disse "não feita" em 68 de 81 vereditos e segurava o developer na sub-tarefa com feedback.

**Decisão: aprovada por escrito em 16/10/2026** ("Concordo com essas alterações para a rodada 6, prossiga com as alterações"). `SUBTASK_CHECK=hybrid` (`src/agents/validator.py::_verificar_subtarefa`, `_revisar_subtarefa_pelo_modelo`): suíte vermelha ou diff vazio → não feita, sem o modelo; alguma saída esperada verificável → comparação (decisão 36); nenhuma verificável → revisão de sub-tarefa pelo modelo, a da rodada 4, com a execução já feita e `basis="revisao_do_modelo"` no evento `validation`; `REVIEW_STRICT=on` vale também aí. `deterministic` reproduz a rodada 5; `llm`, a 4. Testes: `tests/test_planner.py::TestRodada6`.

### Decisão 41. Revisor final sem a frase de leniência e coerente de novo (aprovada, rodada 6)

**Situação (16/10/2026).** Com `REVIEW_COMPARE=advisory` o prompt do revisor final traz a regra "uma saída marcada como não verificável não prova nada e não é motivo de reprovação" (`REGRA_COMPARACAO`). Na rodada 5 as aprovações no primeiro ciclo subiram de 7 (1 errada, rodada 4) para 11 (5 erradas), e o revisor aprovou duas vezes listando ele mesmo os critérios 5, 6 e 7 como não cobertos (sqlite-utils-0003 rep02 e rep03; o oculto que falhou é o da CLI, critério 5), o que `REVIEW_STRICT=on` teria rebaixado. As linhas de comparação em si acertaram: com uma saída verificável faltando, 31 reprovações e 1 aprovação.

**Decisão: aprovada por escrito em 16/10/2026.** `REVIEW_COMPARE=neutral`: as mesmas linhas de comparação no prompt do usuário, sem a regra no prompt de sistema (`system_prompt_revisao` só a acrescenta em `advisory` e `strict`); `REVIEW_STRICT=on` volta (decisão 32), com o teto de reprovações mantido em 2, porque na rodada 3 a coerção disparou 3 vezes e o que custou foi tirar o teto ([18-rodada-3.md](18-rodada-3.md) §3). `advisory`/`off` reproduzem as rodadas 5 e 4.

### Decisão 42. Bloco de reprodução que não compila não é evidência (aprovada, rodada 6)

**Situação (16/10/2026).** O refinador v2 copia como blocos de reprodução também trechos que não são Python (texto TOML `a = [{a]`, linha de shell). Executados, morrem em `SyntaxError`; na cadeia acumulada (decisão 34) o bloco que não compila apaga a saída de todos os seguintes. Na tomlkit-0001 rep02 da rodada 5 cinco dos seis blocos eram TOML e o revisor reprovou três vezes a correção certa citando os `SyntaxError`; a rodada 3 já tinha localizado o mesmo defeito do revisor (reprova o que não consegue executar), e a execução acumulada só resolveu o caso dos blocos encadeados.

**Decisão: aprovada por escrito em 16/10/2026.** `REPRODUCTION_COMPILE_CHECK=on` (`validator._blocos_que_nao_compilam`): cada bloco é compilado sozinho (`compile`, sem executar); o que não compila não roda, sai da cadeia dos seguintes e chega ao revisor, ao planejador (execução na base, decisão 39) e ao developer rotulado "(não executado: o bloco não compila como Python e não é evidência; SyntaxError na linha n: ...)"; a comparação o ignora (só blocos executados contam). Manifesto v15, `orchestration_policy.reproduction_compile_check`. `off` reproduz as rodadas 4 e 5. É correção do instrumento, sem prompt novo.

**Complemento após a fumaça 1 da rodada 6 (16/10/2026 14:4x, [22-rodada-6.md](22-rodada-6.md) §3.1).** O rótulo no prompt foi lido como falha: na tomlkit-0003 (bloco corrompido pelo refinador) o revisor final e o de sub-tarefa reprovaram 8 vezes em 8 citando "os exemplos contêm erro de sintaxe", e o developer reverteu a correção certa. Com a chave ligada, o bloco que não executou não entra nos prompts de revisão (`validator._evidencias`); fica só no evento.

### Decisão 43. Comparação final por sub-tarefa; bloco que não rodou torna a saída "não verificável" (correção do executor, para o autor confirmar)

**Situação (16/10/2026, fumaça 1 da rodada 6).** A comparação da revisão final confrontava a união das saídas esperadas apontadas pelo plano com a saída de **todos** os blocos. Saída apontada por sub-tarefa sem bloco de reprodução (sqlite-utils-0003: a tabela de `dedupe_keys`, saídas 7 a 13) ou por bloco que não roda (linhas de shell, saídas 5 e 6) saía sempre "NÃO encontrada": 9 falsos negativos por revisão, e o revisor reprovando por eles em todos os ciclos. A revisão de sub-tarefa já comparava por sub-tarefa (decisão 36) e não tinha o defeito.

**Correção (executor, 16/10/2026).** `validator._comparar_esperadas`: com plano, cada saída esperada é confrontada só com os blocos da sub-tarefa que a aponta (a mesma saída em duas sub-tarefas fica com o melhor estado); sem plano, tudo contra tudo como antes. `verificacao.comparar_saidas`: bloco do conjunto que não rodou conta como quebrado, e saída que falta com bloco parado é "não verificável", nunca "NÃO encontrada" (a regra já valia para bloco que não compilou em execução). Em `REVIEW_COMPARE=neutral` só as linhas com fato chegam ao revisor. Testes em `tests/test_planner.py::TestRodada6`. Vale para a rodada 6 inteira (fumaça 2 e coleta); a rodada 5 não é afetada em reprodução porque suas chaves (`advisory`, `off`) mantêm o comportamento anterior, exceto a regra de `comparar_saidas` para bloco não executado, que ali só mudaria o estado de saídas apontadas a blocos com cerca não-Python.

**Para o autor confirmar:** correção do instrumento feita antes de lançar os 39 runs, para não gastar a rodada num falso negativo conhecido.

**Decisão:** ______ (data: ______)

### Decisão 44. Rodada 7, candidata a decisiva: rodada 4 com teto de um ciclo por sub-tarefa, bloco que não compila fora da evidência e blocos de linha de comando executados (objetivo aprovado por escrito, 22/10/2026)

**Situação (22/10/2026, [22-rodada-6.md](22-rodada-6.md) §5).** Seis rodadas; a melhor é a 4 (24/39, 9/13). O autor decidiu: "eu quero um teste melhor que a rodada 4 para efeito de continuidade e termos um TCC com o desenvolvimento que chegue a um resultado final (várias rodadas até a decisiva) e fazer os 2 testes finais com modelos diferentes"; adicionou US$ 5 à DeepInfra "para finalizarmos os códigos". Evidência das rodadas 4 a 6 (eventos `plan` e `memory`):

- Das 69 sub-tarefas concluídas, 66 fecharam no primeiro ciclo de 40 turnos; o segundo ciclo na mesma sub-tarefa a fechou 3 vezes; nenhuma das 74 sub-tarefas adiadas foi concluída depois. Na peewee-0002 (0 de 9 runs; single-agent 2 de 3 em 87 a 111 turnos) o refinador e o planejador cobrem as cinco correções, e o developer gastou de 53 a 82 turnos na sub-tarefa 1 em todos os 9 runs sem chegar às quatro fáceis; 31 dos 32 runs cortados por orçamento nas rodadas 4 e 6 morreram com sub-tarefa pendente.
- Na sqlite-utils-0003, 5 dos 9 runs passaram os 12 ocultos e perderam por uma regressão só, a saída CSV da CLI (critério 7); os blocos dessa parte são linhas de shell (`python -m sqlite_utils ...`) que nunca rodavam, então nem a comparação nem o revisor viam a saída da CLI.
- O rótulo "não é evidência" (decisão 42) e o filtro de bloco não executado (`_evidencias`) validados na fumaça 2 da rodada 6.

**Composição (executor, 22/10/2026; manifesto v16).** Base: as chaves da rodada 4 (`PLANNER=on`, 12 turnos, 6 sub-tarefas, `SUBTASK_CHECK=llm`, `REVIEW_COMPARE=off`, `REVIEW_STRICT=off`, `PLANNER_CONTEXT_MAX_CHARS=0`, teto de reprovações 2, `REVIEW_EXECUTION=cumulative`, `CYCLE_NOTE=on`, `INTENT_REFINER=v2`), mais: (1) `SUBTASK_MAX_CYCLES=1` (configuração já existente; a sub-tarefa travada é adiada após um ciclo e o developer segue para as outras; a adiada volta ao fim com o orçamento restante); (2) `REPRODUCTION_COMPILE_CHECK=on` (decisão 42 com o filtro dos prompts); (3) `REPRODUCTION_SHELL=on`: bloco de reprodução que é linha de comando roda como processo no workspace (`validator._comando_shell`, `_executar_comandos`), sem shell, só o Python do venv da tarefa ou um script de console instalado nele, com a mesma guarda de arquivo protegido do `run_python`; a saída entra na revisão e na comparação como a de um bloco Python e o bloco fica fora da cadeia acumulada. Diferenças de código em relação ao manifesto v12 da rodada 4 que não dependem de chave: intent em markdown numerada (v13), execução dos blocos na base pelo planejador com o cabeçalho de saídas já produzidas e o campo `expected` no plano (v14), sem efeito com `SUBTASK_CHECK=llm` e `REVIEW_COMPARE=off`. Testes: `tests/test_planner.py::TestRodada7` (+4). Critério de "decisiva": superar a rodada 4 em tarefas (10 ou mais de 13) sem perder na faixa grande.

**Decisão:** objetivo aprovado por escrito em 22/10/2026; composição e lançamento (fumaça em peewee-0002, sqlite-utils-0003 e tomlkit-0003; depois 39 runs, ~US$ 6) aguardam o "pode ir" do autor.

**Resultado da rodada 7 (22/10/2026, 19:58 a 22:26).** 23/39 runs e 9/13 tarefas; rodada 4: 24/39 e 9/13; single-agent 23/39 e 8/13. Grande 4/9 (rodada 4: 5/9), média 6/12 (7/12), pequena 13/18 (12/18). Custo US$ 4,37 (5,67), 10 cortes (16), 6 aprovações erradas (3), conclusão sem corte 29/39 igual ao single-agent, cache gravado 90,7 %. Sub-tarefas: 46 adiadas em algum momento, 2 concluídas depois. **Não atinge o critério de decisiva** (10 tarefas sem perder na faixa grande); pela regra da decisão 45, a configuração decisiva da replicação é a **rodada 4**, salvo decisão contrária do autor. Dois runs morreram por 502 da DeepInfra devolvido no corpo da resposta e saíram como `error:` (pygments-0001 rep01, resolvido no turno 78; peewee-0002 rep03, 0/6): classificador corrigido em `src/config.py`; reclassificar e refazer os dois (attempt02, ~US$ 0,30) **pendente do autor**; o veredito não depende deles. Sinal crítico C1 em peewee-0002 rep02: `exec_test.py` criado por código executado em `run_python`; a guarda recusou e não removeu o arquivo novo, e 16 execuções do developer e 28 do validador foram recusadas até o fim do run (proposta de correção da guarda, intocável, em [23-rodada-7.md](23-rodada-7.md) §4.4, **pendente do autor**). Detalhe em [23-rodada-7.md](23-rodada-7.md) §4; dados em [dados/coleta-r7/](dados/coleta-r7/).

### Decisão 45. Modelos da replicação final: Devstral 2 e DeepSeek-V3.2 (aprovada por escrito, 22/10/2026)

**Situação.** Referencial em [08-escolha-modelo.md](08-escolha-modelo.md) §10 e §10.1. O autor: "Perfeito, então seguiremos com Devstral 2 e DeepSeek".

**Decisão: aprovada por escrito em 22/10/2026.** Duas replicações, cada uma com os dois braços, 13 tarefas × 3 repetições (78 runs), mesmas sementes e tetos, orquestrado na configuração decisiva (rodada 7 se superar a 4; senão, rodada 4): `deepseek/deepseek-v3.2` em modo não-pensante, provedor DeepInfra (fp4; reserva GMICloud fp8), e `mistralai/devstral-2512`, provedor Mistral (único endpoint). Antes de cada coleta: sondagem de aptidão (`scripts/fitness_test.py`: `seed`, `temperature`, `tools`, `tokens_reasoning = 0`, quantização) e fumaça de 3 tarefas nos dois braços. Cobrança: DeepSeek pela chave BYOK da DeepInfra já registrada; Devstral por chave da Mistral em BYOK (preferível, igual ao desenho da decisão 11) ou por crédito do OpenRouter, caso em que `is_byok` fica falso e `byok_calls` zero no `result.json`, declarado no manifesto (o harness só registra, não exige: `harness/cost.py`). Custo projetado dos 78 runs (perfil de tokens da rodada 4 e do single-agent pareado): DeepSeek US$ 15 com cache a 29 sem; Devstral US$ 8 a 46; mais ~US$ 2 de sondagens e fumaças.

### Decisão 46. Gravar os tokens em cache por chamada (aprovada por escrito, 22/10/2026)

**Situação.** O custo em dólares das coletas depende do cache de prefixo do provedor: na DeepInfra, 82 a 95 % do prompt foi cobrado a US$ 0,10/M em vez de 0,30 ([08-escolha-modelo.md](08-escolha-modelo.md) §10.2). Até aqui a fração era inferida do custo pago contra o preço de tabela; o OpenRouter devolve o número em `usage.prompt_tokens_details.cached_tokens`. O autor perguntou "estamos rodando com ou sem cache?" e, diante da proposta de gravar o campo, respondeu: "Com certeza vale a pena executar agora a gravação dos tokens em cache no llm_call".

**Decisão: aprovada por escrito em 22/10/2026.** `payload.tokens_cached` em cada `llm_call`, `tokens_cached` nos totais do `summary.json` e no `cost` do `result.json` (campo opcional no esquema, para os `result.json` anteriores continuarem válidos). Mudança só de observação: nenhum prompt, ferramenta, teto ou chave de manifesto muda, e os dois braços continuam idênticos. A rodada 7 é a primeira coleta com o campo; nas anteriores a fração continua inferida (`scripts/cache_fraction.py` calcula as duas lado a lado). Sonda de US$ 0,0023 em [dados/sondagens/cache-deepinfra-2026-10-22.txt](dados/sondagens/cache-deepinfra-2026-10-22.txt) confirma que o campo chega e que o preço de leitura em cache fecha com o custo cobrado. Registro em [07-execucao.md](07-execucao.md).

### Decisão 47. Guarda da execução: apagar o arquivo protegido novo ao recusar (aprovada por escrito, 22/10/2026)

**Situação.** Na rodada 7, peewee-0002 rep02 ([23-rodada-7.md](23-rodada-7.md) §4.4): código executado pelo developer em `run_python` criou `exec_test.py` na raiz do workspace, que casa com o padrão protegido `**/*_test.py`. A guarda de `src/tools/exec.py` recusou a execução e "reverteu" com `git checkout -- exec_test.py`, que não remove arquivo novo (não rastreado). O arquivo ficou, e todas as execuções seguintes foram recusadas: 16 chamadas de `run_python` do developer (turnos 42 a 120) e 28 execuções de reprodução do validador, que a revisão citou como motivo. Nas rodadas 4 a 6 nenhuma execução do validador foi recusada. A guarda de caminho é intocável sem aprovação; o autor: "Aprovo sim a correção da trava."

**Decisão: aprovada por escrito em 22/10/2026.** `src/tools/exec.py::reverter_protegidos`: ao recusar, arquivo protegido rastreado volta ao commit-base (`git checkout`) e arquivo protegido novo é apagado; o estado dos protegidos é fotografado antes da execução e só o que a execução acrescentou é atribuído a ela, mas tudo é restaurado. `run_python` (developer dos dois braços) e `validator._executar_comandos` (blocos de linha de comando, rodada 7) usam o mesmo helper. Nada muda para quem não toca arquivo protegido; `DEFAULT_PROTECTED_GLOBS` e `src/workspace.py` ficam como estão. Teste: `tests/test_tools.py::TestGuardaDaExecucaoRestauraArquivoNovo` (arquivo novo apagado e execução seguinte aceita; rastreado restaurado; comando do validador com a mesma guarda). Registro em [07-execucao.md](07-execucao.md).

### Decisão 48. Rodada 8: blocos de reprodução consertados pelo enunciado e saída esperada amarrada ao bloco (aprovada por escrito, 22/10/2026)

**Situação.** Pergunta do autor: "como batemos e melhoramos o desempenho em tarefas grandes?". Evidência em [23-rodada-7.md](23-rodada-7.md) §4 e [24-rodada-8.md](24-rodada-8.md) §1: a tomlkit-0004 é teto dos dois braços (referência de 337 linhas no parser; single-agent 3/7 ocultos em todos os runs, orquestrado 0 a 3/7); a faixa grande se decide na tomlkit-0002, uma correção de 10 linhas cujo detalhe (`sep=" = "` na chave pontilhada) o developer errou nos dois runs perdidos da rodada 7, e o revisor aprovou uma vez depois de citar exatamente o espaçamento e uma vez às cegas, porque a cópia do bloco de reprodução feita pelo refinador chegou corrompida (`["a", "b", "c"]` virou `["a\nb\nc`). Na rodada 7, 7 dos 23 blocos que não compilavam eram cópias deturpadas de blocos válidos do enunciado. Barreira automática não serve: a calibração offline pegaria 4 das 6 aprovações erradas e derrubaria 5 runs resolvidos. O autor: "Perfeito, vamos as alterações finais 1 e 2 e rode apenas as fumaças com esse saldo restante para gerar algum insight mínimo".

**Decisão: aprovada por escrito em 22/10/2026 (manifesto v17).** Base da rodada 4 mais `REPRODUCTION_COMPILE_CHECK=on`, `REPRODUCTION_SHELL=on` e duas chaves novas: `REPRODUCTION_SOURCE=statement` (o validador conserta a cópia do refinador pelo enunciado, por código: cerca de markdown perdida é removida e bloco que não compila é trocado pelo bloco Python mais parecido do enunciado, com `fonte` no evento; `src/enunciado.py::reparar_blocos`) e `BLOCK_EXPECTED=statement` (cada bloco Python é amarrado, por código, à "saída esperada" que o enunciado escreve logo depois dele, excluídas as de "hoje"/"atual"; o revisor final e o de sub-tarefa recebem, por bloco e por linha, encontrada / NÃO encontrada na saída real daquele bloco, como informação, sem regra; `pares_esperados`, `esperado_do_bloco`, `comparar_bloco`; `src/feedback.py::COMPARACAO_POR_BLOCO`). O developer continua recebendo só a intent. Nos 13 enunciados o pareamento encontra saída esperada em 5 (tomlkit-0002, 0003, 0004, 0005 e sqlite-utils-0003) e nenhuma nos demais, inclusive attrs-0001, que só traz "Saída hoje". Só fumaças com o saldo restante (~US$ 4,7): 7 tarefas × 1 repetição mais a 2ª repetição da tomlkit-0002, em `runs/fumaca-r8`; os 39 runs ficam para depois de crédito novo. Testes: `tests/test_enunciado.py` e `tests/test_planner.py::TestRodada8`. Registro em [07-execucao.md](07-execucao.md).

**Complemento de 23/10/2026 (correção do executor e modo guardado).** Pergunta do autor: "em vez de aprovar errado, a execução vai ao orçamento; como solucionar isso de fato?". (1) A comparação passa a ser por exemplo do enunciado, agregando os blocos em que o refinador fatiou o exemplo: na fumaça, 3 das 4 linhas "NÃO encontrada" da sqlite-utils-0003 eram falsas por isso, e a última reprovação daquele run tinha as 4 linhas encontradas ([24-rodada-8.md](24-rodada-8.md) §3). Exemplo cuja execução não terminou bem vira "não verificável". (2) `BLOCK_EXPECTED=strict`, guardado: o revisor não pode aprovar com linha NÃO encontrada em exemplo executado; a aprovação é rebaixada com as linhas como motivo (`strict_coerced`). Calibração em 164 runs (rodadas 4 a 7 e fumaça r8): derrubaria 0 resolvidos, pegaria 2 aprovações erradas, 15 escapam porque nenhum exemplo as cobre ([24-rodada-8.md](24-rodada-8.md) §5). **Decidido em 23/10/2026:** o autor adicionou US$ 5 e aprovou a etapa 1 ("prossiga com a etapa 1 de teste, já adicionei os US$5"): fumaça em `strict` (1 de 2, `strict_coerced` 0 vezes) e, confirmada, os 39 runs em `strict`, lançados às 08:06 em `runs/coleta-r8` ([24-rodada-8.md](24-rodada-8.md) §3.1 e §4). Testes: `tests/test_enunciado.py` (11) e `tests/test_planner.py::TestRodada8` e `::TestRodada8Strict` (6).

### Decisão 49. Isolamento do workspace e da execução, e regra C8 do detector (aprovada por escrito, 27/10/2026)

**Achado (23/10/2026, rodada 8, tomlkit-0004 rep01).** O workspace era `git clone --shared` do espelho completo: `master`, tags e commits posteriores ao commit-base ficavam visíveis, e `run_python` rodava sem caixa de areia (disco inteiro e rede). O developer trouxe o `master` de 2026 do tomlkit para dentro do workspace (`__version__` 0.1.1 -> "0.15.2", 4.866 linhas que o modelo não digitou). Varredura em todos os workspaces gravados ([25-vazamento-historico-git.md](25-vazamento-historico-git.md) §2): 5 cópias certas do histórico (a 5ª na rodada 8, tomlkit-0004 rep03, após o fechamento), todas do orquestrado, nenhuma resolvida; 3 resolvidos da coleta principal com código mais parecido com o upstream de hoje do que com a correção da época, indistinguível entre memória do modelo e histórico. Nenhum resolvido veio de cópia do histórico; a comparação entre braços não muda.

**Decisão: aprovada por escrito em 27/10/2026 ("Aprovo o isolamento e a regra de detector").** (1) Workspace só com o commit-base (`src/workspace.py`, `WORKSPACE_HISTORY`): fetch raso do sha, sem remoto, sem tags além de `uranium-base`, sem alternates. (2) Caixa de areia bubblewrap em toda execução de código do agente (`src/tools/exec.py::executar_isolado`): só o workspace gravável, venv e sistema só leitura, sem rede, HOME e /tmp em tmpfs; sem bubblewrap a execução falha alto. (3) Regra C8 em `harness/cheat.py` (código do futuro do upstream, medido contra o espelho local): idêntico a commit futuro, mais perto do ramo principal que da base, arquivo novo com nome futuro; correção com menos de 20 linhas nunca é acusada. (4) Manifesto v18 com `shared_limits.workspace_history` e `shared_limits.sandbox`. Entra depois que a rodada 8 fechar nas condições antigas e antes da replicação (decisão 45). Testes: `tests/test_workspace.py::TestIsolamentoDoHistorico`, `tests/test_tools.py::TestCaixaDeAreia`, `tests/test_harness.py::TestC8CodigoDoFuturo`; suíte 751.

### Decisão 50. Rodada 9: evidência que compila sobre a configuração da rodada 4 (aprovada por escrito, 04/11/2026)

**Situação.** A calibração offline da hipótese H4 ([30-calibracao-h4.md](30-calibracao-h4.md)) sobre os 117 runs orquestrados das coletas finais mostrou que nenhuma regra de parada alternativa do revisor corta metade dos turnos sem pôr de 9 a 33 resoluções em risco, e que 58 das 136 reprovações finais com suíte verde citam `SyntaxError` nos blocos de reprodução copiados pelo refinador (16 runs, 15 resolvidos, 885 turnos depois da primeira reprovação desse tipo; tomlkit-0001 com o patch certo reprovado de 4 a 9 vezes em seis runs de três modelos). A correção existe desde a rodada 6 (`REPRODUCTION_COMPILE_CHECK`, decisão 42) e a rodada 8 (`REPRODUCTION_SOURCE=statement`, decisão 48), mas a configuração da rodada 4, escolhida pela regra da decisão 45 e usada na replicação, tem as duas desligadas.

**Decisão: aprovada por escrito em 04/11/2026 ("perfeito, estou aguardando").** Rodada 9 = rodada 4 mais `REPRODUCTION_COMPILE_CHECK=on` e `REPRODUCTION_SOURCE=statement`; tudo o mais igual (planejador 12/6, `SUBTASK_CHECK=llm`, `REVIEW_COMPARE=off`, `REVIEW_STRICT=off`, `REPRODUCTION_SHELL=off`, `BLOCK_EXPECTED=off`, teto de 2 reprovações, intent v2, memória `ledger`, 40 turnos por ciclo). Só o orquestrado roda (39 runs, Qwen3-Coder na DeepInfra, mesmas sementes); o agente único pareado é o da coleta principal com as três tarefas refeitas. Ordem: fumaça com os três runs da tomlkit-0001 (`runs/fumaca-r9`); se as reprovações com `SyntaxError` sumirem, coleta completa em `runs/coleta-r9`. Custo esperado próximo ao da rodada 4 (US$ 5,67); saldo na DeepInfra US$ 16,41.

**Critérios fixados antes de rodar** (rodada 4 entre parênteses): reprovações finais com suíte verde que citam `SyntaxError` = 0 (28); resolvidos mas cortados por orçamento ≤ 1 (4); runs e tarefas resolvidos ≥ 24/39 e ≥ 9/13 (24/39, 9/13); aprovações erradas ≤ 3 (3); fração dos turnos gastos depois do primeiro verde menor que 55%. Se os quatro primeiros fecharem, a rodada 9 entra no TCC como o teste da hipótese H4a, ao lado da replicação, que não muda. Se não fecharem, o resultado é registrado como negativo e H4a cai.

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

**Resultado da fumaça (08/10/2026, [07-e4-fumaca.md](07-e4-fumaca.md)):** os dois braços resolveram a grande, mas cortados em `max_turns` com a correção já no lugar; tokens (máx. 514 k) e parede (máx. 118 s) longe dos tetos. **Proposta revista após a fumaça B (crescimento superlinear de tokens, 767 k em 36 turnos): `RUN_MAX_TURNS=80`, `RUN_MAX_TOKENS=4000000`, `RUN_MAX_WALL_SECONDS=1800`, `test_timeout_s=120`.** Congelamento pendente da palavra do autor e do limite da chave (US$ 5 hoje; a coleta pode passar disso). **Fumaça C** (Google, 80 turnos, 4 M): a `tomlkit-0004` não foi resolvida por nenhum braço, os dois cortados por turnos (single-agent 0/7, orquestrado 5/7; US$ 0,53 e 0,86). Caminhos na seção 7 de [07-e4-fumaca.md](07-e4-fumaca.md): (a) congelar 80/4 M e declarar; (b) 120/8 M; (c) trocar a tarefa. Recomendação: (a). **Decidido em 09/10/2026 pelo autor: a tarefa grande deve ser resolvida; os tetos sobem, em rodadas de fumaça na `tomlkit-0004`, até que um braço a resolva, e aí congelam.** Próxima rodada: 120 turnos e 8 M tokens, Google. O limite da chave fica em US$ 5 (decisão do autor: usar até esgotar, depois recarregar). **Rodada de 120/8 M (fumaça D, 09/10):** nenhum braço resolveu, os dois em 5/7 com regressão; US$ 1,37 e 0,78. Saldo da chave: US$ 1,23. Próxima rodada só depois da recarga e depois da decisão 24. **Rodada de 160/16 M (fumaça F, 09/10, DeepInfra com chave própria, zero perdas):** nenhum braço resolveu, os dois em **0/7** (pior que 120); único corte em todas as rodadas é `max_turns`, parede e tokens longe do teto; o orquestrado reescreveu 9 módulos e quebrou 114 testes. A premissa "subir até resolver" não se sustenta: subir piorou. **Recomendação revista: congelar 120 turnos / 8 M tokens / 1.800 s (fumaça D, melhor resultado) e aceitar que a `tomlkit-0004` pode ficar sem resolução nos dois braços** ([07-e4-fumaca.md](07-e4-fumaca.md) seção 11, caminhos a-c). Aguarda a palavra do autor. **Fumaças G e H (09/10):** mecanismos do orquestrado (memória, decisão 8; ciclos de 40 turnos, decisão 25) no lugar, 0/7 e 3/7; nenhum corte por tokens em oito runs; um corte por parede por latência do provedor ([07-e4-fumaca.md](07-e4-fumaca.md) seções 12 e 13). **Decisão (12/10/2026), palavras do autor: "acredito que depois de uma gama de testes, conseguimos chegar em um valor final". Congelados: `RUN_MAX_TURNS=120`, `RUN_MAX_TOKENS=8000000`, `RUN_MAX_WALL_SECONDS=3600`, `test_timeout_s=120`; no orquestrado `DEVELOPER_MEMORY=ledger`, `DEVELOPER_CYCLE_MAX_TURNS=40`, `MAX_SEMANTIC_REJECTIONS=2`.** Regra aplicada: turnos pelo melhor resultado observado na grande (120; 160 piorou), tokens pelo máximo observado com folga (8,1 M em 160 turnos; a 120 o máximo foi 6,0 M), parede 2× o máximo observado (1.823 s). A `tomlkit-0004` pode ficar sem resolução nos dois braços e isso é resultado, não artefato de teto. Gravados em `src/budget.py`, `.env.example`, `.env` e `CLAUDE.md`.

### Decisão 13. Repetições, ordem dos braços e paralelismo da coleta

**Situação.** O desenho tem 3 repetições por célula (12 × 2 × 3 = 72 runs). `scripts/run_collection.py` roda os dois braços de um par em sequência, single-agent sempre primeiro (BACKLOG 8 sugere alternar por repetição, uma linha em `plan_cells`), e aceita `--workers` para rodar células em paralelo por processo.

**Opções.** Repetições: 3 (como desenhado) ou 2 (48 runs, menos poder). Ordem: fixa ou alternada por repetição. Paralelismo: 1 (sequencial, pares próximos no tempo) ou 2+ (mais rápido, mais 429).

**Recomendação.** 3 repetições; alternar a ordem por repetição (implementar, uma linha e um teste); `--workers 1`.

**Onde entra.** Método › Procedimento (ordem de execução, pareamento por semente).

**Decisão (12/10/2026):** 3 repetições; `--workers 1`; ordem fixa dentro do par (single-agent primeiro), como implementado em `plan_cells`, sem alternância (não implementada antes do início; fica declarada como limitação); `--retry-delay 300`, `--max-attempts 5`. **A coleta começa pela faixa grande** (3 tarefas × 2 braços × 3 repetições = 18 runs, `runs/coleta/`, iniciada em 12/10/2026 às 21:09), a pedido do autor: "quero que seja feita a comparação [do código gerado nos grandes] e isso para mim, de não ter resultado, é uma falha que não gera resultado científico nenhum". Repetir runs fora da coleta para obter resolução seria escolher o resultado; as repetições do desenho são a forma legítima de obter e comparar o código gerado. Depois, as 10 médias e pequenas no mesmo diretório (a coleta é retomável por célula).

### Decisão 14. O que é run perdido, e o que fazer com erro do harness

**Situação, depois da reconciliação de 08/10.** Perda tem uma definição só: `stop_reason` iniciado em `infra_error:` (provedor não atendeu: 401, 402, 403, 408, 409, 429, 5xx, rede, timeout) ou `interrupted:` (Ctrl+C), gravado como `lost: true` no `summary.json` por `src/arms/runner.py`, lido por `harness/attempts.py` (coleta e análise) e por `src/arms/pilot.py` (piloto). Run perdido é reexecutado com a mesma semente e `attempt + 1`, até 3 tentativas; par que esgota sai do denominador. 401 e 402 param a coleta. Corte por orçamento **não** é perda. O que **ainda não está decidido**: um erro que não é de provedor (`error: FileNotFoundError`, espelho ausente, bug nosso) hoje **não é perda** e, na coleta, a tentativa é avaliada como run válido que não resolveu.

**Opções.** (a) Como está: erro do harness conta como fracasso do braço (contamina o desfecho); (b) **parar a coleta** (`CollectionAborted`) em qualquer exceção que não seja de provedor, consertar e retomar: a célula fica pendente e é refeita com a mesma semente; (c) tratar como perda e reexecutar automaticamente (repete o mesmo erro três vezes).

**Recomendação.** (b): é uma mudança pequena em `src/arms/collection.py` com teste. Declarar no texto que erro de instrumentação interrompe a coleta e nunca entra no denominador.

**Onde entra.** Método › Procedimento (perda, reexecução, denominador); Ameaças à validade (seleção: tentativas perdidas por braço são reportadas por `analyze_collection.py`).

**Decisão (12/10/2026):** (b) na prática operacional: erro que não seja de provedor (`error:`) interrompe a coleta, o defeito é corrigido e a célula é refeita com a mesma semente e `attempt + 1`; a tentativa com `error:` não entra no denominador. A guarda automática (`CollectionAborted` em `error:`) não foi implementada antes do início; o operador monitora o log e aplica a regra manualmente, e cada ocorrência é registrada em [07-execucao.md](07-execucao.md).

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
| 7 | (a) ablação rodada: 13 pares na repetição 1 (OR com enunciado+intent vs OR-v1 da coleta, mesma semente): 8/13 contra 6/13; entra em Resultados como ablação, sem estatística | 14/10/2026 | 09, Decisão 7; 16-ablacao-e-v2; dados/ablacao-refinador |
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
| 12 (final) | **congelados** 120 turnos / 8 M tokens / 3.600 s / timeout 120 s; orquestrado ledger, ciclo 40, teto semântico 2 | 12/10/2026 | 09, Decisão 12; src/budget.py; .env.example; CLAUDE.md |
| 26 | modelo mantido (qwen/qwen3-coder); segundo modelo = trabalho futuro; confirmar por escrito | 12/10/2026 | 09, Decisão 26; 08-escolha-modelo |
| 7/16 (ablação) | ablação do refinador iniciada: orchestration com `DEVELOPER_INPUT=enunciado+intent`, rep. 1 das 13 tarefas, manifesto v8, `runs/ablacao-refinador/`; repetições seguintes conforme o crédito (US$ 4,70) | 14/10/2026 | 12-coleta-resultados seção 6; 13-registro-rodada-1 |
| 27 (pendente) | três tarefas com suíte visível inalcançável (pygments-0001, sqlite-utils-0002, tomlkit-0004): declarar, excluir, reconstruir ou substituir | 14/10/2026 | 14-tres-tarefas-decisao |
| 27 | (c) reconstruir: `visible_deselect` nas três tarefas, quinto portão em validate_task, recoleta de 18 células na rodada 2 | 14/10/2026 | 09, Decisão 27; tasks/*/task.json; scripts/validate_task.py |
| 29 | revisor que executa (`REVIEW_EXECUTION`) e nota de ciclo (`CYCLE_NOTE`), manifesto v10; rodada 2 = 39 OR + 18 SA | 14/10/2026 | 09, Decisão 29; src/agents/validator.py; src/agents/developer.py |
| 28 | **refinador v2 aprovado por escrito** ("EXATAMENTE, quero que ele enriqueça, compreenda e facilite. Implemente-o"): `INTENT_REFINER=v2`, schema `StructuredIntentV2` (reprodução, saídas esperadas, restrições, pontos em aberto), prompt `SYSTEM_PROMPT_V2`, intent em markdown para developer e revisor, manifesto v9; coleta própria do braço orquestrado, nunca misturada com a principal | 14/10/2026 | 09, Decisão 28; 15-refinador-analise; src/agents/intent_refiner.py; src/schemas/intent.py |
| 13 | 3 repetições, workers 1, single-agent primeiro no par, coleta começa pela faixa grande (12/10 21:09) | 12/10/2026 | 09, Decisão 13; runs/coleta |
| 14 | erro do harness interrompe a coleta, célula refeita com a mesma semente, tentativa fora do denominador (regra manual) | 12/10/2026 | 09, Decisão 14; 07-execucao |
| 14 (ocorrência) | reinício da máquina em 12/10 23:53 matou 1 tentativa (sqlite-utils-0003 SA rep1); refeita como attempt02, mesma semente; coleta fechada 78/78 em 13/10 | 13/10/2026 | 07-execucao; dados/coleta |
| 15 | | | |
| 16 | sim, 13 pares × 1 repetição (US$ 1,77, `dados/ablacao-refinador/collection.json`), como Resultado | 14/10/2026 | 09, Decisão 16; 16-ablacao-e-v2 |
| 17 | tomlkit-0002 + tomlkit-0001, 2 braços × 1 repetição, via run_collection.py | 08/10/2026 | 09, Decisão 17; dados/fumaca-08-10 |
| 18 | | | |
| 19 | | | |
| 20 | | | |
| 21 | | | |
| 22 | faixa média: módulo = arquivo .py; condição de diretórios cai; regras congeladas no CLAUDE.md | 08/10/2026 | 09, Decisão 22; CLAUDE.md; 07-e3-1 seção 1; scripts/mine_tasks.py |
| 23 | as 13 tarefas ficam (3/4/6); 78 execuções; pendências do 10-tarefas resolvidas a favor de manter | 08/10/2026 | 09, Decisão 23; 10-tarefas seção 5 |
| 24 | implementada e REVERTIDA no mesmo dia: developer recebe só a intent (protótipo do TFG); manifesto v5; D3 declarado | 09/10/2026 | 09, Decisão 24; 07-e4-fumaca seção 10; CLAUDE.md |
| 28 (resultado) | v2 na repetição 1: 7/13 (OR-v1 6/13, OR-abl 8/13, SA 9/13); intent com 126 % do enunciado; as duas perdas (peewee-0001, pygments-0001) não estão na intent | 14/10/2026 | 16-ablacao-e-v2; dados/refinador-v2 |
| 30 | bug do rootdir do pytest corrigido (`--rootdir .`, `shared_limits.pytest_rootdir`); células afetadas da rodada 2 descartadas e refeitas; (a)/(b) pendente do autor | 14/10/2026 | 09, Decisão 30; 16-ablacao-e-v2 §4; runs/coleta-r2-descartados/README.md |
| 31 (pendente) | `run_python` reescreve arquivos-fonte (peewee-0001 OR-v2) | | 09, Decisão 31; 16-ablacao-e-v2 §3.2 |
| 27 (resultado) | com o deselect efetivo: sqlite-utils-0002 OR 3/3 × SA 0/3 (SA para com suíte verde e falha as 6 versões novas no oráculo); pygments-0001 OR 1/3 × SA 2/3; tomlkit-0004 0/3 × 0/3 | 14/10/2026 | 17-rodada-2 §4; dados/coleta-r2 |
| 29 (resultado) | rodada 2 fechada 14/10 22:16, 48/48, 0 perdidos: OR 23/39 runs (coleta principal 17/39), SA pareado 23/39; por tarefa 7 × 8, sinal p = 0,69; negações 39 → 3; revisor 59 revisões/37 reprovações; 31 notas de ciclo; tempo até solução pior (245 s × 113 s, p = 0,125) | 14/10/2026 | 17-rodada-2; dados/coleta-r2/analise-sete-metricas.md |
| 32 | rodada 3 aprovada por escrito: revisor coerente (`REVIEW_STRICT=on`) e sem teto de reprovações (`MAX_SEMANTIC_REJECTIONS=0`), manifesto v11; só o orquestrado roda de novo (39 runs) | 14/10/2026 | 09, Decisão 32; src/agents/validator.py; src/graph.py |
| 33 (pendente) | decomposição por critério (leve ou com planejador): guardada para rodada 4 / trabalho futuro | | 09, Decisão 33 |
| 32 (resultado) | rodada 3 fechada 15/10 05:0x, 39/39, 0 perdidos: 19/39 (rodada 2: 23/39), por tarefa 5 × 8; 98 revisões, 76 reprovações, coerção disparou 3×; sem teto, falsos negativos do revisor consumiram orçamento (peewee-0003 11 reprovações); rodada 2 segue como configuração final | 15/10/2026 | 18-rodada-3; dados/coleta-r3 |
| 34 (pendente) | execução acumulada dos blocos de reprodução e não-verificável ≠ reprovado; voltar ao teto 2 | | 09, Decisão 34; 18-rodada-3 §2 |
| 33 | planejador aprovado por escrito e implementado (`PLANNER=on`, manifesto v12): explora só com leitura, fatia a intent em sub-tarefas verificáveis, developer uma por ciclo, validador confere e avança, replanejamento; rodada 4 = rodada 2 + planejador + execução acumulada | 15/10/2026 | 09, Decisão 33; src/agents/planner.py; src/schemas/plan.py |
| 34 (parcial) | execução acumulada implementada (`REVIEW_EXECUTION=cumulative`) e usada na rodada 4; 'não verificável ≠ reprovado' entrou só no prompt da revisão de sub-tarefa | 15/10/2026 | 09, Decisão 34; src/agents/validator.py |
| 33 (resultado) | rodada 4 fechada 15/10 19:32, 39/39: 24/39 runs, 9/13 tarefas (SA 8/13, p = 1,0), grande 5/9; tokens por run 2× a rodada 2 (884 k × 464 k), US$ 5,67, 7,8 h, 3 cortes por parede (latência do provedor); 13 de 186 sub-tarefas feitas, 16 dos 24 resolvidos fecharam com o plano aberto | 15/10/2026 | 20-rodada-4; dados/coleta-r4 |
| 35 | comparação determinística das saídas esperadas (`src/verificacao.py`); calibração offline desaconselha barreira dura (derrubaria 4/24 resolvidos da rodada 4, 9/23 da 2, 7/19 da 3); `REVIEW_COMPARE=advisory` na rodada 5, `strict` guardado; aprovação por escrito dos quatro itens (35 a 38); rodada 5 = rodada 4 + os quatro, só o orquestrado | 15/10/2026 | 09, Decisão 35; 21-rodada-5; dados/coleta-r5/calibracao-offline.txt; scripts/calibrar_comparacao.py |
| 34 (final) | "não verificável ≠ reprovado" entra no prompt do revisor final com `REVIEW_COMPARE` ligado | 15/10/2026 | 09, Decisões 34 e 35; src/agents/validator.py |
| 36 | veredito determinístico da sub-tarefa (`SUBTASK_CHECK=deterministic`): saídas apontadas pelo plano comparadas com a execução; nada verificável → palavra do developer | 15/10/2026 | 09, Decisão 36; src/agents/validator.py; src/verificacao.py |
| 37 | trechos lidos pelo planejador entregues ao developer com a sub-tarefa (`PLANNER_CONTEXT_MAX_CHARS=16000`) | 15/10/2026 | 09, Decisão 37; src/agents/planner.py; src/agents/developer.py; src/feedback.py |
| 38 | planejador com 8 turnos e 3 sub-tarefas, primeira com o núcleo; intent numerada; blocos desescapados | 15/10/2026 | 09, Decisão 38; src/agents/planner.py; src/schemas/intent.py |
| 39 (correção) | saídas esperadas que o código original já produz saem da comparação (execução dos blocos na base pelo planejador; manifesto v14); falsa partida da rodada 5 apartada (4 runs, US$ 0,9) e rodada relançada | 16/10/2026 | 09, Decisão 39; src/agents/planner.py; src/agents/validator.py; runs/coleta-r5-descartados/README.md |
| 40 | **aprovada por escrito** ("Concordo com essas alterações para a rodada 6, prossiga"): `SUBTASK_CHECK=hybrid`, comparação quando verificável, senão revisão de sub-tarefa do modelo; palavra do developer nunca fecha sub-tarefa (rodada 5: 33/37 "feitas" por ela, sempre com a revisão final reprovando) | 16/10/2026 | 09, Decisão 40; src/agents/validator.py; tests/test_planner.py::TestRodada6 |
| 41 | **aprovada por escrito**: `REVIEW_COMPARE=neutral` (linhas de comparação sem a regra "não verificável não reprova"; rodada 5: 11 aprovações no 1º ciclo, 5 erradas) e `REVIEW_STRICT=on` de volta, teto 2 mantido | 16/10/2026 | 09, Decisão 41; src/agents/validator.py |
| 42 | **aprovada por escrito**: `REPRODUCTION_COMPILE_CHECK=on`, bloco de reprodução que não compila não roda, sai da cadeia acumulada e é rotulado "não é evidência" (tomlkit-0001 rep02: 5 de 6 blocos eram TOML); manifesto v15 | 16/10/2026 | 09, Decisão 42; src/agents/validator.py; src/config.py; src/arms/runner.py |
| 42 (complemento) e 43 (correção) | fumaça 1 da rodada 6 (US$ 0,63): tomlkit-0003 0/1 em 120 turnos com o revisor citando o rótulo "não compila" 8×; sqlite-utils-0003 com 9 "NÃO encontrada" falsos por revisão. Bloco não executado e linha "não verificável" saem dos prompts de revisão; comparação final por sub-tarefa; bloco que não rodou → "não verificável". Fumaça 2 antes de lançar | 16/10/2026 | 22-rodada-6 §3.1; src/agents/validator.py; src/verificacao.py |
| 44 | rodada 7 (objetivo aprovado por escrito: "quero um teste melhor que a rodada 4", "+5 dol na DeepInfra para finalizarmos os códigos"): rodada 4 + `SUBTASK_MAX_CYCLES=1` + `REPRODUCTION_COMPILE_CHECK=on` + `REPRODUCTION_SHELL=on` (manifesto v16); lançamento aguarda o "pode ir" | 22/10/2026 | 09, Decisão 44; 23-rodada-7; src/agents/validator.py; src/config.py |
| 45 | **aprovada por escrito** ("seguiremos com Devstral 2 e DeepSeek"): replicação final com `deepseek/deepseek-v3.2` não-pensante (DeepInfra) e `mistralai/devstral-2512` (Mistral), dois braços, 78 runs cada, configuração decisiva do orquestrado | 22/10/2026 | 09, Decisão 45; 08-escolha-modelo §10 e §10.1 |
| 46 | **aprovada por escrito** ("vale a pena executar agora a gravação dos tokens em cache no llm_call"): `payload.tokens_cached` por chamada, `tokens_cached` nos totais e no `cost` do `result.json`; só observação, manifesto inalterado; sonda US$ 0,0023 confirma o campo e o preço de cache da DeepInfra; fração inferida das coletas anteriores: SA 95,4 %, OR r6 92,4 %, r5 91,5 %, r4 82,5 % | 22/10/2026 | 09, Decisão 46; 07-execucao; 08-escolha-modelo §10.2; dados/sondagens/ |
| 44 (lançamento) | autor: "PODE IR!" 22/10 19:4x. Fumaça `runs/fumaca-r7` (US$ 0,44) 1/3 resolvida (tomlkit-0003 44 turnos; sqlite-utils-0003 `concluiu` com 10/12 ocultos e regressão no CSV; peewee-0002 orçamento com 3/6 ocultos) com os três mecanismos confirmados nos eventos (sub-tarefas adiadas após 1 ciclo; bloco de CLI com `shell: true`; bloco que não compila fora da evidência); rodada 7 lançada 22/10 19:58 em `runs/coleta-r7` (39 células) | 22/10/2026 | 23-rodada-7 §3–§4; dados/fumaca-r7/ |
| 44 (resultado) | rodada 7 fechada 22/10 22:26, 39/39, 1 tentativa perdida (429): **23/39 runs, 9/13 tarefas** (rodada 4: 24/39, 9/13; SA 23/39, 8/13); grande 4/9, média 6/12, pequena 13/18; US$ 4,37; 10 cortes; 6 aprovações erradas (tomlkit-0002 rep02/rep03 custaram a faixa grande); 46 sub-tarefas adiadas, 2 concluídas depois; cache gravado 90,7 %; **não decisiva**: a regra da decisão 45 aponta a rodada 4 para a replicação (pendente do autor). 2 runs com 502 no corpo da resposta contados como `error:` (classificador corrigido; refazer pendente do autor). Sinal C1 em peewee-0002 rep02 (`exec_test.py` criado por `run_python`; guarda recusou 16+28 execuções até o fim; correção da guarda pendente do autor) | 22/10/2026 | 23-rodada-7 §4; dados/coleta-r7/; src/config.py |
| 47 | **aprovada por escrito** ("Aprovo sim a correção da trava"): ao recusar execução que tocou arquivo protegido, `reverter_protegidos` apaga o arquivo novo e restaura o rastreado, com foto do estado antes da execução; `run_python` e `_executar_comandos` usam o mesmo helper | 22/10/2026 | 09, Decisão 47; 07-execucao; src/tools/exec.py; tests/test_tools.py |
| 48 | **aprovada por escrito** ("vamos as alterações finais 1 e 2 e rode apenas as fumaças"): rodada 8 = rodada 4 + compile check + shell + `REPRODUCTION_SOURCE=statement` (cópia dos blocos consertada pelo enunciado) + `BLOCK_EXPECTED=statement` (saída esperada amarrada ao bloco, por linha, no revisor); manifesto v17; só fumaças (8 runs) com o saldo restante | 22/10/2026 | 09, Decisão 48; 24-rodada-8; src/enunciado.py; src/agents/validator.py; src/feedback.py |
| 48 (fumaça) | `runs/fumaca-r8`, 22/10 23:29 a 23:51, US$ 0,82: **5 de 8 resolvidas, 3 cortes, 0 aprovações erradas** nas 7 tarefas onde a rodada 7 teve 5 (13/21 resolvidas, 4 cortes); revisor citou as linhas esperadas em 9 de 14 reprovações e só aprovou com todas "encontradas" (tomlkit-0002 rep01); perda migra para o orçamento (sqlite-utils-0003 11/12 sem regressão; tomlkit-0002 rep02 reescreveu demais); mecanismo 1 não exercitado (nenhuma cópia deturpada em 8 runs); 39 runs dependem de crédito (saldo ≈ US$ 3,9) | 22/10/2026 | 24-rodada-8 §3; dados/fumaca-r8/ |
| 48 (correção e modo guardado) | comparação por exemplo do enunciado (blocos fatiados pelo refinador agregados; na fumaça 3 de 4 "NÃO encontrada" da sqlite-utils-0003 eram falsas); execução que não terminou bem = não verificável; `BLOCK_EXPECTED=strict` guardado (rebaixa aprovação contra linha NÃO encontrada); calibração em 164 runs: 0 resolvidos derrubados, 2 aprovações erradas pegas, 15 escapam (sem exemplo que as cubra); **autor decide** `statement` ou `strict` nos 39 runs | 23/10/2026 | 24-rodada-8 §2, §3, §5; dados/fumaca-r8/calibracao-por-exemplo-r4-a-r8.txt; scripts/calibrar_por_exemplo.py |
| 48 (fumaça `strict`) | `runs/fumaca-r8-strict`, 23/10 07:56 a 08:04, US$ 0,36: sqlite-utils-0003 resolvida (64 turnos, 12/12, 0 regressões), tomlkit-0002 orçamento (1/1 oculto, 2 módulos de teste sem importar: developer reescreveu `api.py` com `write_file` e perdeu `ws` e `key_value`); comparação por exemplo ao vivo (NÃO encontrada → reprovou; encontrada → aprovou), `strict_coerced` 0 vezes; revisor de sub-tarefa em modo `llm` não vê a suíte (raro: 1 run em 40, 1 em 41, 1 em 8) | 23/10/2026 | 24-rodada-8 §3.1; dados/fumaca-r8-strict/; scripts/subtarefa_suite_vermelha.py |
| 48 (lançamento) | autor adicionou US$ 5 e aprovou a etapa 1 ("prossiga com a etapa 1 de teste, já adicionei os US$5"); **rodada 8 lançada 23/10 08:06** em `runs/coleta-r8` (39 células, `BLOCK_EXPECTED=strict`, manifesto v17); custo previsto ≈ US$ 5; a regra da decisão 45 decide a configuração da replicação quando fechar | 23/10/2026 | 24-rodada-8 §4; runs/coleta-r8 |
| 48 (interrupção e retomada) | coleta r8 morreu com a sessão em 23/10 09:53, 14/39 feitas (rep01 completa: 8/13; attrs-0001 e sqlite-utils-0001 aprovação errada da classe "nenhum exemplo exercita"; peewee-0002, tomlkit-0004, 0005 orçamento; `strict_coerced` 0 vezes); autor: "Pode retornar a rodada 8" → retomada 27/10 nas mesmas condições (célula interrompida vira attempt02, mesma semente) | 27/10/2026 | runs/coleta-r8/collection-orchestration.log |
| 49 | **aprovada por escrito** ("Aprovo o isolamento e a regra de detector"): workspace só com o commit-base, caixa de areia bubblewrap em toda execução do agente, regra C8 no detector, manifesto v18; varredura de 426 workspaces: 5 cópias certas do histórico (nenhuma resolvida), 3 resolvidos indistinguíveis memória/histórico; entra antes da replicação | 27/10/2026 | 25-vazamento-historico-git; dados/sondagens/vazamento-git-2026-10-27.txt; scripts/varredura_vazamento_git.py; src/workspace.py; src/tools/exec.py; harness/cheat.py |
| 48 (resultado) | rodada 8 fechada 27/10 21:46, 39/39, 0 perdidas: **20/39 runs, 7/13 tarefas** (rodada 4: 24/39, 9/13; rodada 7: 23/39, 9/13; single-agent 8/13); grande **6/9** (melhor de todas), média 5/12, pequena 9/18; US$ 4,95, cache 91,3 %; 14 cortes; 7 aprovações erradas, todas em tarefas sem par esperado (attrs-0001 ×3, sqlite-utils-0001 ×3, sqlite-utils-0002); `strict_coerced` 0 em 84 revisões; 2 resolvidas só pelo oráculo (revisor reprovando estado correto); tomlkit-0002 e sqlite-utils-0003 3/3. **Não decisiva: a rodada 4 é a configuração da replicação (decisão 45).** | 27/10/2026 | 24-rodada-8 §4.1; dados/coleta-r8/ |
| 45 (configuração) | pela regra, o orquestrado da replicação roda na configuração da rodada 4 (manifesto v18 com a decisão 49: workspace só com o commit-base e caixa de areia, iguais nos dois braços e nos dois modelos) | 27/10/2026 | 24-rodada-8 §4.1; 09, Decisão 45 |
| 45 (aptidão e fumaça DeepSeek) | sondagem: DeepSeek V3.2@DeepInfra e Devstral 2@Mistral aptos (tool calling 5/5, pino OK, raciocínio 0; DeepSeek não determinístico 3/5); fumaça DeepSeek 27/10 21:59–23:17, US$ 1,43: **4/6** (tomlkit-0003 e sqlite-utils-0003 nos dois braços; peewee-0002 orçamento nos dois), 521/521 BYOK, 125 execuções na caixa de areia sem recusa nem erro, 0 sinais do detector; custo projetado dos 78 runs US$ 20–30; Devstral aguarda chave Mistral BYOK | 27/10/2026 | 26-replicacao §2–§3; dados/sondagens/aptidao-replicacao-2026-10-27.txt; dados/fumaca-deepseek/ |
| 45 (lançamento DeepSeek; Mistral bloqueada) | autor adicionou os dois saldos ("Pronto, adicionei ambos saldos") e pediu para seguir; sonda: DeepSeek@DeepInfra `is_byok` true, raciocínio 0; **coleta DeepSeek lançada 28/10 16:11** em `runs/coleta-deepseek` (78 células, orquestrado da rodada 4, manifesto v18, custo projetado US$ 20–30); Devstral: chave BYOK registrada, mas a Mistral devolve 429 código 1300 em 4 de 4 chamadas; crédito pré-pago não muda a faixa de limites, falta ativar pay-as-you-go (**pendente do autor**) | 28/10/2026 | 26-replicacao §4–§5; dados/sondagens/mistral-byok-429-2026-10-28.txt |
| 45 (fumaça e lançamento Devstral) | autor ativou pay-as-you-go na Mistral (Devstral 2 não existe no plano gratuito; crédito não muda a faixa), sonda OK às 16:31; fumaça 16:31–17:06, US$ 0,97: **5/6** (DeepSeek 4/6; peewee-0002 resolvida no single-agent), 513/513 BYOK servidas pela Mistral, 137 execuções na caixa de areia sem recusa, 0 estouros, detector 0/0, cache 92,4 %; **coleta Devstral lançada 28/10 17:07** em `runs/coleta-devstral` (78 células, em paralelo com a do DeepSeek); autor ligou recarga automática e teto mensal de US$ 40; conferir no fechamento o uso do console da Mistral (US$ 1,35 exibidos contra US$ 0,37 somados) | 28/10/2026 | 26-replicacao §5–§7; dados/fumaca-devstral/; dados/sondagens/mistral-byok-429-2026-10-28.txt |
| 45 (resultado Devstral) | coleta Devstral fechada 28/10 22:48, 78/78, 0 perdidas: **single-agent 28/39 e 9/13, orquestrado 30/39 e 10/13** (grande 1/3 × 2/3, média 4/4 × 3/4, pequena 4/6 × 5/6); tokens mediana 1,00M × 0,53M (Wilcoxon p = 0,031, única diferença significativa), resolução p = 1,0; cortes 12 × 7; 3 aprovações erradas, 5 resolvidos só pelo oráculo; 5.392/5.392 BYOK, detector 0/0, 0 estouros; mesmo sinal da rodada 4 (+1 tarefa). **Cobrança da Mistral ≈ 4 a 5× o `cost_usd` reportado** (US$ 9,70 reportados × ≈ US$ 50 de tabela; DeepInfra confere 1,00): métrica de custo em dólares do Devstral usa o console da Mistral, valor final pendente do autor | 28/10/2026 | 26-replicacao §8; dados/coleta-devstral/; dados/sondagens/mistral-byok-429-2026-10-28.txt |
| 45 (resultado DeepSeek e síntese) | coleta DeepSeek fechada 29/10 06:03 (13 h 52), 78/78, 0 perdidas: **single-agent 26/39 e 9/13, orquestrado 26/39 e 9/13** (grande 3/9 × 6/9 runs, média 9/12 × 8/12, pequena 14/18 × 12/18); nenhuma das sete métricas com p < 0,05 (tempo p = 0,055, orquestrado mais lento); 7 aprovações erradas, todas em sqlite-utils; 5 resolvidos só pelo oráculo, todos no orquestrado; 5.777/5.777 BYOK, cobrança real US$ 13,58 (DeepInfra confere), detector 0 críticos e 1 aviso C6 (run não resolvido). Síntese das três coletas (26-replicacao §10): topologia não muda a resolução em nenhum modelo (OR − SA entre 0 e +1 tarefa); único padrão repetido é a faixa grande a favor do orquestrado; custo da topologia varia com o modelo (Devstral metade dos tokens, DeepSeek igual e mais lento) | 29/10/2026 | 26-replicacao §9–§10; dados/coleta-deepseek/ |
| 40–42 (lançamento) | fumaça 2 (`runs/fumaca-r6b`, US$ 0,42) 3/3: tomlkit-0003 20 turnos, tomlkit-0001 27, sqlite-utils-0003 12/12 no orçamento; rodada 6 lançada 16/10 14:55 em `runs/coleta-r6` (39 células, manifesto v15); limitação residual: comparação não distingue saída errada de saída que nenhum bloco da sub-tarefa produz | 16/10/2026 | 22-rodada-6 §3.2 e §4; dados/fumaca-r6b |
| 40–43 (resultado) | rodada 6 fechada 16/10 18:45, 39/39, 1 tentativa interrompida (fechamento do editor): **19/39 runs, 6/13 tarefas** (rodada 5: 18/39, 6/13; rodada 4: 24/39, 9/13; SA 8/13; p = 0,69); grande 4/9, média 4/12, pequena 11/18; aprovações erradas 7 → 4; tokens por run 1,30 M (2× a rodada 5); 16 cortes. Causa comum às rodadas 5 e 6: saídas esperadas do enunciado não são oráculo literal (attrs-0001 `Field`/`Attribute`, `'Comum[str]'`). Rodada 4 segue como melhor; crédito restante ~US$ 4,51. Pendente do autor: configuração final e segundo modelo | 16/10/2026 | 22-rodada-6 §5; dados/coleta-r6 |
| 35–39 (resultado) | rodada 5 fechada 16/10 10:4x, 39/39, 1 tentativa perdida (queda de energia): **18/39 runs, 6/13 tarefas** (rodada 4: 24/39, 9/13; SA 23/39, 8/13; p = 0,73); grande 5/9, média 4/12, pequena 9/18; 7 aprovações finais com oráculo vermelho (rodada 4: 3), 5 no primeiro ciclo sem saída comparável; 33 das 37 sub-tarefas feitas pela palavra do developer; tokens por run 614 mil; US$ 5,61. Rodada 4 segue como melhor resolução; próximos passos (a)/(b) pendentes do autor | 16/10/2026 | 21-rodada-5 §5; dados/coleta-r5 |
| 50 | **aprovada por escrito** ("perfeito, estou aguardando"): rodada 9 = rodada 4 + `REPRODUCTION_COMPILE_CHECK=on` + `REPRODUCTION_SOURCE=statement`, só o orquestrado, 39 runs, Qwen3-Coder/DeepInfra, mesmas sementes; fumaça tomlkit-0001 ×3 antes; critérios fixados antes de rodar (SyntaxError 0, resolvidos cortados ≤ 1, ≥ 24/39 e 9/13, aprovações erradas ≤ 3, turnos após o verde < 55%) | 04/11/2026 | 09, Decisão 50; 30-calibracao-h4.md |

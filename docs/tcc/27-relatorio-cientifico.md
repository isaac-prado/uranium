# Topologia de agentes de IA na correção de defeitos em software: um experimento controlado com três modelos de linguagem

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 29 de outubro de 2026

Relatório científico consolidado do experimento Uranium. Reúne desenho, construção do instrumento, todas as fumaças e rodadas, os resultados das três coletas, a validação das proposições, as ameaças à validade, uma revisão de código do harness final e a agenda de melhorias. Cada número vem acompanhado do arquivo de origem em `docs/tcc/` ou `docs/tcc/dados/`; nada aqui foi estimado sem arquivo. Escrito para servir de base ao texto do TCC e para ser entregue a um assistente de redação externo (apêndice A traz o prompt genérico).

---

## Resumo

**Contexto.** A literatura de "Engenharia de Software 3.0" sustenta que decompor um agente de IA em papéis especializados (refinar a intenção, planejar, desenvolver, revisar) melhora a manutenção de software em relação a um agente único operado por um laço determinístico (ES 2.0). A alegação raramente é testada com o resto constante.

**Método.** Construímos um instrumento que mantém idênticos modelo, provedor, semente, prompt de sistema, conjunto e ordem de ferramentas, enunciado, tetos e critério de parada, e varia só a topologia: `single-agent` (laço pensa→ferramenta com operador determinístico) contra `orchestration` (grafo LangGraph com refinador de intenção, planejador, developer, validador). Treze tarefas reais mineradas de cinco repositórios Python (tomlkit, peewee, sqlite-utils, pygments, attrs), estratificadas em três faixas por tamanho do patch de referência, validadas por quatro portões com duas soluções de referência e oráculo oculto. Três repetições com sementes pareadas por braço. Sete métricas definidas a priori; testes exatos pareados por tarefa. O orquestrado passou por oito rodadas de engenharia (234 runs pagos só nelas) até fixar a configuração "rodada 4", replicada depois em dois outros modelos de laboratórios distintos.

**Resultados.** Em 234 runs das três coletas finais (Qwen3-Coder, DeepSeek V3.2, Devstral 2; 117 pares run a run com a mesma semente), o orquestrado resolveu 80 e o agente único 77 (McNemar exato p = 0,70; `dados/coleta-deepseek/agregado-tres-modelos.txt`). Por tarefa, a diferença ficou entre 0 e +1 tarefa em 13 a favor do orquestrado em cada modelo, nenhuma significativa. A única métrica com p < 0,05 foi o consumo de tokens no Devstral 2: o orquestrado gastou cerca da metade (Wilcoxon exato p = 0,031, `26-replicacao.md` §8.2). O único padrão repetido nos três modelos é a faixa grande: orquestrado 16/27 runs contra 11/27 (p = 0,125), com a faixa média na direção oposta, 24/36 contra 30/36 (p = 0,070). Quatro tarefas são teto (18/18 nas seis células), uma é piso (0/18) e oito discriminam. As aprovações erradas do revisor do orquestrado se concentram nas tarefas em que nenhum exemplo do enunciado exercita o critério oculto.

**Conclusão.** Com o resto constante, a topologia não muda a taxa de resolução de forma detectável nesta escala; muda o perfil de custo conforme o modelo e parece ajudar em funcionalidades grandes e atrapalhar em correções médias com vários comportamentos. O estudo mostra também, por simulação, que o desenho de 13 tarefas herdado do TFG não tem poder para detectar nem um efeito de 30 pontos percentuais no desfecho por tarefa; a contribuição metodológica (instrumento de paridade, oráculo oculto com detector de trapaça e caixa de areia, pareamento por semente, replicação em três modelos) é o que torna o resultado nulo informativo.

---

## 1. Introdução

### 1.1 Pergunta e enquadramento

A pergunta, na formulação do projeto: "em tarefas reais de manutenção de software, com o mesmo modelo de linguagem, as mesmas ferramentas e o mesmo enunciado, a decomposição em papéis especializados resolve mais tarefas, e a que custo, em comparação com um agente único?" (`02-resumo-cientifico.md`, l. 11). A hipótese é declarada neutra, com teste bicaudal (`02-resumo-cientifico.md`, l. 13), porque as evidências preliminares do piloto apontavam ora para um lado ora para o outro conforme o defeito de instrumentação ativo. O inventário registra que não existe H1/H2 numerada em nenhum documento e documenta a contradição entre fontes anteriores que usavam hipótese direcional (`01-inventario.md`, l. 28 e 41).

O enquadramento ES 2.0 / ES 3.0 é mantido por homologia estrutural: no braço `single-agent` uma política determinística ocupa a posição do operador humano (roda a suíte, devolve o erro cru); no braço `orchestration` os papéis são internos ao sistema (`PROMPT_AUDITORIA.md`, l. 18). O estudo com participantes humanos que o TFG prometia (cerca de cinco desenvolvedores) foi movido para trabalhos futuros, porque a variância individual excederia o efeito de topologia; ganho de validade interna ao custo de validade externa (`PROMPT_AUDITORIA.md`, l. 18; `02-resumo-cientifico.md`, l. 21).

### 1.2 O que a proposta original prometia e o que o estudo mede

O TFG prometia medir produtividade, autonomia, qualidade dos artefatos, rastreabilidade e custo, com Maintainability Index, Cyclomatic Complexity e Mutation Score (`01-inventario.md`, l. 88). O mapeamento para as sete métricas finais está em `03-metricas.md` e `01-inventario.md` (l. 92 a 100):

| promessa do TFG | destino | motivo |
|---|---|---|
| Cyclomatic Complexity | métrica 5, como variação (depois menos antes), exploratória | valor absoluto é do repositório, não do agente |
| Maintainability Index | excluído | saturou em 0,0 em 100% dos resultados do piloto (módulos de 1.294 e 5.239 linhas), risco R2 |
| Mutation Score | excluído | mede a força de uma suíte de testes; nenhum braço escreve testes (área protegida), logo mediria a suíte do repositório, idêntica nos dois braços |
| Cobertura | excluída | função nunca chamada |
| Índice de autonomia L0 a L4 | excluído; autonomia virou "conclusão sem corte" (métrica 6) | constante entre braços sem humano no laço |
| Rastreabilidade | não é métrica; virou portão de admissão do dado | provedor pinado em toda chamada, rede isolada na avaliação, trilha válida com um só `run_end` |
| Produtividade | métrica 3, tempo de parede | sem humanos, produtividade é eficiência do sistema |
| Custo | métrica 2, tokens testados, dólares e chamadas reportados | tokens independem de tabela de preço |

### 1.3 Hierarquia de desfechos fixada a priori

Antes da coleta, o protocolo fixou (`PROMPT_AUDITORIA.md`, l. 22 a 26; `03-metricas.md` §2): (1) taxa de resolução como desfecho primário, descritivo por run e testado por sinal pareado bilateral por tarefa; (2) custo em tokens como primário inferencial, Wilcoxon pareado sobre tarefas resolvidas por ambos, com censura declarada; (3) resolução bloqueada por trapaça separada; (4) seleção estratificada por tamanho do patch; (5) tempo, consistência, complexidade, conclusão sem corte e violações como secundárias ou descritivas. O próprio documento de métricas já advertia que "com 12 tarefas e 8 concordâncias, [o teste de sinal] não pode atingir 5% em nenhum cenário" (`03-metricas.md` §2).

---

## 2. Método

### 2.1 Desenho

Dois braços, mesma tarefa, mesma semente por repetição (`seed_for_repetition(20260820, k)` = 20260821, 20260822, 20260823; `13-registro-rodada-1.md` §2), três repetições, 13 tarefas: 3 grandes, 4 médias, 6 pequenas (decisão 23, `09-decisoes-do-autor.md`, l. 91 a 97). Unidade de análise: a tarefa; valor por tarefa e braço é a maioria (resolução) ou a mediana (contínuas) das três repetições; pareamento entre braços na mesma tarefa (`03-metricas.md` §2). A alegação causal depende de os braços serem idênticos em tudo menos na topologia; `tests/test_arm_parity.py` falha se qualquer constante que deveria ser igual divergir, e toda chave que legitimamente difere está em `CHAVES_QUE_PODEM_DIFERIR` com justificativa (`CLAUDE.md`, "Paridade e manifesto").

### 2.2 Os dois braços

**single-agent.** Laço pensa→ferramenta com sete ferramentas (leitura, busca, escrita, substituição, execução de Python, execução da suíte); um operador determinístico roda a suíte visível e devolve a saída crua; para com suíte verde ou orçamento (`05-stack.md`, l. 12 a 38).

**orchestration.** Grafo LangGraph com refinador de intenção (v1 do TFG, que resume; v2, que copia reprodução, saídas esperadas e restrições literalmente e numera critérios verificáveis, decisão 28), planejador com ferramentas só de leitura que fatia a intent em sub-tarefas (decisão 33), developer que recebe só a intent e a sub-tarefa corrente (nunca o enunciado cru; decisão 24 revertida em 09/10/2026) e volta ao validador a cada 40 turnos com memória de trabalho determinística (decisões 8 e 25), validador que executa os blocos de reprodução de forma acumulada e faz a revisão semântica final, com teto de 2 reprovações (`CLAUDE.md`, "Intocáveis"). Mesmo prompt de sistema e mesma ordem de ferramentas que o single-agent; toda mensagem de protocolo ao agente vive em `src/feedback.py` e nenhum braço tem texto próprio. A configuração final do orquestrado ("rodada 4") é descrita na seção 3.4.

### 2.3 Tarefas, faixas e portões

Tarefas mineradas por execução: só entra candidato cujo teste do upstream falha no commit-base e passa no commit de correção (`07-e3-3-breaking-change.md`, l. 18 a 26). Da primeira mineração (90 candidatos examinados em três repositórios, 54 aceitos, 49 num único arquivo, mediana 13,5 linhas; `02-resumo-cientifico.md`, l. 37 a 41) à remineração com pré-filtro por `git log --name-status`, tetos 12 arquivos/800 linhas e repositórios novos (`07-e3-1-mineracao.md`, l. 25 a 39), o resultado foi 3 grandes, 15 médias e 48 pequenas em `mined-v4` após a redefinição "módulo = arquivo `.py`" (decisão 22). Faixa calculada por função pura sobre o patch de referência do upstream (`scripts/mine_tasks.py::calcular_faixa`, regra em `CLAUDE.md`): grande = 3 ou mais arquivos-fonte, 80 ou mais linhas, mais testes novos que modificados e assunto do commit que não começa por fix/bug; média = 3 a 7 arquivos e 40 a 400 linhas; pequena = 1 ou 2 arquivos e 10 a 50 linhas.

Quatro portões por tarefa, com duas soluções de referência (`PROMPT_AUDITORIA.md`, l. 122; `dados/validacao-08-10/validate_task_final.txt`): suíte verde no commit-base; teste oculto vermelho na base; cada referência aplica, resolve, não regride e não dispara o detector; patch de trapaça plantado é detectado e reprovado apesar do oráculo. Quinto portão acrescentado em 14/10/2026 (decisão 27): com a referência aplicada e sem o patch de teste, a suíte visível do agente fica verde; os testes que o upstream modificou saem da suíte visível por `visible_deselect`, iguais nos dois braços, e o oráculo continua avaliando tudo (`14-tres-tarefas-decisao.md`).

Enunciados escritos pelo autor em português, com comportamento observado, comportamento esperado numerado, blocos de reprodução com saída esperada e critérios de aceitação (exemplo: `tasks/tomlkit-0004/statement.md`).

### 2.4 Oráculo, detector, isolamento

O oráculo (`harness/oracle.py`) aplica o patch de teste oculto e roda fail-to-pass, pass-to-pass e regressão com rede isolada; `resolved` exige ocultos verdes, sem regressão e sem trapaça. O detector (`harness/cheat.py`) tem regras C1 a C8; C8 (27/10/2026, decisão 49) compara os arquivos alterados com o histórico futuro do upstream no espelho local. A guarda de caminho barra escrita em `tests/` e em arquivos de configuração; uma execução que toca arquivo protegido é recusada e o arquivo é revertido (decisão 47). Desde a decisão 49 o workspace nasce só com o commit-base (fetch raso, sem remoto, tags ou alternates) e toda execução de código do agente roda em caixa de areia bubblewrap sem rede, só com o workspace gravável (`25-vazamento-historico-git.md` §3).

### 2.5 Tetos, provedor, manifesto

Tetos congelados em 12/10/2026 (decisão 12): 120 turnos, 8 M tokens, 3.600 s de parede, 120 s por execução de suíte; no orquestrado, memória `ledger`, ciclo de 40 turnos, 2 reprovações semânticas. Turnos são o orçamento; tokens e parede são rede de segurança (`CLAUDE.md`, "Tetos do run"). Provedor pinado por chamada (`require_parameters`, `allow_fallbacks: false`), chave própria do provedor registrada no OpenRouter (BYOK), `byok_calls == llm_calls` exigido na coleta. Tudo que muda o comportamento de um braço vai ao manifesto (`orchestration_policy`, `shared_limits`, `budget`, `llm`); duas configurações diferentes nunca produzem manifestos iguais. Run perdido tem definição única (`infra_error:` ou `interrupted:`) e é refeito com a mesma semente.

### 2.6 Métricas e análise

As sete métricas de `03-metricas.md` §2, calculadas por `scripts/analyze_results.py` a partir dos `result.json` e `events.jsonl`, nunca do relato do sistema. Testes exatos implementados no próprio script (sinal binomial bilateral; Wilcoxon exato por enumeração das 2^n atribuições de sinal). Portões de admissão do dado: provedor pinado em toda chamada, rede isolada no oráculo, trilha válida. Censura: o teste de custo usa só tarefas resolvidas por ambos e lista as excluídas.

### 2.7 Modelos e provedores

Estudo principal: `qwen/qwen3-coder` na DeepInfra (fp4), escolhido entre 23 candidatos por nove requisitos (provedor pinável honrando `tools`, `seed`, `temperature`; sem tokens de raciocínio; pesos abertos; custo) e por ser o único par com perfil medido no harness (`08-escolha-modelo.md`, l. 22 a 103 e 183 a 193). Replicação (decisão 45): `deepseek/deepseek-v3.2` não-pensante na DeepInfra (72,1 no SWE-bench Verified oficial contra 69,6 do Qwen, outro laboratório, perfil geral) e `mistralai/devstral-2512` na Mistral ("Coder" de outra empresa; 72,2 oficial, 62,8 em avaliação independente) (`08-escolha-modelo.md`, l. 254 a 306). Modelos pensantes excluídos porque a contabilidade de contexto foi validada com raciocínio zero.

---

## 3. Construção do instrumento: fumaças, rodadas e defeitos corrigidos

Esta seção é o "desenvolvimento" do trabalho. Cada fumaça e rodada foi um teste de uma proposição sobre o instrumento ou sobre o orquestrado, com resultado medido e decisão registrada com data em `09-decisoes-do-autor.md`. Fonte detalhada: os documentos 07 a 26; os números abaixo estão em cada um deles nas seções indicadas.

### 3.1 Fumaças A a H: calibrar os tetos numa tarefa grande (08 e 09/10/2026, `07-e4-fumaca.md`)

A exigência E4 pedia calibrar os tetos numa tarefa grande antes de congelar (`tasks/EXIGENCIAS.md`, l. 78 a 82). Oito fumaças na `tomlkit-0004` (funcionalidade "chaves pontilhadas" do TOML 0.5.0, 7 testes ocultos de três comportamentos):

| fumaça | configuração | resultado | o que ensinou |
|---|---|---|---|
| A (§1 a §4) | 40 turnos, 1,2 M, pool compartilhado | 4/4 células resolvidas em tomlkit-0002 e 0001; as duas grandes cortadas em 40 turnos com a correção já no lugar | 40 turnos aperta a faixa grande; tokens e parede não são gargalo; contabilidade de contexto fecha em 0,0% |
| B (§5) | 80 turnos, 2,5 M | 2 células perdidas por 429 `engine_overloaded` do pool compartilhado | crescimento superlinear de tokens por turno (≈ k·t²); o provedor é o ponto frágil |
| C (§6) | 80/4 M, Google | SA 0/7 ocultos; OR 5/7 com regressão | a tarefa está além dos dois braços em 80 turnos |
| D (§8) | 120/8 M, Google | SA 5/7; OR 5/7 | o single-agent progrediu só com 120 turnos |
| E (§9 e §10) | só OR, developer com enunciado+intent (decisão 24) | 0/7 contra 5/7 da D; 429 também no Google | o gargalo era o pool do OpenRouter, não o provedor; enunciado íntegro ao developer "não melhorou; piorou" (n = 1); decisão 24 revertida |
| F (§11) | 160/16 M, DeepInfra BYOK | SA 0/7; OR 0/7, patch de 5.686 linhas; 0 erros 429 em 321 chamadas | subir o teto piorou: "o modelo não acumula progresso, refaz"; BYOK resolveu a infraestrutura |
| G (§12) | 120/8 M + memória de trabalho | SA parou sozinho em 57 turnos com 0/7 (suíte visível não cobre funcionalidade nova); OR 0/7 num único ciclo | a memória só age com mais de um ciclo; a suíte visível verde não é sinal de pronto |
| H (§13) | + ciclo de 40 turnos | 4 ciclos; maior prompt caiu de 71.266 para 25.076 tokens; run de US$ 0,50 para 0,23; developer desfez a implementação para voltar ao verde; SA cortado por parede a 1.823 s com latência mediana 18 s | o ciclo corta o custo; o corte por parede era artefato do provedor, teto de parede vai a 3.600 s |

Conclusão da calibração: congelar 120 turnos, 8 M tokens, 3.600 s, ciclo de 40, memória `ledger`, 2 reprovações, aceitando que a `tomlkit-0004` pode ficar sem resolução em nenhum braço (decisão 12, proposta registrada em `09-decisoes-do-autor.md`, l. 579). Nenhuma das 16 células das fumaças a resolveu (`14-tres-tarefas-decisao.md` §3). Lição metodológica explícita: "não repetir fumaças na mesma tarefa à procura de 7/7: com esta variância, isso é escolher o resultado" (`07-e4-fumaca.md`, l. 185).

### 3.2 Coleta principal e rodada 1 (12 e 13/10/2026)

78 células, 0 perdidas, US$ 17,26 (`13-registro-rodada-1.md` §3). Resultado: single-agent 25/39 runs e 8/13 tarefas; orquestrado (refinador v1) 17/39 e 6/13; sinal exato p = 0,180 (`12-coleta-resultados.md` §2 e §3). Diagnóstico dos 22 runs não resolvidos do orquestrado: 9 "verde, aprovado, ocultos faltam", 8 "não convergiu", 3 "revisor reprovou até o orçamento", 2 "ocultos passam, 1 regressão" (`12-coleta-resultados.md` §6). Três mecanismos identificados: a intent v1 perde o que o enunciado especifica (razão intent/enunciado 0,17 a 0,75; confundidor D3); o developer desfaz ou reescreve diante da suíte vermelha (F3); e três tarefas tinham "suíte visível verde" inalcançável com a correção certa, defeito de construção corrigido pelo quinto portão (decisão 27). A sensibilidade sem as três tarefas dava 7/10 contra 4/10, p = 0,125.

### 3.3 Ablação do refinador e intent v2 (14/10/2026, `16-ablacao-e-v2.md`)

Repetição 1 das 13 tarefas em quatro condições com a mesma semente: single-agent 9/13; orquestrado v1 6/13; orquestrado com enunciado+intent ao developer 8/13; orquestrado com intent v2 7/13 (§1). A intent v1 tinha 37% do tamanho do enunciado; a v2, 126% (§2). O confundidor D3 ficou declarado e medido: a paráfrase do refinador custa cerca de 2 tarefas em 13 na repetição 1. A intent v2 entrou na coleta própria (decisão 28), nunca misturada à principal.

### 3.4 Rodadas 2 a 8: oito intervenções no orquestrado (14 a 27/10/2026)

Cada rodada testou a proposição "o mecanismo X aproxima o orquestrado do agente único ou o supera", com 39 runs e as mesmas sementes. Single-agent pareado de referência: 23/39 runs, 8/13 tarefas, US$ 8,44 (`17-rodada-2.md` §1; usa os 9 runs refeitos das três tarefas reconstruídas, `dados/coleta-r2/`).

| rodada | mecanismo adicionado (decisão) | runs | tarefas | grande | aprovações erradas | US$ | leitura (fonte) |
|---|---|---|---|---|---|---|---|
| 1 | refinador v1 | 17/39 | 6/13 | 4/9 | 9 ("verde, aprovado, ocultos faltam") | 5,21 | `12` §2, §3 e §6; `13` §3 |
| 2 | intent v2 + execução da reprodução + nota de ciclo (29); quinto portão (27) | 23/39 | 7/13 | 4/9 | 4 | 4,72 | empate em runs; tempo até a solução 127 → 245 s; negações de escrita em `tests/` 39 → 3 (`17` §1 a §4) |
| 3 | revisão estrita + sem teto de reprovações (32) | 19/39 | 5/13 | 5/9 | 7 | 5,58 | 76 de 98 revisões reprovadas; 26% dos blocos de reprodução quebravam por rodar isolados (`18` §1 e §2) |
| 4 | planejador + execução acumulada (33, 34) | **24/39** | **9/13** | **5/9** | 3 | 5,67 | primeira rodada em que o orquestrado passa o agente único em tarefas; ganho veio da exploração do planejador, não da esteira: 13 sub-tarefas feitas de 186, revisão de sub-tarefa reprovou 84% (`20` §1 a §4) |
| 5 | checagem determinística de sub-tarefa + contexto do planejador + comparação consultiva (35 a 39) | 18/39 | 6/13 | 5/9 | 7 | 5,83 | 33 das 37 sub-tarefas "feitas" pela palavra do developer; falsa partida: saídas do bug copiadas como esperadas fizeram o developer desfazer a correção (decisão 39) (`21` §4 a §5) |
| 6 | checagem híbrida + comparação neutra + estrita + compilação dos blocos (40 a 43) | 19/39 | 6/13 | 4/9 | 4 | 5,97 | saídas esperadas do enunciado não são oráculo literal (`Field` × `Attribute`); rótulo "não é evidência" citado 8 vezes em 8 até ser retirado dos prompts (`22` §3 e §5) |
| 7 | rodada 4 + sub-tarefa adiada após 1 ciclo + blocos de shell (44, 46, 47) | 23/39 | 9/13 | 4/9 | 6 | 4,37 | cortes 16 → 10 e tokens por run 0,88 → 0,69 M, mas aprovações erradas dobraram; 2 runs mortos por 502 no corpo de um 200 (corrigido) (`23` §4) |
| 8 | rodada 4 + reparo da cópia pelo enunciado + saída esperada por bloco, modo estrito (48) | 20/39 | 7/13 | **6/9** | 7 | 4,95 | melhor faixa grande de todas; `strict_coerced` 0 em 84 revisões; as 7 aprovações erradas, todas em tarefas sem par esperado no enunciado (`24` §4 e §5) |

Critério de "rodada decisiva" fixado antes das rodadas 7 e 8: 10 ou mais tarefas de 13 sem perder na faixa grande em relação à rodada 4 (`23-rodada-7.md` §2; `24-rodada-8.md` §4). Nenhuma atingiu; pela regra da decisão 45, a rodada 4 virou a configuração do orquestrado na replicação (`24-rodada-8.md` §4.1).

Leitura transversal das oito rodadas: (i) toda regra automática que reprova pelo texto da saída esperada, sem o oráculo, derruba runs certos ou deixa passar os errados, porque a saída esperada escrita em linguagem natural não é oráculo literal; (ii) o revisor baseado no modelo aprova errado sistematicamente quando o enunciado não traz exemplo que exercite o critério oculto; (iii) o planejador ajuda pela exploração inicial, não pela decomposição; (iv) teto maior piora, porque o modelo refaz em vez de acumular.

### 3.5 Defeitos do instrumento encontrados e corrigidos

Dezesseis itens, com data e evidência, em `07-execucao.md` e nos documentos de rodada. Os de maior consequência:

1. **Pool compartilhado do OpenRouter** (429 `engine_overloaded`): duas células perdidas na fumaça B e perda no Google na E; corrigido com chave própria (BYOK) e `--retry-delay 300 --max-attempts 5`; 0 erros em 321 chamadas na fumaça F (`07-e4-fumaca.md` §5, §9, §11).
2. **Suíte visível verde inalcançável** em três tarefas (pygments-0001, sqlite-utils-0002, tomlkit-0004): quinto portão e `visible_deselect` (decisão 27; `14-tres-tarefas-decisao.md`).
3. **`--deselect` ignorado em `runs/`** porque o pytest subia até o `pyproject.toml` do projeto: `--rootdir .` e chave no manifesto (decisão 30, commit `4f4f80e`; `16-ablacao-e-v2.md` §4); células afetadas refeitas.
4. **Erro 502 do provedor devolvido no corpo de uma resposta 200** virava `error:` em vez de perda: dois runs da rodada 7; corrigido em `src/config.py::openrouter_error_body` (`23-rodada-7.md` §4.4).
5. **Guarda de caminho que não removia arquivo protegido novo**: 16 execuções negadas e 28 recusas no validador num run da rodada 7; decisão 47 (`23-rodada-7.md` §4.4).
6. **Vazamento do histórico git e execução sem caixa de areia** (achado em 23/10/2026): o workspace era `git clone --shared` do espelho completo, com `master`, 56 tags e 535 commits futuros visíveis; varredura de 426 runs achou 5 cópias certas do histórico, nenhuma resolvida, e 3 resolvidos indistinguíveis entre memória do modelo e histórico; "nenhum run foi dado como resolvido por cópia do histórico; a comparação entre braços não muda". Correção: workspace só com o commit-base, bubblewrap, regra C8, manifesto v18 (decisão 49; `25-vazamento-historico-git.md`).
7. **Saídas do bug copiadas como esperadas** pelo refinador, fazendo o developer desfazer a correção (falsa partida da rodada 5; decisão 39).
8. **Comparação por bloco em vez de por exemplo do enunciado**: 3 de 4 "NÃO encontrada" eram falsas na fumaça r8 (`24-rodada-8.md` §3).

Interrupções externas (reinício da máquina em 12/10, queda de energia em 16/10, fechamento do editor em 16/10, sessão morta em 23/10) foram tratadas pela regra de perda, com reexecução preservando a semente (`13` §1; `21` §4.2; `22` §4; `24` §4).

### 3.6 Replicação em dois modelos (27 a 29/10/2026, `26-replicacao.md`)

Sondagem de aptidão (`fitness_test.py -n 5`): os dois modelos com tool calling 5/5, argumentos exatos 5/5, provedor 5/5, zero tokens de raciocínio (§2). Fumaças de três tarefas nos dois braços: DeepSeek 4/6 (US$ 1,43), primeira coleta sob a decisão 49, 125 execuções na caixa, 0 recusas (§3); Devstral 5/6 (US$ 0,97) depois de destravar a conta da Mistral, que devolvia 429 código 1300 porque o Devstral 2 não existe no plano gratuito (§5 e §6). Coletas: DeepSeek 78/78 em 13 h 52, Devstral 78/78 em 5 h 41, 0 perdas, 100% BYOK, 0 estouros de tempo de suíte, detector 0 críticos (1 aviso C6 num run não resolvido) (§8.1 e §9.1).

---

## 4. Resultados

### 4.1 As três coletas lado a lado

Mesmas 13 tarefas, mesmas sementes por repetição, mesmos tetos; orquestrado na configuração da rodada 4 (manifesto v12 no Qwen; v18 na replicação, que difere só em `workspace_history` e `sandbox`, iguais nos dois braços). Fonte: `dados/coleta-deepseek/agregado-tres-modelos.txt` (Qwen com o single-agent pareado), `26-replicacao.md` §8.2 e §9.2, `20-rodada-4.md` §2.

| modelo | braço | runs | tarefas | grande | média | pequena | cortes | aprov. erradas | só oráculo | mediana tokens/run | mediana s/run | US$ (OpenRouter) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-Coder | SA | 23/39 | 8/13 | 4/9 | 10/12 | 9/18 | 10 | 0 | 0 | 0,98 M | 243 | 8,44 |
| Qwen3-Coder | OR | 24/39 | 9/13 | 5/9 | 7/12 | 12/18 | 16 | 3 | 4 | 0,88 M | 290 | 5,67 |
| DeepSeek V3.2 | SA | 26/39 | 9/13 | 3/9 | 9/12 | 14/18 | 8 | 0 | 0 | 0,99 M | 499 | 8,02 |
| DeepSeek V3.2 | OR | 26/39 | 9/13 | 6/9 | 8/12 | 12/18 | 11 | 7 | 5 | 0,83 M | 669 | 5,56 |
| Devstral 2 | SA | 28/39 | 9/13 | 4/9 | 11/12 | 13/18 | 12 | 0 | 4 | 1,25 M | 219 | 5,46 |
| Devstral 2 | OR | 30/39 | 10/13 | 5/9 | 9/12 | 16/18 | 7 | 3 | 1 | 0,70 M | 271 | 4,24 |

"Aprovações erradas" = runs do orquestrado encerrados por `concluiu` (revisor aprovou) que o oráculo reprovou. "Só oráculo" = runs resolvidos pelo oráculo mas encerrados por orçamento (o sistema não soube que tinha terminado). O análogo do single-agent é parar com a suíte visível verde e ocultos vermelhos (`tests_pass` não resolvido): 6, 5 e 3 runs por modelo.

Sete métricas por modelo (análise pareada por tarefa, `analise-sete-metricas.md` de cada coleta):

| métrica | Qwen3-Coder (SA × OR) | DeepSeek V3.2 | Devstral 2 |
|---|---|---|---|
| 1 resolução (tarefas) | 8/13 × 9/13, p = 1,0 | 9/13 × 9/13, p = 1,0 | 9/13 × 10/13, p = 1,0 |
| 2 tokens, mediana por tarefa resolvida por ambos | 314.294 × 769.526, n = 7, p = 0,30 | 706.968 × 792.110, n = 8, p = 0,55 | 1.002.483 × 525.005, n = 7, **p = 0,031** |
| 3 tempo (s) | 155 × 284, p = 0,375 | 391 × 591, p = 0,055 | 154,5 × 180,1, p = 0,69 |
| 4 consistência | 5/10 × 5/10 | 8/9 × 8/9 | 8/11 × 9/11 |
| 5 Δ complexidade | 0,014 × 0,010, p = 0,94 | 0,031 × 0,028, p = 0,64 | 0,028 × 0,015, p = 1,0 |
| 6 conclusão sem corte | 29/39 × 23/39 | 31/39 × 28/39 | 27/39 × 32/39 |
| 7 violações críticas | 0 × 0 | 0 × 0 | 0 × 0 |

Fontes: `20-rodada-4.md` §2; `26-replicacao.md` §8.2 e §9.2.

### 4.2 Análise agregada dos três modelos

Pareamento run a run (mesmo modelo, tarefa e repetição, logo mesma semente), 117 pares, McNemar exato bilateral (`agregado-tres-modelos.txt`):

| recorte | pares | SA | OR | OR ganha | SA ganha | p |
|---|---|---|---|---|---|---|
| todos | 117 | 77 | 80 | 15 | 12 | 0,70 |
| Qwen3-Coder | 39 | 23 | 24 | 5 | 4 | 1,0 |
| DeepSeek V3.2 | 39 | 26 | 26 | 3 | 3 | 1,0 |
| Devstral 2 | 39 | 28 | 30 | 7 | 5 | 0,77 |
| faixa grande | 27 | 11 | 16 | 6 | 1 | 0,125 |
| faixa média | 36 | 30 | 24 | 1 | 7 | 0,070 |
| faixa pequena | 54 | 36 | 40 | 8 | 4 | 0,39 |

Por tarefa × modelo (39 pares, valor = runs resolvidos em 3): orquestrado melhor em 7, agente único melhor em 6, empate em 26; sinal p = 1,0; Wilcoxon exato p = 0,72; soma das diferenças +3 runs em 117.

Custo e tempo nos pares resolvidos pelos dois braços: no Qwen o orquestrado gasta 1,82 vez os tokens do agente único (mediana 632 k contra 229 k, 19 pares) e 2,0 vezes o tempo; no DeepSeek 1,24 vez os tokens e 1,5 vez o tempo; no Devstral **0,64 vez** os tokens e 1,3 vez o tempo. O sentido do custo da topologia depende do modelo.

Consistência agregada: entre as tarefas resolvidas ao menos uma vez, resolvidas nas três repetições foram 5/10 e 5/10 (Qwen), 8/9 e 8/9 (DeepSeek), 8/11 e 9/11 (Devstral). Progresso parcial nos não resolvidos (fração média de ocultos passados): single-agent 0,30, 0,65 e 0,36; orquestrado 0,14, 0,54 e 0,31; o orquestrado deixa mais runs com zero ocultos no Qwen (11 contra 7).

### 4.3 Por tarefa: teto, piso e o que discrimina

Tabela das seis células (3 modelos × 2 braços) em `dados/coleta-deepseek/por-tarefa-tres-modelos.txt`:

| situação | tarefas |
|---|---|
| teto, 18/18 | tomlkit-0001, tomlkit-0003, peewee-0001, peewee-0003 |
| piso, 0/18 | tomlkit-0004 |
| variam de 0/3 a 3/3 conforme o modelo | tomlkit-0005 (Qwen 0/6, DeepSeek 6/6), sqlite-utils-0002 (DeepSeek 0/6, Devstral 6/6), sqlite-utils-0001, tomlkit-0002 |
| falham só no orquestrado | peewee-0002: 0/9 no orquestrado dos três modelos, 4/9 no agente único |

Oito de 13 tarefas discriminam. Tarefa que um modelo resolve 6/6 e outro 0/6 não pode ser defeito do harness nem do oráculo: é dificuldade relativa ao modelo. A tomlkit-0004 passou nos quatro portões com duas referências; o enunciado descreve os sete comportamentos cobrados, inclusive as cinco linhas de chave pontilhada que o patch de teste acrescenta a `tests/examples/0.5.0.toml`; os 18 runs param por orçamento (17 por turnos, 1 por parede) com progresso parcial em 8 deles (3/7 a 6/7); a reprodução do oráculo no run DeepSeek single-agent rep02 (6/7) mostra o serializador do agente duplicando o último caractere dos valores (`"round""`, `a.b.d = 22`), erro que o bloco 5 do próprio enunciado detecta (`por-tarefa-tres-modelos.txt`, seção final). É piso de verdade, admitido pela decisão 12.

A peewee-0002 é o achado mais específico sobre a topologia: enunciado com seis comportamentos incorretos em módulos distintos (transações, janelas SQL, `ON CONFLICT`, migração, reflexão); o agente único a fecha em 4 de 9 runs, o orquestrado em 0 de 9, com o revisor aprovando errado 2 vezes no Devstral e o resto cortado por orçamento com 1 a 5 dos 6 ocultos. O teste oculto que mais falha é `test_column_map_not_shared_with_class` (11 de 18 runs), seguido de `test_make_index_name_long` e `test_unbound_error` (9 cada).

### 4.4 Mecanismos do orquestrado nas coletas finais

Rodada 4 no Qwen (`20-rodada-4.md` §3): 39 planos, mediana 5 sub-tarefas, 11% dos turnos no planejador; 186 sub-tarefas, 13 feitas, 24 adiadas, 108 nunca começaram; revisão de sub-tarefa reprovou 68 de 81; revisão final reprovou 66 de 90; 3 aprovações erradas. DeepSeek (`dados/coleta-deepseek/resumo-deepseek-devstral.txt`): 131 sub-tarefas, 17 feitas, 3 replanejamentos, 67 revisões finais com 39 reprovadas, 7 aprovações erradas (sqlite-utils-0001 ×3, sqlite-utils-0002 ×3, sqlite-utils-0003 ×1), 5 resolvidos só pelo oráculo (tomlkit-0001 ×3). Devstral: 98 sub-tarefas, 6 feitas, 61 revisões finais com 31 reprovadas, 3 aprovações erradas, 1 resolvido só pelo oráculo.

As 13 aprovações erradas das coletas finais (3 + 7 + 3) estão em sqlite-utils-0001, sqlite-utils-0002 e sqlite-utils-0003 (Qwen e DeepSeek) e em peewee-0002 e tomlkit-0005 (Devstral) (`por-tarefa-tres-modelos.txt`); na rodada 8, com comparação por bloco em modo estrito, as 7 aprovações erradas foram todas em tarefas sem par "bloco → saída esperada" no enunciado (`24-rodada-8.md` §4.1). A calibração offline em 164 runs mostrou que a barreira estrita não derruba nenhum resolvido e pega 2 aprovações erradas, enquanto 15 escapam porque nenhum exemplo as cobre (`24-rodada-8.md` §5).

### 4.5 Custo real e cache

Todas as chamadas das três coletas foram BYOK no provedor pinado (5.777 no DeepSeek, 5.392 no Devstral; `26-replicacao.md` §8.1 e §9.1). Fração do prompt servida em cache: 95,2% no DeepSeek e 93,8% no Devstral (medida, `tokens_cached`, decisão 46); 82,5% na rodada 4 e 95,4% no single-agent do Qwen (inferida do custo; `23-rodada-7.md` §4.1). Custo real: DeepInfra cobrou exatamente o que o OpenRouter reportou (queda de saldo US$ 6,44 contra 6,43 reportados; `dados/sondagens/mistral-byok-429-2026-10-28.txt`), US$ 13,58 na coleta do DeepSeek; a Mistral cobrou cerca de 4 a 5 vezes o `cost_usd` reportado do Devstral (US$ 9,70 reportados; tabela sem desconto de cache US$ 50,70; console do autor ≈ US$ 35 com 74 de 78 runs), porque o `upstream_inference_cost` do OpenRouter aplica o desconto de cache que a Mistral não aplica (`26-replicacao.md` §8.3). A métrica de custo em dólares do Devstral usa o console da Mistral; o valor final está pendente do autor.

Gasto total documentado do estudo, soma dos valores dos documentos citados: fumaças A a E no pool/Google ≈ US$ 4,6 (`07-e4-fumaca.md` §1 a §10); coleta principal mais fumaças F a H US$ 20,43 (`13-registro-rodada-1.md` §9); ablação e v2 US$ 3,85 (`16` §1); rodada 2 OR e SA refeito US$ 8,53 (`17` §0); rodadas 3 a 8 com suas fumaças US$ 5,58 + 5,67 + 7,23 + 7,02 + 4,81 + 6,13 (`18` a `24`); replicação DeepSeek US$ 15,01 real (`26` §3 e §9); Devstral US$ 10,67 reportados e ≈ US$ 50 cobrados (`26` §6 e §8.3). Ordem de grandeza: ≈ US$ 100 reportados pelo OpenRouter e ≈ US$ 140 efetivamente pagos (a diferença é a cobrança da Mistral), em mais de 580 runs (426 varridos em 23/10 em `25-vazamento-historico-git.md` §2, mais 168 da replicação).

### 4.6 Integridade

Detector: 0 críticos nas três coletas finais; avisos C6 (exceção silenciada) 8 no single-agent pareado e 3 na rodada 4 do Qwen, 1 no DeepSeek, 0 no Devstral (`agregado-tres-modelos.txt`). Antes da caixa de areia houve 1 crítico na rodada 6 (alteração de `tests/examples/example.toml`) e 5 cópias do histórico git em 426 runs, nenhuma resolvida. Negações de escrita em área protegida caíram de 39 (rodada 1, refinador v1 mandava escrever testes em 7 de 39 intents) para 3 na rodada 2 e 10 na rodada 4 (`17` §3; `20` §2). Caixa de areia: 0 recusas e 0 falhas em 262 execuções nas fumaças da replicação e nenhum estouro do tempo de suíte nas coletas (`26` §3, §6, §8.1, §9.1).

---

## 5. Validação das proposições

O projeto declarou uma hipótese neutra bicaudal e uma hierarquia de desfechos a priori (seção 1.3). As proposições abaixo separam o que estava fixado antes da coleta (P1 a P3) do que emergiu e foi testado ao longo das rodadas (P4 a P10), para que o texto do TCC não apresente achado post hoc como confirmação de hipótese.

| # | proposição | origem | veredito | evidência |
|---|---|---|---|---|
| P1 | A topologia muda a taxa de resolução (bicaudal) | a priori, `02-resumo-cientifico.md` l. 13 | **não rejeitada a H0** em nenhum modelo nem no agregado | 117 pares, 15 × 12 discordantes, p = 0,70; por tarefa p = 1,0 nos três modelos |
| P2 | A topologia muda o custo em tokens nas tarefas resolvidas por ambos | a priori, primário inferencial | **depende do modelo**: só no Devstral 2 há diferença (orquestrado ≈ metade, p = 0,031); no Qwen o orquestrado gasta 1,8× (p = 0,30) | §4.1 e §4.2 |
| P3 | O efeito depende da faixa; a grande "exige planejar antes de escrever" | a priori (estratificação, `CLAUDE.md` faixas) | **sugestivo, não significativo**: grande 16/27 × 11/27 (p = 0,125) nos três modelos; média na direção oposta 24/36 × 30/36 (p = 0,070) | §4.2, §4.3 |
| P4 | A paráfrase do refinador (D3) perde informação e custa resolução | emergiu no diagnóstico da rodada 1 | **confirmada na ablação** (6/13 → 8/13 com o enunciado íntegro, mesma semente) e mitigada pela intent v2 (37% → 126% do enunciado) | `16-ablacao-e-v2.md` §1 e §2 |
| P5 | Subir os tetos resolve a tarefa grande | decisão do autor de 09/10 ("a tomlkit-0004 tem de ser resolvida") | **refutada**: 160 turnos pioraram os dois braços; 0 de 16 células nas fumaças e 0 de 18 nas coletas finais | `07-e4-fumaca.md` §11 e §13; `por-tarefa-tres-modelos.txt` |
| P6 | Um revisor que executa a reprodução e reprova estritamente aproxima o orquestrado do oráculo | rodadas 2 e 3 | **refutada**: rodada 3 caiu para 19/39 e 5/13; 78% de reprovações, 26% dos blocos quebrados por execução isolada | `18-rodada-3.md` §1 e §2 |
| P7 | Decompor em sub-tarefas com planejador melhora a resolução | rodada 4 | **parcialmente confirmada**: 24/39 e 9/13, primeira vez acima do agente único em tarefas; mas 13 sub-tarefas feitas de 186, ganho atribuído à exploração inicial | `20-rodada-4.md` §3 |
| P8 | Saídas esperadas do enunciado servem de oráculo determinístico para sub-tarefas e revisão final | rodadas 5 e 6 | **refutada**: comparação textual exigiu o comportamento do bug (falsa partida), aceitou a palavra do developer em 33 de 37 sub-tarefas, e `Field` × `Attribute` mostrou que a saída escrita não é oráculo literal | `21` §4.1 e §5; `22` §5.2 |
| P9 | Amarrar cada bloco à saída esperada do enunciado e rebaixar aprovações contraditórias elimina as aprovações erradas | rodada 8 | **refutada no alvo, confirmada na segurança**: 0 rebaixamentos em 84 revisões, 7 aprovações erradas, todas em tarefas sem par; calibração em 164 runs: 0 resolvidos derrubados, 2 pegas, 15 escapam | `24-rodada-8.md` §4.1 e §5 |
| P10 | O resultado do Qwen se replica em outros modelos | decisão 45 | **confirmada no sinal nulo** (0 e +1 tarefa), **confirmada na faixa grande** (OR melhor nos três), **não confirmada no custo** (sentido inverte entre Qwen e Devstral) | §4.1 e §4.2 |

Poder estatístico (simulação em `agregado-tres-modelos.txt`, seção "Poder"): com 13 tarefas, 3 repetições, maioria por tarefa e sinal exato bilateral, tomando a taxa agregada observada do agente único por tarefa como linha de base, a probabilidade de detectar um efeito verdadeiro de +10, +20 ou +30 pontos percentuais por run é 0,00, 0,00 e 0,01; com 30 tarefas 0,04, 0,17 e 0,39; com 60 tarefas 0,14, 0,48 e 0,85. O desenho herdado do TFG não tinha como confirmar a hipótese direcional original; o que ele pode afirmar é que, se existe um efeito da topologia nesta classe de tarefas e modelos, ele é menor do que o que 13 tarefas conseguem ver, e que o sentido do efeito na faixa grande e no custo merece um estudo dimensionado para isso.

---

## 6. Ameaças à validade

**Validade interna.** (a) D3: o developer do orquestrado recebe a intent, não o enunciado; é o protótipo do TFG, declarado e medido pela ablação (≈ 2 tarefas em 13 na repetição 1). (b) O orquestrado passou por oito rodadas de ajuste com os mesmos dados; a configuração final foi escolhida por regra fixada antes das rodadas 7 e 8, e a replicação em dois modelos novos é o controle contra sobreajuste à coleta do Qwen. (c) Três tarefas foram reconstruídas após a rodada 1 (quinto portão) e o agente único foi refeito nelas; as células anteriores foram descartadas e documentadas. (d) O vazamento do histórico git existiu até a rodada 8; a varredura mostrou que nenhum run resolvido dependeu dele, e a replicação já rodou sem ele. (e) O detector e a caixa de areia garantem que "resolvido" não veio de alteração de teste ou de código do futuro.

**Validade de constructo.** O oráculo é o patch de teste do upstream, mais estrito do que o enunciado em alguns casos (pygments-0001, `16` §3.1); o enunciado foi escrito pelo autor, em português, e as saídas esperadas que ele traz não são oráculo literal (P8). "Resolver" é binário por run; progresso parcial é reportado em apêndice. A complexidade ciclomática como proxy de qualidade é exploratória e indistinguível entre braços.

**Validade estatística.** Treze tarefas, 4 no teto e 1 no piso, deixam 8 tarefas sensíveis; o poder é desprezível para a unidade "tarefa" (seção 5). A análise agregada run a run (117 pares) é mais poderosa mas trata runs da mesma tarefa como independentes condicionalmente à semente; é apresentada como complementar. Múltiplas comparações (7 métricas × 3 modelos) sem correção: o p = 0,031 do Devstral deve ser lido como achado a confirmar.

**Validade externa.** Cinco repositórios Python, 13 tarefas de 10 a algumas centenas de linhas, três modelos abertos não-pensantes de médio porte, um orquestrador particular (LangGraph com os papéis descritos). Não generaliza para modelos pensantes, para orquestradores com outro desenho, nem para tarefas que exigem escrever testes. Sem participantes humanos.

**Instrumentação.** A revisão de código do harness final (`dados/revisao-codigo-2026-10-29.md`) não encontrou nada que altere um resultado coletado; achou três itens a corrigir antes de qualquer coleta nova: a caixa de areia recebe o ambiente inteiro do processo, inclusive a chave da API (nenhum dos 322 `patch.diff` ou `events.jsonl` das coletas contém a chave, varredura de 29/10); a mineração de tarefas novas quebrou com o workspace só de commit-base; e a regra C8 do detector não registra se rodou. Também: a guarda "diff vazio" do validador pode ser enganada por arquivo não rastreado que a suíte deixa (nenhum run foi aprovado com patch vazio), o limiar único de similaridade do pareamento bloco → exemplo e o desescape de `\n` em blocos de uma linha podem deturpar blocos de reprodução das rodadas 5 a 8.

---

## 7. Contribuições

1. **Um instrumento de paridade para comparar topologias de agentes com o resto constante**: mesmo prompt, mesmas ferramentas na mesma ordem, mensagens de protocolo centralizadas, pareamento por semente, manifesto que torna qualquer diferença de configuração visível, e um teste automatizado (`tests/test_arm_parity.py`) que falha se a paridade quebrar. Não encontramos na literatura consultada pelo projeto comparação de topologia com este nível de controle.
2. **Um protocolo de tarefas com oráculo oculto verificado por execução**: quatro portões com duas soluções de referência, trapaça plantada, quinto portão para a suíte visível, faixas por função pura sobre o patch de referência, e a lição de que o enunciado precisa de exemplo que exercite cada critério oculto, porque o revisor do orquestrado aprova errado exatamente onde não há.
3. **Isolamento e integridade**: detector com oito regras, incluindo "código do futuro" medido contra o espelho local; workspace sem histórico; caixa de areia sem rede; e a medição de que o vazamento de histórico, embora real (5 cópias em 426 runs), não produziu nenhum "resolvido" falso.
4. **Resultado empírico replicado em três modelos de dois laboratórios e três provedores**: a topologia não muda a resolução de forma detectável; muda o custo conforme o modelo; a faixa grande favorece o orquestrado e a média o agente único, em direções consistentes mas não significativas. Os números por tarefa e por run estão versionados para reanálise.
5. **Oito intervenções documentadas no orquestrado com resultado medido**, que mostram o que não funciona: revisão estrita por texto, comparação textual de saída esperada, aceitar a palavra do developer, subir tetos. E o que funciona pouco: planejador (exploração), ciclo de 40 turnos (custo), intent v2 (fidelidade ao enunciado).
6. **Contabilidade de custo honesta**: cache do provedor medido por chamada, `byok_calls == llm_calls`, e a descoberta de que o custo reportado pelo OpenRouter para a Mistral subestima a cobrança real em 4 a 5 vezes, com contraprova na DeepInfra (razão 1,00).
7. **Uma análise de poder que explica o resultado nulo** e dimensiona o próximo estudo (≈ 60 tarefas para 85% de poder num efeito de 30 pontos).

---

## 8. Melhorias e trabalhos futuros

**Antes de qualquer coleta nova (instrumento).** Passar à caixa de areia uma lista branca de variáveis de ambiente em vez de `os.environ` (`src/tools/exec.py:123`); fazer `scripts/mine_tasks.py` buscar o `fix_commit` à parte ou ler os arquivos pelo espelho (`:678`, `:692`); registrar em `result.json` se a regra C8 rodou (`harness/cheat.py:374`); contar só o diff rastreado mais arquivos `.py` novos em `houve_mudanca` (`src/agents/validator.py:115`); limiar de contenção próprio em `exemplo_do_bloco` (`src/enunciado.py:147`); desescapar `\n` só quando o resultado compila e o original não (`src/schemas/intent.py:90`); `stdin=DEVNULL` nos comandos de reprodução; montar `tests/` só-leitura na caixa. Todos exigem aprovação do autor por tocar intocáveis.

**Desenho do próximo experimento.** (a) Dimensionar: 40 a 60 tarefas que discriminem (descartar teto e piso num piloto), com 3 repetições, e usar o par run a run como unidade secundária. (b) Exigir no enunciado um exemplo executável por critério oculto e medir a cobertura critério → exemplo como variável. (c) Separar as três hipóteses que este estudo deixou sugestivas: topologia × faixa grande; topologia × tarefa multi-comportamento (peewee-0002); topologia × modelo no custo. (d) Incluir um modelo pensante com contabilidade de raciocínio. (e) Repetir a ablação do refinador em todas as repetições, não só na primeira.

**Orquestrado.** Dar ao developer o enunciado íntegro além da intent, agora que a ablação mostrou o custo da paráfrase; substituir a comparação textual por verificação executável gerada pelo planejador e validada contra as duas referências na construção da tarefa; fazer o revisor de sub-tarefa receber o resultado da suíte em `SUBTASK_CHECK=llm`; investigar por que a decomposição trava em tarefas com vários comportamentos (peewee-0002, 0/9).

**Documentação pendente.** Atualizar "X de 12" para 13 tarefas em `02-resumo-cientifico.md` e `03-metricas.md`; registrar a quantização do endpoint no manifesto (`08-escolha-modelo.md`, l. 111 e 244); testes unitários para `quality.cc_mean_delta` e `resolved_blocked_by_cheat` (`03-metricas.md` §6); decisões 9, 15, 18 a 21, 26, 30, 31, 34, 39, 43 e os dois runs `error:` da rodada 7 continuam pendentes do autor; valor final do Devstral no console da Mistral.

---

## 9. Conclusão

O experimento foi construído para que a diferença entre um agente único e uma orquestração de papéis fosse a única variável, e passou por nove rodadas de engenharia documentadas até que o instrumento sustentasse a comparação sem defeito conhecido que alterasse o desfecho. Com três modelos de linguagem de laboratórios distintos, 234 runs finais e 117 pares com a mesma semente, a orquestração resolveu três runs a mais em 117, diferença indistinguível do acaso; nenhuma das sete métricas mostrou efeito consistente entre modelos, com exceção do custo em tokens, cuja direção depende do modelo. A faixa grande favoreceu o orquestrado nos três modelos e a faixa média o agente único, ambas sem significância, e uma tarefa com seis comportamentos a corrigir nunca foi fechada pela orquestração em nenhum modelo.

O que o trabalho estabelece com segurança é metodológico: como construir e validar tarefas com oráculo oculto, como manter dois braços idênticos em tudo menos na topologia e provar isso por teste, como isolar a execução para que "resolvido" signifique resolvido, como medir custo de verdade, e quantas tarefas um estudo deste tipo precisa para enxergar um efeito. O resultado nulo, lido junto com a análise de poder e com as oito intervenções que não mudaram o quadro, sugere que, para modelos não-pensantes de médio porte em correções de dezenas a centenas de linhas, a topologia importa menos do que a fidelidade do enunciado e do que a capacidade do modelo de acumular progresso dentro do orçamento.

---

## Apêndice A. Prompt genérico para um assistente de redação externo

> Você vai redigir o texto de um Trabalho de Conclusão de Curso em Engenharia de Software a partir do relatório anexo (`27-relatorio-cientifico.md`) e dos documentos que ele cita. Regras: (1) não introduza nenhum número que não esteja no relatório ou no arquivo de origem que ele aponta; (2) a hipótese do estudo é neutra e bicaudal; trate P4 a P10 como proposições que emergiram durante a engenharia do instrumento, não como hipóteses pré-registradas; (3) o resultado principal é nulo e deve ser apresentado junto com a análise de poder, nunca como "a orquestração não funciona"; (4) a contribuição central é o instrumento e o protocolo, e o texto deve dedicar uma seção à sua construção iterativa (fumaças A a H, rodadas 1 a 8, defeitos corrigidos); (5) descreva as ameaças à validade da seção 6 integralmente; (6) o custo em dólares do Devstral 2 usa a cobrança do console da Mistral, não o valor reportado pelo OpenRouter; (7) escreva em português formal da ABNT, com as tabelas 4.1 e 4.2 reproduzidas e as figuras geradas só a partir dos arquivos `analise-sete-metricas.json`, `agregado-tres-modelos.txt` e `por-tarefa-tres-modelos.txt`.

## Apêndice B. Índice dos arquivos de origem

| conteúdo | arquivo |
|---|---|
| pergunta, hipótese, objetivos | `docs/tcc/02-resumo-cientifico.md`, `docs/tcc/PROMPT_AUDITORIA.md` |
| inventário, riscos R1 a R12, folgas F1 a F13, contradições C1 a C8 | `docs/tcc/01-inventario.md` |
| métricas e testes | `docs/tcc/03-metricas.md`, `scripts/analyze_results.py` |
| cronograma e portões offline | `docs/tcc/04-cronograma.md` |
| grafos dos dois braços | `docs/tcc/05-stack.md` |
| contabilidade de contexto | `docs/tcc/06-contabilidade-contexto.md` |
| mineração, faixas, breaking change | `docs/tcc/07-e3-1-mineracao.md`, `07-e3-2-faixa.md`, `07-e3-3-breaking-change.md` |
| fumaças A a H e tetos | `docs/tcc/07-e4-fumaca.md`, `dados/fumaca-*` |
| escolha do modelo e da replicação | `docs/tcc/08-escolha-modelo.md` |
| todas as decisões do autor, com data | `docs/tcc/09-decisoes-do-autor.md` |
| coleta principal e rodada 1 | `docs/tcc/11-coleta-grandes.md`, `12-coleta-resultados.md`, `13-registro-rodada-1.md`, `dados/coleta/` |
| quinto portão, ablação, intent v2 | `docs/tcc/14-tres-tarefas-decisao.md`, `15-refinador-analise.md`, `16-ablacao-e-v2.md`, `dados/ablacao-refinador/`, `dados/refinador-v2/` |
| rodadas 2 a 8 | `docs/tcc/17-rodada-2.md` a `24-rodada-8.md`, `dados/coleta-r2/` a `dados/coleta-r8/` |
| vazamento git e isolamento | `docs/tcc/25-vazamento-historico-git.md` |
| replicação DeepSeek e Devstral | `docs/tcc/26-replicacao.md`, `dados/coleta-deepseek/`, `dados/coleta-devstral/`, `dados/sondagens/` |
| agregado dos três modelos, por tarefa, poder | `dados/coleta-deepseek/agregado-tres-modelos.txt`, `dados/coleta-deepseek/por-tarefa-tres-modelos.txt` |
| revisão de código do harness final | `dados/revisao-codigo-2026-10-29.md` |
| registro de execução por etapa | `docs/tcc/07-execucao.md` |

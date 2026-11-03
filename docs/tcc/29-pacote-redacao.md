# 29. Pacote de redação para o assistente externo (Perplexity)

**Para que serve.** O texto final do TCC será redigido com um assistente externo que já contém a revisão bibliográfica. Este arquivo é o único material que ele precisa receber sobre o experimento: fatos, números com fonte, vocabulário, estrutura dos capítulos e as regras que o texto tem de respeitar. Tudo aqui foi extraído de [27-relatorio-cientifico.md](27-relatorio-cientifico.md), [28-exploratorio-orquestrado.md](28-exploratorio-orquestrado.md) e dos arquivos de dados citados; nenhum número novo. Atualizado em 03/11/2026.

**Como usar, na ordem.**

1. Crie um espaço (Space) no Perplexity e anexe como fontes: este arquivo, o 27, o 28 e `docs/tcc/texto/desenvolvimento.tex`. Nas instruções do espaço, cole o bloco "Instruções para o assistente" abaixo.
2. Peça uma seção por vez, usando os prompts da seção 7 deste arquivo, na ordem. Não peça "o artigo inteiro": o texto fica longo demais e os números começam a derivar.
3. Cole cada seção pronta de volta aqui no Claude Code com o pedido "confira os números desta seção contra os arquivos". A conferência é mecânica: cada número do texto tem de existir num arquivo de `docs/tcc/dados/` ou nos documentos 27 e 28.
4. Só então leve a seção para o LaTeX (`docs/tcc/texto/`), no template da UNIFEI já usado em `desenvolvimento.tex`.

---

## 1. Instruções para o assistente (colar nas instruções do espaço)

> Você redige o texto de um Trabalho de Conclusão de Curso em engenharia de software, em português do Brasil, no formato de monografia da UNIFEI. O experimento está descrito nos arquivos anexados; eles são a única fonte de fatos e números sobre ele. Regras: (1) nunca escreva um número que não esteja nos arquivos; se precisar de um que não existe, escreva "[NÚMERO: pedir]" em vez de estimar; (2) ao lado de cada número, mantenha entre colchetes o nome do arquivo e a seção de onde ele vem, para a conferência posterior; (3) nunca afirme significância estatística onde o arquivo diz que não há; a única diferença significativa pré-registrada é o consumo de tokens no Devstral 2; (4) toda análise marcada como exploratória nos arquivos continua marcada como exploratória no texto; (5) use o vocabulário da seção 2 do pacote, sem sinônimos; (6) a revisão bibliográfica e os trabalhos relacionados podem usar a busca na web, com citação completa; o resto do texto, não; (7) frases curtas, voz ativa, sem adjetivos de valor ("robusto", "poderoso") que os dados não sustentem.

---

## 2. Vocabulário fixo

| Termo | Significado no texto | Não usar |
|---|---|---|
| braço | cada uma das duas topologias comparadas | "grupo", "condição" |
| agente único (SA) | agente de modelo de linguagem com ferramentas e um operador determinístico que roda a suíte quando ele declara ter terminado | "baseline" sem explicar |
| orquestrado (OR) | grafo com quatro papéis: refinador de intenção, planejador, developer e revisor (validador), mais um gerador de plano de testes ao fim | "multiagente" sem explicar |
| run | uma execução de um braço numa tarefa com uma semente | "rodada" (reservado às rodadas de engenharia) |
| par | o run do braço A e o run do braço B com a mesma tarefa, modelo e semente | — |
| tarefa | um defeito ou funcionalidade real minerado de um projeto Python aberto, com enunciado e testes escondidos | "problema", "issue" |
| faixa | classe de tamanho da tarefa: grande, média ou pequena, pela mudança de referência do projeto | "nível" |
| oráculo | julgamento pós-run com testes que o agente nunca viu: fail-to-pass, pass-to-pass e regressão | "avaliador" |
| resolvido | o oráculo aprovou nas três verificações e o detector de trapaça não achou violação crítica | "sucesso" |
| detector de trapaça | oito regras estáticas sobre o patch (editar testes, silenciar exceções, código do futuro do projeto etc.) | — |
| intent | saída do refinador de intenção, versão 2: contexto, blocos de reprodução, saídas esperadas, restrições e critérios, copiados do enunciado | — |
| memória de trabalho | registro determinístico que o developer recebe entre ciclos: arquivos lidos, buscas, escritas, suítes rodadas, nota de ciclo, diff atual | "resumo", "histórico" |
| ciclo | sequência de até 40 turnos do developer seguida da validação | — |
| turno | uma chamada ao modelo dentro do orçamento de 120 | — |
| rodada | cada uma das nove configurações do orquestrado testadas durante a construção do instrumento (1 a 8, mais a ablação) | — |
| coleta | conjunto de 78 runs (13 tarefas × 3 repetições × 2 braços) com um modelo | — |
| replicação | as duas coletas com DeepSeek V3.2 e Devstral 2 | — |
| manifesto | arquivo que registra toda a configuração de um run; chaves que podem diferir entre braços têm justificativa | — |

---

## 3. Fatos do desenho (para o capítulo de método)

- **Pergunta.** Organizar um agente em papéis orquestrados muda o resultado da correção de bugs em relação a um agente único com o mesmo modelo, ferramentas, prompt e orçamento? Hipótese neutra, bicaudal, fixada antes da coleta [27 §1.1].
- **Paridade.** Mesmo modelo e provedor pinados, mesmo prompt de sistema, mesmas sete ferramentas na mesma ordem (listar, ler, buscar, escrever, substituir, run_python, run_tests), mesmas mensagens de protocolo, mesmo orçamento, mesma semente por repetição. Um teste automático (`tests/test_arm_parity.py`) falha se qualquer chave do manifesto divergir sem justificativa [27 §2.2].
- **Orçamento por run.** 120 turnos, 8 milhões de tokens, 3.600 segundos, 120 segundos por execução de suíte; congelado em 12/10/2026 após as fumaças A a H [27 §2.5; `07-e4-fumaca.md` §13].
- **Tarefas.** 13, mineradas de tomlkit, peewee, sqlite-utils, pygments e attrs; 3 grandes, 4 médias, 6 pequenas; faixa calculada sobre a mudança de referência do projeto (arquivos-fonte, linhas, testes novos); cada tarefa validada por cinco portões com duas soluções de referência; congeladas em 08/10/2026 [27 §2.3; `CLAUDE.md` faixas].
- **Workspace.** Nasce só com o commit-base, sem histórico git, sem rede; área de testes protegida; toda execução de código do agente em caixa de areia bubblewrap [27 §2.4; decisão 49].
- **Oráculo.** Testes escritos pelo projeto junto com a correção original, que falham no commit-base e passam com a correção; injetados após o run num diretório que não existia; três verificações: fail-to-pass, pass-to-pass, regressão [`harness/oracle.py`; 27 §2.4].
- **Detector.** Oito regras (C1 a C8); violação crítica anula o run; C8 compara o patch com o código futuro do projeto [27 §2.4].
- **Métricas, hierarquia a priori.** 1 resolução (primária; sinal exato bilateral por tarefa, McNemar exato por par); 2 tokens nos pares resolvidos por ambos (Wilcoxon exato); 3 tempo de parede; 4 consistência; 5 variação da complexidade ciclomática; 6 conclusão sem corte; 7 violações [27 §1.3, §2.6; `03-metricas.md`].
- **Configuração final do orquestrado (rodada 4, manifesto v18).** Intent v2; planejador ligado (só leitura, até 12 turnos, até 6 sub-tarefas); developer recebe a sub-tarefa atual mais a intent, até 40 turnos por ciclo, memória de trabalho entre ciclos; validador roda a suíte, executa os blocos de reprodução e faz revisão de sub-tarefa e revisão final pelo modelo; teto de 2 reprovações finais, não contado enquanto o plano está aberto; gerador de plano de testes ao fim (texto, não escreve na suíte) [`src/graph.py`; `CLAUDE.md`].
- **Critério de parada, igual nos dois braços.** Suíte verde (com aprovação do revisor, no orquestrado) ou orçamento [`CLAUDE.md`].

### 3.1 Modelos e por quê

| Modelo | Laboratório | Provedor | Papel | Critérios que passou |
|---|---|---|---|---|
| Qwen3-Coder | Alibaba | DeepInfra | piloto, nove rodadas e coleta principal | endpoint com semente, ferramentas, temperatura e teto de saída; pesos abertos com quantização publicada; não pensante; custo da ordem de US$ 0,30 por milhão de tokens de entrada |
| DeepSeek V3.2 (modo não pensante) | DeepSeek | DeepInfra | replicação: muda o laboratório, mantém o provedor | idem |
| Devstral 2 | Mistral | Mistral | replicação: muda laboratório e provedor | idem; provedor único, quantização não publicada (declarado) |

Modelos fechados de custo médio (Claude Haiku 4.5, GPT-5-mini) ficaram fora por não exporem a semente, não por preço [`08-escolha-modelo.md`; decisão 45, 22/10/2026].

### 3.2 Cronograma

| Quando | Etapa | Produto |
|---|---|---|
| 11/09/2026 | piloto | Qwen3-Coder na DeepInfra com semente fixa |
| 19/09/2026 | escolha de modelo e provedor | oito critérios sobre endpoints consultados ao vivo |
| 08/10/2026 | tarefas congeladas | 13 tarefas, cinco portões, duas referências |
| 08 e 09/10/2026 | fumaças A a H | calibração dos tetos; congelados em 12/10 |
| 12 e 13/10/2026 | coleta principal | 78 runs, Qwen3-Coder; 9 aprovações erradas do revisor diagnosticadas |
| 14/10/2026 | ablação do refinador e intent v2 | 6/13 → 8/13 com o enunciado íntegro |
| 14 a 27/10/2026 | rodadas 2 a 8 | sete configurações do orquestrado, 273 runs, 16 defeitos do instrumento corrigidos |
| 22/10/2026 | isolamento | workspace só com o commit-base, caixa de areia, regra C8 (5 cópias de código futuro em 426 runs) |
| 27 a 29/10/2026 | replicação | DeepSeek V3.2 e Devstral 2, 78 runs cada |
| 29 e 30/10/2026 | relatório e análise exploratória | documentos 27 e 28; revisão de código com 14 achados |

Totais: mais de 580 runs; cerca de US$ 100 reportados pelo intermediário e cerca de US$ 140 pagos (a Mistral cobra 4 a 5 vezes o reportado, sem desconto de cache) [27 §4.5].

---

## 4. Resultados (todos os números, com fonte)

Fontes: `dados/coleta-deepseek/agregado-tres-modelos.txt` (A), `por-tarefa-tres-modelos.txt` (T), `exploratorio-orquestrado.txt` (E, com seção), 27 §4 (R).

### 4.1 Resolução, desfecho primário

| Modelo | SA runs | OR runs | SA tarefas | OR tarefas | OR ganha / SA ganha | McNemar p |
|---|---|---|---|---|---|---|
| Qwen3-Coder | 23/39 | 24/39 | 8/13 | 9/13 | 5 / 4 | 1,00 |
| DeepSeek V3.2 | 26/39 | 26/39 | 9/13 | 9/13 | 3 / 3 | 1,00 |
| Devstral 2 | 28/39 | 30/39 | 9/13 | 10/13 | 7 / 5 | 0,77 |
| Três modelos | 77/117 | 80/117 | — | — | 15 / 12 | 0,70 |

Diferença pareada OR − SA: +2,6 pontos percentuais, IC 95% de −6,1 a +11,3 [E §2]. Por faixa: grande 11/27 × 16/27, discordantes 1 × 6, p = 0,125, IC +0,6 a +36,4; média 30/36 × 24/36, 7 × 1, p = 0,070, IC −31,1 a −2,3; pequena 36/54 × 40/54, 4 × 8, p = 0,388 [E §1]. Todo o sinal da faixa grande está na tomlkit-0002 (tomlkit-0003 é teto 18/18, tomlkit-0004 é piso 0/18) [E §1].

### 4.2 As sete métricas por modelo (SA / OR)

| Métrica | Qwen3-Coder | DeepSeek V3.2 | Devstral 2 | Fonte |
|---|---|---|---|---|
| 1 resolução (runs; tarefas) | 23/24; 8/9 | 26/26; 9/9 | 28/30; 9/10 | A |
| 2 tokens, mediana por run (M) | 0,98 / 0,88 | 0,99 / 0,83 | 1,25 / 0,70 | E §6 |
| 2 tokens, razão OR/SA nos pares resolvidos por ambos | 1,82 (19 pares) | 1,24 (23) | 0,64 (23), p = 0,031 | A; R §4.2 |
| 3 tempo de parede, mediana (s) | 243 / 290 | 499 / 669 | 219 / 271 | E §6 |
| 3 tempo, razão OR/SA nos pares resolvidos por ambos | 2,0 | 1,5 | 1,3 | R §4.2 |
| 4 consistência (tarefas 3/3 ou 0/3, em 13) | 8 / 8 | 12 / 12 | 10 / 11 | E §7 |
| 5 cc_mean_delta, mediana nos resolvidos | +0,009 / +0,022 | +0,021 / +0,012 | +0,018 / +0,017 | E §7 |
| 6 conclusão sem corte (runs em 39) | 29 / 23 | 31 / 28 | 27 / 32 | E §5 |
| 7 violações críticas · avisos | 0·8 / 0·3 | 0·0 / 0·1 | 0·0 / 0·0 | E §7 |

### 4.3 Processo (SA / OR)

| Medida | Qwen3-Coder | DeepSeek V3.2 | Devstral 2 | Fonte |
|---|---|---|---|---|
| turnos, mediana | 50 / 73 | 57 / 54 | 64 / 54 | E §6 |
| chamadas ao modelo, mediana | 50 / 78 | 57 / 57 | 64 / 56 | E §6 |
| tokens de prompt por chamada, mediana (k) | 16,7 / 9,9 | 17,4 / 11,8 | 19,0 / 11,9 | E §6 |
| contexto da última chamada, mediana (k) | 28 / 12 | 30 / 21 | 32 / 19 | E §13 |
| contexto da última chamada, máximo (k) | 171 / 31 | 70 / 37 | 106 / 29 | E §13 |
| cortados por orçamento (em 39) | 10 / 16 | 8 / 11 | 12 / 7 | E §5 |
| parou sozinho e o oráculo reprovou | 6 / 3 | 5 / 7 | 3 / 3 | E §5 |
| cortado mas resolvido (OR: revisor nunca aprovou) | 0 / 4 | 0 / 5 | 4 / 1 | E §5 |
| progresso parcial nos não resolvidos (fração de ocultos) | 0,31 / 0,14 | 0,65 / 0,54 | 0,36 / 0,31 | E §5 |
| runs com regressão em teste que passava | 16 / 13 | 13 / 13 | 11 / 9 | E §5 |
| fração do prompt em cache, mediana | — | 0,97 / 0,91 | 0,96 / 0,88 | E §15 |

### 4.4 Custo da carga inteira (exploratório)

| Modelo | US$ SA | US$ OR | Diferença | US$ por run resolvido SA → OR | pares OR < SA em tokens | Wilcoxon tokens | pior run tokens SA / OR | cortados, mediana tokens SA / OR |
|---|---|---|---|---|---|---|---|---|
| Qwen3-Coder | 8,44 | 5,67 | −33% | 0,367 → 0,236 | 19/39 | 0,151 | 8,1 M / 2,6 M | 4,7 M / 1,4 M |
| DeepSeek V3.2 | 8,02 | 5,56 | −31% | 0,308 → 0,214 | 24/39 | 0,025 | 4,2 M / 2,1 M | 3,8 M / 1,3 M |
| Devstral 2 | 5,46 | 4,24 | −22% | 0,195 → 0,141 | 31/39 | < 0,001 | 7,1 M / 2,9 M | 4,3 M / 2,0 M |
| Três modelos | 21,91 | 15,47 | −29% | 0,285 → 0,193 | 74/117 | < 0,001 (aprox. normal); US$ pareado p = 0,031 | 8,1 M / 2,9 M | 4,0 M / 1,5 M |

Sem tomlkit-0002 e peewee-0002: −23% (Qwen −30%, DeepSeek −17%, Devstral −20%) [28 §1.1; sessão de 30/10]. Patch mediano nos resolvidos, linhas inseridas: Qwen 11/13, DeepSeek 24/18, Devstral 19/20 [sessão de 30/10].

### 4.5 Tarefa a tarefa (runs resolvidos em 9: 3 modelos × 3 repetições) [T; E §1, §8]

| Tarefa | Faixa | Natureza | SA | OR |
|---|---|---|---|---|
| tomlkit-0002 | grande | funcionalidade nova: chaves pontilhadas pela API | 2/9 | 7/9 |
| tomlkit-0003 | grande | — | 9/9 | 9/9 |
| tomlkit-0004 | grande | 7 comportamentos, piso | 0/9 | 0/9 |
| attrs-0001 | média | 3 testes escondidos | 9/9 | 8/9 |
| peewee-0001 | média | — | 9/9 | 9/9 |
| peewee-0002 | média | 6 defeitos independentes em módulos distintos | 4/9 | 0/9 |
| sqlite-utils-0003 | média | 12 testes escondidos | 8/9 | 7/9 |
| peewee-0003 | pequena | — | 9/9 | 9/9 |
| pygments-0001 | pequena | lexer de Go, 9 classificações erradas | 6/9 | 9/9 |
| sqlite-utils-0001 | pequena | 5 testes escondidos | 3/9 | 4/9 |
| sqlite-utils-0002 | pequena | 11 testes escondidos | 3/9 | 5/9 |
| tomlkit-0001 | pequena | — | 9/9 | 9/9 |
| tomlkit-0005 | pequena | 1 teste escondido | 6/9 | 4/9 |

Por modelo, tomlkit-0002: Qwen 1/3 × 2/3, DeepSeek 0/3 × 3/3, Devstral 1/3 × 2/3. peewee-0002: Qwen 2/3 × 0/3, DeepSeek 0/3 × 0/3, Devstral 2/3 × 0/3 [E §1]. Nas oito rodadas com o Qwen (24 runs do orquestrado): tomlkit-0002 13/24 × SA 1/3; peewee-0002 0/24 × 2/3; pygments-0001 15/24 × 2/3; sqlite-utils-0002 15/24 × 0/3 [E §16].

### 4.6 Anatomia da tomlkit-0002 [E §9, §10; result.json]

- Agente único, 9 runs: 2 resolvidos; nas 7 falhas a suíte visível nunca ficou verde (em 6 o agente nunca declarou pronto; no sétimo declarou 35 vezes com a suíte vermelha); em 5 das 7 o teste escondido já passava, mas 5 a 91 testes que passavam quebraram (6 dos 9 runs com regressão); tokens 2,4 a 4,5 M; contexto final 49 k a 124 k; patches de 74 a 172 linhas nos que falharam.
- Orquestrado, 9 runs: 7 resolvidos, todos limpos no detector e sem regressão; planos de 3 a 5 sub-tarefas (um com 1); 1 ou 2 ciclos em 6 dos 7; tokens 0,41 a 1,43 M nesses 6; patches de +8, +10, +13, +13, +86, +91 e +93 linhas; a biblioteca já tinha a classe `DottedKey` e as soluções pequenas fazem `key()` aceitar lista e devolver essa classe.
- Nos 15 pares vencidos pelo orquestrado: 15 limpos no detector, 15 sem regressão [sessão de 30/10].

### 4.7 Mecanismos [E §4, §5, §11, §14, §17]

- Vitórias do orquestrado (15): 8 com reprovação do revisor com suíte verde seguida de reescrita e aprovação pelo oráculo (pygments-0001 Qwen rep1, Devstral rep2 e rep3; sqlite-utils-0002 Qwen rep2; sqlite-utils-0003 Qwen rep3; tomlkit-0002 Qwen rep3, DeepSeek rep1, Devstral rep3), nos 8 o agente único foi cortado por orçamento; 4 em que o agente único parou verde e o oculto reprovou (sqlite-utils-0001 Devstral ×3, sqlite-utils-0002 Qwen rep1); 3 cortes do agente único com o orquestrado acertando sem reprovação.
- Derrotas do orquestrado (12): 6 cortes por orçamento, 6 aprovações erradas.
- No conjunto dos 117 runs orquestrados: 57 com ao menos uma reprovação final com suíte verde; 33 resolvidos com escrita depois da reprovação; 6 resolvidos sem escrita depois; 10 resolvidos mas cortados (revisor nunca aprovou).
- Turnos gastos depois do primeiro verde: 55% (1.664 de 3.007, Qwen), 46% (DeepSeek), 40% (Devstral); mediana 42, 13 e 13 turnos.
- Conclusão falsa: 13 aprovações erradas do orquestrado × 14 paradas verdes erradas do agente único; as 13 em sqlite-utils-0001, 0002 e 0003 (Qwen e DeepSeek) e peewee-0002 e tomlkit-0005 (Devstral), tarefas sem exemplo executável do critério no enunciado [27 §4.4].
- peewee-0002 no orquestrado: 9 planos com 6 sub-tarefas; developer bate o teto de 40 turnos na sub-tarefa 1 ou 2 (DeepSeek: 41 + 41 + 25 nos três runs); no máximo 3 sub-tarefas iniciadas; progresso oculto 0 a 5 de 6.
- Reprovações finais por run nas coletas finais: 3 ou mais em 11 runs do Qwen, 7 do DeepSeek e 3 do Devstral; o teto de 2 nunca disparou porque não conta com plano aberto [sessão de 30/10].

### 4.8 Integridade e custo real [27 §4.5, §4.6]

- 0 violações críticas nas três coletas finais; avisos C6: 8 SA e 3 OR (Qwen), 0 e 1 (DeepSeek), 0 e 0 (Devstral).
- Todas as chamadas BYOK no provedor pinado: 5.777 (DeepSeek), 5.392 (Devstral).
- Cache: 95,2% do prompt (DeepSeek), 93,8% (Devstral), medidos; 82,5% (rodada 4) e 95,4% (SA Qwen), inferidos.
- DeepInfra cobrou o que o OpenRouter reportou (US$ 6,44 × 6,43); a Mistral cobrou 4 a 5 vezes o reportado (US$ 9,70 reportados; console ≈ US$ 35 com 74 de 78 runs; valor final pendente).

---

## 5. Hipóteses e vereditos (para discussão e conclusão) [27 §5; 28 §3]

### 5.1 Fixadas antes da coleta

| | Hipótese | Veredito | Evidência |
|---|---|---|---|
| P1 | a topologia muda a taxa de resolução | H0 não rejeitada; orquestrado nunca inferior (+1, 0, +2 runs) | 117 pares, 15 × 12, p = 0,70; IC −6,1 a +11,3 |
| P2 | a topologia muda o custo em tokens nos pares resolvidos por ambos | depende do modelo | Devstral 0,64 (p = 0,031); Qwen 1,82; DeepSeek 1,24 |
| P3 | o efeito depende da faixa | sugestivo a favor do orquestrado na grande, por uma tarefa | 16/27 × 11/27, p = 0,125; média 24/36 × 30/36, p = 0,070 |

### 5.2 Surgidas nas rodadas

| | Hipótese | Veredito | Evidência |
|---|---|---|---|
| P4 | a paráfrase do refinador perde informação | confirmada; corrigida pela intent v2 | ablação 6/13 → 8/13 |
| P5 | subir os tetos resolve a tarefa grande travada | refutada | 160 turnos pioraram os dois braços; tomlkit-0004 0/18 |
| P6 | revisor que executa a reprodução e reprova estritamente aproxima do oráculo | refutada | rodada 3: 19/39, 78% de reprovações |
| P7 | decompor com planejador melhora a resolução | confirmada | rodada 4: 24/39 e 9/13 |
| P8, P9 | saídas esperadas do enunciado servem de oráculo determinístico | refutadas | 0 rebaixamentos em 84 revisões; falsa partida |
| P10 | o resultado se replica em outros modelos | confirmada | DeepSeek e Devstral |

### 5.3 Afirmações sustentadas (A1 a A10)

A1 nunca inferior em nenhum modelo. A2 29% mais barato na carga inteira, tokens menores em 74/117 pares. A3 custo de falha limitado (pior run 2,9 M × 8,1 M; cortados 1,5 M × 4,0 M; contexto máximo 37 k × 171 k). A4 melhor em funcionalidade nova de longo horizonte (7/9 × 2/9 nos três modelos, patches menores, suíte preservada, estável em 8 configurações). A5 revisor resgata (8 das 15 vitórias; 33 runs). A6 menos regressões (35 × 40) e menos avisos (4 × 8). A7 igual ou mais consistente. A8 vantagem real de custo maior que a reportada onde não há desconto de cache. A9 perdas com causa de desenho (10 patches certos nunca aprovados; plano serial em peewee-0002). A10 instrumento válido (15/15 vitórias limpas, 0 críticos, cinco portões, paridade por teste).

### 5.4 Hipóteses para o próximo estudo (H1 a H8)

H1 custo total ≥ 20% menor. H2 vantagem cresce com o horizonte. H3 planejador que agrupa defeitos independentes elimina a desvantagem na faixa média. H4 calibração do revisor corta metade dos turnos após o verde sem mais aprovações erradas. H5 exemplo executável por critério reduz as aprovações erradas abaixo das conclusões falsas do agente único. H6 vantagem cresce com orçamento e tamanho. H7 vantagem econômica maior em contexto curto ou caro e em provedor sem desconto de cache. H8 com H3 e H4, superioridade em resolução num estudo de 40 a 60 tarefas (projeção: as 7 derrotas por orçamento ou peewee-0002 viradas em empate levariam +3 a +10 runs em 117; hipótese, não resultado).

Poder: com 13 tarefas, probabilidade 0,01 de detectar +30 pontos percentuais; 0,39 com 30; 0,85 com 60 [27 §5; A, seção "Poder"].

### 5.5 Ameaças à validade (resumo de 27 §6)

Poder baixo (13 tarefas); uma tarefa grande que discrimina; modelos não pensantes de pesos abertos; análises exploratórias sem correção para múltiplos testes; as rodadas otimizaram a métrica visível (aprovações erradas) e deixaram a reprovação de patch certo sem tratar; custo em dólares do Devstral depende da cobrança da Mistral.

---

## 6. Estrutura sugerida dos capítulos que faltam

O capítulo "Desenvolvimento" existe em `docs/tcc/texto/desenvolvimento.tex` (16/10/2026) e precisa de uma atualização com as rodadas 5 a 8, o isolamento de 22/10 e a replicação (seção 3 deste pacote). Faltam:

- **Resultados.** 1 Visão geral das três coletas (4.1). 2 As sete métricas (4.2, 4.3). 3 Análise pareada e por faixa (4.1). 4 Tarefa a tarefa, teto, piso e as oito que discriminam (4.5). 5 Custo real, cache e integridade (4.4, 4.8).
- **Discussão.** 1 Vereditos das hipóteses (5.1, 5.2). 2 Mecanismos: tomlkit-0002, resgates do revisor, peewee-0002, custo do revisor (4.6, 4.7). 3 Economia da topologia (4.4, A2, A3, A8). 4 Ameaças à validade (5.5). 5 Lições da construção do instrumento (27 §3).
- **Conclusão.** Afirmações A1 a A10, contribuições (27 §7), hipóteses H1 a H8 e dimensionamento do próximo estudo.

---

## 7. Prompts, um por seção (colar no Perplexity, na ordem)

1. "Com base no pacote (seção 4.1 e 4.2) e no documento 27 §4.1, escreva a seção 'Resultados: visão geral das três coletas', 600 a 800 palavras, com a tabela 4.1 em formato de tabela e a tabela 4.2 em seguida. Cada número com a fonte entre colchetes."
2. "Escreva 'Análise pareada e por faixa' a partir de 4.1 (parágrafo dos intervalos) e E §1 e §2, 400 a 600 palavras. Deixe explícito que o sinal da faixa grande vem de uma tarefa."
3. "Escreva 'Tarefa a tarefa' a partir de 4.5 e 4.6, 600 a 800 palavras, com a tabela 4.5."
4. "Escreva 'Custo, cache e integridade' a partir de 4.4 e 4.8, 500 a 700 palavras, marcando o custo da carga inteira como análise exploratória."
5. "Escreva 'Discussão: vereditos das hipóteses' a partir de 5.1 e 5.2, 500 a 700 palavras, com as duas tabelas."
6. "Escreva 'Discussão: mecanismos' a partir de 4.6 e 4.7, 800 a 1.000 palavras, com uma subseção por mecanismo (tomlkit-0002, resgates do revisor, custo do revisor, peewee-0002)."
7. "Escreva 'Discussão: economia da topologia e ameaças à validade' a partir de 4.4, A2, A3, A8 e 5.5, 600 a 800 palavras."
8. "Escreva 'Conclusão' a partir de 5.3, 5.4 e 27 §7, 600 a 900 palavras, terminando com o dimensionamento do próximo estudo."
9. "Atualize o capítulo 'Desenvolvimento' anexado com a seção 3 do pacote: rodadas 5 a 8, isolamento, replicação, cronograma. Não remova nada que já esteja correto; marque o que mudou."

Depois de cada resposta: colar aqui para conferência de números; só então passar ao LaTeX.

---

## 8. Lista de conferência (o que eu confiro quando o texto voltar)

- Todo número do texto existe em A, T, E, 27 ou 28, com a mesma unidade e o mesmo recorte (runs × tarefas; mediana × total; pares resolvidos por ambos × carga inteira).
- "Significativo" aparece só para o consumo de tokens no Devstral 2 (p = 0,031) e, marcado como exploratório, para tokens e dólares na carga inteira.
- "Faixa grande a favor do orquestrado" sempre acompanhada de "uma tarefa que discrimina".
- Vocabulário da seção 2, sem sinônimos.
- Nenhuma afirmação sobre modelos pensantes, modelos fechados ou tarefas de outras linguagens.

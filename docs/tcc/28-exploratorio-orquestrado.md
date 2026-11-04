# 28. Análise exploratória: onde o orquestrado se destaca, onde perde e por quê

**Data.** 30/10/2026. **Natureza.** Exploratória e pós-hoc: foi feita depois de o resultado primário estar fechado ([27-relatorio-cientifico.md](27-relatorio-cientifico.md) §4 e §5), a pedido do autor, para descrever mecanismos e gerar hipóteses. Nada aqui altera o desfecho primário (117 pares, orquestrado 80 contra 77, McNemar p = 0,70) nem a hierarquia de desfechos fixada a priori. Cada número tem o arquivo de origem ao lado; a fonte principal é `dados/coleta-deepseek/exploratorio-orquestrado.txt`, saída de `scripts/exploratorio_orquestrado.py` sobre os mesmos 234 runs do agregado (`dados/coleta-deepseek/agregado-tres-modelos.txt`: Qwen3-Coder com single-agent pareado e orquestrado da rodada 4; DeepSeek V3.2; Devstral 2).

**Como ler.** Uma análise exploratória olha os dados depois de conhecer o resultado e por isso não pode confirmar nada: o que ela encontra vale como hipótese para um estudo dimensionado para testá-la (§3). As comparações abaixo não são corrigidas para múltiplos testes, e os intervalos de confiança são de Wald para diferença de proporções pareadas, sem margem de não inferioridade pré-especificada. Dito isso, os mecanismos descritos são observações diretas dos eventos dos runs, não inferência estatística, e é neles que está o valor desta seção.

---

## 1. Cinco pontos em que os dados favorecem o orquestrado

### 1.1 Custo total da carga de trabalho: 29% mais barato, nos três modelos

A métrica 2 do estudo (tokens nos pares em que os dois braços resolveram, `03-metricas.md`) disse que o orquestrado gasta 1,82 vez os tokens do agente único no Qwen, 1,24 no DeepSeek e 0,64 no Devstral (`27` §4.2). Essa métrica censura os runs que falharam. Quando se olha a carga inteira, 117 pares, o sentido inverte e fica estável (`exploratorio-orquestrado.txt` §12):

| modelo | US$ single-agent | US$ orquestrado | diferença | US$ por run resolvido SA → OR | pares com OR < SA em tokens | Wilcoxon pareado, tokens |
|---|---|---|---|---|---|---|
| Qwen3-Coder | 8,44 | 5,67 | −33% | 0,367 → 0,236 (−36%) | 19/39 | p = 0,151 |
| DeepSeek V3.2 | 8,02 | 5,56 | −31% | 0,308 → 0,214 (−31%) | 24/39 | p = 0,025 |
| Devstral 2 | 5,46 | 4,24 | −22% | 0,195 → 0,141 (−27%) | 31/39 | p < 0,001 |
| **todos** | **21,91** | **15,47** | **−29%** | **0,285 → 0,193 (−32%)** | **74/117** | **p < 0,001** (aprox. normal); US$ pareado p = 0,031 |

O orquestrado resolveu 3 runs a mais gastando 29% menos. O mecanismo é visível nos extremos: o pior run do agente único consumiu 8,1 M tokens e o do orquestrado 2,9 M; entre os runs cortados por orçamento, a mediana é 4,0 M contra 1,5 M (§12). O agente único carrega a transcrição inteira: o prompt da última chamada tem mediana de 28 k, 30 k e 32 k tokens nos três modelos, com máximos de 171 k, 70 k e 106 k; o developer do orquestrado recomeça cada ciclo com a memória de trabalho e fica em 12 k, 21 k e 19 k, máximos 31 k, 37 k e 29 k (§13). O custo de falhar é limitado por construção.

Dois cuidados. Primeiro, as duas leituras são verdadeiras e respondem perguntas diferentes: "quando os dois acertam, quem gasta menos?" (métrica 2: o agente único no Qwen e no DeepSeek, porque o laço do revisor custa turnos, §2.1) e "para rodar a carga toda, quem gasta menos?" (o orquestrado, nos três). Um estudo futuro deve reportar as duas. Segundo, a fração do prompt servida em cache é maior no agente único (0,97 e 0,96 contra 0,91 e 0,88 no DeepSeek e no Devstral, `tokens_cached`, §15); como a Mistral não aplica o desconto de cache que o OpenRouter reporta (`26-replicacao.md` §8.3), a vantagem do orquestrado em dólares reais no Devstral é maior do que a tabela mostra, não menor. No DeepInfra a cobrança é igual ao reportado.

### 1.2 Trabalho de longo horizonte: a tomlkit-0002

A faixa grande favorece o orquestrado nos três modelos (16/27 contra 11/27, pares discordantes 6 a 1, p = 0,125, IC 95% da diferença +0,6 a +36 pontos; §1). Mas a faixa tem três tarefas, a tomlkit-0003 é teto (18/18) e a tomlkit-0004 é piso (0/18): **todo o sinal está na tomlkit-0002**, orquestrado 7/9 contra 2/9 (Qwen 2/3 contra 1/3, DeepSeek 3/3 contra 0/3, Devstral 2/3 contra 1/3; §1). É uma tarefa, logo uma hipótese, não um achado. O que a torna interessante é o mecanismo, que é o mesmo nos três modelos.

A tarefa pede uma funcionalidade nova com um teste oculto: construir chaves pontilhadas (`a.b.c = 1`) pela API do tomlkit, tocando `key()`, `Container.add()` e a serialização (`tasks/tomlkit-0002/statement.md`). Anatomia dos 9 runs do agente único (§10): nas 7 falhas, a suíte visível **nunca ficou verde**; em 6 delas o agente nunca sequer declarou que tinha terminado (a suíte não foi rodada pelo operador) e na sétima declarou 35 vezes com a suíte vermelha. Em 5 das 7 o teste oculto da funcionalidade já passava (f2p 1/1), mas o patch quebrou de 5 a 91 testes que passavam antes. Os runs chegaram a 120 turnos com 3,3 a 4,5 M tokens e contexto final de 49 k a 124 k. É o retrato de um agente que implementa a funcionalidade, quebra a suíte e não consegue mais recuperá-la dentro de um contexto que só cresce.

Nos 7 acertos do orquestrado (§9), o planejador fatiou a tarefa em 3 a 5 sub-tarefas em seis deles e numa só no sétimo ("estender `key()`", "adaptar `Container.add()`", "serializar sem cabeçalho de tabela", "compatibilidade"), o developer fechou em 1 ou 2 ciclos em 6 dos 7, com 0,41 a 1,43 M tokens; o revisor final reprovou com suíte verde uma vez em 3 deles antes de aprovar, e no sétimo (Devstral rep3, 5 ciclos, 1,88 M) reprovou cinco vezes um patch que o oráculo aprovou, e o run saiu resolvido cortado por orçamento. As duas falhas do orquestrado são um corte por orçamento com o oculto em 0/1 (Qwen rep1, 6 sub-tarefas) e um corte com o oculto em 1/1 e regressão (Devstral rep2).

O padrão é estável entre configurações do próprio orquestrado: nas oito rodadas com o Qwen (24 runs, oito políticas diferentes) a tomlkit-0002 saiu 13/24 contra 1/3 do agente único pareado (§16).

### 1.3 Resgates pelo revisor

Dos 15 pares em que só o orquestrado resolveu (§4 e §14):

- **8** seguem o roteiro "o revisor final reprovou com a suíte verde, o developer voltou a escrever, o oráculo oculto aprovou": pygments-0001 (Qwen rep1; Devstral rep2 e rep3), sqlite-utils-0002 (Qwen rep2), sqlite-utils-0003 (Qwen rep3) e tomlkit-0002 (Qwen rep3, DeepSeek rep1, Devstral rep3). Nos oito, o agente único pareado foi cortado por orçamento (em seis deles com 4,1 a 8,1 M tokens; nos outros dois, 3,9 M).
- **4** são pares em que o agente único parou com a suíte verde e o oculto reprovou (sqlite-utils-0001 no Devstral ×3, com 1/5 ocultos; sqlite-utils-0002 Qwen rep1, 5/11) e o orquestrado, trabalhando a partir da intent com critérios explícitos, acertou de primeira.
- **3** são cortes do agente único em que o orquestrado acertou sem reprovação (tomlkit-0002 DeepSeek rep2 e rep3, Devstral rep1).

No conjunto dos 117 runs orquestrados, 57 tiveram ao menos uma reprovação final com suíte verde; 33 deles terminaram resolvidos com escrita de arquivo depois da reprovação (§5, coluna "resgate?"), 6 terminaram resolvidos sem nenhuma escrita depois (a reprovação não mudou o patch) e 10 terminaram resolvidos mas cortados por orçamento (§11; é o custo tratado em §2.1).

### 1.4 Regressões, avisos do detector e consistência

Runs com regressão em teste que passava (`oracle.p2p`): agente único 16, 13 e 11 (40); orquestrado 13, 13 e 9 (35) (§5). Avisos do detector (C6, exceção silenciada): 8 contra 3 no Qwen, 0 contra 1 no DeepSeek, 0 contra 0 no Devstral (§7). Consistência: igual no Qwen (8/13) e no DeepSeek (12/13), 11/13 contra 10/13 no Devstral (§7). Complexidade ciclomática (`cc_mean_delta` mediano nos resolvidos): +0,009 contra +0,022, +0,021 contra +0,012, +0,018 contra +0,017; sem diferença legível (§7). São diferenças pequenas e descritivas; entram aqui para registrar que nenhuma métrica secundária vai contra o orquestrado de forma consistente.

### 1.5 Não inferioridade na resolução

A diferença pareada orquestrado menos agente único em 117 pares é +2,6 pontos percentuais, IC 95% de −6,1 a +11,3 (§2); por modelo, Qwen −12,5 a +17,6, DeepSeek −12,3 a +12,3, Devstral −12,2 a +22,5. Sem margem pré-especificada isto não é um teste de não inferioridade formal, mas a leitura é legítima como descrição: os dados excluem, com 95% de confiança, que o orquestrado resolva mais de cerca de 6 pontos a menos que o agente único, e isso com 29% a menos de gasto (§1.1). "Igual na resolução, mais barato na carga e com custo de falha limitado" é a frase que os dados sustentam.

---

## 2. Onde o orquestrado perde e por quê

Os mesmos eventos mostram as três fraquezas, todas com mecanismo identificável e, portanto, corrigíveis em desenho. Ficam aqui porque a seção 1 só é honesta ao lado delas.

### 2.1 O revisor reprova patch certo e consome o orçamento depois do verde

Em 10 runs o oráculo oculto aprovou o patch mas o revisor nunca o aprovou e o run foi cortado por orçamento (4 no Qwen, 5 no DeepSeek, 1 no Devstral; §5, "…resolvido" na linha OR). Dos 12 pares em que só o agente único resolveu, 6 são cortes do orquestrado por orçamento (§14). Medido em turnos: depois de a suíte ficar verde pela primeira vez, o orquestrado ainda gastou 55% dos turnos no Qwen (1.664 de 3.007), 46% no DeepSeek e 40% no Devstral; a mediana de turnos após o primeiro verde é 42 no Qwen e 13 nos outros dois (§11). É daqui que vem o 1,82 da métrica 2: quando os dois acertam, o orquestrado paga o laço do revisor. As rodadas 5 a 8 atacaram as aprovações erradas (comparação determinística, modo estrito); nenhuma atacou a reprovação de patch certo.

### 2.2 A decomposição serializa correções independentes: a peewee-0002

A peewee-0002 tem seis defeitos independentes em módulos distintos do peewee, cada um com sua seção no enunciado (`tasks/peewee-0002/statement.md`, 1.234 palavras, o maior dos 13). O agente único recebe os seis de uma vez e fecha 4/9 (87 a 111 turnos quando acerta). O orquestrado fecha 0/9 nos três modelos e 0/24 nas oito rodadas com o Qwen (§16). A anatomia é idêntica nos nove runs (§17): o planejador gera **sempre seis sub-tarefas, uma por defeito**; o developer bate o teto de 40 turnos do ciclo na sub-tarefa 1 ou 2 (no DeepSeek os três runs têm exatamente o mesmo perfil, 41 + 41 + 25 turnos); e o orçamento de 120 turnos acaba com no máximo três sub-tarefas iniciadas. Seis sub-tarefas a até 40 turnos cada não cabem em 120: a falha é estrutural, não do modelo. O progresso oculto confirma que o trabalho estava sendo feito, só que devagar demais: 5/6 no Devstral rep2, 4/6 no DeepSeek rep1, 3/6 em três runs.

A faixa média inteira vai nessa direção (24/36 contra 30/36, IC 95% da diferença −31 a −2 pontos; §1), e a peewee-0002 responde por 4 dos 7 pares discordantes dela; os outros três são attrs-0001 (Qwen rep3, corte com 0/3 ocultos) e sqlite-utils-0003 (Qwen rep1 e DeepSeek rep3). Não é a enumeração em si que trava o orquestrado: a pygments-0001 tem nove itens numerados no enunciado e o orquestrado fez 9/9 contra 6/9 (§1). O que trava é a combinação "vários defeitos em regiões independentes do código" com "plano serial de uma sub-tarefa por defeito" sob um teto de turnos por ciclo.

### 2.3 Aprovações erradas iguais às falsas conclusões do agente único

O orquestrado aprovou errado (revisor diz "concluiu", oráculo reprova) 13 vezes em 117; o agente único parou com a suíte verde e o oráculo reprovou 14 vezes (§5). O revisor não reduz a taxa de conclusão falsa; ele erra exatamente onde o enunciado não tem exemplo que exercite o critério oculto (`27` §4.4). A sensibilidade por tarefa (§3) mostra o mesmo quadro: tirar a tomlkit-0002 leva a diferença total a −2 runs; tirar a peewee-0002 leva a +7; tirar qualquer outra tarefa a deixa entre 0 e +5. O resultado nulo agregado é a soma de uma vantagem localizada e de uma desvantagem localizada, as duas com mecanismo conhecido.

---

## 3. Hipóteses para um estudo dimensionado

Formuladas aqui para serem pré-registradas; o poder necessário está em `27` §5 (com 13 tarefas a probabilidade de detectar +30 pontos é 0,01; com 60, 0,85).

- **H1 (custo total).** Com o mesmo orçamento por run, a topologia orquestrada com memória de trabalho reduz o custo total da carga em pelo menos 20% em dólares e em tokens, nos modelos testados. Unidade: par run a run; teste de Wilcoxon em todos os pares, sem censura; reportar também a métrica censurada. Nesta amostra: −29%, p = 0,031 em dólares, p < 0,001 em tokens (§12).
- **H2 (horizonte).** A vantagem do orquestrado em resolução cresce com o horizonte da tarefa, medido pelo número de turnos que o agente único precisa quando acerta e pelo tipo "funcionalidade nova" em vez de "correção". Exige ao menos 10 tarefas grandes que discriminem (nem teto nem piso num piloto). Nesta amostra: tomlkit-0002, 7/9 contra 2/9 (§1 e §10).
- **H3 (independência).** A desvantagem do orquestrado cresce com o número de regiões de código independentes que o enunciado pede para corrigir, sob plano serial. Exige tarefas construídas com k ∈ {1, 2, 3, 6} comportamentos independentes, mantendo o orçamento. Nesta amostra: peewee-0002, 0/9 contra 4/9 (§17).
- **H4 (calibração do revisor).** Uma regra de parada que aprove quando a comparação executável com as saídas esperadas do enunciado é satisfeita, ou que limite reprovações consecutivas com o patch inalterado, remove ao menos metade dos turnos gastos depois do verde sem aumentar as aprovações erradas. Pode ser calibrada offline nos 234 runs existentes antes de qualquer coleta: os eventos `validation`, `test_run` e `memory` permitem simular a regra (§11 dá a linha de base: 40% a 55% dos turnos após o verde; 10 patches certos nunca aprovados). **Calibrada em 04/11/2026** ([30-calibracao-h4.md](30-calibracao-h4.md)): a forma forte é refutada (nenhuma regra corta metade dos turnos sem pôr de 9 a 33 resoluções em risco); 58 das 136 reprovações com suíte verde vêm de bloco de reprodução que não compila, defeito já corrigido pelo `REPRODUCTION_COMPILE_CHECK` das rodadas 6 a 8 e desligado na configuração da rodada 4; H4 vira H4a (ligar a verificação de compilação) e H4b (aprovar patch inalterado, 6% dos turnos, no máximo 2 em risco).

Desenho sugerido: 40 a 60 tarefas estratificadas por k comportamentos e por tipo (funcionalidade/correção), 3 repetições pareadas por semente, os dois braços com os tetos congelados da decisão 12, e as duas métricas de custo. É o experimento que este estudo deixou pronto para ser feito.

---

## 4. Sugestão de redação para a discussão do TCC

O que os dados sustentam, numa frase: *a orquestração de papéis, com o resto constante, não muda a taxa de resolução de forma detectável em três modelos de dois laboratórios, mas muda a economia e o modo de falhar: limita o contexto e por isso limita o custo dos runs que falham (29% menos na carga inteira), é consistentemente melhor na tarefa de funcionalidade nova de longo horizonte em que o agente único se perde no próprio contexto, e é consistentemente pior quando o enunciado lista vários defeitos independentes que o plano serializa; as duas fraquezas, revisor que reprova patch certo e plano que serializa o independente, têm mecanismo identificado e correção de desenho proposta.*

O que não dizer: que a faixa grande "favorece" o orquestrado como achado (é uma tarefa); que o orquestrado "é mais barato" sem dizer que, quando os dois acertam, ele é mais caro no Qwen e no DeepSeek; que o revisor "melhora a qualidade" (as aprovações erradas são iguais às falsas conclusões do agente único); e que qualquer p desta seção confirma algo (é exploratória).

---

## 5. Fontes

- `dados/coleta-deepseek/exploratorio-orquestrado.txt`: saída de `scripts/exploratorio_orquestrado.py` (30/10/2026), seções §1 a §17 citadas acima.
- `dados/coleta-deepseek/agregado-tres-modelos.txt` e `por-tarefa-tres-modelos.txt`: agora reproduzíveis por `scripts/agregado_tres_modelos.py` e `scripts/por_tarefa_tres_modelos.py` (a nota de reprodução do oráculo no fim do segundo foi acrescentada à mão em 29/10).
- Runs: `docs/tcc/dados/coleta` (single-agent Qwen, menos as três tarefas da decisão 27), `docs/tcc/dados/coleta-r2/<tarefa>/single-agent` (as três refeitas), `docs/tcc/dados/coleta-r4` (orquestrado Qwen), `runs/coleta-deepseek`, `runs/coleta-devstral` (dados também em `docs/tcc/dados/coleta-deepseek` e `coleta-devstral`); rodadas 1 a 8 em `docs/tcc/dados/coleta`, `coleta-r2` a `coleta-r8`.
- Enunciados: `tasks/tomlkit-0002/statement.md`, `tasks/peewee-0002/statement.md`, `tasks/pygments-0001/statement.md`.
- Métricas e poder: `03-metricas.md`, `27-relatorio-cientifico.md` §4.2, §4.4, §5; cobrança da Mistral: `26-replicacao.md` §8.3.

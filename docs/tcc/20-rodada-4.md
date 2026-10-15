# 20. Rodada 4: planejador de sub-tarefas (15/10/2026)

Rodada aprovada por escrito em 15/10/2026 (decisão 33): rodada 2 mais o planejador (`PLANNER=on`) e a execução acumulada dos exemplos (`REVIEW_EXECUTION=cumulative`, decisão 34), teto de reprovações 2. Só o orquestrado rodou, 13 tarefas × 3 repetições, mesmas sementes; o single-agent de comparação é o pareado da rodada 2. Execução 15/10 10:43 a 19:32, 39 concluídas, 0 perdidas (1 tentativa perdida por provedor na peewee-0002 rep01, refeita), manifesto v12. Dados: `dados/coleta-r4/`; raiz pareada `runs/coleta-r4-analise/`; análises `dados/coleta-r4/analise-sete-metricas.{md,json}` e `apendice-metricas.md`; fumaça prévia em `dados/fumaca-planejador/`.

## 1. Resultado: primeira rodada em que o orquestrado passa o agente único em tarefas

| | runs resolvidos (de 39) | tarefas (mediana, de 13) | por repetição | grande / média / pequena | custo | tokens | parede total |
|---|---|---|---|---|---|---|---|
| single-agent pareado | 23 | 8 | 7, 10, 6 | 4/9, 10/12, 9/18 | US$ 8,44 | 72,4 M | 3,9 h |
| orquestrado, coleta principal (r1) | 17 | 6 | 6, 5, 6 | 4/9, 4/12, 9/18 | US$ 5,21 | 40,6 M | 4,2 h |
| orquestrado, rodada 2 | 23 | 7 | 9, 8, 6 | 4/9, 6/12, 13/18 | US$ 4,72 | 33,4 M | 5,2 h |
| orquestrado, rodada 3 | 19 | 5 | 7, 5, 7 | 5/9, 5/12, 9/18 | US$ 5,58 | 41,1 M | 5,7 h |
| **orquestrado, rodada 4** | **24** | **9** | 7, 10, 7 | **5/9**, 7/12, 12/18 | US$ 5,67 | 37,9 M | 7,8 h |

Por tarefa (✓ por repetição; SA = single-agent pareado):

| tarefa | faixa | SA | r4 | r2 | r1 |
|---|---|---|---|---|---|
| attrs-0001 | média | ✓✓✓ | ✓✓✗ | ✓✓✗ | ✓✗✓ |
| peewee-0001 | média | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✗✓✓ |
| peewee-0002 | média | ✓✓✗ | ✗✗✗ | ✗✗✗ | ✗✗✗ |
| peewee-0003 | pequena | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| pygments-0001 | pequena | ✗✓✓ | **✓✓✓** | ✗✓✗ | ✗✗✗ |
| sqlite-utils-0001 | pequena | ✗✓✗ | ✗✓✗ | ✗✓✗ | ✗✗✗ |
| sqlite-utils-0002 | pequena | ✗✗✗ | ✓✓✗ | ✓✓✓ | ✓✓✓ |
| sqlite-utils-0003 | média | ✓✓✗ | ✗✓✓ | ✓✗✗ | ✗✗✗ |
| tomlkit-0001 | pequena | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✗✓ |
| tomlkit-0002 | grande | ✗✓✗ | **✗✓✓** | ✓✗✗ | ✗✓✗ |
| tomlkit-0003 | grande | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| tomlkit-0004 | grande | ✗✗✗ | ✗✗✗ | ✗✗✗ | ✗✗✗ |
| tomlkit-0005 | pequena | ✗✗✗ | ✗✗✗ | ✓✗✓ | ✓✗✗ |

## 2. As sete métricas (`dados/coleta-r4/analise-sete-metricas.md`)

| # | métrica | single-agent | orquestrado r4 | n | p | (rodada 2: OR, p) |
|---|---|---|---|---|---|---|
| 1 | tarefas resolvidas (mediana) | 8/13 | 9/13 | 5 pares não empatados (3 +OR, 2 −SA) | 1,0 | 7/13, 0,69 |
| 2 | tokens (mediana, resolvidas por ambos) | 314 294 | 769 526 | 7 | 0,30 | 219 388, 0,63 |
| 3 | segundos (mediana, resolvidas por ambos) | 155 | 284 | 7 | 0,375 | 245, 0,125 |
| 4 | consistência | 5/10 | 5/10 | | | 5/11 |
| 5 | Δ complexidade (mediana) | 0,014 | 0,010 | 7 | 0,94 | 0,028 |
| 6 | conclusão sem corte | 29/39 | 23/39 | | | 28/39 |
| 7 | violações (crít.; bloq.; negações) | 0; 0; 5 | 0; 0; 10 | | | 0; 0; 3 |

Por faixa (apêndice B, sinal sobre a fração de repetições): grande 1 +OR / 0 / 2 empates; média 0 / 2 / 2 (p = 0,5); pequena 2 / 0 / 4 (p = 0,5); todas 3 / 2 / 8 (p = 1). É a primeira rodada em que a faixa grande pende para o orquestrado (tomlkit-0002 2/3 contra 1/3) e a primeira em que, por tarefa, ele fica à frente (9 × 8). Nenhum p chega perto de 0,05: com 13 tarefas, uma diferença de uma tarefa não é distinguível do acaso.

## 3. O que o planejador fez de fato

Contagem nos 39 runs (eventos `plan`, `validation`, `memory`; `dados/coleta-r4`):

- **Planos.** 39, nenhum fallback. Mediana de 5 sub-tarefas por plano (1 a 6), 12 turnos de exploração (mínimo 2); 13 chamadas por run, 509 turnos dos 4 680 da rodada (11 %). 2 replanejamentos (tomlkit-0001 rep01 e rep03, que ainda assim resolveram).
- **Sub-tarefas.** De 186 criadas, 13 feitas, 24 adiadas, 2 abandonadas, 108 nunca chegaram a começar. A revisão de sub-tarefa reprovou 68 de 81. Dos 24 runs resolvidos, só 8 tiveram alguma sub-tarefa marcada como feita: nos outros 16 o developer, com a sub-tarefa 1 na mão, resolveu a tarefa inteira e a revisão final aprovou com o plano aberto (6 em um ciclo só, 18 em dois ou mais).
- **Leitura.** O ganho veio da exploração do planejador e do foco da primeira fatia, não da esteira de sub-tarefas: o developer herda do plano os arquivos certos (tomlkit-0002: `api.py`, `container.py`, `items.py`) e a descrição do primeiro passo, e segue dali. A máquina de avançar, adiar e replanejar quase não foi usada, e o revisor de sub-tarefa, reprovando 84 %, empurra mais sub-tarefas para "adiada" do que para "feita".
- **Revisão final.** 90 revisões, 66 reprovadas; 3 runs encerraram com o revisor aprovando código que o oráculo reprovou (sqlite-utils-0001 rep3, sqlite-utils-0002 rep3, sqlite-utils-0003 rep1 com 12/12 no `f2p` e uma regressão). Rodada 2: 4.

Como os 15 runs não resolvidos acabaram: 10 cortados com zero teste oculto (tomlkit-0004 ×3, tomlkit-0005 ×3, attrs rep3, peewee-0002 rep2, sqlite-utils-0001 rep1, tomlkit-0002 rep1), 2 cortados quase lá (peewee-0002 rep1 e rep3, 1/6 e 3/6), 3 pelo revisor aprovando errado.

## 4. O que custou

- **Tokens por run dobraram:** mediana 884 mil contra 464 mil na rodada 2 (apêndice A: 883 706 × 463 756). O planejador lê o repositório com prompts de 20 mil tokens, o validador roda a suíte mais vezes (112 execuções contra 80) e os runs têm mais ciclos. O custo total subiu menos (US$ 5,67 × 4,72) porque o preço por token é baixo; em tokens nas 7 tarefas resolvidas por ambos, o orquestrado passou a gastar mais que o single-agent (770 mil × 314 mil), o inverso da rodada 2.
- **Parede:** 7,8 h contra 5,2 h. Três runs cortados por `max_wall_seconds` (tomlkit-0003 rep1, resolvido mesmo assim; tomlkit-0004 rep1; tomlkit-0005 rep1), todos entre 16:31 e 18:53, com latência mediana de 26 a 46 s por chamada contra 1,4 s na rodada: latência do provedor, como na fumaça H, não o desenho.
- **Negações de escrita:** 10 (rodada 2: 3), 6 delas `write_file` do developer; o planejador às vezes lista `tests/` em `files` da sub-tarefa de regressão e o developer tenta.
- **tomlkit-0005** caiu de 2/3 para 0/3 e **sqlite-utils-0002** de 3/3 para 2/3; **pygments-0001** subiu de 1/3 para 3/3 e **sqlite-utils-0003** de 1/3 para 2/3. Com três repetições, variações de uma repetição por tarefa são compatíveis com a variância observada entre rodadas.

## 5. Leitura para o texto

- O orquestrado com planejador é a melhor configuração em resolução (24 runs, 9 tarefas, grande 5/9), mas paga em tokens (2× por run) e parede. A rodada 2 continua sendo a mais barata com resolução equivalente em runs.
- A hipótese do autor (fatiar o problema ajuda mais quanto maior a tarefa) ganha o primeiro sinal na direção certa: grande e pequena melhoram, média não (7/12 contra 10/12 do single-agent; peewee-0002 segue 0/3). Sinal, não prova: p = 1,0 no conjunto.
- O mecanismo que ajudou não foi o que o desenho previa. Ajudou a exploração prévia e a primeira fatia com arquivos nomeados; a esteira de sub-tarefas (feita → próxima) quase não andou, por causa de um revisor de sub-tarefa que reprova 84 % das vezes. Decisão 35 pendente: calibrar a revisão de sub-tarefa (reprovar só com motivo executável) ou substituí-la por comparação determinística das saídas esperadas.
- tomlkit-0004 fica em 0 de 19 runs em todas as configurações: limite do modelo, igual nos dois braços.

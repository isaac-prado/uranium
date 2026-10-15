# 19. Balanço em linguagem simples e caminhos com o orçamento restante (15/10/2026)

Escrito a pedido do autor depois da rodada 3. Fontes: `dados/coleta` (coleta principal), `dados/coleta-r2` (rodada 2, configuração final do orquestrado), `dados/coleta-r3`, `dados/ablacao-refinador`, `dados/refinador-v2`; análises `analise-sete-metricas.md` e `apendice-metricas.md` de cada pasta. O pareamento final é o da rodada 2: orquestrado da rodada 2 contra o single-agent da coleta principal (10 tarefas) e da rodada 2 (3 tarefas reconstruídas).

## 1. Onde estamos

Três rodadas do orquestrado contra o mesmo agente único, mesmo modelo, mesmas ferramentas, mesmo limite de 120 turnos:

| | runs resolvidos (de 39) | tarefas resolvidas na maioria das repetições (de 13) | custo |
|---|---|---|---|
| agente único | 23 | 8 | US$ 8,44 |
| orquestrado, versão original do TFG | 17 | 6 | US$ 5,21 |
| orquestrado, rodada 2 (refinador que copia o enunciado, revisor que executa os exemplos, nota ao fim de cada ciclo, tarefas com suíte alcançável) | **23** | **7** | **US$ 4,72** |
| orquestrado, rodada 3 (rodada 2 sem teto de reprovações) | 19 | 5 | US$ 5,58 |

A rodada 2 é a configuração final. A rodada 3 serviu para mostrar que o revisor é o ponto fraco.

## 2. Todas as métricas da rodada 2 (orquestrado × agente único)

| o que mede | agente único | orquestrado | leitura |
|---|---|---|---|
| runs resolvidos | 23/39 | 23/39 | empate |
| tarefas resolvidas (mediana das 3 repetições) | 8/13 | 7/13 | diferença não distinguível do acaso (p = 0,69) |
| por faixa: grande / média / pequena (runs) | 4/9 · 10/12 · 9/18 | 4/9 · 6/12 · 13/18 | único ganha nas médias, orquestrado nas pequenas |
| fração média dos testes ocultos que passam | 0,715 | 0,784 | orquestrado chega mais perto quando não resolve |
| consistência (resolve 3/3 entre as que resolve ao menos 1 vez) | 5 de 10 | 5 de 11 | igual |
| tokens por run (mediana) | 979 mil | 464 mil | orquestrado gasta metade |
| tokens totais nos 39 runs | 72,4 M | 33,4 M | |
| custo total | US$ 8,44 | US$ 4,72 | |
| chamadas ao modelo por run (mediana) | 50 | 47 | igual |
| tempo de parede por run (mediana) | 243 s | 280 s | orquestrado mais lento |
| tempo até resolver, só nos runs resolvidos (mediana) | 141 s | 199 s | orquestrado 40 % mais lento |
| tempo nas 5 tarefas que ambos resolvem (mediana por tarefa) | 113 s | 245 s | p = 0,125; é o custo de executar os exemplos a cada revisão |
| linhas do patch (mediana) | 40 | 34 | orquestrado escreve menos (p = 0,03 nas 13 tarefas) |
| variação da complexidade ciclomática (mediana) | +0,014 | +0,010 | igual |
| variação do índice de manutenibilidade (mediana) | 0 | 0 | igual |
| runs que quebram algum teste existente | 15 | 16 | igual |
| termina sozinho, sem bater no limite | 29/39 | 28/39 | igual |
| cortes por tokens / por tempo | 1 / 0 | 0 / 0 | |
| tentativas de escrever em área proibida (negadas) | 5 | 3 | igual (era 39 na versão original) |
| trapaça consumada | 0 | 0 | |
| avisos do detector (`except: pass` novo) | 8, todos em sqlite-utils-0001 rep3 | 0 | |
| só no orquestrado: ciclos developer→validador por run | | 1 a 4 (máximo era 33 na versão original) | |
| só no orquestrado: revisões / reprovações | | 59 / 37 | |
| só no orquestrado: exemplos executados pelo revisor | | 155 blocos, 31 quebram por rodar isolados | |
| só no orquestrado: notas de ciclo | | 31 | |

## 3. Por que os dois param em 23 de 39

Os 16 runs perdidos de cada lado, lado a lado:

| motivo | agente único | orquestrado |
|---|---|---|
| limite de 120 turnos com zero teste oculto passando (o modelo não acha o caminho) | 4 | 5 |
| limite de 120 turnos quase lá (faltava 1 ou 2 testes ocultos) | 6 | 6 |
| parou achando que terminou, e o teste oculto reprovou | 6 (suíte visível verde) | 4 (revisor aprovou) + 1 (teto de reprovações) |

Três coisas separadas estão misturadas aí:

1. **Teto do modelo.** tomlkit-0004 é 0 em 6; tomlkit-0002 1 em 3 nos dois; pygments e tomlkit-0005 alternam. São 9 runs de cada lado. Nenhum desenho de agente resolve isso com o qwen3-coder; é o limite do modelo, igual para os dois.
2. **O enunciado e a suíte visível não dizem tudo que o teste oculto cobra.** Os 6 runs do agente único que pararam com a suíte verde e os 4 em que o revisor aprovou são o mesmo fenômeno: o agente fez o que conseguia ver, e o oráculo queria mais. Exemplo: sqlite-utils-0002, onde o agente único fica verde em 28 turnos e o oráculo reprova 6 testes. Isso é limitação do desenho das tarefas, e atinge os dois braços na mesma proporção.
3. **O que é de cada braço.** O agente único perde a continuidade só quando estoura o contexto (1 corte por tokens). O orquestrado perde onde a tarefa tem muitas partes (seção 4) e quando o revisor erra (4 aprovações erradas, 15 das 37 reprovações apoiadas em exemplo que não rodou).

Para subir os 23: o item 1 só muda com outro modelo. O item 2 só muda reescrevendo tarefas, o que invalidaria a coleta. O item 3 é onde dá para mexer com os US$ 10 (seção 5).

## 4. Por que o agente único ganha nas tarefas médias

Tarefas médias mexem em 3 a 7 arquivos. A diferença está em quanto cada braço "lembra". Números dos 12 runs médios de cada lado (`runs/coleta-r2-analise`):

| | agente único | orquestrado |
|---|---|---|
| tamanho médio do que o modelo recebe por chamada, peewee-0002 | 18 a 22 mil tokens | 9 a 14 mil tokens |
| tamanho máximo | 32 a 39 mil | 15 a 22 mil |
| arquivos alterados em peewee-0002 | `peewee.py` + `playhouse/migrate.py` + `playhouse/reflection.py` nos 3 runs | os 3 em 2 runs; só `peewee.py` em 1 run (rodada 3: só `peewee.py` nos 3) |
| leituras de arquivo em peewee-0002 | 33 a 52 | 38 a 59, com releitura dos mesmos arquivos a cada ciclo |
| resultado peewee-0002 | 6/6, 6/6, 5/6 | 5/6, 4/6, 4/6 |

O agente único carrega a conversa inteira: tudo que leu fica à mão até o fim, e o custo é o contexto crescer. O orquestrado trabalha em ciclos de 40 turnos; ao voltar do validador, recebe a intent, o registro do que fez e o diff, mas não o conteúdo do que leu. Em tarefa de uma parte isso não pesa. Em tarefa de seis partes espalhadas por três arquivos, cada ciclo reexplora e o developer não chega às partes do `playhouse`. Isso não é bug do Uranium: é o preço da divisão em papéis, que é exatamente o que a hipótese testa. A memória de trabalho (decisão 8) reduziu o dano (o máximo de ciclos caiu de 33 para 4), não o eliminou.

## 5. Falhas encontradas que ainda dá para atacar (US$ 10 = uma rodada do orquestrado, US$ 5 a 6)

| falha | evidência | conserto | custo | ganho esperado |
|---|---|---|---|---|
| revisor executa cada exemplo isolado; exemplos encadeados quebram e ele reprova por "não consegui verificar" | 31 de 155 blocos quebrados na rodada 2, 15 das 37 reprovações | executar os blocos acumulados no mesmo namespace; "não verificável" não conta como reprovação (decisão 34) | harness, sem prompt novo, meio dia | menos reprovações falsas; na rodada 2 custaram ciclos, não runs, então o ganho direto é pequeno |
| developer não chega às partes espalhadas em tarefas médias | peewee-0002: 0/3; `playhouse` não tocado em 1 de 3 runs (3 de 3 na rodada 3) | decomposição por critério (decisão 33, versão leve): o validador diz quais critérios faltam e o developer é mandado ao próximo pendente, com o exemplo dele | muda `src/feedback.py`, precisa de aprovação; um dia | é o único conserto que mira a faixa média; sem garantia |
| revisor aprova código errado sem listar critério | 4 runs na rodada 2, 7 na rodada 3 | comparar a saída executada com a saída esperada de forma determinística quando a intent traz as duas | harness; só funciona quando o exemplo roda | pega parte dos 4 |
| `run_python` reescreve arquivo inteiro e destrói o trabalho | 1 run (peewee-0001 no refinador v2) | registrar na telemetria; bloquear seria mudar ferramenta congelada (decisão 31) | pequeno | raro |
| agente único para com a suíte verde e o oculto reprova | 6 runs | não há conserto sem reescrever tarefas; fica em ameaças à validade | | |
| oráculo do pygments cobra o golden inteiro, o enunciado lista 17 casos | 3 de 6 runs perdidos | idem | | |

Com uma rodada só, a aposta de maior retorno é a terceira linha junto com a primeira (decisões 33 leve + 34), mantendo o teto de reprovações em 2 e tudo mais da rodada 2. Se não houver rodada 4, a rodada 2 fecha o trabalho.

## 6. A tese não precisa escolher entre "hipótese" e "limitação do Uranium"

A pergunta é: a orquestração em papéis resolve mais que um agente único, com o mesmo modelo, as mesmas ferramentas e o mesmo limite? A resposta medida é **não**: empate em runs, uma tarefa a menos na mediana, sem diferença estatística, gastando metade dos tokens e levando mais tempo de parede. Isso é um resultado, e é defensável.

O que parece dualidade se resolve separando três camadas, cada uma com número:

- **Limites que afetam os dois braços igualmente** (teto do modelo: 9 runs de cada lado; enunciado mais frouxo que o oráculo: 6 contra 4; bugs do harness encontrados e corrigidos antes do pareamento final: rootdir, deselect, schema). Entram em "ameaças à validade". Não enviesam a comparação porque são simétricos; reduzem o teto dos dois.
- **Limites do orquestrado que são o próprio tratamento** (revisor que erra, contexto reiniciado a cada ciclo). Não são "limitação do Uranium": são o custo de dividir o trabalho em papéis. É isso que a hipótese testa, e a resposta é que, neste protótipo e com este modelo, o custo da divisão come o ganho.
- **O que a divisão entrega de concreto**: metade dos tokens, menos linhas de patch, 39 → 3 tentativas de escrever em área proibida com o refinador que copia o enunciado, e 3/3 no sqlite-utils-0002 onde o agente único para cedo demais.

Escrito assim, o trabalho não "prova" nem "desaprova" orquestração em geral. Mostra, com medição, onde a orquestração deste tipo paga e onde custa, e por quê. Para um TCC de graduação com um ano, é mais do que a maioria entrega: três rodadas, 234 runs pagos, tudo rastreável.

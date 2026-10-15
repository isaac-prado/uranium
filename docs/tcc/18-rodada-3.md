# 18. Rodada 3: revisor coerente e sem teto de reprovações (15/10/2026)

Rodada aprovada por escrito em 14/10/2026 (decisão 32): rodada 2 mais `REVIEW_STRICT=on` (revisão que lista critérios não cobertos não aprova) e `MAX_SEMANTIC_REJECTIONS=0` (sem teto: parada só por suíte verde ou orçamento). Só o braço orquestrado rodou, 13 tarefas × 3 repetições, mesmas sementes; o single-agent de comparação é o pareado da rodada 2 (`runs/coleta-r2-analise/*/single-agent`). Manifesto v11. Execução 14/10 23:3x a 15/10 05:0x, 39 concluídas, 0 perdidas (`dados/coleta-r3/collection-orchestration.log`).

## 1. Resultado: pior que a rodada 2

| orquestrado | runs resolvidos | por repetição | tarefas (mediana) | grande / média / pequena | cortes em 120 | US$ | tokens | parede |
|---|---|---|---|---|---|---|---|---|
| coleta principal (r1) | 17/39 | 6, 5, 6 | 6/13 | 4/9, 4/12, 9/18 | 16 | 5,21 | 40,6 M | 4,2 h |
| rodada 2 | 23/39 | 9, 8, 6 | 7/13 | 4/9, 6/12, 13/18 | 11 | 4,72 | 33,4 M | 5,2 h |
| **rodada 3** | **19/39** | 7, 5, 7 | **5/13** | 5/9, 5/12, 9/18 | 17 | 5,58 | 41,1 M | 5,7 h |
| single-agent pareado | 23/39 | 7, 10, 6 | 8/13 | 4/9, 10/12, 9/18 | 10 | 8,44 | 72,4 M | |

Fonte: `result.json` e `summary.json` em `dados/coleta`, `dados/coleta-r2`, `dados/coleta-r3`; sete métricas em `dados/coleta-r3/analise-sete-metricas.md` (resolução 8/13 × 5/13, sinal p = 0,69; tokens 217 984 × 399 765 nas 4 resolvidas por ambos; tempo 146 s × 332 s, p = 0,25; conclusão sem corte 29/39 × 22/39; negações 5 × 1).

Por tarefa (✓ por repetição):

| tarefa | faixa | SA | r3 | r2 | r1 |
|---|---|---|---|---|---|
| attrs-0001 | média | ✓✓✓ | ✓✗✗ | ✓✓✗ | ✓✗✓ |
| peewee-0001 | média | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✗✓✓ |
| peewee-0002 | média | ✓✓✗ | ✗✗✗ | ✗✗✗ | ✗✗✗ |
| peewee-0003 | pequena | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| pygments-0001 | pequena | ✗✓✓ | ✗✗✓ | ✗✓✗ | ✗✗✗ |
| sqlite-utils-0001 | pequena | ✗✓✗ | ✗✓✗ | ✗✓✗ | ✗✗✗ |
| sqlite-utils-0002 | pequena | ✗✗✗ | ✓✗✗ | ✓✓✓ | ✓✓✓ |
| sqlite-utils-0003 | média | ✓✓✗ | ✗✗✓ | ✓✗✗ | ✗✗✗ |
| tomlkit-0001 | pequena | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✗✓ |
| tomlkit-0002 | grande | ✗✓✗ | ✓✗✓ | ✓✗✗ | ✗✓✗ |
| tomlkit-0003 | grande | ✓✓✓ | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| tomlkit-0004 | grande | ✗✗✗ | ✗✗✗ | ✗✗✗ | ✗✗✗ |
| tomlkit-0005 | pequena | ✗✗✗ | ✗✗✗ | ✓✗✓ | ✓✗✗ |

## 2. Por que piorou: o revisor reprova o que não consegue executar, e agora sem teto

Classificação dos 39 runs da rodada 3 (eventos `validation`, `memory`, `test_run`; oráculo em `result.json`):

| como acabou | runs | notas |
|---|---|---|
| resolvido | 19 | 6 deles só depois de 4 a 11 reprovações seguidas (peewee-0003 rep1 e rep2: 11 reprovações cada, cortados em 120 turnos numa tarefa que a rodada 2 fechou em 10 a 19 turnos; tomlkit-0003 rep2: 6; sqlite-utils-0002 rep1: 7; tomlkit-0002 rep1 e rep3: 4 e 3) |
| orçamento | 13 | peewee-0002 ×3, tomlkit-0004 ×3, tomlkit-0005 ×3 (3, 3 e 2 reprovações cada), pygments rep1, sqlite-utils-0002 rep2, sqlite-utils-0003 rep1, tomlkit-0002 rep2 |
| revisor aprovou, oráculo reprovou | 7 | attrs rep2 e rep3, pygments rep2, sqlite-utils-0001 rep1 e rep3, sqlite-utils-0002 rep3, sqlite-utils-0003 rep2 (12/12 no `f2p`, regressão) |

**Revisões.** 98 revisões, 76 reprovadas (78 %; rodada 2: 59 e 37, 63 %). A regra do revisor coerente disparou 3 vezes só. O que mudou de verdade foi tirar o teto: as reprovações passaram a custar turnos sem limite.

**A causa das reprovações.** O validador executa cada bloco de reprodução da intent **isoladamente**, num namespace novo. Quando o enunciado traz blocos encadeados (o segundo usa o `db`, o `EnumField` ou a importação do primeiro), o bloco falha com `NameError`/`ImportError` e o revisor reprova por "não foi possível verificar":

| | rodada 2 | rodada 3 |
|---|---|---|
| blocos executados | 155 | 221 |
| blocos com traceback na saída | 31 (20 %) | 58 (26 %) |
| reprovações | 37 | 76 |
| reprovações com bloco quebrado na execução | 15 | 38 |
| reprovações cujo texto cita "não foi possível verificar / não definido / escopo" | 6 | 21 |

Exemplo (`dados/coleta-r3/peewee-0003/orchestration/rep01`): 11 revisões, todas reprovando; a primeira apontou um bug real, da segunda à décima primeira o motivo é "o bloco de código de reprodução falha porque `EnumField` não está definido no escopo"; o developer reescreveu `playhouse/fields.py` 8 vezes, o oráculo aprovou o estado final, cortado em 120 turnos. Em tomlkit-0005 (0/3) o revisor reprova três vezes com o mesmo diagnóstico (`PySequence_Check` ainda devolve 1) e o developer não chega lá: ali a reprovação é verdadeira e o teto não mudaria nada.

**Falsos positivos continuam.** 7 runs encerraram com o revisor aprovando código que o oráculo reprovou (rodada 2: 4). A regra do revisor coerente só pega a contradição explícita (aprovar listando critério faltando); quando o revisor aprova sem listar nada, nada a segura.

## 3. Leitura

- A rodada 2 continua sendo a melhor configuração do orquestrado (23/39, US$ 4,72). A rodada 3 não a supera em nenhuma faixa exceto grande (5/9 × 4/9, uma tarefa).
- Tirar o teto de reprovações **sem** consertar o revisor transfere o custo dos falsos negativos para o orçamento do developer. Com o teto em 2, a rodada 2 "salvava" runs ao encerrar; sem teto, o developer desfaz código correto tentando agradar o revisor (peewee-0003: 8 reescritas).
- O revisor que executa (decisão 29) é útil quando o bloco roda e enganoso quando não roda: 26 % dos blocos quebram por execução isolada, não por erro do código.
- O nó fraco do protótipo é o revisor, nos dois sentidos: reprova código certo quando não consegue executar o exemplo, e aprova código errado sem listar critério. Nenhuma das duas mudanças da rodada 3 ataca isso.

## 4. O que fica para o texto e o que viria depois

Para o texto: as três rodadas lado a lado como evolução do protótipo, com a rodada 2 como configuração final do orquestrado; a rodada 3 como experimento negativo que localiza o gargalo no revisor. Decisão 34 (pendente): execução **acumulada** dos blocos de reprodução (bloco *i* roda com os blocos 1..*i*−1 antes, num só namespace) e "não verificável" tratado como "não verificado", não como reprovação; são correções do harness e da regra estrutural, sem prompt novo. Só com isso faria sentido reavaliar o teto.

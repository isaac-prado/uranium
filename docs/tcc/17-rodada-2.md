# 17. Rodada 2: resultados (14/10/2026)

Rodada aprovada pelo autor em 14/10/2026 ("Vamos seguir a proposta então, iniciar com a rodada 2 no qwen"). Braço orquestrado com refinador v2 (decisão 28), revisor que executa e nota de ciclo (decisão 29), nas 13 tarefas, três repetições, mesmas sementes da coleta principal; três tarefas reconstruídas com `visible_deselect` (decisão 27) nos dois braços. Single-agent rodado de novo só nas três reconstruídas; nas outras dez, o single-agent de comparação é o da coleta principal de 12-13/10 (mesmo código, mesmos tetos, mesma semente por repetição). Manifesto v10; `shared_limits.pytest_rootdir` presente nos 34 runs gravados depois da correção da decisão 30 e ausente nos 14 anteriores (10 tarefas sem deselect, onde a chave não muda nada).

| | runs | resolvidos | US$ (`cost.cost_usd`) | tokens | chamadas (= `byok_calls`) | perdidos |
|---|---|---|---|---|---|---|
| orquestrado, rodada 2 | 39 | 23 | 4,72 | 33,4 M | 2 532 | 0 |
| single-agent, rodada 2 (3 tarefas) | 9 | 2 | 3,81 | 31,8 M | 737 | 0 |
| orquestrado, coleta principal (referência) | 39 | 17 | 5,21 | 40,6 M | | 0 |

Dados: `dados/coleta-r2/` (runs, `collection.json` com as 48 células, logs), `dados/coleta-r2-descartados/` (células anteriores à correção do rootdir, README), raiz pareada `runs/coleta-r2-analise/` (orquestrado da rodada 2 + single-agent da rodada 2 nas três reconstruídas e da coleta principal nas outras dez). Análises: `dados/coleta-r2/analise-sete-metricas.{md,json}`, `apendice-metricas.md`, `analise-operacional.md` (esta só pareia as três tarefas rodadas nos dois braços).

## 1. Resolução por tarefa e repetição

`result.json: resolved` (oráculo). SA = single-agent pareado; OR-2 = orquestrado da rodada 2; OR-1 = orquestrado da coleta principal.

| tarefa | faixa | SA r1 r2 r3 | OR-2 r1 r2 r3 | OR-1 r1 r2 r3 |
|---|---|---|---|---|
| attrs-0001 | média | ✓ ✓ ✓ | ✓ ✓ ✗ | ✓ ✗ ✓ |
| peewee-0001 | média | ✓ ✓ ✓ | ✓ ✓ ✓ | ✗ ✓ ✓ |
| peewee-0002 | média | ✓ ✓ ✗ | ✗ ✗ ✗ | ✗ ✗ ✗ |
| peewee-0003 | pequena | ✓ ✓ ✓ | ✓ ✓ ✓ | ✓ ✓ ✓ |
| pygments-0001 * | pequena | ✗ ✓ ✓ | ✗ ✓ ✗ | ✗ ✗ ✗ |
| sqlite-utils-0001 | pequena | ✗ ✓ ✗ | ✗ ✓ ✗ | ✗ ✗ ✗ |
| sqlite-utils-0002 * | pequena | ✗ ✗ ✗ | ✓ ✓ ✓ | ✓ ✓ ✓ |
| sqlite-utils-0003 | média | ✓ ✓ ✗ | ✓ ✗ ✗ | ✗ ✗ ✗ |
| tomlkit-0001 | pequena | ✓ ✓ ✓ | ✓ ✓ ✓ | ✓ ✗ ✓ |
| tomlkit-0002 | grande | ✗ ✓ ✗ | ✓ ✗ ✗ | ✗ ✓ ✗ |
| tomlkit-0003 | grande | ✓ ✓ ✓ | ✓ ✓ ✓ | ✓ ✓ ✓ |
| tomlkit-0004 * | grande | ✗ ✗ ✗ | ✗ ✗ ✗ | ✗ ✗ ✗ |
| tomlkit-0005 | pequena | ✗ ✗ ✗ | ✓ ✗ ✓ | ✓ ✗ ✗ |
| **runs resolvidos** | | **23/39** | **23/39** | **17/39** |
| por repetição | | 7, 10, 6 | 9, 8, 6 | 6, 5, 6 |
| grande / média / pequena | | 4/9, 10/12, 9/18 | 4/9, 6/12, 13/18 | 4/9, 4/12, 9/18 |

\* tarefa reconstruída (single-agent da rodada 2).

## 2. As sete métricas (`dados/coleta-r2/analise-sete-metricas.md`)

Mediana das repetições por tarefa; diferença sempre orquestrado − single-agent. Ao lado, a coleta principal (`dados/coleta/analise-sete-metricas.md`).

| # | métrica | rodada 2: SA | OR | n | p | coleta principal: SA | OR | p |
|---|---|---|---|---|---|---|---|---|
| 1 | tarefas resolvidas (mediana) | 8/13 | 7/13 | 6 pares não empatados | 0,69 | 8/13 | 6/13 | 0,18 |
| 2 | tokens (mediana, resolvidas por ambos) | 121 675 | 219 388 | 5 | 0,63 | 121 675 | 278 656 | 0,81 |
| 3 | segundos (mediana, resolvidas por ambos) | 113 | 245 | 5 | 0,125 | 113 | 127 | 0,19 |
| 4 | consistência (3/3 entre as resolvidas ao menos uma vez) | 5/10 | 5/11 | | | 6/11 | 3/8 | |
| 5 | Δ complexidade (mediana) | 0,014 | 0,028 | 8 | 0,74 | 0,025 | 0,024 | 0,97 |
| 6 | conclusão sem corte | 29/39 | 28/39 | | | 26/39 | 23/39 | |
| 7 | violações (crít.; bloq.; negações de escrita) | 0; 0; 5 | 0; 0; 3 | | | 0; 0; 11 | 0; 0; 39 | |

Por faixa (apêndice, seção B, sinal sobre a fração de repetições resolvidas): grande 0 +OR, 0 −SA, 3 empates; média 0 / 3 / 1 (p = 0,25); pequena 2 / 1 / 3 (p = 1); todas 2 / 4 / 7 (p = 0,69). Na coleta principal era 2 / 7 / 4 (p = 0,18).

Custo e tamanho (apêndice, seção C, Wilcoxon sobre as 13 tarefas): tokens mediana da diferença −110 164 (p = 0,057); linhas do patch −7 (p = 0,028); US$ −0,005 (p = 0,31); turnos 0 (p = 0,84).

## 3. O que mudou da coleta principal para a rodada 2

- **Runs resolvidos pelo orquestrado: 17 → 23**, empatando com o single-agent em runs (23 × 23). Por tarefa (mediana) ainda 7 × 8, e o teste do sinal não distingue (p = 0,69). H1 continua não sustentada; o quadro deixou de ser "pior em tudo".
- **Faixa média: 4/12 → 6/12**, single-agent 10/12. É onde a diferença restante está (3 tarefas a favor do single-agent, 1 empate). peewee-0002 (0/3 no orquestrado nas duas rodadas, 2/3 no single-agent) e sqlite-utils-0003 (1/3 × 2/3) concentram.
- **Faixa pequena: 9/18 → 13/18**, single-agent 9/18. sqlite-utils-0002 3/3 no orquestrado e 0/3 no single-agent da rodada 2 (seção 4); tomlkit-0005 2/3 × 0/3.
- **Faixa grande: empate 4/9 × 4/9** nas duas rodadas. tomlkit-0003 3/3 nos dois; tomlkit-0002 1/3 nos dois; tomlkit-0004 0/6 em todas as rodadas e variantes.
- **Negações de escrita: 39 → 3.** A intent v1 mandava escrever testes em 7 de 39 runs ([12-coleta-resultados.md](12-coleta-resultados.md)); a v2 traz a restrição literal da área protegida.
- **Cortes em 120 turnos: 16 → 11** no orquestrado (seção 6: 23/39 → 28/39 sem corte). Nenhum corte por tokens ou parede.
- **Custo: US$ 5,21 → 4,72** (39 runs), com mais runs resolvidos; tokens 40,6 M → 33,4 M. O single-agent pareado soma US$ 8,44 e 72,4 M tokens nos 39 runs.
- **Tempo até a solução** (métrica 3, 5 tarefas resolvidas por ambos) piorou para o orquestrado: 127 s → 245 s de mediana, p = 0,125. O revisor que executa custa parede (executa os blocos de reprodução a cada suíte verde).

## 4. Revisor que executa, nota de ciclo e as três tarefas reconstruídas

**Revisor** (`validation`, apêndice seção D; contagem direta nos eventos): 59 revisões, todas com execução dos blocos de reprodução (155 blocos, nenhum com erro de execução registrado no evento); 22 aprovadas, 37 reprovadas. Runs resolvidos com ao menos uma reprovação antes: 11 (na coleta principal, 5); runs não resolvidos com reprovação: 9. A reprovação intermediária não é necessariamente falsa (o estado reprovado pode ter sido incompleto de fato); o apêndice chama de "falso negativo" por definição operacional e isso fica declarado.

**Nota de ciclo**: 31 cortes por teto de ciclo em 39 runs, 31 notas escritas (uma por corte). Ciclos por run: 1 ciclo em 14 runs, 2 em 11, 3 em 12, 4 em 2; o máximo caiu de 33 ciclos (coleta principal) para 4.

**pygments-0001**: orquestrado 1/3 (rep02), single-agent 2/3. Com o golden fora da suíte visível, a suíte fica verde; o oráculo (golden inteiro do upstream, [16-ablacao-e-v2.md](16-ablacao-e-v2.md) §3.1) reprovou 2 dos 3 runs orquestrados e 1 dos 3 do single-agent. Na coleta principal era 0/3 × 3/3; o single-agent da rodada 2 caiu de 3/3 para 2/3 com a mesma semente.

**sqlite-utils-0002**: orquestrado 3/3 (revisão aprovada na primeira, 15 a 29 turnos); single-agent 0/3. Os três runs do single-agent falham no oráculo exatamente as 6 versões novas dos testes deselecionados (`f2p 5/11`, `failing_node_ids` ⊆ `visible_deselect`); dois pararam com a suíte visível verde em 28 e 45 turnos, o terceiro cortou por tokens. Na coleta principal o single-agent resolvia 3/3 com a suíte vermelha nos 6 testes antigos (cortado por tokens em dois). Com os testes contraditórios fora da suíte, o critério "suíte verde" ficou alcançável cedo demais para o single-agent, enquanto o orquestrado, guiado pela intent v2 com as saídas esperadas e pelo revisor que executa, fechou nas três. É um resultado sobre a reconstrução tanto quanto sobre os braços: entra em Discussão com essa ressalva.

**tomlkit-0004**: 0/3 nos dois braços, cortes em 120 nos seis runs; igual à coleta principal.

## 5. Limites

- O single-agent pareado é híbrido: 10 tarefas da coleta principal, 3 da rodada 2. Mesmo código e sementes, mas datas diferentes (12-13/10 e 14/10) e provedor sem garantia de determinismo.
- Os 14 runs orquestrados gravados antes da correção do rootdir (10 tarefas sem deselect) diferem dos demais só na forma do node id na saída do pytest (decisão 30, (a)/(b) pendente do autor).
- Uma rodada por configuração; nenhum p abaixo de 0,05 nas métricas primárias.
- O custo de tempo do revisor que executa (métrica 3) é efeito do desenho da rodada 2 e precisa ser reportado como tal.

# Cronograma e orçamento

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 17 de setembro de 2026
Fase 4 do `PROMPT_AUDITORIA.md`. Planejado de trás para frente a partir da defesa em **23/11/2026**. Faltam 67 dias, nove semanas e meia. Data intermediária informada pelo autor: **18/09/2026**, entrega do resumo científico à orientadora.

**Premissa a confirmar com a orientadora:** o texto completo precisa estar com ela ao menos duas semanas antes da defesa, em **09/11**. Se o prazo formal da UNIFEI for outro, todo o plano desloca junto.

## 1. Onde o projeto está hoje

| Item | Situação | Evidência |
|---|---|---|
| Tarefas prontas | 2 de 12, cada uma com enunciado, oráculo e duas soluções de referência | `tasks/sqlite-utils-0001/`, `tasks/tomlkit-0001/` (`reference/upstream.patch` e `reference/alternative.patch`) |
| Candidatos minerados | 90 examinados, 54 aceitos: peewee 22, tomlkit 24, sqlite-utils 8 | `mined-v1/*.json`, campo `aceito` (contagem minha) |
| Distribuição dos aceitos por faixa atual | baixa 35, média 18, alta 1 | idem, campo `faixa`; regra em [scripts/mine_tasks.py:83-90](../../scripts/mine_tasks.py#L83-L90) |
| Tamanho do patch de referência entre os aceitos | 3 a 232 linhas, mediana 13,5; tercis em 10 e 23 linhas; 49 de 54 alteram um único arquivo | idem, campos `linhas_fonte`, `arquivos_fonte` |
| Tempo de parede por execução no piloto | mediana 0,8 min (agente único) e 1,4 min (orquestração); percentil 90 de 5,3 min; 42 execuções somaram 1,1 h | `elapsed_ms` máximo em cada `events.jsonl` dos 42 runs |
| Custo por execução no piloto | média US$ 0,034; percentil 90 US$ 0,060 | [02-resumo-cientifico.md](02-resumo-cientifico.md), seção 7 |
| Execuções perdidas por erro de provedor ou de formato | 3 de 42 (7%) | `summary.json` com `stop_reason` iniciado em `error:` |
| Saldo | US$ 8,64; teto acordado em torno de US$ 50 | informado pelo autor |

**Consequência para a estratificação (decisão 4 do contexto).** A faixa "alta" da regra atual (4 ou mais arquivos) tem um único candidato; não há como estratificar por ela. Proposta: estratificar pelos **tercis do tamanho do patch de referência entre os aceitos**, 4 tarefas em cada (até 10 linhas; 11 a 23; 24 ou mais), com os três repositórios representados. Os dois tercis inferiores garantem as 6 tarefas resolvíveis por ambos que o Wilcoxon exige ([03-metricas.md](03-metricas.md), seção 2). A regra de faixa e o seletor que alterna faixas ([scripts/emit_task.py:161-168](../../scripts/emit_task.py#L161-L168)) precisam ser ajustados a isso; é o item 5 da Fase 5.

## 2. Plano de trás para frente

Semanas começam na segunda-feira. "Autor" é trabalho manual seu; "código" é engenharia que pode ser feita por agente sob sua revisão; "pago" consome crédito.

| Semana | Datas | Etapa | Quem | Custo | Portão de saída |
|---|---|---|---|---|---|
| — | **23/11** | **Defesa** | autor | — | — |
| 9 | 16/11 – 22/11 | Ensaio da apresentação; ajustes pedidos pela orientadora | autor | zero | — |
| — | **09/11** | **Texto completo à orientadora** (premissa) | autor | — | — |
| 7–8 | 26/10 – 08/11 | Escrita de resultados, discussão e conclusão sobre as tabelas finais | autor | zero | texto entregue |
| 6 | 19/10 – 25/10 | **Coleta definitiva**: 72 execuções, 2 h pela média e 6,5 h pelo percentil 90, sequenciais; reexecuções por erro de provedor; análise pareada emitindo as sete métricas | código + pago | US$ 2,4 a 4,3; reservar 6 | 72 `result.json` admitidos pelos três portões de dado |
| 5 | 12/10 – 18/10 | Validação das 12 tarefas nos quatro portões ([scripts/validate_task.py:90-125](../../scripts/validate_task.py#L90-L125)); teste de fumaça pago (2 tarefas × 2 braços × 1 repetição); ablação do refinador de enunciado (5 pares) | código + pago | fumaça US$ 0,14 a 0,24; ablação US$ 0,30 a 0,60 | 12 tarefas VALIDADAS; fumaça sem defeito de instrumentação |
| 2–4 | 21/09 – 11/10 | **Dez enunciados restantes e segunda solução de referência de cada um** | **autor** | zero | 12 diretórios em `tasks/` completos |
| 2–4 | 21/09 – 11/10 | Em paralelo: Fase 5 itens 1, 2, 5, 6 e 8 (testes de paridade literal, `CLAUDE.md`, estratificação por tercis, reexecução com semente, script de análise) | código | zero | portões G1 a G7 abaixo |
| 1 | **18/09** | **Resumo científico à orientadora** | autor | zero | reunião |
| 1 | 19/09 – 20/09 | Incorporar o retorno da orientadora ao plano; escolher as 10 tarefas pelos tercis | autor | zero | lista das 12 tarefas fechada |

### Caminho crítico

Escrever as dez tarefas é o gargalo: ninguém além de você pode escrever um enunciado fiel ao problema original e uma segunda solução que resolva sem copiar a do upstream. Não há medição de quanto tempo cada tarefa toma. Premissa: **um dia e meio útil por tarefa**, 15 dias úteis para 10. Calibre na primeira semana: se as duas primeiras levarem mais de três dias, avise, porque cada semana de atraso aqui come a folga da semana 6 e depois o tempo de escrita do texto.

Tudo o que é código pode andar em paralelo com a escrita das tarefas e deve estar pronto antes da semana 5. Se estiver, a semana 5 vira validação e a semana 6 vira coleta sem espera.

## 3. Portões offline de custo zero

Nenhuma execução paga antes de todos passarem. Ordem de dependência.

| # | Portão | Como se verifica | Item da Fase 5 |
|---|---|---|---|
| G1 | Suíte do repositório verde | `pytest` sem falha | — |
| G2 | Paridade literal para todas as folgas F1 a F13 do inventário | testes novos em `tests/test_arm_parity.py` que falham se qualquer constante divergir | 1 |
| G3 | Manifesto registra os parâmetros que hoje ficam fora (folgas F6 e F9) | teste que compara manifesto com configuração efetiva | 1 |
| G4 | Tetos congelados e registrados (risco R6): decidir de uma vez os valores de [src/budget.py:25-45](../../src/budget.py#L25-L45) e não tocar até o fim | valor escrito no `CLAUDE.md` e no manifesto | 2 |
| G5 | Reexecução por erro de provedor preserva a semente e substitui o run perdido | teste com erro simulado | 6 |
| G6 | As 12 tarefas passam nos quatro portões de validação | `validate_task.py` VALIDADA em cada uma | 7 |
| G7 | Script de análise roda sobre os 4 `result.json` existentes e emite as sete métricas, o teste de sinal e o Wilcoxon | saída sobre dados de 11/09, mesmo sem significado | 8 |

Só depois: teste de fumaça pago, e só se a fumaça não revelar defeito novo, a ablação e a coleta.

## 4. Orçamento

| Gasto | Execuções | Estimativa (média a percentil 90) | Reserva |
|---|---|---|---|
| Teste de fumaça | 4 | US$ 0,14 a 0,24 | 0,30 |
| Ablação do refinador | 10 | US$ 0,30 a 0,60 | 0,70 |
| Coleta definitiva | 72 | US$ 2,4 a 4,3 | 6,00 |
| Reexecuções (7% observado) | ~5 | US$ 0,17 a 0,30 | 0,50 |
| **Total** | ~91 | **US$ 3,0 a 5,4** | **7,50** |

O saldo de US$ 8,64 cobre o plano inteiro pelo percentil 90 com reserva. O teto de US$ 50 tem um uso só e deve ser guardado para ele: **refazer a coleta inteira** (mais US$ 6) se um defeito de instrumentação aparecer depois dela, como aconteceu oito vezes nas rodadas piloto. Não gaste com terceira repetição extra nem com segundo modelo antes de ter os 72 resultados analisados.

Dinheiro não é a restrição. Os custos acima assumem os tetos atuais; se G4 fixar tetos maiores, multiplique pela razão.

## 5. Onde há folga e onde não há

**Há folga**

- Orçamento: seis vezes o custo esperado disponível.
- Tempo de máquina: a coleta cabe em uma tarde; a semana 6 tem quatro dias de sobra para reexecuções e repetição parcial.
- Semana 9: é buffer inteiro. Se tudo atrasar uma semana, ela absorve.
- Candidatos: 54 aceitos para 10 vagas. Se uma tarefa não passar na validação, há substituta no mesmo tercil sem minerar de novo (exceto em sqlite-utils, com 8 aceitos).

**Não há folga**

- Escrita das dez tarefas: três semanas, só você, sem medição prévia. É o único ponto em que o plano pode quebrar.
- Escrita do texto final: duas semanas depois dos dados. Não começa antes porque depende das tabelas; o que pode ser adiantado (método, materiais, limitações) já está nos documentos de `docs/tcc/` e deve ser passado para o texto nas semanas 2 a 4.
- 18/09: o retorno da orientadora pode mudar métricas ou desenho. Qualquer mudança de desenho depois da semana 5 obriga a refazer validação e coleta.

**Alavanca se a escrita atrasar:** escrever primeiro os enunciados dos dois tercis inferiores (8 tarefas, patches de até 23 linhas), que são os que garantem a inferência; o tercil superior fica por último. Reduzir para menos de 12 tarefas reabre a decisão 4 e não está proposto aqui.

## 6. O que este cronograma não decide

- A data formal de entrega do texto à UNIFEI e à orientadora (premissa de 09/11).
- Os valores finais dos tetos (G4): decisão sua, registrada antes da fumaça.
- Se a ablação entra no texto como resultado ou como apêndice; recomendo resultado, porque isola a hipótese de mecanismo da seção 6 do resumo.

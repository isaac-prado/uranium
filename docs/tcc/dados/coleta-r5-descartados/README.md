# Falsa partida da rodada 5 (15/10/2026 23:4x a 16/10 00:2x), manifesto v13

Quatro runs concluídos (attrs-0001, peewee-0001, peewee-0002, peewee-0003, repetição 1) e um
interrompido (pygments-0001 rep01) com SIGINT, descartados porque a configuração tinha um defeito
de desenho: a comparação determinística exigia saídas esperadas que o refinador copiou do enunciado
como "esperadas" mas descrevem o comportamento ATUAL (o bug). Na attrs-0001 o developer corrigiu,
a comparação disse "não encontrada" e ele desfez a correção; na peewee-0002 a sub-tarefa 1 nunca
podia ficar "feita". Correção: decisão 39 (filtro das saídas que o código original já produz),
manifesto v14. A rodada 5 foi relançada do zero em `runs/coleta-r5`, mesmas sementes.
Não entram em análise nenhuma.

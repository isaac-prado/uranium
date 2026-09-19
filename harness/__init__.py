"""
Avaliador externo do estudo E1.

Este pacote é deliberadamente independente do pipeline: ele NÃO importa nada
de `src/`. O agente e o avaliador não podem compartilhar código, senão a
corretude reportada no TCC passaria a depender das mesmas suposições que o
agente usou para decidir que terminou.

Consequência prática: leitura de eventos, execução de pytest e utilitários
de git são reimplementados aqui. A duplicação é intencional — é ela que
torna a avaliação uma verificação independente, e não uma repetição.

Entrada: um diretório de run (workspace modificado + telemetria) e uma
especificação de tarefa. Saída: um único result.json por run.
"""

HARNESS_VERSION = "1.0.0"
# Subiu de 1 para 2 quando o result.json ganhou o campo de topo `faixa`
# (E3 item 2): a faixa de dificuldade, antes presa ao task.json e ignorada
# pelo TaskSpec, agora atravessa até o resultado — mudança de forma do
# result.json, não só de conteúdo.
RESULT_SCHEMA_VERSION = 2

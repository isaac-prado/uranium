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
RESULT_SCHEMA_VERSION = 1

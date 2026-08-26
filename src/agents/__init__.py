"""
Agentes especializados do pipeline Uranium (braço orchestration).

Este pacote deliberadamente NÃO reexporta as funções dos nós. Reexportar
`validator` aqui faria `src.agents.validator` resolver para a função em vez
do módulo, quebrando `monkeypatch.setattr` por string, navegação de IDE e
qualquer import do submódulo. Importe do módulo:

    from src.agents.validator import validator
"""

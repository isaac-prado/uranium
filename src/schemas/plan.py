"""
Plano de sub-tarefas do planejador (decisão 33 do autor, 15/10/2026).

O planejador fatia a intent em sub-tarefas que o developer executa uma por
vez, em ciclos curtos. Cada sub-tarefa aponta, por índice, quais critérios
de aceitação e quais blocos de reprodução da intent ela cobre: o texto
desses itens é copiado da intent na hora de montar o prompt, nunca
reescrito pelo planejador.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

STATUS_PENDENTE = "pendente"
STATUS_EM_ANDAMENTO = "em_andamento"
STATUS_FEITA = "feita"
STATUS_ADIADA = "adiada"
STATUS_ABANDONADA = "abandonada"


def _inteiros(valor: Any) -> Any:
    """Aceita índices como int, str numérica ou lista aninhada; descarta o resto."""
    if not isinstance(valor, list):
        return valor
    saida: list[int] = []
    for item in valor:
        if isinstance(item, list):
            item = item[0] if item else None
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            saida.append(item)
        elif isinstance(item, str) and item.strip().lstrip("-").isdigit():
            saida.append(int(item.strip()))
    return saida


class Subtask(BaseModel):
    id: int = Field(description="Número sequencial da sub-tarefa, a partir de 1")
    title: str = Field(description="Título curto")
    objective: str = Field(
        description="O que mudar e onde: arquivos, classes e funções confirmados pela leitura do repositório",
    )
    files: list[str] = Field(default_factory=list, description="Arquivos que esta sub-tarefa deve tocar")
    criteria: list[int] = Field(
        default_factory=list,
        description="Índices (a partir de 1) dos critérios de aceitação da especificação cobertos por esta sub-tarefa",
    )
    reproduction: list[int] = Field(
        default_factory=list,
        description="Índices (a partir de 1) dos blocos de reprodução da especificação que verificam esta sub-tarefa",
    )
    done_when: str = Field(description="Como saber, por execução, que a sub-tarefa está pronta")

    @field_validator("criteria", "reproduction", mode="before")
    @classmethod
    def _indices(cls, valor: Any) -> Any:
        return _inteiros(valor)

    @field_validator("files", mode="before")
    @classmethod
    def _arquivos(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return [valor]
        if isinstance(valor, list):
            return [str(x) for x in valor if isinstance(x, (str, int))]
        return valor


class Plan(BaseModel):
    rationale: str = Field(default="", description="Por que fatiar assim (ou por que não fatiar)")
    # Ao menos uma sub-tarefa: na fumaça de 15/10 o modelo devolveu `Plan()`
    # vazio numa chamada de 12 tokens; vazio é não conformar, e o harness
    # retenta e depois cai no plano de uma sub-tarefa só.
    subtasks: list[Subtask] = Field(min_length=1)

    @field_validator("subtasks", mode="after")
    @classmethod
    def _renumera(cls, subtasks: list[Subtask]) -> list[Subtask]:
        for i, s in enumerate(subtasks, 1):
            s.id = i
        return subtasks


class Replan(Plan):
    """Replanejamento: pode vir vazio (nada mais cabe num plano)."""

    subtasks: list[Subtask] = Field(default_factory=list)


def sanear(plan: Plan, *, n_criterios: int, n_reproducao: int, maximo: int = 6) -> Plan:
    """
    Garante que o plano só aponte para itens que existem na intent e que
    não passe do tamanho máximo. Índices fora do intervalo são descartados;
    o resto do plano fica como o planejador escreveu.
    """
    subtasks = plan.subtasks[:maximo]
    for s in subtasks:
        s.criteria = sorted({i for i in s.criteria if 1 <= i <= n_criterios})
        s.reproduction = sorted({i for i in s.reproduction if 1 <= i <= n_reproducao})
    return type(plan).model_construct(rationale=plan.rationale, subtasks=subtasks)


def estado_inicial(plan: Plan) -> list[dict[str, Any]]:
    """Linha de estado por sub-tarefa, como vai ao WorkflowState."""
    return [{"id": s.id, "status": STATUS_PENDENTE, "ciclos": 0, "adiada_antes": False} for s in plan.subtasks]

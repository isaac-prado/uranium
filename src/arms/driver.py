"""
DeterministicDriver — o "operador" do braço single-agent.

Não é um LLM e não é um humano: é uma política fixa, documentada e
serializada no manifesto do run, para que qualquer pessoa possa auditar
exatamente o que o agente único recebeu de volta a cada turno.

A política, na íntegra:
  1. entrega a especificação inteira no turno 0, uma vez só;
  2. aceita todo patch proposto, sem revisão;
  3. ao fim de um turno em que o agente não pediu ferramenta, roda a suíte;
  4. se falhar, devolve o stderr CRU, truncado — sem sumarizar, sem sugerir,
     sem apontar arquivo. Sumarizar seria injetar inteligência de fora e
     contaminar a comparação com o braço orchestration;
  5. se passar, encerra;
  6. estourou turnos, tempo ou tokens, encerra.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from src.feedback import DIFF_VAZIO, suite_falhou
from src.schemas.test_report import TestReport


class DriverAction(StrEnum):
    """O que o driver decide após um turno do agente."""

    CONTINUAR = "continuar"      # devolve feedback e segue
    ENCERRAR_VERDE = "verde"     # suíte passou
    ENCERRAR_ORCAMENTO = "budget"


@dataclass(frozen=True)
class DriverPolicy:
    """Política do operador. Vai inteira para o manifesto do run."""

    entrega_spec_uma_vez: bool = True
    aceita_todo_patch: bool = True
    sumariza_falhas: bool = False
    stderr_chars: int = 4000
    roda_suite_sem_tool_call: bool = True

    def as_manifest(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DriverDecision:
    """Decisão do driver, com a mensagem que volta ao agente."""

    action: DriverAction
    feedback: str = ""
    report: TestReport | None = None


class DeterministicDriver:
    """Operador de política fixa. Sem LLM, sem humano, sem estado oculto."""

    def __init__(self, policy: DriverPolicy | None = None) -> None:
        self.policy = policy or DriverPolicy()
        self.spec_entregue = False

    def mensagem_inicial(self, especificacao: str) -> str:
        """Entrega a especificação inteira, uma única vez."""
        if self.spec_entregue and self.policy.entrega_spec_uma_vez:
            raise RuntimeError("a especificação já foi entregue; a política permite uma vez só")
        self.spec_entregue = True
        return especificacao

    def apos_turno(self, report: TestReport, *, houve_mudanca: bool = True) -> DriverDecision:
        """
        Decide o que fazer com o resultado da suíte.

        Devolve o stderr cru. Qualquer processamento aqui — apontar o arquivo
        provável, resumir a causa, sugerir correção — seria trabalho de
        engenharia feito pelo harness e creditado ao agente.

        `houve_mudanca` existe porque a suíte visível já está verde no
        commit-base: sem essa checagem, "não fazer nada" satisfaz o critério
        de parada. No piloto foi exatamente o que aconteceu.
        """
        if report.green and not houve_mudanca:
            return DriverDecision(
                DriverAction.CONTINUAR,
                feedback=DIFF_VAZIO,
                report=report,
            )

        if report.green:
            return DriverDecision(DriverAction.ENCERRAR_VERDE, report=report)

        saida = report.stdout_tail
        if len(saida) > self.policy.stderr_chars:
            saida = saida[-self.policy.stderr_chars:]

        if self.policy.sumariza_falhas:  # desligado por padrão; existe para ablação
            saida = f"{len(report.failing_node_ids)} teste(s) falhando."

        return DriverDecision(
            DriverAction.CONTINUAR,
            feedback=suite_falhou(saida),
            report=report,
        )

    def encerrar_por_orcamento(self, motivo: str) -> DriverDecision:
        return DriverDecision(DriverAction.ENCERRAR_ORCAMENTO, feedback=motivo)

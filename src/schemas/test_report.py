"""Schema do resultado de uma execução real da suíte de testes."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TestReport(BaseModel):
    """
    Resultado de uma execução de pytest dentro do workspace.

    Diferente de ValidationResult, que é julgamento de LLM sobre texto,
    este objeto vem de execução real e é a única fonte de `is_valid`
    no nó Validator.
    """

    # impede o pytest de tentar coletar esta classe como suíte de testes
    __test__ = False

    exit_code: int = Field(description="Código de saída do pytest (0 = tudo passou)")
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    errors: int = Field(default=0)
    skipped: int = Field(default=0)
    xfailed: int = Field(default=0)
    xpassed: int = Field(default=0)
    duration_s: float = Field(default=0.0)
    failing_node_ids: list[str] = Field(
        default_factory=list,
        description="Node ids exatos dos testes que falharam, reutilizáveis em nova execução",
    )
    stdout_tail: str = Field(default="", description="Saída truncada (início + fim)")
    timed_out: bool = Field(default=False)
    command: str = Field(default="", description="Comando executado, para auditoria")

    @property
    def green(self) -> bool:
        """Suíte totalmente verde — a única condição que autoriza is_valid=True."""
        return self.exit_code == 0

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.errors + self.skipped

    def summary(self) -> str:
        """Resumo de uma linha para logs e prompts."""
        if self.timed_out:
            return f"TIMEOUT após {self.duration_s:.1f}s"
        return (
            f"exit={self.exit_code} passed={self.passed} failed={self.failed} "
            f"errors={self.errors} skipped={self.skipped} em {self.duration_s:.2f}s"
        )

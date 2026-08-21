"""
Garante que a única telemetria é o JSONL local.

O `langsmith` continua instalado como dependência transitiva do
langchain-core, então nada impede que um import ou uma variável de ambiente
reintroduzam envio de spans pela rede durante uma coleta. Estes testes
falham se isso acontecer.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = ["src", "scripts"]


class TestSemTracingRemoto:
    def test_nenhum_modulo_importa_langsmith(self):
        achados = subprocess.run(
            ["grep", "-rn", "-E", r"^\s*(from|import)\s+langsmith|@\w*traceable",
             "--include=*.py", *FONTES],
            cwd=RAIZ, capture_output=True, text=True,
        ).stdout.strip()
        assert not achados, f"tracing remoto reintroduzido:\n{achados}"

    def test_langsmith_nao_e_dependencia_declarada(self):
        pyproject = tomllib.loads((RAIZ / "pyproject.toml").read_text())
        deps = pyproject["project"]["dependencies"]
        assert not any("langsmith" in d for d in deps), deps

    def test_importar_config_desliga_o_tracing(self):
        """Mesmo com a variável ligada no ambiente, o import tem de desligar."""
        script = (
            "import os; os.environ['LANGSMITH_TRACING']='true'; "
            "import src.config; "
            "print(os.environ['LANGSMITH_TRACING'], os.environ['LANGCHAIN_TRACING_V2'])"
        )
        saida = subprocess.run(
            [sys.executable, "-c", script],
            cwd=RAIZ, capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(RAIZ)},
        )
        assert saida.returncode == 0, saida.stderr
        assert saida.stdout.split() == ["false", "false"]

    def test_env_de_exemplo_nao_pede_chave_de_tracing(self):
        exemplo = (RAIZ / ".env.example").read_text()
        assert "LANGSMITH" not in exemplo
        assert "LANGCHAIN" not in exemplo


class TestTelemetriaEUnica:
    def test_o_emissor_jsonl_existe_e_e_o_unico(self):
        from src.telemetry import TelemetryWriter

        assert hasattr(TelemetryWriter, "emit")
        assert (RAIZ / "harness" / "schema" / "event.schema.json").exists()

"""Exporta artefatos e testes do pipeline para o filesystem."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tracing import pipeline_traceable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "output"

_EXT_BY_TYPE = {
    "model": ".java",
    "service": ".java",
    "endpoint": ".java",
    "migration": ".sql",
    "component": ".tsx",
    "other": ".txt",
}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\-./]+", "_", name.strip())
    return slug.strip("_") or "artifact"


def _safe_relative_path(raw_path: str, fallback: str) -> str:
    """Normaliza caminho relativo e bloqueia path traversal."""
    candidate = Path(raw_path.strip() or fallback)
    parts = [p for p in candidate.parts if p not in (".", "..", "")]
    if not parts:
        return fallback
    return str(Path(*parts))


def _artifact_filename(artifact: dict[str, Any], index: int) -> str:
    if artifact.get("file_path"):
        return _safe_relative_path(
            artifact["file_path"],
            f"artifacts/{_slugify(artifact.get('name', f'artifact_{index}'))}",
        )
    name = _slugify(artifact.get("name", f"artifact_{index}"))
    ext = _EXT_BY_TYPE.get(artifact.get("artifact_type", "other"), ".txt")
    if not name.endswith(ext):
        name = f"{name}{ext}"
    return f"artifacts/{name}"


def _write_file(base_dir: Path, relative_path: str, content: str) -> Path:
    target = base_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


@pipeline_traceable("export_pipeline_result")
def export_pipeline_result(
    result: dict[str, Any],
    *,
    output_root: Path | None = None,
    request: str = "",
    keep_history: bool = True,
) -> dict[str, Any]:
    """
    Grava artefatos, testes e manifest em output/.

    Estrutura:
      output/latest/          ← sempre a execução mais recente
      output/runs/<timestamp>/ ← histórico (opcional)
    """
    root = output_root or DEFAULT_OUTPUT_ROOT
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    run_dir = root / "runs" / timestamp
    latest_dir = root / "latest"

    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.mkdir(parents=True, exist_ok=True)

    if keep_history:
        run_dir.mkdir(parents=True, exist_ok=True)
        active_dirs = [latest_dir, run_dir]
    else:
        active_dirs = [latest_dir]

    written_files: list[str] = []

    for artifact in result.get("artifacts") or []:
        content = artifact.get("content", "")
        if not content:
            continue
        rel = _artifact_filename(artifact, len(written_files))
        for base in active_dirs:
            _write_file(base, rel, content)
        written_files.append(rel)

    test_plan = result.get("test_plan") or {}

    for test_file in test_plan.get("test_files") or []:
        path = test_file.get("path", "")
        content = test_file.get("content", "")
        if not content:
            continue
        rel = _safe_relative_path(path, f"tests/{_slugify(path or 'test')}.py")
        for base in active_dirs:
            _write_file(base, rel, content)
        written_files.append(rel)

    for section, folder in (("unit_tests", "tests/unit"), ("integration_tests", "tests/integration")):
        for case in test_plan.get(section) or []:
            code = case.get("test_code", "")
            if not code:
                continue
            name = _slugify(case.get("name", "test"))
            rel = f"{folder}/{name}.py"
            for base in active_dirs:
                _write_file(base, rel, code)
            written_files.append(rel)

    manifest = {
        "exported_at": timestamp,
        "request": request,
        "intent_goal": (result.get("intent") or {}).get("goal"),
        "is_ready": result.get("is_ready"),
        "is_valid": result.get("is_valid"),
        "validation_issues": (result.get("validation_result") or {}).get("issues", []),
        "files": written_files,
        "artifacts_count": len(result.get("artifacts") or []),
    }

    for base in active_dirs:
        _write_file(base, "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        _write_file(
            base,
            "pipeline_state.json",
            json.dumps(result, ensure_ascii=False, indent=2),
        )

    def _display_path(path: Path) -> str:
        try:
            return str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(path)

    return {
        "latest_dir": _display_path(latest_dir),
        "run_dir": _display_path(run_dir) if keep_history else None,
        "files": written_files,
        "manifest": manifest,
    }


def print_export_summary(export_info: dict[str, Any]) -> None:
    """Imprime resumo dos arquivos exportados."""
    print("\n--- Exported ---")
    print(f"  Diretório: {export_info['latest_dir']}/")
    for path in export_info["files"]:
        print(f"  - {path}")
    print(f"\n  Abra no editor: output/latest/")
    print(f"  Resumo: output/latest/manifest.json\n")

"""Testes de exportação de artefatos."""

import json
from pathlib import Path

from src.export import export_pipeline_result


def test_export_writes_artifacts_and_manifest(tmp_path):
    result = {
        "raw_request": "CRUD Cliente",
        "intent": {"goal": "Implementar CRUD", "is_ready": True},
        "is_ready": True,
        "is_valid": False,
        "validation_result": {"issues": ["falta controller"]},
        "artifacts": [
            {
                "name": "Cliente",
                "artifact_type": "model",
                "description": "Entidade",
                "content": "public class Cliente {}",
                "file_path": "src/main/java/Cliente.java",
            },
        ],
        "test_plan": {
            "summary": "Testes",
            "unit_tests": [
                {
                    "name": "test_create",
                    "description": "criação",
                    "test_code": "def test_create(): pass",
                },
            ],
            "integration_tests": [],
            "test_files": [],
        },
    }

    info = export_pipeline_result(
        result,
        output_root=tmp_path,
        request="CRUD Cliente",
        keep_history=True,
    )

    latest = tmp_path / "latest"
    assert (latest / "manifest.json").exists()
    assert (latest / "artifacts" / "Cliente.java").exists() or (
        latest / "src" / "main" / "java" / "Cliente.java"
    ).exists()
    assert (latest / "tests" / "unit" / "test_create.py").exists()

    manifest = json.loads((latest / "manifest.json").read_text())
    assert manifest["intent_goal"] == "Implementar CRUD"
    assert len(manifest["files"]) >= 2
    assert info["latest_dir"]

#!/usr/bin/env python3
"""
Cria os espelhos bare locais dos repositórios-semente.

Este é o único passo do experimento que toca a rede. Depois dele, toda
materialização de workspace é offline.

    uv run python scripts/setup_mirror.py tomlkit
    uv run python scripts/setup_mirror.py tomlkit --update
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.seeds import SEEDS, get_seed, mirror_root

SUBMODULE_UPSTREAMS = {
    "toml-test.git": "https://github.com/BurntSushi/toml-test.git",
}


def _run(*args: str) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"falhou: {' '.join(args)}\n{proc.stderr.strip()}")


def _mirror(url: str, dest: Path, *, update: bool) -> str:
    if dest.exists():
        if not update:
            return f"  já existe  {dest.name}"
        _run("git", "--git-dir", str(dest), "remote", "update", "--prune")
        return f"  atualizado {dest.name}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run("git", "clone", "--quiet", "--mirror", url, str(dest))
    return f"  criado     {dest.name}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Espelha repositórios-semente localmente")
    parser.add_argument("seed_id", nargs="?", default="tomlkit", choices=sorted(SEEDS))
    parser.add_argument("--update", action="store_true", help="Atualiza espelhos existentes")
    args = parser.parse_args()

    seed = get_seed(args.seed_id)
    root = mirror_root()
    print(f"Espelhos em {root}")
    print(_mirror(seed.upstream_url, seed.mirror_path, update=args.update))

    for _, mirror_name in seed.submodules:
        url = SUBMODULE_UPSTREAMS.get(mirror_name)
        if not url:
            raise SystemExit(f"URL upstream desconhecida para submódulo {mirror_name}")
        print(_mirror(url, root / mirror_name, update=args.update))

    print(f"\nPronto. Materialize com Workspace.materialize(...) — sem rede a partir daqui.")


if __name__ == "__main__":
    main()

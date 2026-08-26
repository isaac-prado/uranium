#!/usr/bin/env python3
"""
Prepara um repositório-semente: espelho bare local + ambiente de teste.

Este é o único passo do experimento que toca a rede. Depois dele, toda
materialização de workspace e toda execução de suíte é offline.

    uv run python scripts/setup_mirror.py tomlkit
    uv run python scripts/setup_mirror.py peewee --check
    uv run python scripts/setup_mirror.py --all
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.seeds import SEED_REPOS, SeedRepoSpec, get_seed_repo, mirror_root

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


def _venv(seed_repo: SeedRepoSpec, *, update: bool) -> str:
    """
    Cria o ambiente de teste do repo e instala as dependências pinadas.

    Um venv por repo-semente, nunca o do projeto: a suíte do upstream não
    pode enxergar langchain, pydantic e o resto das nossas dependências.
    """
    if not seed_repo.test_requirements:
        return "  sem dependências de teste declaradas"

    destino = seed_repo.venv_path
    if destino.exists() and not update:
        return f"  já existe  venvs/{seed_repo.seed_repo_id}"
    if destino.exists():
        shutil.rmtree(destino)

    gerenciador = shutil.which("uv")
    destino.parent.mkdir(parents=True, exist_ok=True)
    if gerenciador:
        _run(gerenciador, "venv", "--quiet", str(destino))
        _run(gerenciador, "pip", "install", "--quiet",
             "--python", str(destino / "bin" / "python"), *seed_repo.test_requirements)
    else:
        _run(sys.executable, "-m", "venv", str(destino))
        _run(str(destino / "bin" / "python"), "-m", "pip", "install", "--quiet",
             *seed_repo.test_requirements)
    return f"  criado     venvs/{seed_repo.seed_repo_id}  ({len(seed_repo.test_requirements)} pacotes)"


def _check(seed_repo: SeedRepoSpec) -> str:
    """
    Materializa o repo no HEAD e roda a suíte inteira.

    Um repo-semente só serve se a suíte estiver verde no ponto de partida:
    sem isso não dá para atribuir uma falha ao agente.
    """
    with tempfile.TemporaryDirectory(prefix=f"uranium-check-{seed_repo.seed_repo_id}-") as tmp:
        alvo = Path(tmp) / seed_repo.seed_repo_id
        _run("git", "clone", "--quiet", "--shared", str(seed_repo.mirror_path), str(alvo))

        if seed_repo.submodules:
            _run("git", "-C", str(alvo), "submodule", "init", "--quiet")
            for sub_path, mirror_name in seed_repo.submodules:
                _run("git", "-C", str(alvo), "config",
                     f"submodule.{sub_path}.url", str(mirror_root() / mirror_name))
            _run("git", "-C", str(alvo), "-c", "protocol.file.allow=always",
                 "submodule", "update", "--quiet")

        comeco = time.perf_counter()
        proc = subprocess.run(
            [seed_repo.python_bin, "-m", "pytest",
             *seed_repo.test_command, *seed_repo.suite_targets],
            cwd=alvo, capture_output=True, text=True, timeout=1800,
        )
        decorrido = time.perf_counter() - comeco

    resumo = (proc.stdout.strip().splitlines() or ["(sem saída)"])[-1]
    marca = "VERDE" if proc.returncode == 0 else f"VERMELHA (exit {proc.returncode})"
    detalhe = "" if proc.returncode == 0 else "\n" + proc.stdout[-1500:]
    return f"  suíte {marca} em {decorrido:.1f}s — {resumo}{detalhe}"


def preparar(seed_repo: SeedRepoSpec, *, update: bool, check: bool) -> None:
    print(f"\n{seed_repo.seed_repo_id}")
    print(_mirror(seed_repo.upstream_url, seed_repo.mirror_path, update=update))

    for _, mirror_name in seed_repo.submodules:
        url = SUBMODULE_UPSTREAMS.get(mirror_name)
        if not url:
            raise SystemExit(f"URL upstream desconhecida para submódulo {mirror_name}")
        print(_mirror(url, mirror_root() / mirror_name, update=update))

    print(_venv(seed_repo, update=update))
    if check:
        print(_check(seed_repo))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara repositórios-semente localmente")
    parser.add_argument("seed_repo_id", nargs="?", choices=sorted(SEED_REPOS))
    parser.add_argument("--all", action="store_true", help="Prepara todos os repos-semente")
    parser.add_argument("--update", action="store_true", help="Recria espelho e ambiente existentes")
    parser.add_argument("--check", action="store_true",
                        help="Roda a suíte inteira no HEAD e cronometra")
    args = parser.parse_args()

    if not args.all and not args.seed_repo_id:
        parser.error("informe um repo-semente ou --all")

    alvos = sorted(SEED_REPOS) if args.all else [args.seed_repo_id]
    print(f"Espelhos em {mirror_root()}")
    for seed_repo_id in alvos:
        preparar(get_seed_repo(seed_repo_id), update=args.update, check=args.check)

    print("\nPronto. Sem rede a partir daqui.")


if __name__ == "__main__":
    main()

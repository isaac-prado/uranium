"""
Workspace: clone isolado de um repositório-semente num commit-base.

Converte o pipeline de "gerador de texto" em "agente que age sobre um
repositório real". Toda escrita passa pela guarda de caminho; nada fora
da raiz do workspace é alcançável, e caminhos protegidos (testes e
configuração) são recusados.

Materialização é 100% offline: clona de um espelho bare local, nunca da rede.
"""

from __future__ import annotations

import fnmatch
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from src.seeds import SeedRepoSpec, mirror_root, workspace_root

# Sempre bloqueado, independente dos globs protegidos do repo-semente.
_FORBIDDEN_PREFIXES = (".git/",)

BASE_TAG = "uranium-base"


class WorkspaceError(RuntimeError):
    """Falha ao materializar ou operar o workspace."""


class PathNotAllowed(WorkspaceError):
    """Caminho fora da raiz do workspace ou em área proibida."""


def _git(*args: str, cwd: Path, check: bool = True) -> str:
    """Executa git capturando stdout; levanta WorkspaceError em falha."""
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise WorkspaceError(
            f"git {' '.join(args)} falhou ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


def matches_glob(rel_path: str, pattern: str) -> bool:
    """
    Casa um caminho relativo POSIX contra um glob no estilo gitignore.

    Suporta `dir/**` (tudo sob dir) e `**/nome` (nome em qualquer nível),
    que fnmatch sozinho não resolve corretamente.
    """
    path = PurePosixPath(rel_path).as_posix()

    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(f"{prefix}/")

    if pattern.startswith("**/"):
        tail = pattern[3:]
        # casa na raiz ou em qualquer profundidade
        return fnmatch.fnmatch(path, tail) or fnmatch.fnmatch(path, f"*/{tail}")

    return fnmatch.fnmatch(path, pattern)


@dataclass(frozen=True)
class WorkspaceSpec:
    """Parâmetros de materialização de um workspace para uma tarefa."""

    seed_repo: SeedRepoSpec
    base_commit: str

    @property
    def protected_globs(self) -> tuple[str, ...]:
        return self.seed_repo.protected_globs


class Workspace:
    """Clone de trabalho isolado, versionado, no qual o agente atua."""

    def __init__(self, spec: WorkspaceSpec, run_id: str, root: Path) -> None:
        self.spec = spec
        self.run_id = run_id
        self.root = root.resolve()

    # ------------------------------------------------------------------ setup

    @classmethod
    def materialize(
        cls,
        spec: WorkspaceSpec,
        run_id: str,
        *,
        dest: Path | None = None,
        overwrite: bool = False,
    ) -> "Workspace":
        """
        Cria o workspace clonando do espelho bare local, sem tocar na rede.

        Deixa o repositório no branch `uranium/<run_id>`, apontando para
        `base_commit`, com a tag `uranium-base` marcando o estado inicial.
        """
        mirror = spec.seed_repo.mirror_path
        if not mirror.exists():
            raise WorkspaceError(
                f"Espelho ausente: {mirror}. Rode scripts/setup_mirror.py primeiro."
            )

        root = (dest or workspace_root() / run_id).resolve()
        if root.exists():
            if not overwrite:
                raise WorkspaceError(f"Workspace já existe: {root}")
            shutil.rmtree(root)
        root.parent.mkdir(parents=True, exist_ok=True)

        _git(
            "clone", "--quiet", "--shared", "--no-checkout",
            str(mirror), str(root),
            cwd=root.parent,
        )
        _git("checkout", "--quiet", spec.base_commit, cwd=root)

        cls._init_submodules(spec.seed_repo, root)

        _git("checkout", "--quiet", "-b", f"uranium/{run_id}", cwd=root)
        _git("tag", "--force", BASE_TAG, cwd=root)

        # Identidade local: alguns comandos git recusam operar sem ela.
        _git("config", "user.email", "agent@uranium.local", cwd=root)
        _git("config", "user.name", "Uranium Agent", cwd=root)

        return cls(spec, run_id, root)

    @staticmethod
    def _init_submodules(seed_repo: SeedRepoSpec, root: Path) -> None:
        """
        Inicializa submódulos a partir de espelhos locais.

        A ordem importa: `submodule init` sobrescreve a URL com a do
        .gitmodules, então o override tem de vir depois. E o git bloqueia
        transporte `file` em submódulos desde a CVE-2022-39253, daí o
        `-c protocol.file.allow=always` — seguro porque a origem é um
        espelho local sob nosso controle.
        """
        if not seed_repo.submodules:
            return

        _git("submodule", "init", "--quiet", cwd=root)
        for sub_path, mirror_name in seed_repo.submodules:
            local_mirror = mirror_root() / mirror_name
            if not local_mirror.exists():
                raise WorkspaceError(f"Espelho de submódulo ausente: {local_mirror}")
            _git(
                "config", f"submodule.{sub_path}.url", str(local_mirror),
                cwd=root,
            )
        _git(
            "-c", "protocol.file.allow=always",
            "submodule", "update", "--quiet",
            cwd=root,
        )

    # ------------------------------------------------------------- path guard

    def resolve(self, rel_path: str) -> Path:
        """
        Resolve um caminho relativo para absoluto dentro do workspace.

        Bloqueia caminho absoluto, traversal (`../`) e escape por symlink.
        Não exige que o arquivo exista (permite criação).
        """
        raw = str(rel_path).strip()
        if not raw:
            raise PathNotAllowed("Caminho vazio")

        candidate = Path(raw)
        if candidate.is_absolute():
            raise PathNotAllowed(f"Caminho absoluto não permitido: {raw}")

        resolved = (self.root / candidate).resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise PathNotAllowed(f"Caminho escapa do workspace: {raw}")

        rel = resolved.relative_to(self.root).as_posix()
        if any(rel == p.rstrip("/") or rel.startswith(p) for p in _FORBIDDEN_PREFIXES):
            raise PathNotAllowed(f"Área interna do git não é acessível: {raw}")

        return resolved

    def is_protected(self, rel_path: str) -> bool:
        """Indica se o caminho está numa área que o agente não pode sobrescrever."""
        try:
            resolved = self.resolve(rel_path)
        except PathNotAllowed:
            return True
        rel = resolved.relative_to(self.root).as_posix()
        return any(matches_glob(rel, g) for g in self.spec.protected_globs)

    # ----------------------------------------------------------------- estado

    def diff(self) -> str:
        """Diff unificado do estado atual contra o commit-base."""
        return _git("diff", BASE_TAG, cwd=self.root)

    def changed_files(self) -> list[str]:
        """Arquivos modificados em relação ao commit-base, incluindo não rastreados."""
        tracked = _git("diff", "--name-only", BASE_TAG, cwd=self.root).split()
        untracked = _git(
            "ls-files", "--others", "--exclude-standard", cwd=self.root
        ).split()
        return sorted(set(tracked) | set(untracked))

    def protected_touched(self) -> list[str]:
        """Arquivos protegidos que foram modificados — sinal para o harness."""
        return [f for f in self.changed_files() if self.is_protected(f)]

    def diffstat(self) -> dict[str, int]:
        """Contagem de arquivos, inserções e remoções contra o commit-base."""
        out = _git("diff", "--numstat", BASE_TAG, cwd=self.root)
        files = insertions = deletions = 0
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            files += 1
            if parts[0].isdigit():
                insertions += int(parts[0])
            if parts[1].isdigit():
                deletions += int(parts[1])
        return {"files_changed": files, "insertions": insertions, "deletions": deletions}

    # ------------------------------------------------------------------ saída

    def snapshot(self, dest: Path) -> Path:
        """Empacota o workspace (com .git) para entrega ao harness externo."""
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(dest, "w:gz") as tar:
            tar.add(self.root, arcname=self.root.name)
        return dest

    def cleanup(self) -> None:
        """Remove o workspace do disco."""
        if self.root.exists():
            shutil.rmtree(self.root)

    def __repr__(self) -> str:
        return f"Workspace(run_id={self.run_id!r}, root={self.root!s})"

#!/usr/bin/env python3
"""
Minera candidatos a tarefa no histórico de um repositório-semente.

Uma tarefa do E1 precisa de um oráculo que discrimine: um teste que FALHA
antes da correção e PASSA depois. O histórico do upstream é cheio desses
pares — commit que corrige um bug e traz o teste junto —, mas descobrir
quais servem é trabalho de execução, não de leitura de mensagem de commit.

Para cada commit candidato, com o pai como commit-base:

  0. a suíte tem de estar VERDE no pai — sem isso não dá para atribuir
     falha nenhuma ao agente, e o passo 1 ficaria vermelho pelo motivo
     errado;
  1. traz os arquivos de teste do commit de correção, deixa a fonte velha;
     a suíte tem de ficar VERMELHA — se não ficar, o teste não discrimina;
  2. traz também a fonte; a suíte tem de ficar VERDE — se não ficar, o
     corte está errado.

O fail-to-pass sai daí: são exatamente os node ids que falharam em (1) e
passaram em (2). Nada é inferido do texto do commit.

    uv run python scripts/mine_tasks.py peewee --limit 25
    uv run python scripts/mine_tasks.py --all --limit 25 --out mined/
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.seeds import SEED_REPOS, SeedRepoSpec, get_seed_repo  # noqa: E402
from src.tools.exec import run_pytest  # noqa: E402
from src.workspace import Workspace, WorkspaceSpec, matches_glob  # noqa: E402

# Um patch de fonte muito pequeno costuma ser typo ou bump de versão; muito
# grande vira "reescreva o módulo", que mede outra coisa. A faixa é larga de
# propósito — a estratificação por dificuldade vem depois, sobre o que passar.
MIN_LINHAS_FONTE = 3
MAX_LINHAS_FONTE = 400
MAX_ARQUIVOS_FONTE = 6

# Mensagens que quase nunca rendem tarefa e custariam duas rodadas de suíte.
RUIDO = ("bump version", "release ", "prepare release", "update changelog",
         "fix typo", "typos", "merge pull request", "revert ")


@dataclass
class Candidato:
    """Um commit avaliado, aceito ou não, com o motivo registrado."""

    seed_repo_id: str
    fix_commit: str
    base_commit: str
    subject: str
    arquivos_fonte: list[str]
    arquivos_teste: list[str]
    linhas_fonte: int
    aceito: bool = False
    motivo: str = ""
    fail_to_pass: list[str] = field(default_factory=list)
    segundos: float = 0.0

    @property
    def f2p_arquivos(self) -> int:
        """
        Em quantos arquivos de teste o fail-to-pass se espalha.

        Sinal de que o commit é um lote de correções sem relação entre si, e
        não um problema. O peewee 08b28d14 tem 6 f2p em 6 arquivos: seriam
        seis tarefas espremidas numa, com enunciado incoerente.
        """
        return len({n.split("::", 1)[0] for n in self.fail_to_pass})

    @property
    def faixa(self) -> str:
        """Estratificação por dificuldade, pelo tamanho do patch de referência."""
        n = len(self.arquivos_fonte)
        if n == 1 and self.linhas_fonte < 30:
            return "baixa"
        if n <= 3:
            return "media"
        return "alta"


def _git(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])}: {proc.stderr.strip()[:300]}")
    return proc.stdout


def _classificar(repo: SeedRepoSpec, caminhos: list[str]) -> tuple[list[str], list[str]]:
    """Separa fonte de teste/configuração pelos globs protegidos do repo."""
    fonte, teste = [], []
    for caminho in caminhos:
        if any(matches_glob(caminho, g) for g in repo.protected_globs):
            teste.append(caminho)
        elif caminho.endswith(".py"):
            fonte.append(caminho)
    return fonte, teste


def levantar_candidatos(repo: SeedRepoSpec, *, max_commits: int) -> list[Candidato]:
    """Varre o histórico e devolve os commits que valem o custo de executar."""
    bruto = _git(
        "--git-dir", str(repo.mirror_path), "log", "--no-merges",
        f"-n{max_commits}", "--format=%x1e%H%x1f%s", "--name-only",
    )

    candidatos = []
    for registro in bruto.split("\x1e"):
        registro = registro.strip("\n")
        if not registro:
            continue
        cabecalho, _, corpo = registro.partition("\n")
        sha, _, subject = cabecalho.partition("\x1f")
        if not sha:
            continue
        if any(r in subject.lower() for r in RUIDO):
            continue

        fonte, teste = _classificar(repo, [l for l in corpo.split("\n") if l.strip()])
        if not fonte or not teste:
            continue  # sem teste não há oráculo; sem fonte não há o que corrigir
        if len(fonte) > MAX_ARQUIVOS_FONTE:
            continue

        try:
            numstat = _git("--git-dir", str(repo.mirror_path), "diff", "--numstat",
                           f"{sha}^", sha, "--", *fonte)
        except RuntimeError:
            continue  # commit raiz, sem pai
        linhas = sum(
            int(p) for linha in numstat.splitlines()
            for p in linha.split("\t")[:2] if p.isdigit()
        )
        if not MIN_LINHAS_FONTE <= linhas <= MAX_LINHAS_FONTE:
            continue

        candidatos.append(Candidato(
            seed_repo_id=repo.seed_repo_id,
            fix_commit=sha,
            base_commit=_git("--git-dir", str(repo.mirror_path),
                             "rev-parse", f"{sha}^").strip(),
            subject=subject[:120],
            arquivos_fonte=fonte,
            arquivos_teste=teste,
            linhas_fonte=linhas,
        ))
    return candidatos


def avaliar(cand: Candidato, repo: SeedRepoSpec, raiz: Path, *, timeout_s: int) -> Candidato:
    """Executa a suíte duas vezes e decide se o commit discrimina."""
    comeco = time.perf_counter()
    ws = Workspace.materialize(
        WorkspaceSpec(seed_repo=repo, base_commit=cand.base_commit),
        run_id=f"mina-{cand.fix_commit[:8]}", dest=raiz / cand.fix_commit[:8],
        overwrite=True,
    )

    try:
        # 0. a base precisa estar sadia. Sem esta checagem entram commits cuja
        # suíte já estava vermelha, e o vermelho do passo 1 seria por outro
        # motivo — o sqlite-utils d9a0fd26 passou assim, com 3 dos 4 f2p num
        # arquivo de teste que o commit sequer tocou.
        base = run_pytest(ws, timeout_s=timeout_s)
        if not base.green:
            return _fechar(cand, comeco,
                           f"commit-base já vermelho ({base.failed} falhas)")

        # 1. testes novos sobre a fonte velha: tem de ficar vermelho
        _git("checkout", cand.fix_commit, "--", *cand.arquivos_teste, cwd=ws.root)
        antes = run_pytest(ws, timeout_s=timeout_s)
        if antes.timed_out:
            return _fechar(cand, comeco, "suíte estourou o tempo com os testes novos")
        if antes.green:
            return _fechar(cand, comeco, "teste passa sem a correção — não discrimina")
        if not antes.failing_node_ids:
            return _fechar(cand, comeco, "vermelho sem node id: erro de coleta")

        # 2. fonte corrigida também: tem de ficar verde
        _git("checkout", cand.fix_commit, "--", *cand.arquivos_fonte, cwd=ws.root)
        depois = run_pytest(ws, timeout_s=timeout_s)
        if not depois.green:
            faltam = [n for n in antes.failing_node_ids if n in depois.failing_node_ids]
            return _fechar(
                cand, comeco,
                f"não fica verde com a correção ({depois.failed} falhas, "
                f"{len(faltam)} das mesmas) — base insalubre ou corte errado",
            )

        cand.fail_to_pass = sorted(antes.failing_node_ids)
        cand.aceito = True
        cand.motivo = (f"discrimina: {len(cand.fail_to_pass)} teste(s) f2p "
                       f"em {cand.f2p_arquivos} arquivo(s)")
        return _fechar(cand, comeco, cand.motivo)
    finally:
        ws.cleanup()


def _fechar(cand: Candidato, comeco: float, motivo: str) -> Candidato:
    cand.segundos = round(time.perf_counter() - comeco, 1)
    cand.motivo = motivo
    return cand


def minerar(repo: SeedRepoSpec, *, limite: int, varredura: int, timeout_s: int,
            raiz: Path) -> list[Candidato]:
    candidatos = levantar_candidatos(repo, max_commits=varredura)
    print(f"\n{repo.seed_repo_id}: {len(candidatos)} candidatos em {varredura} commits "
          f"— executando os {min(limite, len(candidatos))} mais recentes")

    avaliados = []
    for i, cand in enumerate(candidatos[:limite], 1):
        resultado = avaliar(cand, repo, raiz, timeout_s=timeout_s)
        avaliados.append(resultado)
        marca = "ACEITO " if resultado.aceito else "recusa "
        print(f"  [{i:>3}/{min(limite, len(candidatos))}] {marca} {resultado.fix_commit[:8]} "
              f"{resultado.faixa:<6} {resultado.segundos:>5.1f}s  {resultado.subject[:60]}")
        if resultado.aceito and resultado.f2p_arquivos > 2:
            print(f"                atenção: f2p em {resultado.f2p_arquivos} arquivos "
                  f"— provável lote de correções, não um problema")
        if not resultado.aceito:
            print(f"                {resultado.motivo[:100]}")
    return avaliados


def main() -> None:
    p = argparse.ArgumentParser(description="Minera candidatos a tarefa do E1")
    p.add_argument("seed_repo_id", nargs="?", choices=sorted(SEED_REPOS))
    p.add_argument("--all", action="store_true")
    p.add_argument("--limit", type=int, default=25, help="Commits a executar por repo")
    p.add_argument("--scan", type=int, default=400, help="Commits a varrer no histórico")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--out", type=Path, default=Path("mined"))
    args = p.parse_args()

    if not args.all and not args.seed_repo_id:
        p.error("informe um repo-semente ou --all")

    alvos = sorted(SEED_REPOS) if args.all else [args.seed_repo_id]
    args.out.mkdir(parents=True, exist_ok=True)
    raiz = args.out / ".workspaces"
    raiz.mkdir(exist_ok=True)

    total = []
    for seed_repo_id in alvos:
        repo = get_seed_repo(seed_repo_id)
        if not repo.mirror_path.exists() or not repo.has_venv:
            print(f"\n{seed_repo_id}: pulado — rode scripts/setup_mirror.py {seed_repo_id}")
            continue
        avaliados = minerar(repo, limite=args.limit, varredura=args.scan,
                            timeout_s=args.timeout, raiz=raiz)
        destino = args.out / f"{seed_repo_id}.json"
        destino.write_text(
            json.dumps([asdict(c) | {"faixa": c.faixa, "f2p_arquivos": c.f2p_arquivos}
                       for c in avaliados],
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        total += avaliados
        print(f"  -> {destino}")

    aceitos = [c for c in total if c.aceito]
    print(f"\n{'─' * 70}")
    print(f"{len(aceitos)} aceitos de {len(total)} executados")
    for faixa in ("baixa", "media", "alta"):
        na_faixa = [c for c in aceitos if c.faixa == faixa]
        por_repo = ", ".join(
            f"{r}={sum(1 for c in na_faixa if c.seed_repo_id == r)}" for r in alvos
        )
        print(f"  {faixa:<6} {len(na_faixa):>3}   ({por_repo})")


if __name__ == "__main__":
    main()

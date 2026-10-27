"""
Varredura de vazamento pelo histórico git do workspace.

O workspace de cada run é `git clone --shared` do espelho completo do repositório-semente
(`src/workspace.py`): `master`, tags e commits posteriores ao commit-base ficam visíveis, e um
trecho Python executado por `run_python` pode fazer `git show master:arquivo`. Achado em
23/10/2026 na rodada 8, tomlkit-0004 rep01 (workspace com o `master` de 2026 copiado, versão
0.1.1 -> "0.15.2"). Para cada workspace de run, este script mede sinais de uso desse histórico:

- BLOB FUTURO: arquivo modificado idêntico a um blob de commit que não é ancestral da base;
- MAIS PERTO DE MASTER: arquivo com 50+ linhas de diff contra a base e menos diff contra o ramo principal (`origin/HEAD`: master ou main);
- NOVO COM NOME FUTURO: arquivo novo (não rastreado) cujo caminho existe no ramo principal e não na base;
- VERSÃO: `__version__` alterado.

Uso: .venv/bin/python scripts/varredura_vazamento_git.py [raiz ...]  (padrão: runs/* sem "-analise")
Uma linha por run; os sinais vêm depois de " | ".
"""
import glob
import os
import subprocess
import sys


def git(ws: str, *args: str) -> str:
    return subprocess.run(["git", "-C", ws, *args], capture_output=True, text=True).stdout


def ok(ws: str, *args: str) -> bool:
    return subprocess.run(["git", "-C", ws, *args], capture_output=True).returncode == 0


def diff_total(ws: str, ref: str, path: str) -> int:
    saida = git(ws, "diff", "--numstat", ref, "--", path).strip()
    if not saida:
        return 0
    add, rem, _ = saida.split("\t", 2)
    return (int(add) if add.isdigit() else 0) + (int(rem) if rem.isdigit() else 0)


def versao(texto: str) -> str | None:
    for linha in texto.splitlines():
        if "__version__" in linha:
            return linha.strip()
    return None


def ramo_principal(ws: str) -> str | None:
    """`origin/HEAD` do espelho (master ou main); senão master, senão main."""
    for ref in ("origin/HEAD", "master", "main", "origin/master", "origin/main"):
        if ok(ws, "rev-parse", "-q", "--verify", ref):
            return ref
    return None


def sinais_do_workspace(ws: str) -> tuple[int, int, bool, list[str]]:
    principal = ramo_principal(ws)
    tem_master = principal is not None
    status = git(ws, "status", "--porcelain").splitlines()
    mods = [l[3:] for l in status if l[:2] in (" M", "M ", "MM")]
    novos = [l[3:] for l in status if l.startswith("??")]
    sinais: list[str] = []
    for f in mods:
        if not f.endswith(".py"):
            continue
        d_base = diff_total(ws, "HEAD", f)
        h = git(ws, "hash-object", f).strip()
        commits = git(ws, "log", "--all", "--format=%H", f"--find-object={h}").split()
        futuros = [c for c in commits if not ok(ws, "merge-base", "--is-ancestor", c, "HEAD")]
        if futuros:
            sinais.append(f"BLOB FUTURO {f} = {git(ws, 'describe', '--tags', '--always', futuros[0]).strip()}")
        if tem_master and d_base >= 50:
            d_master = diff_total(ws, principal, f)
            if d_master < d_base:
                sinais.append(f"MAIS PERTO DE MASTER {f} (base {d_base} vs master {d_master})")
        if f.endswith(("__init__.py", "version.py", "_version.py")):
            antes = versao(git(ws, "show", f"HEAD:{f}"))
            with open(os.path.join(ws, f), errors="replace") as fh:
                depois = versao(fh.read())
            if antes and depois and antes != depois:
                sinais.append(f"VERSÃO {f}: {antes} -> {depois}")
    for f in novos:
        if not f.endswith(".py") or f.startswith(("tests/", "test")):
            continue
        if tem_master and ok(ws, "cat-file", "-e", f"{principal}:{f}") and not ok(ws, "cat-file", "-e", f"HEAD:{f}"):
            sinais.append(f"NOVO COM NOME FUTURO {f}")
    return len(mods), len(novos), tem_master, sinais


def main() -> None:
    raizes = sys.argv[1:] or sorted(d for d in glob.glob("runs/*") if "-analise" not in d)
    for raiz in raizes:
        for ws in sorted(glob.glob(f"{raiz}/*/*/rep*/attempt*/workspace")):
            if not os.path.isdir(os.path.join(ws, ".git")):
                continue
            run = ws.split("runs/", 1)[1].replace("/workspace", "")
            mods, novos, tem_master, sinais = sinais_do_workspace(ws)
            linha = f"{run}: mods={mods} novos={novos} master_visivel={'sim' if tem_master else 'não'}"
            if sinais:
                linha += " | " + "; ".join(sinais)
            print(linha, flush=True)


if __name__ == "__main__":
    main()

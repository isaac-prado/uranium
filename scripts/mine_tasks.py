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

v2 (E3 item 1 das exigências, docs/tcc/tasks/EXIGENCIAS.md): a rede da v1
examinava só os `--limit`/`--scan` commits mais recentes, e o que filtrou
os candidatos multi-arquivo foi esse corte, não a escassez de histórico
— peewee sozinho tem milhares de commits. v2 varre o histórico inteiro (ou
`--desde` um ponto) com um PRÉ-FILTRO barato (`git log --numstat`, sem
checkout, sem suíte) que classifica cada candidato numa faixa de tamanho —
pequena/média/grande, ver `calcular_faixa` — e só então roda a suíte,
na ordem grande → média → pequena, com tetos por faixa
(`--max-verificar-por-faixa`, `--parar-em`). Detalhe e números em
docs/tcc/07-e3-1-mineracao.md.

    uv run python scripts/mine_tasks.py peewee
    uv run python scripts/mine_tasks.py --all --out mined-v2/
    uv run python scripts/mine_tasks.py peewee --desde 2024-01-01 --parar-em 12
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.seeds import SEED_REPOS, SeedRepoSpec, get_seed_repo  # noqa: E402
from src.tools.exec import run_pytest  # noqa: E402
from src.workspace import Workspace, WorkspaceSpec, matches_glob  # noqa: E402

# Um patch de fonte muito pequeno costuma ser typo ou bump de versão. O teto
# superior era 400/6 na v1 — pequeno demais para a faixa "média" (até 7
# arquivos-fonte, até 400 linhas) e para a "grande" (3+ arquivos, patches
# maiores). Ampliado para 800/12 — ver docs/tcc/07-e3-1-mineracao.md.
MIN_LINHAS_FONTE = 3
MAX_LINHAS_FONTE = 800
MAX_ARQUIVOS_FONTE = 12

# Mensagens que quase nunca rendem tarefa e custariam duas rodadas de suíte.
RUIDO = ("bump version", "release ", "prepare release", "update changelog",
         "fix typo", "typos", "merge pull request", "revert ")

# Ordem de verificação por execução: a faixa mais rara e mais cara de achar
# (grande) vai primeiro, para não gastar o teto de commits verificados só
# com pequenas antes de sequer olhar para as grandes.
FAIXAS_EXECUTAVEIS = ("grande", "media", "pequena")

# Revisão do autor sobre os aceitos de mined-v2 (E3.3): `protected_globs`
# mistura teste de verdade (`tests/**`, `**/test_*.py`, `**/conftest.py`)
# com arquivo de configuração/build que também é protegido mas não é teste
# (`pyproject.toml`, `setup.cfg`, `tox.ini`, `runtests.py` do peewee...).
# Só os primeiros contam como "teste" (oráculo); tocar qualquer um dos
# segundos na referência é candidato irreprodutível — o agente não pode
# tocar em `pyproject.toml`, então a correção de referência do tqdm
# e4d97426 (que acrescenta a dependência `envwrap` ali) não é algo que o
# agente consiga replicar dentro das regras. Ver `_classificar_status`.
GLOBS_DE_TESTE = ("tests/**", "test/**", "**/test_*.py", "**/*_test.py", "**/conftest.py")

_RE_DEF_TEST_LINE = re.compile(r"^([+-])\s*def\s+(test_[A-Za-z0-9_]*)\s*\(")
_RE_HUNK_CONTEXTO = re.compile(r"^@@[^@]*@@ ?(.*)$")
_RE_DEF_TEST_QUALQUER = re.compile(r"\bdef\s+(test_[A-Za-z0-9_]*)\s*\(")
_RE_MENSAGEM_DE_CORRECAO = re.compile(r"^\s*(fix|bug)\b", re.IGNORECASE)


def contar_testes_novos_e_modificados(diff_teste: str) -> tuple[int, int]:
    """
    Conta funções `def test_` adicionadas e alteradas no diff dos testes.

    Heurística sobre o diff unificado do git, não parsing de AST — é o que
    dá para fazer sem checkout. Duas fontes de sinal:

    - uma linha `def test_x(` que só aparece do lado `+` (nunca do lado
      `-`, em nenhum hunk do arquivo) é função NOVA;
    - o cabeçalho de hunk do git (`@@ ... @@ def test_x(...):`) é
      preenchido com a assinatura da função em que a mudança caiu quando o
      corpo mudou sem tocar a linha `def` — isso é função MODIFICADA, mas
      só conta quando o hunk tem alguma linha `-` de verdade: um hunk só
      com adições é uma inserção logo depois da função de contexto, que
      em si não foi tocada (é o que aconteceria ao inserir `test_novo`
      logo após `test_existente`: o contexto mostra `test_existente`, mas
      quem mudou foi só o arquivo, não essa função);
      o mesmo vale para uma linha `def test_x(` que aparece dos dois lados
      (assinatura alterada, função pré-existente).

    Item 3 das exigências (breaking change) usa este número: um patch cujo
    fail_to_pass é majoritariamente teste MODIFICADO, não novo, é sinal de
    que o comportamento antigo mudou — o oráculo pode não conseguir julgar
    isso, porque o agente não pode tocar em `tests/` para acompanhar.
    """
    adicionadas: set[str] = set()
    removidas: set[str] = set()
    tocadas_por_contexto: set[str] = set()
    contexto_atual: str | None = None
    tem_remocao_no_hunk = False

    def fechar_hunk() -> None:
        if contexto_atual and tem_remocao_no_hunk:
            tocadas_por_contexto.add(contexto_atual)

    for linha in diff_teste.splitlines():
        if linha.startswith("+++") or linha.startswith("---"):
            continue
        if linha.startswith("@@"):
            fechar_hunk()
            contexto_atual, tem_remocao_no_hunk = None, False
            m = _RE_HUNK_CONTEXTO.match(linha)
            if m and m.group(1):
                m2 = _RE_DEF_TEST_QUALQUER.search(m.group(1))
                if m2:
                    contexto_atual = m2.group(1)
            continue
        if linha.startswith("-"):
            tem_remocao_no_hunk = True
        m = _RE_DEF_TEST_LINE.match(linha)
        if m:
            sinal, nome = m.group(1), m.group(2)
            (adicionadas if sinal == "+" else removidas).add(nome)
    fechar_hunk()

    novas = adicionadas - removidas
    modificadas = (adicionadas & removidas) | (tocadas_por_contexto - novas)
    return len(novas), len(modificadas)


def calcular_modulos_fonte(arquivos_fonte: list[str]) -> int:
    """
    Conta módulos distintos entre os arquivos-fonte tocados.

    "Módulo" é o DIRETÓRIO que contém o arquivo (não o AST, é caminho de
    arquivo — proxy barato de "atravessa módulos" para o critério da faixa
    média). Dois arquivos na mesma pasta são o mesmo módulo; um arquivo
    solto na raiz do repositório (sem `/` no caminho, caso de `peewee.py`
    ao lado de `playhouse/`) é módulo próprio, pelo nome sem extensão.

    Testado com as duas formas que os repositórios-semente realmente têm:
    pacote raso de um nível (`tomlkit/items.py` e `tomlkit/parser.py`,
    mesma pasta `tomlkit` — 1 módulo, tomlkit não tem subpacote nenhum) e
    pacote com subpacote (`playhouse/sqlite_ext.py` ao lado de
    `peewee.py` solto na raiz — 2 módulos). Um candidato a repositório
    novo com subpacotes de verdade (`pygments/lexers/`, `pygments/`
    solto) já separa `pygments` de `pygments/lexers` corretamente — a
    primeira versão desta função (só o primeiro componente do caminho)
    não distinguia isso, porque colapsava todo arquivo dentro de
    `pygments/` num módulo só, não importa a profundidade.
    """
    modulos = set()
    for caminho in arquivos_fonte:
        diretorio = caminho.rsplit("/", 1)[0] if "/" in caminho else None
        modulos.add(diretorio or caminho.rsplit(".", 1)[0])
    return len(modulos)


def calcular_faixa(*, arquivos_fonte: int, linhas_fonte: int, modulos_fonte: int,
                    testes_novos: int, testes_modificados: int, subject: str) -> tuple[str, str]:
    """
    Faixa é função pura dos campos medidos — sem depender de execução.

    Regra operacional (docs/tcc/tasks/EXIGENCIAS.md, tabela da etapa E3,
    e justificativa de cada limiar em docs/tcc/07-e3-1-mineracao.md):

    - PEQUENA: 1 ou 2 arquivos-fonte, 10 a 50 linhas de patch — localizar e
      corrigir, sem decisão de onde uma mudança se propaga. Também
      pequena, com `motivo_faixa` explicando: 3 ou mais arquivos-fonte mas
      menos de 40 linhas — revisão do autor (E3.3) sobre peewee b8a336d0
      (11 linhas em 3 arquivos, tinha saído como média): patch pequeno
      não vira "média" só por tocar 3 arquivos, e não é uma pequena
      "típica" de 1-2 arquivos, mas o tamanho é de pequena.
    - MÉDIA: 3 a 7 arquivos-fonte, **40** a 400 linhas — exige entender a
      interação entre módulos, não só um arquivo maior. "Módulo" é o
      arquivo `.py` (decisão 22 do autor, 08/10/2026,
      docs/tcc/09-decisoes-do-autor.md): a versão de 19/09 exigia também
      2 ou mais DIRETÓRIOS distintos (`modulos_fonte >= 2`), o que em
      pacote plano (tomlkit, sqlite-utils, jinja, marshmallow, todos os
      `.py` numa pasta) tornava a faixa vazia por construção — a
      mineração de 08/10 (`mined-v3/`) achou 54 candidatos com perfil
      médio escondidos por essa condição. `modulos_fonte` continua
      medido e registrado, só não decide a faixa. Piso de 40 linhas
      acrescentado na revisão de 19/09: sem ele, um patch de poucas
      linhas espalhado por 3 arquivos (ex.: renomear um parâmetro em 3
      lugares) contava como média por número de arquivo, não por
      dificuldade real.
    - GRANDE: 3 ou mais arquivos-fonte, 80 ou mais linhas, e o
      fail-to-pass é majoritariamente teste NOVO (mais funções `def test_`
      adicionadas do que alteradas) com mensagem que não é de correção —
      sinal de funcionalidade nova escrita com teste, que pede
      planejamento antes de codificar, e não conserto de um teste que já
      existia.

    Checada NESTA ordem (grande, média, pequena, pequena-por-linhas-poucas):
    um candidato grande também costuma caber nos limites soltos de
    arquivos/linhas da média; se a pequena fosse checada primeiro nada
    sobraria para as faixas maiores. Fora das três: `faixa = "fora"`, com
    o motivo.

    `arquivos_fonte` aqui é a contagem LÓGICA (`arquivos_fonte_logicos` de
    `_classificar_status`) e `linhas_fonte` já exclui arquivo apagado ou
    fora do `source_dir` do repositório — ver `_classificar_status` e o
    aviso do coordenador (E3.3) sobre pygments 2c463c68 (saiu como média
    com 267 linhas; a correção de verdade é 1 linha em
    `pygments/lexers/json5.py`, o resto era remoção de arquivos soltos em
    `json5-tests/`, fora do pacote).
    """
    eh_mensagem_de_correcao = bool(_RE_MENSAGEM_DE_CORRECAO.match(subject))

    if (arquivos_fonte >= 3 and linhas_fonte >= 80 and testes_novos > 0
            and testes_novos > testes_modificados and not eh_mensagem_de_correcao):
        return "grande", ""

    if 3 <= arquivos_fonte <= 7 and 40 <= linhas_fonte <= 400:
        return "media", ""

    if 1 <= arquivos_fonte <= 2 and 10 <= linhas_fonte <= 50:
        return "pequena", ""

    if arquivos_fonte >= 3 and linhas_fonte < 40:
        return "pequena", (
            f"pequena por tamanho, não pela contagem de arquivo: "
            f"{arquivos_fonte} arquivos-fonte mas só {linhas_fonte} linhas "
            f"(< 40) — pequeno demais para média mesmo tocando vários "
            f"arquivos (revisão do autor, E3.3)"
        )

    motivo = (
        f"fora das faixas: arquivos_fonte={arquivos_fonte} linhas_fonte={linhas_fonte} "
        f"modulos_fonte={modulos_fonte} testes_novos={testes_novos} "
        f"testes_modificados={testes_modificados} "
        f"mensagem_de_correcao={eh_mensagem_de_correcao}"
    )
    return "fora", motivo


@dataclass
class Candidato:
    """Um commit classificado pelo pré-filtro e, se elegível, avaliado por execução."""

    seed_repo_id: str
    fix_commit: str
    base_commit: str
    subject: str
    arquivos_fonte: list[str]
    arquivos_teste: list[str]
    linhas_fonte: int
    modulos_fonte: int
    testes_novos: int
    testes_modificados: int
    altera_testes_existentes: bool
    faixa: str
    motivo_faixa: str = ""
    # Caminhos de `arquivos_fonte`/`arquivos_teste` que NÃO existem mais no
    # fix_commit — apagados, ou nome antigo de um renomeado. `avaliar` tira
    # esses do workspace em vez de tentar `git checkout <fix> -- <path>`,
    # que falharia (pathspec não casa em `fix`) e derrubaria o candidato
    # com RuntimeError. Ver `_classificar_status`.
    arquivos_fonte_desaparecidos: list[str] = field(default_factory=list)
    arquivos_teste_desaparecidos: list[str] = field(default_factory=list)
    # Arquivo-fonte apagado pelo commit (status D), dentro do source_dir.
    # NÃO entra em `arquivos_fonte`/`linhas_fonte`/`modulos_fonte` — conta
    # como fonte de verdade infla a faixa sem representar dificuldade
    # real (revisão do autor, E3.3, pygments 2c463c68: 267 linhas de
    # arquivo apagado por cima de 1 linha de correção de verdade).
    # Registrado à parte, só para auditoria.
    arquivos_fonte_apagados: list[str] = field(default_factory=list)
    # Contagens (não listas) para o relatório, só do lado teste — é o que
    # a exigência pede e o que o item 3 (breaking change) usa: um commit
    # que apaga ou renomeia teste em vez de só acrescentar é outro sinal
    # de que ele pode estar mudando comportamento, não só corrigindo.
    testes_apagados: int = 0
    testes_renomeados: int = 0
    # A referência toca um arquivo protegido que não é teste (pyproject.toml,
    # setup.cfg, tox.ini, runtests.py do peewee...) — o agente não pode
    # tocar nesses arquivos, então essa referência é irreprodutível dentro
    # das regras. Candidato sempre rejeitado quando True (revisão do
    # autor, E3.3, tqdm e4d97426: acrescenta dependência em pyproject.toml).
    toca_protegido: bool = False
    verificado: bool = False
    aceito: bool = False
    motivo: str = ""
    # Só preenchido quando `motivo` é "suíte não executa na base" (aviso
    # do coordenador, E3.3): a cauda do stdout de pytest, para diagnosticar
    # sem precisar reexecutar — dependência ausente no venv, arquivo do
    # `suite_targets` que ainda não existia nesse commit, etc.
    stdout_tail: str = ""
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


def _git(*args: str, cwd: Path | None = None) -> str:
    # errors="replace": um diff pode tocar arquivo de amostra em codificação
    # esquisita (pygments tem `tests/examplefiles/` cheio disso, de
    # propósito — são amostras de linguagens de verdade para testar o
    # lexer). Sem isso, `text=True` decodifica como UTF-8 estrito e
    # levanta UnicodeDecodeError, que sem a rede de segurança do item 3 do
    # aviso do coordenador derrubaria a mineração inteira num caminho que
    # nem passa por lá (aqui é levantamento, não avaliação por execução).
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])}: {proc.stderr.strip()[:300]}")
    return proc.stdout


def _parse_name_status(linhas: list[str]) -> list[tuple[str, str, str | None]]:
    """
    Decodifica linhas de `git log`/`git diff --name-status -M`.

    Cada linha é `M\\tcaminho`, `A\\tcaminho`, `D\\tcaminho` ou
    `R<similaridade>\\tantigo\\tnovo` (renomeado — com ou sem edição junto).
    Devolve tuplas `(status, caminho_atual, caminho_antigo | None)`; para
    renomeado, `caminho_atual` é o nome novo e `caminho_antigo` o que
    sumiu. Só a primeira letra do status importa (R100, R87, ... viram R).
    """
    resultado = []
    for linha in linhas:
        if not linha.strip():
            continue
        partes = linha.split("\t")
        status = partes[0][0]
        if status in ("R", "C") and len(partes) >= 3:
            resultado.append((status, partes[2], partes[1]))
        elif len(partes) >= 2:
            resultado.append((status, partes[1], None))
    return resultado


def _eh_teste(caminho: str) -> bool:
    """Só os globs de conteúdo de teste de verdade — não config/build protegido."""
    return any(matches_glob(caminho, g) for g in GLOBS_DE_TESTE)


def _em_source_dir(caminho: str, source_dir: str) -> bool:
    """
    Confere se `caminho` está dentro de um dos diretórios/arquivos-fonte
    declarados em `SeedRepoSpec.source_dir` — lista separada por vírgula
    (`"peewee,playhouse"`, `"tomlkit"`, ...). Além do diretório
    (`playhouse/sqlite_ext.py` casa com o prefixo `"playhouse"`), casa o
    módulo solto de arquivo único citado pelo próprio nome (`peewee.py`
    casa com o prefixo `"peewee"`).

    Revisão do autor (E3.3): antes, qualquer `.py` fora dos globs
    protegidos virava "fonte", sem checar se pertencia mesmo ao pacote —
    pygments 2c463c68 contava arquivo apagado em `json5-tests/` (pasta de
    amostras fora do pacote `pygments/`) como fonte.
    """
    for prefixo in (p.strip() for p in source_dir.split(",")):
        if not prefixo:
            continue
        if caminho == prefixo or caminho == f"{prefixo}.py" or caminho.startswith(f"{prefixo}/"):
            return True
    return False


@dataclass
class Classificacao:
    """Resultado de classificar os caminhos de um commit por status git."""

    fonte: list[str] = field(default_factory=list)
    teste: list[str] = field(default_factory=list)
    fonte_desaparecidos: list[str] = field(default_factory=list)
    teste_desaparecidos: list[str] = field(default_factory=list)
    fonte_apagados: list[str] = field(default_factory=list)
    arquivos_fonte_logicos: int = 0
    testes_apagados: int = 0
    testes_renomeados: int = 0
    toca_protegido: bool = False


def _classificar_status(
    repo: SeedRepoSpec, entradas: list[tuple[str, str, str | None]],
) -> Classificacao:
    """
    Separa fonte de teste, resolvendo apagado e renomeado a partir do
    status de cada caminho.

    "Teste" é só `GLOBS_DE_TESTE` (conteúdo de teste de verdade); um
    caminho protegido que NÃO é teste (`pyproject.toml`, `setup.cfg`,
    `runtests.py` do peewee...) marca `toca_protegido=True` — a
    referência ficou irreprodutível pelo agente (revisão do autor, E3.3).
    "Fonte" exige `.py` E dentro do `source_dir` do repositório
    (`_em_source_dir`); apagado (status `D`) dentro do `source_dir` vai
    para `fonte_apagados`, não para `fonte` — não conta em
    `arquivos_fonte_logicos` nem entra no pathspec do `--numstat` de
    linhas (revisão do autor, E3.3, pygments 2c463c68).

    `fonte`/`teste` trazem os caminhos que EXISTEM em `fix_commit`, mais o
    nome antigo de um renomeado — testado à mão (sqlite-utils f9473ace,
    renomeia `tests/test_enable_fts.py` -> `tests/test_fts.py`): `git
    diff`/`--numstat` só com o nome novo no pathspec NÃO reconhece o
    rename e mostra o arquivo inteiro como novo (130 linhas incluídas em
    vez de 36 de diferença de verdade) — precisa dos dois nomes no
    pathspec para o `-M` casar o par.

    Isso conta um renomeado como 2 arquivos se `len(fonte)` for usado
    direto — daí `arquivos_fonte_logicos`: uma contagem de EVENTOS (1 por
    linha de status classificada como fonte), que é o que
    `MAX_ARQUIVOS_FONTE` e `calcular_faixa` devem usar.

    `fonte_desaparecidos`/`teste_desaparecidos` são o subconjunto que não
    existe mais em `fix_commit` (apagado, ou nome antigo de um renomeado):
    quem chama tira esses do workspace em vez de fazer checkout deles, que
    falharia (pathspec não casa em `fix_commit`). As contagens
    `testes_apagados`/`testes_renomeados` só contam o lado teste — insumo
    do item 3 (breaking change): apagar ou renomear teste, em vez de só
    acrescentar, é outro sinal de mudança de comportamento.
    """
    r = Classificacao()

    for status, atual, antigo in entradas:
        eh_teste_atual = _eh_teste(atual)
        eh_teste_antigo = antigo is not None and _eh_teste(antigo)
        eh_teste = eh_teste_atual or eh_teste_antigo

        eh_protegido_atual = any(matches_glob(atual, g) for g in repo.protected_globs)
        eh_protegido_antigo = antigo is not None and any(
            matches_glob(antigo, g) for g in repo.protected_globs
        )
        if (eh_protegido_atual and not eh_teste_atual) or (eh_protegido_antigo and not eh_teste_antigo):
            r.toca_protegido = True

        eh_fonte_atual = (atual.endswith(".py") and not eh_teste_atual
                          and _em_source_dir(atual, repo.source_dir))
        eh_fonte_antigo = (antigo is not None and antigo.endswith(".py") and not eh_teste_antigo
                          and _em_source_dir(antigo, repo.source_dir))

        if status == "D":
            if eh_teste:
                r.teste.append(atual)
                r.teste_desaparecidos.append(atual)
                r.testes_apagados += 1
            elif eh_fonte_atual:
                r.fonte_apagados.append(atual)  # NÃO entra em fonte/logicos/linhas
            continue

        if status == "R":
            if eh_teste:
                r.teste.append(atual)
                if antigo:
                    r.teste.append(antigo)
                    r.teste_desaparecidos.append(antigo)
                r.testes_renomeados += 1
            elif eh_fonte_atual:
                r.fonte.append(atual)
                if antigo and eh_fonte_antigo:
                    r.fonte.append(antigo)
                    r.fonte_desaparecidos.append(antigo)
                r.arquivos_fonte_logicos += 1
            continue

        # A, M, T, ... — caminho existe em fix_commit, checkout normal.
        if eh_teste_atual:
            r.teste.append(atual)
        elif eh_fonte_atual:
            r.fonte.append(atual)
            r.arquivos_fonte_logicos += 1

    return r


def _linhas_numstat(numstat: str) -> int:
    return sum(
        int(p) for linha in numstat.splitlines()
        for p in linha.split("\t")[:2] if p.isdigit()
    )


def _medir(repo: SeedRepoSpec, sha: str, subject: str, cls: Classificacao) -> dict:
    """
    A partir de uma classificação já feita (`_classificar_status`), mede
    linhas do patch de fonte (só o que sobrou em `cls.fonte` depois de
    excluir apagado e fora do `source_dir`) e calcula a faixa — sem
    checkout, sem suíte.

    Compartilhado entre `levantar_candidatos` (varredura em massa, que
    ainda aplica os portões de tamanho antes de chamar isto) e
    `reclassificar` (recalcula um candidato já registrado sem reexecutar
    a suíte, revisão do autor E3.3) — este último não aplica portão
    nenhum, só atualiza os campos do candidato existente.
    """
    numstat = (
        _git("--git-dir", str(repo.mirror_path), "diff", "--numstat", "-M",
             f"{sha}^", sha, "--", *cls.fonte)
        if cls.fonte else ""
    )
    linhas = _linhas_numstat(numstat)

    diff_teste = (
        _git("--git-dir", str(repo.mirror_path), "diff", "-M",
             f"{sha}^", sha, "--", *cls.teste)
        if cls.teste else ""
    )
    testes_novos, testes_modificados = contar_testes_novos_e_modificados(diff_teste)
    modulos_fonte = calcular_modulos_fonte(cls.fonte)
    faixa, motivo_faixa = calcular_faixa(
        arquivos_fonte=cls.arquivos_fonte_logicos, linhas_fonte=linhas, modulos_fonte=modulos_fonte,
        testes_novos=testes_novos, testes_modificados=testes_modificados, subject=subject,
    )

    return {
        "arquivos_fonte": cls.fonte,
        "arquivos_teste": cls.teste,
        "arquivos_fonte_desaparecidos": cls.fonte_desaparecidos,
        "arquivos_teste_desaparecidos": cls.teste_desaparecidos,
        "arquivos_fonte_apagados": cls.fonte_apagados,
        "linhas_fonte": linhas,
        "modulos_fonte": modulos_fonte,
        "testes_novos": testes_novos,
        "testes_modificados": testes_modificados,
        "testes_apagados": cls.testes_apagados,
        "testes_renomeados": cls.testes_renomeados,
        "toca_protegido": cls.toca_protegido,
        "faixa": faixa,
        "motivo_faixa": motivo_faixa,
    }


def levantar_candidatos(repo: SeedRepoSpec, *, desde: str | None = None) -> tuple[list[Candidato], int]:
    """
    Pré-filtro barato: só `git log --numstat` e `git diff` de texto, sem
    checkout e sem suíte. Devolve os candidatos classificados por faixa
    (`"fora"` incluída) e o total de commits examinados no histórico.

    `desde` aceita data ISO (`2024-01-01`) ou commit/tag — tenta resolver
    como commit primeiro; se não for um commit válido no espelho, trata
    como data e usa `git log --since`.
    """
    args_intervalo = ["HEAD"]
    if desde:
        try:
            _git("--git-dir", str(repo.mirror_path), "rev-parse", "--verify", f"{desde}^{{commit}}")
            args_intervalo = [f"{desde}..HEAD"]
        except RuntimeError:
            args_intervalo = [f"--since={desde}", "HEAD"]

    bruto = _git(
        "--git-dir", str(repo.mirror_path), "log", "--no-merges", "-M",
        "--format=%x1e%H%x1f%s", "--name-status", *args_intervalo,
    )

    total_commits = 0
    candidatos: list[Candidato] = []
    for registro in bruto.split("\x1e"):
        registro = registro.strip("\n")
        if not registro:
            continue
        cabecalho, _, corpo = registro.partition("\n")
        sha, _, subject = cabecalho.partition("\x1f")
        if not sha:
            continue
        total_commits += 1
        if any(r in subject.lower() for r in RUIDO):
            continue

        entradas = _parse_name_status([l for l in corpo.split("\n") if l.strip()])
        cls = _classificar_status(repo, entradas)
        if not cls.fonte or not cls.teste:
            continue  # sem teste não há oráculo; sem fonte não há o que corrigir
        if cls.arquivos_fonte_logicos > MAX_ARQUIVOS_FONTE:
            continue

        try:
            base_commit = _git("--git-dir", str(repo.mirror_path),
                               "rev-parse", f"{sha}^").strip()
        except RuntimeError:
            continue  # commit raiz, sem pai

        campos = _medir(repo, sha, subject, cls)
        if not MIN_LINHAS_FONTE <= campos["linhas_fonte"] <= MAX_LINHAS_FONTE:
            continue

        cand = Candidato(
            seed_repo_id=repo.seed_repo_id,
            fix_commit=sha,
            base_commit=base_commit,
            subject=subject[:120],
            altera_testes_existentes=campos["testes_modificados"] > 0,
            **campos,
        )
        # Referência irreprodutível pelo agente: já sai rejeitada, sem
        # gastar suíte (revisão do autor, E3.3).
        if cand.toca_protegido:
            cand.motivo = "referência toca arquivo protegido"
        candidatos.append(cand)
    return candidatos, total_commits


def _suite_nao_executou(relatorio) -> bool:
    """
    Distingue "suíte não roda nesta base" de "suíte roda e está vermelha".

    As duas aparecem como `not relatorio.green` (exit_code != 0), mas só a
    segunda é uma base vermelha de verdade. A primeira é ambiente
    incompleto para ESTE commit-base — erro de coleta, import ausente,
    arquivo do `suite_targets` que ainda não existia — e teria `passed` e
    `failed` ambos zero (sem node id nenhum) e, tipicamente, exit_code de
    uso (2 erro de coleta, 4 erro de linha de comando, 5 nada coletado),
    não o exit_code 1 de teste reprovado. Achado do E3.3 (aviso do
    coordenador): no sqlite-utils, 35 candidatos foram recusados como
    "commit-base já vermelho (0 falhas)" em 0,1 a 0,2s — tempo curto demais
    para rodar 1.400+ testes; a causa real era `ModuleNotFoundError:
    typing_extensions`, dependência que o sqlite-utils passou a exigir em
    agosto de 2026 e que não estava pinada em `SeedRepoSpec.test_requirements`
    (corrigido em `src/seeds.py`) — não falta de correção nenhuma.
    """
    return relatorio.passed == 0 and relatorio.failed == 0


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
            if _suite_nao_executou(base):
                cand.stdout_tail = base.stdout_tail[-800:]
                return _fechar(
                    cand, comeco,
                    f"suíte não executa na base (exit={base.exit_code}, "
                    f"{base.errors} erro(s) de coleta, {base.duration_s:.1f}s) "
                    f"— ver stdout_tail",
                )
            return _fechar(cand, comeco,
                           f"commit-base já vermelho ({base.failed} falhas)")

        # 1. testes novos sobre a fonte velha: tem de ficar vermelho.
        # Caminho que não existe mais em fix_commit (apagado, ou nome
        # antigo de um renomeado) sai do workspace em vez de checkout —
        # `git checkout <fix> -- <path>` falharia com RuntimeError porque
        # o pathspec não casa em `fix`.
        _remover_desaparecidos(ws.root, cand.arquivos_teste_desaparecidos)
        presentes_teste = _presentes(cand.arquivos_teste, cand.arquivos_teste_desaparecidos)
        if presentes_teste:
            _git("checkout", cand.fix_commit, "--", *presentes_teste, cwd=ws.root)
        antes = run_pytest(ws, timeout_s=timeout_s)
        if antes.timed_out:
            return _fechar(cand, comeco, "suíte estourou o tempo com os testes novos")
        if antes.green:
            return _fechar(cand, comeco, "teste passa sem a correção — não discrimina")
        if not antes.failing_node_ids:
            return _fechar(cand, comeco, "vermelho sem node id: erro de coleta")

        # 2. fonte corrigida também: tem de ficar verde. Mesmo tratamento
        # para fonte apagada/renomeada (E3.3, aviso do coordenador).
        _remover_desaparecidos(ws.root, cand.arquivos_fonte_desaparecidos)
        presentes_fonte = _presentes(cand.arquivos_fonte, cand.arquivos_fonte_desaparecidos)
        if presentes_fonte:
            _git("checkout", cand.fix_commit, "--", *presentes_fonte, cwd=ws.root)
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
    except Exception as exc:  # noqa: BLE001 — candidato ruim não pode derrubar o laço
        # Segunda folga do E3.3: commit com arquivo apagado/renomeado que
        # escapou do tratamento acima (ou qualquer outra falha de git no
        # meio da avaliação) rejeita SÓ este candidato, não a mineração
        # inteira.
        return _fechar(cand, comeco, f"erro inesperado na avaliação: {exc}"[:200])
    finally:
        ws.cleanup()


def _presentes(caminhos: list[str], desaparecidos: list[str]) -> list[str]:
    """Caminhos de `caminhos` que ainda existem em fix_commit (não estão em `desaparecidos`)."""
    fora = set(desaparecidos)
    # preserva ordem e remove duplicata (renomeado entra 2x em `caminhos`)
    vistos: set[str] = set()
    resultado = []
    for c in caminhos:
        if c in fora or c in vistos:
            continue
        vistos.add(c)
        resultado.append(c)
    return resultado


def _remover_desaparecidos(raiz: Path, caminhos: list[str]) -> None:
    """Tira do workspace os caminhos que não existem mais em fix_commit."""
    if not caminhos:
        return
    _git("rm", "-f", "--ignore-unmatch", "--", *caminhos, cwd=raiz)


def _fechar(cand: Candidato, comeco: float, motivo: str) -> Candidato:
    cand.segundos = round(time.perf_counter() - comeco, 1)
    cand.motivo = motivo
    cand.verificado = True
    return cand


def minerar(repo: SeedRepoSpec, *, max_verificar_por_faixa: int, parar_em: int,
            timeout_s: int, desde: str | None, raiz: Path) -> tuple[list[Candidato], dict]:
    """
    Pré-filtra o histórico inteiro (ou `--desde`) e só então verifica por
    execução, na ordem grande -> média -> pequena, até `parar_em` aceitos
    ou `max_verificar_por_faixa` verificados em cada faixa.
    """
    inicio = time.perf_counter()
    candidatos, total_commits = levantar_candidatos(repo, desde=desde)

    # toca_protegido já vem rejeitado de `levantar_candidatos` (referência
    # irreprodutível pelo agente) — nunca entra na fila de execução, some
    # gastar suíte à toa (revisão do autor, E3.3).
    verificaveis = [c for c in candidatos if not c.toca_protegido]
    por_faixa = {f: [c for c in verificaveis if c.faixa == f] for f in FAIXAS_EXECUTAVEIS}
    fora = [c for c in candidatos if c.faixa == "fora" and not c.toca_protegido]
    protegidos = [c for c in candidatos if c.toca_protegido]

    print(f"\n{repo.seed_repo_id}: {total_commits} commits no histórico"
          + (f" desde {desde}" if desde else "") + f", {len(candidatos)} candidatos após o pré-filtro")
    for faixa in FAIXAS_EXECUTAVEIS:
        print(f"  pré-filtro {faixa:<8} {len(por_faixa[faixa]):>5} candidatos")
    print(f"  pré-filtro fora     {len(fora):>5} candidatos (descartados, não verificados)")
    print(f"  pré-filtro protegido{len(protegidos):>5} candidatos "
          f"(referência toca arquivo protegido, não é teste — rejeitados sem suíte)")

    avaliados: list[Candidato] = list(fora) + list(protegidos)
    verificados_por_faixa = {f: 0 for f in FAIXAS_EXECUTAVEIS}
    aceitos_por_faixa = {f: 0 for f in FAIXAS_EXECUTAVEIS}
    motivos_rejeicao: dict[str, int] = {}

    for faixa in FAIXAS_EXECUTAVEIS:
        fila = por_faixa[faixa][:max_verificar_por_faixa]
        aceitos_na_faixa = 0
        for i, cand in enumerate(fila, 1):
            try:
                resultado = avaliar(cand, repo, raiz, timeout_s=timeout_s)
            except Exception as exc:  # noqa: BLE001 — um candidato ruim não pode
                # derrubar a mineração inteira (E3.3): isto cobre falha antes
                # de `avaliar` entrar no try (ex.: Workspace.materialize com
                # base_commit inválido); dentro de `avaliar` já há a mesma
                # rede.
                resultado = _fechar(cand, time.perf_counter(), f"erro inesperado: {exc}"[:200])
            avaliados.append(resultado)
            verificados_por_faixa[faixa] += 1
            marca = "ACEITO " if resultado.aceito else "recusa "
            print(f"  [{faixa:<8} {i:>3}/{len(fila)}] {marca} {resultado.fix_commit[:8]} "
                  f"{resultado.segundos:>5.1f}s  {resultado.subject[:55]}")
            if resultado.aceito:
                aceitos_na_faixa += 1
                aceitos_por_faixa[faixa] += 1
                if resultado.f2p_arquivos > 2:
                    print(f"                atenção: f2p em {resultado.f2p_arquivos} arquivos "
                          f"— provável lote de correções, não um problema")
            else:
                chave = resultado.motivo[:60]
                motivos_rejeicao[chave] = motivos_rejeicao.get(chave, 0) + 1
                print(f"                {resultado.motivo[:100]}")
            if aceitos_na_faixa >= parar_em:
                print(f"  {faixa}: {parar_em} aceito(s) — parando de verificar esta faixa")
                break

    tempo_total_s = round(time.perf_counter() - inicio, 1)
    relatorio = {
        "seed_repo_id": repo.seed_repo_id,
        "commits_historico": total_commits,
        "candidatos_prefiltro": ({f: len(por_faixa[f]) for f in FAIXAS_EXECUTAVEIS}
                                 | {"fora": len(fora), "protegido": len(protegidos)}),
        "verificados_por_faixa": verificados_por_faixa,
        "aceitos_por_faixa": aceitos_por_faixa,
        "motivos_rejeicao": motivos_rejeicao,
        "tempo_total_s": tempo_total_s,
    }
    return avaliados, relatorio


def escrever_relatorio_md(relatorios: list[dict], destino: Path) -> None:
    """Gera `mined-v2/RELATORIO.md` com as contagens por repositório e faixa."""
    linhas = [
        "# Relatório de mineração — mined-v2",
        "",
        "Gerado por `scripts/mine_tasks.py`. Números vêm só desta rodada;",
        "veja `mined-v2/<repo>.json` para o detalhe candidato a candidato.",
        "",
        "| repositório | commits no histórico | pré-filtro grande | pré-filtro média | "
        "pré-filtro pequena | pré-filtro fora | pré-filtro protegido | verificados grande | "
        "verificados média | verificados pequena | aceitos grande | aceitos média | "
        "aceitos pequena | tempo (s) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in relatorios:
        cp, vp, ap = r["candidatos_prefiltro"], r["verificados_por_faixa"], r["aceitos_por_faixa"]
        linhas.append(
            f"| {r['seed_repo_id']} | {r['commits_historico']} | {cp['grande']} | {cp['media']} | "
            f"{cp['pequena']} | {cp['fora']} | {cp.get('protegido', 0)} | {vp['grande']} | "
            f"{vp['media']} | {vp['pequena']} | "
            f"{ap['grande']} | {ap['media']} | {ap['pequena']} | {r['tempo_total_s']} |"
        )

    linhas += ["", "## Motivos de rejeição por repositório", ""]
    for r in relatorios:
        linhas.append(f"### {r['seed_repo_id']}")
        if not r["motivos_rejeicao"]:
            linhas.append("(nenhuma rejeição — todos os verificados foram aceitos)")
        for motivo, n in sorted(r["motivos_rejeicao"].items(), key=lambda kv: -kv[1]):
            linhas.append(f"- {n}x — {motivo}")
        linhas.append("")

    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def reclassificar(repo: SeedRepoSpec, caminho: Path) -> dict:
    """
    Recalcula fonte/linhas/módulos/faixa/toca_protegido de TODOS os
    candidatos já registrados em `caminho` (um `mined-v2/<repo>.json`),
    só com git (numstat/diff) — sem reexecutar suíte nenhuma.

    Corrige três defeitos que a revisão do autor achou nos aceitos do
    mined-v2 (E3.3): arquivo apagado inflando `arquivos_fonte`/
    `linhas_fonte` (pygments 2c463c68); arquivo fora do `source_dir`
    contando como fonte (idem); falta de piso de linhas na média (peewee
    b8a336d0). `aceito`/`verificado`/`fail_to_pass`/`segundos` são
    preservados tal como a suíte os deixou — a reclassificação não muda
    se o oráculo discrimina — EXCETO quando o candidato passa a
    `toca_protegido=True`: a referência ficou irreprodutível pelo agente
    (tqdm e4d97426, altera `pyproject.toml`) e o candidato é forçado a
    `aceito=False`, `fail_to_pass=[]`, não importa o que a suíte tinha
    dito antes.

    Devolve um resumo: quantos candidatos, quantos mudaram de faixa,
    quantos passaram a `toca_protegido` e quantos destes estavam aceitos.
    """
    dados = json.loads(caminho.read_text())
    mudaram_faixa = 0
    novos_protegidos = 0
    protegidos_que_eram_aceitos = 0

    for registro in dados:
        sha = registro["fix_commit"]
        subject = registro["subject"]
        faixa_antiga = registro["faixa"]

        bruto = _git("--git-dir", str(repo.mirror_path), "show", "--no-merges", "-M",
                     "--format=", "--name-status", sha)
        entradas = _parse_name_status([l for l in bruto.split("\n") if l.strip()])
        cls = _classificar_status(repo, entradas)
        campos = _medir(repo, sha, subject, cls)

        registro.update(campos)
        registro["altera_testes_existentes"] = campos["testes_modificados"] > 0

        if campos["faixa"] != faixa_antiga:
            mudaram_faixa += 1

        if campos["toca_protegido"]:
            novos_protegidos += 1
            if registro.get("aceito"):
                protegidos_que_eram_aceitos += 1
            registro["aceito"] = False
            registro["motivo"] = "referência toca arquivo protegido"
            registro["fail_to_pass"] = []
            registro["f2p_arquivos"] = 0

    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "seed_repo_id": repo.seed_repo_id,
        "candidatos": len(dados),
        "mudaram_faixa": mudaram_faixa,
        "novos_protegidos": novos_protegidos,
        "protegidos_que_eram_aceitos": protegidos_que_eram_aceitos,
    }


def relatorio_de_json(repo: SeedRepoSpec, caminho: Path) -> dict:
    """
    Reconstrói o dicionário de relatório (mesmo formato do que `minerar`
    devolve) a partir de um `mined-v2/<repo>.json` já gravado — usado
    depois de `reclassificar`, que só atualiza campos, sem rodar
    `minerar`/`avaliar` de novo.
    """
    dados = json.loads(caminho.read_text())
    _, total_commits = levantar_candidatos(repo)  # só a contagem do histórico, sem suíte

    candidatos_prefiltro = {
        f: sum(1 for c in dados if c["faixa"] == f and not c.get("toca_protegido"))
        for f in FAIXAS_EXECUTAVEIS
    }
    candidatos_prefiltro["fora"] = sum(
        1 for c in dados if c["faixa"] == "fora" and not c.get("toca_protegido"))
    candidatos_prefiltro["protegido"] = sum(1 for c in dados if c.get("toca_protegido"))

    verificados_por_faixa = {
        f: sum(1 for c in dados if c["faixa"] == f and c["verificado"]) for f in FAIXAS_EXECUTAVEIS
    }
    aceitos_por_faixa = {
        f: sum(1 for c in dados if c["faixa"] == f and c["aceito"]) for f in FAIXAS_EXECUTAVEIS
    }
    motivos_rejeicao: dict[str, int] = {}
    for c in dados:
        if c["verificado"] and not c["aceito"]:
            chave = c["motivo"][:60]
            motivos_rejeicao[chave] = motivos_rejeicao.get(chave, 0) + 1

    return {
        "seed_repo_id": repo.seed_repo_id,
        "commits_historico": total_commits,
        "candidatos_prefiltro": candidatos_prefiltro,
        "verificados_por_faixa": verificados_por_faixa,
        "aceitos_por_faixa": aceitos_por_faixa,
        "motivos_rejeicao": motivos_rejeicao,
        "tempo_total_s": round(sum(c["segundos"] for c in dados), 1),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Minera candidatos a tarefa do E1")
    p.add_argument("seed_repo_id", nargs="?", choices=sorted(SEED_REPOS))
    p.add_argument("--all", action="store_true")
    p.add_argument("--max-verificar-por-faixa", type=int, default=30,
                   help="Teto de commits verificados por execução, por faixa")
    p.add_argument("--parar-em", type=int, default=12,
                   help="Para de verificar uma faixa ao atingir este número de aceitos")
    p.add_argument("--desde", default=None,
                   help="Data ISO ou commit; limita o histórico varrido a partir daí")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--out", type=Path, default=Path("mined-v2"))
    p.add_argument("--reclassificar", action="store_true",
                   help="Não minera de novo: só recalcula fonte/faixa dos candidatos já em "
                        "--out (git, sem suíte) e regrava os *.json e o RELATORIO.md")
    args = p.parse_args()

    if not args.all and not args.seed_repo_id:
        p.error("informe um repo-semente ou --all")

    alvos = sorted(SEED_REPOS) if args.all else [args.seed_repo_id]
    args.out.mkdir(parents=True, exist_ok=True)

    if args.reclassificar:
        relatorios = []
        for seed_repo_id in alvos:
            repo = get_seed_repo(seed_repo_id)
            caminho = args.out / f"{seed_repo_id}.json"
            if not caminho.exists():
                print(f"\n{seed_repo_id}: pulado — {caminho} não existe")
                continue
            resumo = reclassificar(repo, caminho)
            print(f"\n{seed_repo_id}: {resumo['candidatos']} candidatos recalculados, "
                  f"{resumo['mudaram_faixa']} mudaram de faixa, "
                  f"{resumo['novos_protegidos']} passaram a toca_protegido "
                  f"({resumo['protegidos_que_eram_aceitos']} deles estavam aceitos)")
            relatorios.append(relatorio_de_json(repo, caminho))
        if relatorios:
            relatorio_md = args.out / "RELATORIO.md"
            escrever_relatorio_md(relatorios, relatorio_md)
            print(f"\n  -> {relatorio_md}")
        return

    raiz = args.out / ".workspaces"
    raiz.mkdir(exist_ok=True)

    total: list[Candidato] = []
    relatorios: list[dict] = []
    for seed_repo_id in alvos:
        repo = get_seed_repo(seed_repo_id)
        if not repo.mirror_path.exists() or not repo.has_venv:
            print(f"\n{seed_repo_id}: pulado — rode scripts/setup_mirror.py {seed_repo_id}")
            continue
        avaliados, relatorio = minerar(
            repo, max_verificar_por_faixa=args.max_verificar_por_faixa,
            parar_em=args.parar_em, timeout_s=args.timeout, desde=args.desde, raiz=raiz,
        )
        destino = args.out / f"{seed_repo_id}.json"
        destino.write_text(
            json.dumps([asdict(c) | {"f2p_arquivos": c.f2p_arquivos} for c in avaliados],
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        total += avaliados
        relatorios.append(relatorio)
        print(f"  -> {destino}")

    if relatorios:
        relatorio_md = args.out / "RELATORIO.md"
        escrever_relatorio_md(relatorios, relatorio_md)
        print(f"  -> {relatorio_md}")

    aceitos = [c for c in total if c.aceito]
    print(f"\n{'─' * 70}")
    print(f"{len(aceitos)} aceitos de {sum(1 for c in total if c.verificado)} verificados "
          f"({len(total)} candidatos registrados, incluindo os fora de faixa)")
    for faixa in FAIXAS_EXECUTAVEIS:
        na_faixa = [c for c in aceitos if c.faixa == faixa]
        por_repo = ", ".join(
            f"{r}={sum(1 for c in na_faixa if c.seed_repo_id == r)}" for r in alvos
        )
        print(f"  {faixa:<7} {len(na_faixa):>3}   ({por_repo})")


if __name__ == "__main__":
    main()

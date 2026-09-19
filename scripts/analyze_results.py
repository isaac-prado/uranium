#!/usr/bin/env python3
"""
Análise pareada dos `result.json`: as sete métricas do estudo.

Lê todo `result.json` sob as raízes dadas, aplica os portões de admissão da
seção 3 de `docs/tcc/03-metricas.md`, agrega por (tarefa, braço) tomando a
mediana das repetições e emite as sete métricas da seção 2, com teste de
sinal exato e Wilcoxon exato, reportando a faixa ao lado de cada par.

O desenho é 12 tarefas × 2 braços × 3 repetições. A unidade de análise é a
TAREFA: a repetição k de um braço e a k do outro rodam com a mesma semente e
formam um par, e o valor de uma tarefa num braço é a mediana das repetições.
A comparação é sempre `orchestration` menos `single-agent`.

Sem `scipy`: os dois testes são exatos, por enumeração, e ficam em funções
puras neste mesmo arquivo (`teste_sinal`, `wilcoxon`) para poderem ser
importadas pelos testes.

Uso:

    uv run python scripts/analyze_results.py runs/ --markdown
    uv run python scripts/analyze_results.py runs/ --json analise.json

Nenhuma chamada de rede. Nenhum número que não venha de arquivo.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any, Iterable, Sequence

RAIZ = Path(__file__).resolve().parent.parent
EVENT_SCHEMA = RAIZ / "harness" / "schema" / "event.schema.json"

BRACOS = ("single-agent", "orchestration")
REFERENCIA, COMPARADO = BRACOS          # diferença = COMPARADO − REFERENCIA

# Acima disso a enumeração de 2^n sinais deixa de ser barata. O desenho tem
# 12 tarefas; a folga existe só para não estourar em uso indevido.
MAX_N_ENUMERACAO = 20


# =====================================================================
# Testes exatos (funções puras, sem dependência externa)
# =====================================================================


@dataclass
class Teste:
    """Resultado de um teste pareado exato."""

    nome: str
    n: int                              # pares efetivamente usados (sem empates)
    n_empates: int                      # pares descartados por diferença zero
    estatistica: float | None
    p: float | None                     # bilateral
    mediana_diferencas: float | None
    detalhe: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "nome": self.nome, "n": self.n, "n_empates": self.n_empates,
            "estatistica": self.estatistica, "p": self.p,
            "mediana_diferencas": self.mediana_diferencas, "detalhe": self.detalhe,
        }


def teste_sinal(diferencas: Sequence[float]) -> Teste:
    """
    Teste de sinal binomial exato bilateral.

    Só conta o SINAL de cada diferença; empates (diferença zero) saem da
    conta e são reportados. Sob H0 cada sinal é cara ou coroa, então

        p = 2 · Σ_{k=0..min(n+, n−)} C(n, k) / 2^n,   limitado a 1.

    `estatistica` é o número de diferenças positivas (favoráveis ao braço
    comparado, `orchestration`).
    """
    positivos = sum(1 for d in diferencas if d > 0)
    negativos = sum(1 for d in diferencas if d < 0)
    empates = sum(1 for d in diferencas if d == 0)
    n = positivos + negativos

    mediana = statistics.median(diferencas) if diferencas else None
    if n == 0:
        return Teste("sinal exato bilateral", 0, empates, None, None, mediana,
                     "sem pares discordantes")

    k = min(positivos, negativos)
    cauda = sum(math.comb(n, i) for i in range(k + 1))
    p = min(1.0, 2 * cauda / (2 ** n))
    return Teste("sinal exato bilateral", n, empates, float(positivos), p, mediana,
                 f"{positivos} positivas, {negativos} negativas")


def postos_medios(valores: Sequence[float]) -> list[float]:
    """Postos de 1 a n, com posto médio dentro de cada grupo de empate."""
    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    postos = [0.0] * len(valores)
    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and valores[ordem[j + 1]] == valores[ordem[i]]:
            j += 1
        media = (i + j) / 2 + 1          # postos 1-indexados
        for k in range(i, j + 1):
            postos[ordem[k]] = media
        i = j + 1
    return postos


def wilcoxon(diferencas: Sequence[float]) -> Teste:
    """
    Wilcoxon signed-rank pareado, exato e bilateral, por enumeração.

    Diferenças zero são descartadas (regra de Wilcoxon). Os módulos das
    restantes recebem postos médios em caso de empate. Sob H0 cada posto
    entra com sinal + ou − com probabilidade 1/2, então o p exato é a fração
    das 2^n atribuições de sinal cuja soma dos postos positivos se afasta da
    média tanto quanto a observada. Enumerar sobre os postos REAIS (com as
    médias dos empates) é o que trata o empate corretamente: a distribuição
    nula usada é a do conjunto de postos que de fato ocorreu.

    `estatistica` é W = min(W+, W−).
    """
    usadas = [float(d) for d in diferencas if d != 0]
    empates = len(diferencas) - len(usadas)
    n = len(usadas)
    mediana = statistics.median(diferencas) if diferencas else None

    if n == 0:
        return Teste("Wilcoxon exato bilateral", 0, empates, None, None, mediana,
                     "todas as diferenças nulas")
    if n > MAX_N_ENUMERACAO:
        raise ValueError(
            f"enumeração exata só até n={MAX_N_ENUMERACAO}; recebido n={n}"
        )

    postos = postos_medios([abs(d) for d in usadas])
    w_mais = sum(p for p, d in zip(postos, usadas) if d > 0)
    total = sum(postos)
    w_menos = total - w_mais
    alvo = total / 2
    desvio = abs(w_mais - alvo)

    extremos = 0
    for sinais in product((0, 1), repeat=n):
        s = sum(p for p, bit in zip(postos, sinais) if bit)
        if abs(s - alvo) >= desvio - 1e-9:
            extremos += 1
    p = min(1.0, extremos / (2 ** n))

    return Teste("Wilcoxon exato bilateral", n, empates, min(w_mais, w_menos), p, mediana,
                 f"W+={w_mais:g}, W-={w_menos:g}")


# =====================================================================
# Leitura dos runs e portões de admissão
# =====================================================================


@dataclass
class Run:
    """Um `result.json` com o que a análise precisa saber dele."""

    path: Path
    dados: dict[str, Any]
    task_id: str
    arm: str | None
    repetition: int | None
    faixa: str
    motivos: list[str] = field(default_factory=list)   # vazio = admitido

    @property
    def admitido(self) -> bool:
        return not self.motivos

    @property
    def run_id(self) -> str:
        return str(self.dados.get("run_id") or self.path.parent.name)

    def numero(self, caminho: str) -> float | None:
        """Lê um campo aninhado ('cost.tokens_total') como número, ou None."""
        no: Any = self.dados
        for parte in caminho.split("."):
            if not isinstance(no, dict) or parte not in no:
                return None
            no = no[parte]
        if isinstance(no, bool):
            return float(no)
        if isinstance(no, (int, float)):
            return float(no)
        return None


def find_results(raizes: Iterable[Path]) -> list[Path]:
    """Mesmo padrão de descoberta de `scripts/context_accounting.py`."""
    achados: list[Path] = []
    for raiz in raizes:
        if (raiz / "result.json").exists():
            achados.append(raiz / "result.json")
        elif raiz.is_file() and raiz.name == "result.json":
            achados.append(raiz)
        else:
            achados.extend(sorted(raiz.rglob("result.json")))
    vistos: set[Path] = set()
    unicos: list[Path] = []
    for p in achados:
        chave = p.resolve()
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(p)
    return unicos


def _validador_eventos():
    """Validador do esquema de evento, se `jsonschema` estiver disponível."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None
    if not EVENT_SCHEMA.exists():
        return None
    return Draft202012Validator(json.loads(EVENT_SCHEMA.read_text(encoding="utf-8")))


def checar_trilha(caminho: Path, validador: Any) -> list[str]:
    """
    Portão (3): a trilha valida contra o esquema e tem um único `run_end`.

    Sem `jsonschema` instalado, valida o mínimo verificável sem ele: uma
    linha, um objeto JSON, e um único `run_end`.
    """
    motivos: list[str] = []
    run_end = 0
    linhas_invalidas: list[int] = []
    erros_schema: list[str] = []

    for i, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), start=1):
        if not linha.strip():
            continue
        try:
            evento = json.loads(linha)
        except json.JSONDecodeError:
            linhas_invalidas.append(i)
            continue
        if not isinstance(evento, dict):
            linhas_invalidas.append(i)
            continue
        if evento.get("event_type") == "run_end":
            run_end += 1
        if validador is not None and len(erros_schema) < 3:
            for erro in validador.iter_errors(evento):
                erros_schema.append(f"linha {i}: {erro.message}")
                break

    if linhas_invalidas:
        motivos.append(f"events.jsonl com linha não-JSON ({len(linhas_invalidas)}: "
                       f"{linhas_invalidas[:3]})")
    if erros_schema:
        motivos.append("events.jsonl não valida contra o esquema (" + "; ".join(erros_schema) + ")")
    if run_end != 1:
        motivos.append(f"events.jsonl com {run_end} evento(s) run_end, esperado exatamente 1")
    # Sem `jsonschema` instalado só foi possível validar o mínimo (uma linha,
    # um objeto JSON, um único `run_end`); isso não reprova por si.
    return motivos


def portoes_de_admissao(dados: dict[str, Any], run_dir: Path, validador: Any) -> list[str]:
    """
    Seção 3 de 03-metricas.md. Devolve a lista de motivos de NÃO admissão.

    (1) toda chamada atendida pelo provedor pinado;
    (2) avaliação com rede isolada nas três suítes do oráculo;
    (3) trilha válida com um único `run_end`, quando existe ao lado.
    """
    motivos: list[str] = []

    prov = dados.get("provenance") or {}
    pedido = prov.get("provider_requested")
    servidos = prov.get("providers_served")
    if not isinstance(servidos, list) or not servidos:
        motivos.append("provenance.providers_served vazio: nenhum provedor registrado")
    elif pedido is None:
        motivos.append("provenance.provider_requested ausente: pino não verificável")
    else:
        divergentes = sorted({s for s in servidos if s != pedido})
        if divergentes:
            motivos.append(
                f"provedor divergente do pino: pedido {pedido!r}, servido(s) "
                + ", ".join(repr(d) for d in divergentes)
            )

    oraculo = dados.get("oracle") or {}
    sem_isolamento = [
        suite for suite in ("f2p", "p2p", "regression")
        if not (oraculo.get(suite) or {}).get("network_isolated", False)
    ]
    if sem_isolamento:
        motivos.append("avaliação sem rede isolada em: " + ", ".join(sem_isolamento))

    trilha = run_dir / "events.jsonl"
    if trilha.exists():
        motivos.extend(m for m in checar_trilha(trilha, validador) if m)

    return motivos


def faixa_da_tarefa(dados: dict[str, Any], tasks_dir: Path, cache: dict[str, str]) -> str:
    """`faixa` do result.json; senão de tasks/<id>/task.json; senão '?'."""
    direta = dados.get("faixa")
    if isinstance(direta, str) and direta:
        return direta
    task_id = str(dados.get("task_id") or "")
    if task_id in cache:
        return cache[task_id]
    arquivo = tasks_dir / task_id / "task.json"
    valor = "?"
    if arquivo.exists():
        try:
            spec = json.loads(arquivo.read_text(encoding="utf-8"))
            if isinstance(spec.get("faixa"), str) and spec["faixa"]:
                valor = spec["faixa"]
        except json.JSONDecodeError:
            valor = "?"
    cache[task_id] = valor
    return valor


def carregar_runs(raizes: list[Path], tasks_dir: Path) -> list[Run]:
    validador = _validador_eventos()
    cache: dict[str, str] = {}
    runs: list[Run] = []
    for caminho in find_results(raizes):
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            runs.append(Run(
                path=caminho, dados={}, task_id="?", arm=None, repetition=None,
                faixa="?", motivos=[f"result.json ilegível: {exc}"],
            ))
            continue
        runs.append(Run(
            path=caminho, dados=dados,
            task_id=str(dados.get("task_id") or "?"),
            arm=dados.get("arm"),
            repetition=dados.get("repetition"),
            faixa=faixa_da_tarefa(dados, tasks_dir, cache),
            motivos=portoes_de_admissao(dados, caminho.parent, validador),
        ))
    return runs


# =====================================================================
# Agregação por (tarefa, braço)
# =====================================================================

# Grandezas numéricas agregadas por mediana das repetições.
GRANDEZAS = (
    "cost.tokens_total",
    "cost.cost_usd",
    "cost.llm_calls",
    "cost.tool_calls",
    "cost.wall_seconds",
    "quality.cc_mean_delta",
)


@dataclass
class Celula:
    """Uma tarefa num braço: a mediana das repetições admitidas."""

    task_id: str
    arm: str
    faixa: str
    repeticoes: list[int | None]
    resolvidas: int
    valores: dict[str, float | None]

    @property
    def n_reps(self) -> int:
        return len(self.repeticoes)

    @property
    def fracao_resolvida(self) -> float:
        return self.resolvidas / self.n_reps if self.n_reps else 0.0

    @property
    def resolvida(self) -> bool:
        """
        Mediana de 0/1 sobre as repetições, isto é, maioria estrita.

        Com 3 repetições coincide com a mediana. Com número par de
        repetições admitidas a mediana pode dar 0,5; aí o desempate é para
        baixo (não resolvida), que é a leitura conservadora.
        """
        return self.fracao_resolvida > 0.5

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id, "arm": self.arm, "faixa": self.faixa,
            "repeticoes": self.repeticoes, "n_reps": self.n_reps,
            "resolvidas": self.resolvidas,
            "fracao_resolvida": self.fracao_resolvida,
            "resolvida": self.resolvida,
            "valores": self.valores,
        }


def _mediana(valores: list[float | None]) -> float | None:
    presentes = [v for v in valores if v is not None]
    return statistics.median(presentes) if presentes else None


def agregar(runs: list[Run]) -> dict[tuple[str, str], Celula]:
    """Agrupa os runs admitidos por (task_id, arm) e tira a mediana."""
    grupos: dict[tuple[str, str], list[Run]] = {}
    for r in runs:
        if r.admitido and r.arm in BRACOS:
            grupos.setdefault((r.task_id, r.arm), []).append(r)

    celulas: dict[tuple[str, str], Celula] = {}
    for (task_id, arm), lista in grupos.items():
        lista.sort(key=lambda r: (r.repetition is None, r.repetition or 0))
        celulas[(task_id, arm)] = Celula(
            task_id=task_id, arm=arm, faixa=lista[0].faixa,
            repeticoes=[r.repetition for r in lista],
            resolvidas=sum(1 for r in lista if r.dados.get("resolved") is True),
            valores={g: _mediana([r.numero(g) for r in lista]) for g in GRANDEZAS},
        )
    return celulas


def pares_quebrados(runs: list[Run]) -> list[dict[str, Any]]:
    """
    Repetição em que um braço foi admitido e o outro não.

    A repetição k de um braço e a k do outro rodam com a mesma semente e
    formam um par; se um dos dois cai num portão, o par deixa de existir.
    """
    por_chave: dict[tuple[str, int | None], dict[str, Run]] = {}
    for r in runs:
        if r.arm in BRACOS:
            por_chave.setdefault((r.task_id, r.repetition), {})[r.arm] = r

    quebrados: list[dict[str, Any]] = []
    for (task_id, rep), lado in sorted(por_chave.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        estados = {arm: (lado[arm].admitido if arm in lado else None) for arm in BRACOS}
        if all(e is True for e in estados.values()):
            continue
        quebrados.append({
            "task_id": task_id, "repetition": rep,
            "single-agent": ("ausente" if estados[REFERENCIA] is None
                             else "admitido" if estados[REFERENCIA] else "não admitido"),
            "orchestration": ("ausente" if estados[COMPARADO] is None
                              else "admitido" if estados[COMPARADO] else "não admitido"),
        })
    return quebrados


# =====================================================================
# As sete métricas
# =====================================================================


def _par(celulas: dict[tuple[str, str], Celula], task_id: str) -> tuple[Celula, Celula] | None:
    a = celulas.get((task_id, REFERENCIA))
    b = celulas.get((task_id, COMPARADO))
    return (a, b) if a and b else None


def _tarefas(celulas: dict[tuple[str, str], Celula]) -> list[str]:
    return sorted({t for t, _ in celulas})


def resolvida_por_ambos(celulas: dict[tuple[str, str], Celula], task_id: str) -> bool:
    par = _par(celulas, task_id)
    return bool(par) and par[0].resolvida and par[1].resolvida


def metricas(celulas: dict[tuple[str, str], Celula], runs: list[Run]) -> dict[str, Any]:
    """As sete métricas da seção 2 de 03-metricas.md, nesta ordem."""
    tarefas = _tarefas(celulas)
    admitidos = [r for r in runs if r.admitido and r.arm in BRACOS]
    saida: dict[str, Any] = {}

    # ---- 1. Efetividade: taxa de resolução -------------------------------
    pareadas = [t for t in tarefas if _par(celulas, t)]
    por_braco_resolvidas = {
        arm: sum(1 for t in tarefas
                 if (c := celulas.get((t, arm))) is not None and c.resolvida)
        for arm in BRACOS
    }
    difs_resolucao: list[float] = []
    detalhe_1: list[dict[str, Any]] = []
    for t in pareadas:
        a, b = _par(celulas, t)          # type: ignore[misc]
        d = b.fracao_resolvida - a.fracao_resolvida
        difs_resolucao.append(d)
        detalhe_1.append({
            "task_id": t, "faixa": a.faixa,
            REFERENCIA: a.fracao_resolvida, COMPARADO: b.fracao_resolvida, "diferenca": d,
        })
    saida["1_efetividade"] = {
        "nome": "Taxa de resolução", "campo": "resolved", "unidade": "proporção",
        "melhor": "maior",
        "por_braco": {
            arm: {
                "tarefas_resolvidas": por_braco_resolvidas[arm],
                "tarefas_com_dado": sum(1 for t in tarefas if (t, arm) in celulas),
                "execucoes_resolvidas": sum(1 for r in admitidos
                                            if r.arm == arm and r.dados.get("resolved") is True),
                "execucoes": sum(1 for r in admitidos if r.arm == arm),
            }
            for arm in BRACOS
        },
        "teste": teste_sinal(difs_resolucao).as_dict(),
        "por_tarefa": detalhe_1,
    }

    # ---- 2, 3 e 5: testes pareados sobre grandezas ------------------------
    def pareado(chave: str, campo: str, nome: str, unidade: str, melhor: str,
                censura: str, papel: str) -> dict[str, Any]:
        """
        `censura` = 'resolvidas_por_ambos' (métricas 2 e 3) ou 'ambos_com_valor'
        (métrica 5, exploratória).
        """
        usadas: list[str] = []
        difs: list[float] = []
        detalhe: list[dict[str, Any]] = []
        excluidas: list[dict[str, str]] = []
        for t in tarefas:
            par = _par(celulas, t)
            if par is None:
                falta = REFERENCIA if (t, REFERENCIA) not in celulas else COMPARADO
                excluidas.append({"task_id": t, "faixa": (celulas.get((t, REFERENCIA))
                                                          or celulas[(t, COMPARADO)]).faixa,
                                  "motivo": f"sem dado admitido no braço {falta}"})
                continue
            a, b = par
            if censura == "resolvidas_por_ambos" and not (a.resolvida and b.resolvida):
                quem = [arm for arm, c in ((REFERENCIA, a), (COMPARADO, b)) if not c.resolvida]
                excluidas.append({"task_id": t, "faixa": a.faixa,
                                  "motivo": "não resolvida por " + " e ".join(quem)})
                continue
            va, vb = a.valores.get(campo), b.valores.get(campo)
            if va is None or vb is None:
                falta = REFERENCIA if va is None else COMPARADO
                excluidas.append({"task_id": t, "faixa": a.faixa,
                                  "motivo": f"{campo} ausente no braço {falta}"})
                continue
            usadas.append(t)
            difs.append(vb - va)
            detalhe.append({"task_id": t, "faixa": a.faixa,
                            REFERENCIA: va, COMPARADO: vb, "diferenca": vb - va})
        return {
            "nome": nome, "campo": campo, "unidade": unidade, "melhor": melhor, "papel": papel,
            "censura": censura,
            "por_braco": {
                arm: {
                    "mediana_das_tarefas_usadas": statistics.median(
                        [celulas[(t, arm)].valores[campo] for t in usadas]) if usadas else None,
                    "mediana_de_todas_as_tarefas": _mediana(
                        [c.valores[campo] for (t, a2), c in celulas.items() if a2 == arm]),
                }
                for arm in BRACOS
            },
            "tarefas_usadas": usadas,
            "tarefas_excluidas": excluidas,
            "teste": wilcoxon(difs).as_dict(),
            "por_tarefa": detalhe,
        }

    saida["2_custo"] = pareado(
        "2", "cost.tokens_total", "Custo computacional", "tokens", "menor",
        "resolvidas_por_ambos", "primária inferencial")
    saida["2_custo"]["acompanham"] = {
        campo: {
            arm: _mediana([c.valores[campo] for (t, a2), c in celulas.items()
                           if a2 == arm and t in saida["2_custo"]["tarefas_usadas"]])
            for arm in BRACOS
        }
        for campo in ("cost.cost_usd", "cost.llm_calls")
    }
    saida["3_tempo"] = pareado(
        "3", "cost.wall_seconds", "Tempo até a solução", "segundos", "menor",
        "resolvidas_por_ambos", "secundária")
    saida["5_qualidade"] = pareado(
        "5", "quality.cc_mean_delta", "Variação da complexidade",
        "pontos de complexidade", "menor", "ambos_com_valor", "secundária exploratória")

    # ---- 4. Confiabilidade: consistência ---------------------------------
    consistencia: dict[str, Any] = {}
    for arm in BRACOS:
        cels = [c for (t, a2), c in celulas.items() if a2 == arm]
        ao_menos_uma = [c for c in cels if c.resolvidas > 0]
        sempre = [c for c in ao_menos_uma if c.resolvidas == c.n_reps]
        consistencia[arm] = {
            "tarefas_resolvidas_ao_menos_uma_vez": len(ao_menos_uma),
            "tarefas_resolvidas_em_todas_as_repeticoes": len(sempre),
            "proporcao": (len(sempre) / len(ao_menos_uma)) if ao_menos_uma else None,
            "tarefas": sorted(c.task_id for c in sempre),
        }
    saida["4_consistencia"] = {
        "nome": "Consistência", "campo": "resolved por repetição", "unidade": "proporção",
        "melhor": "maior", "teste": None, "por_braco": consistencia,
    }

    # ---- 6. Autonomia: conclusão sem corte -------------------------------
    autonomia: dict[str, Any] = {}
    for arm in BRACOS:
        exec_arm = [r for r in admitidos if r.arm == arm]
        motivos = [(r.dados.get("process") or {}).get("stop_reason") for r in exec_arm]
        por_corte = [m for m in motivos if isinstance(m, str) and m.startswith("budget:")]
        sem_motivo = [m for m in motivos if m is None]
        autonomia[arm] = {
            "execucoes": len(exec_arm),
            "encerradas_por_corte": len(por_corte),
            "sem_stop_reason": len(sem_motivo),
            "proporcao_sem_corte": ((len(exec_arm) - len(por_corte)) / len(exec_arm))
            if exec_arm else None,
            "motivos_de_corte": sorted(set(por_corte)),
        }
    saida["6_autonomia"] = {
        "nome": "Conclusão sem corte", "campo": "process.stop_reason", "unidade": "proporção",
        "melhor": "maior", "teste": None, "por_braco": autonomia,
    }

    # ---- 7. Integridade: violações ---------------------------------------
    integridade: dict[str, Any] = {}
    for arm in BRACOS:
        exec_arm = [r for r in admitidos if r.arm == arm]
        integridade[arm] = {
            "execucoes": len(exec_arm),
            "cheat_critical_count": sum(int((r.dados.get("cheat") or {}).get("critical_count") or 0)
                                        for r in exec_arm),
            "execucoes_com_trapaca_critica": sum(
                1 for r in exec_arm if int((r.dados.get("cheat") or {}).get("critical_count") or 0) > 0),
            "resolved_blocked_by_cheat": sum(
                1 for r in exec_arm if r.dados.get("resolved_blocked_by_cheat") is True),
            "tool_denials": sum(int((r.dados.get("process") or {}).get("tool_denials") or 0)
                                for r in exec_arm),
        }
    saida["7_integridade"] = {
        "nome": "Violações",
        "campo": "cheat.critical_count; resolved_blocked_by_cheat; process.tool_denials",
        "unidade": "contagem por braço", "melhor": "menor", "teste": None,
        "por_braco": integridade,
    }

    return saida


# =====================================================================
# Relatório
# =====================================================================


def _num(v: Any, casas: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return f"{v:.{casas}f}"
    return str(v)


def _p(teste: dict[str, Any] | None) -> str:
    if not teste or teste.get("p") is None:
        return "—"
    return f"{teste['p']:.4f}"


def markdown(analise: dict[str, Any]) -> str:
    m = analise["metricas"]
    celulas = analise["celulas"]
    out: list[str] = []

    out.append(f"## As sete métricas ({REFERENCIA} × {COMPARADO})\n")
    out.append("Diferença e sinal do teste sempre `orchestration` − `single-agent`. "
               "Unidade de análise: a tarefa; valor por tarefa e braço: mediana das repetições admitidas.\n")
    out.append(f"| # | Métrica | {REFERENCIA} | {COMPARADO} | Teste | estatística | n | p |")
    out.append("|---|---|---|---|---|---|---|---|")

    e = m["1_efetividade"]
    linha_ref = f"{e['por_braco'][REFERENCIA]['tarefas_resolvidas']}/{e['por_braco'][REFERENCIA]['tarefas_com_dado']}"
    linha_cmp = f"{e['por_braco'][COMPARADO]['tarefas_resolvidas']}/{e['por_braco'][COMPARADO]['tarefas_com_dado']}"
    t = e["teste"]
    out.append(f"| 1 | Taxa de resolução (tarefas) | {linha_ref} | {linha_cmp} | "
               f"{t['nome']} | {_num(t['estatistica'])} | {t['n']} | {_p(t)} |")

    for chave, rotulo in (("2_custo", "Custo (tokens, mediana)"),
                          ("3_tempo", "Tempo (s, mediana)"),
                          ("5_qualidade", "Δ complexidade (mediana)")):
        d = m[chave]
        t = d["teste"]
        out.append(
            f"| {chave[0]} | {rotulo} | "
            f"{_num(d['por_braco'][REFERENCIA]['mediana_das_tarefas_usadas'])} | "
            f"{_num(d['por_braco'][COMPARADO]['mediana_das_tarefas_usadas'])} | "
            f"{t['nome']} | {_num(t['estatistica'])} | {t['n']} | {_p(t)} |"
        )

    c = m["4_consistencia"]["por_braco"]
    out.append(
        f"| 4 | Consistência | "
        f"{c[REFERENCIA]['tarefas_resolvidas_em_todas_as_repeticoes']}/{c[REFERENCIA]['tarefas_resolvidas_ao_menos_uma_vez']} | "
        f"{c[COMPARADO]['tarefas_resolvidas_em_todas_as_repeticoes']}/{c[COMPARADO]['tarefas_resolvidas_ao_menos_uma_vez']} | "
        f"descritivo | — | — | — |"
    )
    a = m["6_autonomia"]["por_braco"]
    out.append(
        f"| 6 | Conclusão sem corte | "
        f"{a[REFERENCIA]['execucoes'] - a[REFERENCIA]['encerradas_por_corte']}/{a[REFERENCIA]['execucoes']} | "
        f"{a[COMPARADO]['execucoes'] - a[COMPARADO]['encerradas_por_corte']}/{a[COMPARADO]['execucoes']} | "
        f"descritivo | — | — | — |"
    )
    i = m["7_integridade"]["por_braco"]
    out.append(
        f"| 7 | Violações (crít.; bloq.; negações) | "
        f"{i[REFERENCIA]['cheat_critical_count']}; {i[REFERENCIA]['resolved_blocked_by_cheat']}; {i[REFERENCIA]['tool_denials']} | "
        f"{i[COMPARADO]['cheat_critical_count']}; {i[COMPARADO]['resolved_blocked_by_cheat']}; {i[COMPARADO]['tool_denials']} | "
        f"descritivo | — | — | — |"
    )
    out.append("")

    custo = m["2_custo"]["acompanham"]
    out.append(
        f"Acompanham a métrica 2, sobre as mesmas tarefas: custo em dólares "
        f"(mediana) {_num(custo['cost.cost_usd'][REFERENCIA], 6)} × {_num(custo['cost.cost_usd'][COMPARADO], 6)}; "
        f"chamadas ao modelo (mediana) {_num(custo['cost.llm_calls'][REFERENCIA])} × "
        f"{_num(custo['cost.llm_calls'][COMPARADO])}.\n"
    )

    # ------------------------------------------------ tabela por tarefa
    out.append("## Por tarefa\n")
    out.append("| tarefa | faixa | resolvida (frações) | tokens | Δ tokens | segundos | Δ s | Δ CC |")
    out.append("|---|---|---|---|---|---|---|---|")
    tarefas = sorted({c["task_id"] for c in celulas})
    for t in tarefas:
        ca = next((c for c in celulas if c["task_id"] == t and c["arm"] == REFERENCIA), None)
        cb = next((c for c in celulas if c["task_id"] == t and c["arm"] == COMPARADO), None)
        faixa = (ca or cb or {}).get("faixa", "?")

        def campo(c: dict[str, Any] | None, nome: str) -> float | None:
            return c["valores"].get(nome) if c else None

        def delta(nome: str) -> str:
            va, vb = campo(ca, nome), campo(cb, nome)
            return _num(vb - va) if va is not None and vb is not None else "—"

        frac = (f"{_num(ca['fracao_resolvida'], 2) if ca else '—'} × "
                f"{_num(cb['fracao_resolvida'], 2) if cb else '—'}")
        out.append(
            f"| `{t}` | {faixa} | {frac} | "
            f"{_num(campo(ca, 'cost.tokens_total'))} × {_num(campo(cb, 'cost.tokens_total'))} | "
            f"{delta('cost.tokens_total')} | "
            f"{_num(campo(ca, 'cost.wall_seconds'))} × {_num(campo(cb, 'cost.wall_seconds'))} | "
            f"{delta('cost.wall_seconds')} | {delta('quality.cc_mean_delta')} |"
        )
    out.append("")

    # ------------------------------------------------ censura
    out.append("## Censura declarada\n")
    for chave in ("2_custo", "3_tempo", "5_qualidade"):
        d = m[chave]
        out.append(f"**{chave[0]}. {d['nome']}** — censura `{d['censura']}`; "
                   f"{len(d['tarefas_usadas'])} tarefa(s) no teste.")
        if d["tarefas_excluidas"]:
            for x in d["tarefas_excluidas"]:
                out.append(f"- `{x['task_id']}` (faixa {x['faixa']}): {x['motivo']}")
        else:
            out.append("- nenhuma tarefa excluída.")
        out.append("")

    # ------------------------------------------------ admissão
    out.append("## Portões de admissão\n")
    nao = analise["nao_admitidos"]
    out.append(f"{analise['runs_admitidos']} de {analise['runs_encontrados']} execução(ões) admitida(s).\n")
    if nao:
        out.append("| run | tarefa | braço | rep | motivo |")
        out.append("|---|---|---|---|---|")
        for r in nao:
            out.append(f"| `{r['run_id']}` | {r['task_id']} | {r['arm']} | {r['repetition']} | "
                       + "; ".join(r["motivos"]) + " |")
        out.append("")
    quebrados = analise["pares_quebrados"]
    if quebrados:
        out.append("Pares quebrados (a repetição de mesmo índice existe e é admitida num braço só):\n")
        out.append("| tarefa | rep | single-agent | orchestration |")
        out.append("|---|---|---|---|")
        for q in quebrados:
            out.append(f"| `{q['task_id']}` | {q['repetition']} | {q['single-agent']} | {q['orchestration']} |")
        out.append("")
    else:
        out.append("Nenhum par quebrado.\n")

    return "\n".join(out)


def analisar(raizes: list[Path], tasks_dir: Path) -> dict[str, Any]:
    runs = carregar_runs(raizes, tasks_dir)
    celulas = agregar(runs)
    return {
        "raizes": [str(r) for r in raizes],
        "tasks_dir": str(tasks_dir),
        "referencia": REFERENCIA,
        "comparado": COMPARADO,
        "runs_encontrados": len(runs),
        "runs_admitidos": sum(1 for r in runs if r.admitido),
        "nao_admitidos": [
            {"run_id": r.run_id, "path": str(r.path), "task_id": r.task_id,
             "arm": r.arm, "repetition": r.repetition, "motivos": r.motivos}
            for r in runs if not r.admitido
        ],
        "pares_quebrados": pares_quebrados(runs),
        "celulas": [c.as_dict() for c in sorted(celulas.values(), key=lambda c: (c.task_id, c.arm))],
        "metricas": metricas(celulas, runs),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Análise pareada dos result.json: as sete métricas do estudo")
    parser.add_argument("raizes", nargs="+", type=Path,
                        help="Diretórios de run ou raízes com runs")
    parser.add_argument("--tasks-dir", type=Path, default=Path("tasks"),
                        help="Onde procurar tasks/<id>/task.json para a faixa (padrão: tasks/)")
    parser.add_argument("--json", type=Path, help="Grava a análise completa em JSON")
    parser.add_argument("--markdown", action="store_true", help="Imprime as tabelas em Markdown")
    args = parser.parse_args(argv)

    analise = analisar(list(args.raizes), args.tasks_dir)
    if args.json:
        args.json.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown or not args.json:
        if not analise["runs_encontrados"]:
            print("Nenhum result.json encontrado nas raízes dadas.")
            return 1
        print(markdown(analise))
    return 0


if __name__ == "__main__":
    sys.exit(main())

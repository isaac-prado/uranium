"""
ValidatorAgent — corretude por execução real, não por julgamento de texto.

Regra estrutural deste nó: `is_valid` só pode ser verdadeiro se a suíte
tiver saído com exit code 0. O LLM pode REBAIXAR o veredito (apontar que a
mudança resolve o teste mas viola a intenção), nunca promovê-lo. Sem essa
monotonicidade o pipeline volta a medir a auto-avaliação do modelo em vez
de medir corretude.

Isto é o tratamento ES 3.0: o agente usa execução para decidir se refina.
A corretude reportada no TCC continua vindo do harness externo, com
oráculos que o agente nunca viu.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from src import config
from src.feedback import COMPARACAO_DE_SAIDAS, COMPARACAO_POR_BLOCO, comparacao_de_saidas, comparacao_por_bloco
from src.runtime import RunContext
from src.schemas.intent import StructuredIntentV2, intent_as_text
from src.schemas.plan import (
    STATUS_ABANDONADA,
    STATUS_ADIADA,
    STATUS_EM_ANDAMENTO,
    STATUS_FEITA,
    STATUS_PENDENTE,
)
from src.schemas.validation_result import ValidationResult
from src.state import WorkflowState, parse_intent
from src.structured_llm import StructuredOutputError, invoke_structured
from src.tools.base import truncate
from src.enunciado import anotar_comparacoes, reparar_blocos
from src.tools.exec import executar_isolado, reverter_protegidos, run_pytest, run_python
from src.verificacao import ENCONTRADA as ENCONTRADA_
from src.verificacao import NAO_ENCONTRADA as NAO_ENCONTRADA_
from src.verificacao import NAO_VERIFICAVEL as NAO_VERIFICAVEL_
from src.verificacao import comparar_saidas, faltantes, verificaveis

SYSTEM_PROMPT = """\
Você é um revisor técnico. A suíte de testes JÁ PASSOU — isto não está em
discussão e você não pode reverter esse fato.

Sua única pergunta é: a mudança resolve o problema descrito na tarefa, ou
apenas faz os testes passarem por acidente (código morto, caso especial
grudado, comportamento não relacionado alterado)?

Retorne JSON com is_valid, issues, suggestions, covered_criteria e
missing_criteria. Use is_valid=false apenas se houver lacuna real frente à
tarefa.
"""

# Rodada 5 (decisão 34, parte final, e 35): com a comparação automática das
# saídas esperadas no prompt, o revisor final recebe a regra "não
# verificável não reprova". Só entra com `REVIEW_COMPARE=advisory` (rodada
# 5) ou `strict`; "off" reproduz a rodada 4 literalmente e "neutral"
# (decisão 41, rodada 6) entrega as linhas de comparação sem a regra: na
# rodada 5 ela deslocou o erro do revisor para aprovações no primeiro ciclo
# (11, 5 erradas; rodada 4: 7 e 1), inclusive aprovando com critérios que
# ele mesmo listou como não cobertos (sqlite-utils-0003 rep02 e rep03).
REGRA_COMPARACAO = """
Quando houver uma comparação automática das saídas esperadas com a execução
dos exemplos: uma saída esperada NÃO encontrada, com o bloco executado, é
lacuna real; uma saída marcada como não verificável não prova nada e não é
motivo de reprovação.
"""


def system_prompt_revisao() -> str:
    """Prompt do revisor final, com a regra da comparação só em `advisory` e `strict`."""
    return SYSTEM_PROMPT + (REGRA_COMPARACAO if config.REVIEW_COMPARE in ("advisory", "strict") else "")


# Revisão de sub-tarefa (decisão 33): o mesmo revisor, com a pergunta
# restrita à sub-tarefa corrente do plano. Rodada 4 (`SUBTASK_CHECK=llm`);
# na rodada 5 o veredito é determinístico (`_verificar_subtarefa`).
SYSTEM_PROMPT_SUBTAREFA = """\
Você é o revisor técnico de uma equipe de agentes de IA. O desenvolvedor
trabalhou numa sub-tarefa de um plano. Decida só isto: a sub-tarefa atual está
concluída? Use os critérios dela, a saída real dos exemplos executados e o
diff. Um exemplo que não rodou por falta de contexto (import ou variável de
outro bloco) não prova nada: não conte isso como falha do código.

Retorne JSON com is_valid (true = sub-tarefa concluída), issues, suggestions,
covered_criteria e missing_criteria, restritos a esta sub-tarefa. Não julgue o
resto do plano.
"""


def semantic_review_enabled() -> bool:
    """Revisão semântica complementar; desligável para isolar o efeito."""
    return os.getenv("SEMANTIC_REVIEW", "true").strip().lower() in ("1", "true", "yes")


def validator(state: WorkflowState) -> dict[str, Any]:
    """Roda a suíte de verdade e, só se ela passar, complementa com revisão."""
    ctx = RunContext.from_state(state)

    with ctx.telemetry.node("validator", agent_role="validator"):
        report = run_pytest(ctx.workspace, timeout_s=ctx.test_timeout_s)
        ctx.telemetry.emit_test_run(report)

        # Diff vazio não pode ser sucesso. A suíte visível já está verde no
        # commit-base — o teste que discrimina é oculto —, então "testes passam"
        # é satisfeito por não fazer nada. No piloto foi exatamente isso: o
        # agente explorou 10 turnos, não escreveu nada, a suíte passou e o run
        # foi dado como válido com patch.diff de zero byte.
        houve_mudanca = bool(ctx.workspace.changed_files())

        semantic: ValidationResult | None = None
        execucoes: list[dict[str, Any]] = []
        if report.green and semantic_review_enabled():
            execucoes = _executar_reproducao(state, ctx)
            comparacoes = _comparar_esperadas(state, execucoes)
            if config.REVIEW_COMPARE == "strict" and faltantes(comparacoes):
                # Modo estrito (guardado, decisão 35): saída esperada
                # verificável ausente reprova sem consultar o revisor.
                semantic = ValidationResult(
                    is_valid=False, issues=[COMPARACAO_DE_SAIDAS, *comparacao_de_saidas(comparacoes)],
                )
                ctx.telemetry.emit_validation(
                    semantic, executions=execucoes, comparisons=comparacoes, deterministic=True,
                )
            else:
                try:
                    semantic = ctx.invoke_structured(
                        ValidationResult,
                        [
                            ("system", system_prompt_revisao()),
                            ("user", _build_review_prompt(state, ctx, execucoes, comparacoes)),
                        ],
                    )
                    # Revisor coerente (decisão 32): aprovar listando critérios
                    # não cobertos é contradição; o harness rebaixa, nunca promove.
                    coagida = (
                        config.REVIEW_STRICT == "on" and semantic.is_valid and bool(semantic.missing_criteria)
                    )
                    if coagida:
                        semantic = semantic.model_copy(update={"is_valid": False})
                    # Rodada 8, modo guardado (decisão 48): aprovar com linha
                    # esperada do enunciado NÃO encontrada em exemplo executado
                    # é contradição com um fato; o harness rebaixa com as
                    # próprias linhas como motivo, nunca promove.
                    faltam_por_exemplo = _linhas_nao_encontradas(execucoes)
                    if config.BLOCK_EXPECTED == "strict" and semantic.is_valid and faltam_por_exemplo:
                        semantic = semantic.model_copy(update={
                            "is_valid": False,
                            "issues": [*semantic.issues, COMPARACAO_POR_BLOCO, *faltam_por_exemplo],
                        })
                        coagida = True
                    # O veredito vai à telemetria: na fumaça D de 09/10 o revisor
                    # reprovou um patch com a suíte verde e nada registrava o motivo.
                    ctx.telemetry.emit_validation(
                        semantic, executions=execucoes, comparisons=comparacoes, strict_coerced=coagida,
                    )
                except StructuredOutputError as exc:
                    # Falha de conformidade não pode reprovar código que passa nos
                    # testes; fica registrada e o veredito segue pela execução.
                    ctx.telemetry.emit_error(exc)

        # O LLM só rebaixa. Nunca promove.
        is_valid = report.green and houve_mudanca and (semantic is None or semantic.is_valid)

        # Planejador (decisão 33): se a tarefa não fechou, confere a sub-tarefa
        # corrente e avança o plano.
        avanco: dict[str, Any] = {}
        if config.PLANNER == "on" and state.get("plan") and not is_valid:
            avanco = _avancar_plano(
                state, ctx, houve_mudanca=houve_mudanca, suite_verde=report.green, execucoes=execucoes,
            )
    plano_aberto = avanco.get("subtask_current") is not None or bool(avanco.get("replan_requested"))

    # O teto de reprovações vale para o laço "developer diz que terminou,
    # revisor discorda". Quando o developer chegou aqui pelo teto do ciclo
    # (decisão 25), ou quando o plano ainda tem sub-tarefas (decisão 33), a
    # reprovação é feedback do ponto de checagem, não uma submissão
    # recusada, e não conta.
    submeteu = not str(state.get("stop_reason") or "").startswith("cycle:") and not plano_aberto

    return avanco | {
        "test_report": report.model_dump(),
        "is_valid": is_valid,
        "validation_result": semantic.model_dump() if semantic else None,
        "validation_iteration_count": state.get("validation_iteration_count", 0) + 1,
        # Conta só a reprovação do revisor sobre código verde e alterado, que é
        # o único motivo de volta com teto (ver `route_after_validator`).
        "semantic_rejections": state.get("semantic_rejections", 0)
        + int(
            submeteu
            and report.green and houve_mudanca and semantic is not None and not semantic.is_valid
        ),
    }


_CERCA = re.compile(r"^```([\w+-]*)\s*\n(.*?)\n?```\s*$", re.S)
MAX_SAIDA_EXECUCAO_CHARS = 2_000


def _codigo_python(bloco: str) -> str | None:
    """Conteúdo de um bloco de `reproduction` se for Python (cerca `python` ou sem cerca)."""
    m = _CERCA.match(bloco.strip())
    if not m:
        return bloco.strip()
    linguagem = (m.group(1) or "").lower()
    return m.group(2) if linguagem in ("", "python", "py", "python3") else None


# Rodada 7 (decisão 44): bloco de reprodução que é linha de comando. Só
# programas conhecidos, sem shell: o Python do venv da tarefa (`python`,
# `python3`) ou um script de console instalado nesse venv (`sqlite-utils`).
_PROGRAMAS_PYTHON = ("python", "python3")
# Operadores de shell que, como token separado, indicariam pipe, redirecionamento
# ou encadeamento; dentro de aspas (`python -c "a; b"`) não são operadores.
_OPERADORES_SHELL = {"|", "||", "&", "&&", ";", ">", ">>", "<", "<<", "2>", "2>>", "&>"}
_CERCAS_SHELL = ("", "bash", "sh", "shell", "console", "zsh", "text")


def _comando_shell(bloco: str, python_bin: str) -> list[list[str]] | None:
    """
    Comandos (argv prontos) de um bloco de reprodução escrito como linha de
    comando, ou None quando o bloco não é isso. Com `$ ` no início das
    linhas, só essas são comandos e as demais são saída copiada; sem o
    prefixo, toda linha precisa ser um comando reconhecido. Linha com
    metacaractere de shell, ou programa fora do venv da tarefa, invalida o
    bloco inteiro: é melhor não rodar do que rodar outra coisa.
    """
    m = _CERCA.match(bloco.strip())
    if m and (m.group(1) or "").lower() not in _CERCAS_SHELL:
        return None
    texto = m.group(2) if m else bloco
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not linhas:
        return None
    com_prompt = [l for l in linhas if l.startswith("$ ")]
    candidatas = [l[2:].strip() for l in com_prompt] if com_prompt else linhas
    bin_dir = Path(python_bin).parent
    comandos: list[list[str]] = []
    for linha in candidatas:
        try:
            argv = shlex.split(linha)
        except ValueError:
            return None
        if not argv or any(tok in _OPERADORES_SHELL or tok.startswith(("`", "$(")) for tok in argv):
            return None
        programa = argv[0]
        if programa in _PROGRAMAS_PYTHON:
            argv[0] = python_bin
        elif "/" not in programa and (bin_dir / programa).is_file():
            argv[0] = str(bin_dir / programa)
        else:
            return None
        comandos.append(argv)
    return comandos or None


def _executar_comandos(ctx: RunContext, comandos: list[list[str]], timeout_s: int) -> str:
    """Roda os comandos em sequência no workspace, como `run_python` roda um trecho: mesma guarda de arquivo protegido."""
    ws = ctx.workspace
    partes: list[str] = []
    for argv in comandos:
        mostrado = " ".join(shlex.quote(a) for a in [Path(argv[0]).name, *argv[1:]])
        antes = set(ws.protected_touched())
        inicio = time.perf_counter()
        try:
            proc = executar_isolado(ws, argv, timeout_s=timeout_s)
            saida, codigo, estourou = (proc.stdout + proc.stderr).strip(), proc.returncode, False
        except subprocess.TimeoutExpired:
            saida, codigo, estourou = "", -1, True
        duracao = time.perf_counter() - inicio
        violados = reverter_protegidos(ws, antes)
        if violados:
            partes.append(f"$ {mostrado}\nRECUSADO: o comando alterou arquivo protegido ({', '.join(violados)}). A alteração foi revertida.")
            break
        if estourou:
            partes.append(f"$ {mostrado}\nTIMEOUT: o comando excedeu {timeout_s}s e foi interrompido.")
            break
        partes.append(f"$ {mostrado}\nexit={codigo} em {duracao:.2f}s\n{saida or '(sem saída)'}")
    return "\n".join(partes)


# Rodada 6 (decisão 42): rótulo do bloco que não compila sozinho. Vai ao
# revisor e ao developer no lugar de um traceback de SyntaxError, que na
# rodada 5 foi lido como falha do código.
BLOCO_NAO_COMPILA = "(não executado: o bloco não compila como Python e não é evidência; {erro})"


def _blocos_que_nao_compilam(codigos: dict[int, str | None]) -> dict[int, str]:
    """Índice → erro dos blocos Python que não compilam sozinhos (`compile`, sem executar)."""
    erros: dict[int, str] = {}
    for i, codigo in codigos.items():
        if not codigo or not codigo.strip():
            continue
        try:
            compile(codigo, f"<bloco {i}>", "exec")
        except SyntaxError as exc:  # IndentationError é subclasse
            erros[i] = f"{type(exc).__name__} na linha {exc.lineno}: {exc.msg}"
    return erros


def _executar_reproducao(
    state: WorkflowState, ctx: RunContext, *, indices: list[int] | None = None
) -> list[dict[str, Any]]:
    """
    Revisor que executa (decisão 29): roda os blocos de reprodução da intent
    v2 no código atual e devolve as saídas reais. Com `REVIEW_EXECUTION=off`,
    ou com intent v1 (sem `reproduction`), não faz nada e o revisor segue
    lendo só o diff, como na coleta principal.
    """
    intent = parse_intent(state)
    if config.REVIEW_EXECUTION == "off" or not isinstance(intent, StructuredIntentV2):
        return []
    # Decisão 44 (rodada 7): bloco que é linha de comando roda como processo
    # e fica fora da cadeia Python (não é Python).
    python_bin = ctx.workspace.spec.seed_repo.python_bin
    shell = ({i: _comando_shell(b, python_bin) for i, b in enumerate(intent.reproduction, 1)}
             if config.REPRODUCTION_SHELL == "on" else {})
    shell = {i: c for i, c in shell.items() if c}
    codigos = {i: (None if i in shell else _codigo_python(b)) for i, b in enumerate(intent.reproduction, 1)}
    # Rodada 8 (decisão 48): a cópia do refinador é consertada pelo enunciado
    # (cerca perdida; bloco que não compila trocado pelo mais parecido).
    enunciado = str(state.get("raw_request") or "")
    fontes: dict[int, str] = {}
    if config.REPRODUCTION_SOURCE == "statement":
        codigos, fontes = reparar_blocos(codigos, enunciado)
    # Decisão 42 (rodada 6): o bloco que não compila sozinho não roda e não
    # entra na cadeia acumulada; na rodada 5 (tomlkit-0001) cinco blocos
    # eram texto TOML e o SyntaxError do 2º apagava a saída dos seguintes.
    nao_compila = _blocos_que_nao_compilam(codigos) if config.REPRODUCTION_COMPILE_CHECK == "on" else {}
    acumulado = config.REVIEW_EXECUTION == "cumulative"
    selecionados = (list(codigos) if indices is None
                    else [i for i in indices if i in codigos])
    saidas: list[dict[str, Any]] = []
    for i in selecionados:
        codigo = codigos[i]
        if i in shell:
            saida = _executar_comandos(ctx, shell[i], timeout_s=min(60, ctx.test_timeout_s))
            saidas.append({"bloco": i, "executado": True, "shell": True, "acumulado": False,
                           "saida": truncate(saida, MAX_SAIDA_EXECUCAO_CHARS)})
            continue
        if codigo is None or not codigo.strip():
            saidas.append({"bloco": i, "executado": False, "saida": "(não executado: não é Python)"})
            continue
        if i in nao_compila:
            saidas.append({"bloco": i, "executado": False, "nao_compila": True,
                           "saida": BLOCO_NAO_COMPILA.format(erro=nao_compila[i])})
            continue
        if acumulado:
            # Decisão 34: o bloco i roda precedido dos blocos 1..i-1, porque
            # os enunciados encadeiam (o segundo usa o `db` do primeiro).
            anteriores = [codigos[j] for j in range(1, i)
                          if codigos[j] and codigos[j].strip() and j not in nao_compila]
            codigo = "\n\n".join(anteriores + [codigo])
        saida = run_python(ctx.workspace, codigo, timeout_s=min(60, ctx.test_timeout_s))
        registro: dict[str, Any] = {"bloco": i, "executado": True, "acumulado": acumulado and i > 1,
                                    "saida": truncate(saida, MAX_SAIDA_EXECUCAO_CHARS)}
        if i in fontes:
            registro["fonte"] = fontes[i]
        saidas.append(registro)
    # Rodada 8 (decisão 48): saída esperada do enunciado amarrada ao exemplo
    # de que cada bloco é cópia ou pedaço, comparada linha a linha com a
    # junção das saídas dos blocos daquele exemplo.
    if config.BLOCK_EXPECTED in ("statement", "strict"):
        anotar_comparacoes(saidas, codigos, enunciado)
    return saidas


# ------------------------------------------- comparação de saídas (rodada 5)


def _esperadas_apontadas(state: WorkflowState) -> list[tuple[int, str]]:
    """
    Saídas esperadas que entram na comparação da revisão final: as que o
    plano aponta (união das sub-tarefas, decisão 36); sem plano, ou com um
    plano que não apontou nenhuma, todas as da intent.
    """
    intent = parse_intent(state)
    if not isinstance(intent, StructuredIntentV2) or not intent.expected_outputs:
        return []
    n = len(intent.expected_outputs)
    plano = state.get("plan") or {}
    indices = sorted({int(i) for s in plano.get("subtasks") or [] for i in s.get("expected") or []
                      if 1 <= int(i) <= n})
    if not indices:
        indices = list(range(1, n + 1))
    # Decisão 39: o que o código original já produzia fica fora.
    fora = _saidas_na_base(state)
    return [(i, intent.expected_outputs[i - 1]) for i in indices if i not in fora]


def _saidas_na_base(state: WorkflowState) -> set[int]:
    """Índices das saídas esperadas que o código original já produzia (planejador, decisão 39)."""
    return {int(i) for i in ((state.get("plan") or {}).get("saidas_na_base") or [])}


def _comparar_esperadas(state: WorkflowState, execucoes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Comparação automática (decisão 35); vazia com `REVIEW_COMPARE=off` ou
    sem execução. Com plano, cada saída esperada é confrontada só com os
    blocos da sub-tarefa que a aponta, como em `_verificar_subtarefa`
    (correção após a fumaça da rodada 6, 16/10/2026): confrontada com a
    saída de todos os blocos, uma saída esperada apontada por sub-tarefa
    sem bloco de reprodução saía sempre "NÃO encontrada" (sqlite-utils-0003:
    7 falsos negativos por revisão, e o revisor reprovando por eles). Sem
    plano, ou com plano que não aponta nada, todas as esperadas contra
    todas as execuções, como antes.
    """
    if config.REVIEW_COMPARE == "off" or not execucoes:
        return []
    intent = parse_intent(state)
    if not isinstance(intent, StructuredIntentV2) or not intent.expected_outputs:
        return []
    n = len(intent.expected_outputs)
    fora = _saidas_na_base(state)
    subtasks = [s for s in (state.get("plan") or {}).get("subtasks") or [] if s.get("expected")]
    if not subtasks:
        return comparar_saidas(_esperadas_apontadas(state), execucoes)
    ordem_estado = {ENCONTRADA_: 2, NAO_ENCONTRADA_: 1, NAO_VERIFICAVEL_: 0}
    por_indice: dict[int, dict[str, Any]] = {}
    for s in subtasks:
        blocos = {int(i) for i in s.get("reproduction") or []}
        esperadas = [(int(i), intent.expected_outputs[int(i) - 1]) for i in s.get("expected") or []
                     if 1 <= int(i) <= n and int(i) not in fora]
        execs = [e for e in execucoes if e.get("bloco") in blocos]
        for c in comparar_saidas(esperadas, execs):
            atual = por_indice.get(c["indice"])
            # A mesma saída apontada por duas sub-tarefas fica com o melhor estado.
            if atual is None or ordem_estado[c["estado"]] > ordem_estado[atual["estado"]]:
                por_indice[c["indice"]] = c
    return [por_indice[i] for i in sorted(por_indice)]


def _build_review_prompt(
    state: WorkflowState, ctx: RunContext, execucoes: list[dict[str, Any]] | None = None,
    comparacoes: list[dict[str, Any]] | None = None,
) -> str:
    """Tarefa + diff efetivo, que é o artefato real produzido pelo agente."""
    intent = parse_intent(state)
    diff = ctx.workspace.diff()
    if len(diff) > 20_000:
        diff = diff[:20_000] + "\n[... diff truncado ...]"

    partes = [
        "Tarefa:",
        intent_as_text(intent),
        "",
        "Diff aplicado pelo agente (a suíte passou com ele):",
        diff or "(nenhuma alteração)",
    ]
    execucoes = _evidencias(execucoes or [])
    if execucoes:
        partes += ["", "Execução dos exemplos de reprodução sobre o código atual "
                       "(saída real, para comparar com as saídas esperadas da tarefa):"]
        for ex in execucoes:
            rotulo = f"[bloco {ex['bloco']}]" + (" (executado junto com os blocos anteriores)" if ex.get("acumulado") else "")
            partes += [rotulo, ex["saida"]]
        por_bloco = comparacao_por_bloco(execucoes)
        if por_bloco:
            partes += ["", COMPARACAO_POR_BLOCO, *por_bloco]
    # Decisão 41, após a fumaça da rodada 6: em `neutral` só as linhas com
    # fato (encontrada / NÃO encontrada) chegam ao revisor; "não verificável"
    # virava motivo de reprovação (tomlkit-0003: 8 reprovações citando-a).
    if comparacoes and config.REVIEW_COMPARE == "neutral":
        comparacoes = verificaveis(comparacoes)
    if comparacoes:
        partes += ["", COMPARACAO_DE_SAIDAS,
                   *(f"- {linha}" for linha in comparacao_de_saidas(comparacoes, ja_na_base=sorted(_saidas_na_base(state))))]
    return "\n".join(partes)


def _linhas_nao_encontradas(execucoes: list[dict[str, Any]]) -> list[str]:
    """Linhas da comparação por exemplo do enunciado com estado NÃO encontrada (rodada 8, modo strict)."""
    so_faltantes = [
        {**ex, "comparacao_enunciado": [c for c in ex.get("comparacao_enunciado") or [] if c.get("estado") == NAO_ENCONTRADA_]}
        for ex in execucoes
    ]
    return comparacao_por_bloco(so_faltantes)


def _evidencias(execucoes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Execuções que entram nos prompts de revisão. Com a decisão 42 ligada, o
    bloco que não executou (não é Python ou não compila) fica fora: na fumaça
    da rodada 6 o rótulo "não é evidência" foi citado como motivo de
    reprovação em 8 de 8 revisões da tomlkit-0003. O evento `validation`
    continua registrando todas as execuções, rótulos inclusive.
    """
    if config.REPRODUCTION_COMPILE_CHECK != "on":
        return execucoes
    return [e for e in execucoes if e.get("executado")]


# ------------------------------------------------------- plano (decisão 33)


def _proxima_subtarefa(status: list[dict[str, Any]]) -> int | None:
    """Sub-tarefa a atacar: a em andamento; senão a primeira pendente; senão uma adiada."""
    for s in status:
        if s["status"] == STATUS_EM_ANDAMENTO:
            return s["id"]
    for estado in (STATUS_PENDENTE, STATUS_ADIADA):
        for s in status:
            if s["status"] == estado:
                s["status"] = STATUS_EM_ANDAMENTO
                return s["id"]
    return None


def _build_subtask_review_prompt(
    state: WorkflowState, ctx: RunContext, sub: dict[str, Any], execucoes: list[dict[str, Any]]
) -> str:
    intent = parse_intent(state)
    criterios = [intent.acceptance_criteria[i - 1] for i in sub.get("criteria") or []
                 if 1 <= i <= len(intent.acceptance_criteria)]
    diff = ctx.workspace.diff()
    if len(diff) > 20_000:
        diff = diff[:20_000] + "\n[... diff truncado ...]"
    partes = [
        f"Sub-tarefa {sub.get('id')}: {sub.get('title', '')}",
        "O que fazer:", str(sub.get("objective", "")),
        f"Pronto quando: {sub.get('done_when', '')}",
    ]
    if criterios:
        partes += ["", "Critérios desta sub-tarefa:", *(f"- {c}" for c in criterios)]
    partes += ["", "Diff atual do workspace:", diff or "(nenhuma alteração)"]
    execucoes = _evidencias(execucoes or [])
    if execucoes:
        partes += ["", "Execução dos exemplos desta sub-tarefa sobre o código atual (saída real):"]
        for ex in execucoes:
            rotulo = f"[bloco {ex['bloco']}]" + (" (executado junto com os blocos anteriores)" if ex.get("acumulado") else "")
            partes += [rotulo, ex["saida"]]
        por_bloco = comparacao_por_bloco(execucoes)
        if por_bloco:
            partes += ["", COMPARACAO_POR_BLOCO, *por_bloco]
    return "\n".join(partes)


def _verificar_subtarefa(
    state: WorkflowState, ctx: RunContext, sub: dict[str, Any], *,
    houve_mudanca: bool, suite_verde: bool, execucoes: list[dict[str, Any]],
) -> tuple[bool | None, ValidationResult | None, list[dict[str, Any]]]:
    """
    Veredito determinístico da sub-tarefa (decisão 36, rodada 5), sem
    chamada ao modelo. Devolve (veredito, parecer, execuções); em
    `SUBTASK_CHECK=hybrid` (decisão 40, rodada 6) o veredito é None quando
    nada é verificável, e o chamador consulta o revisor de sub-tarefa com
    as mesmas execuções: a palavra do developer deixa de fechar sub-tarefa. Com a suíte verde e mudança no workspace: as saídas
    esperadas que o planejador apontou para a sub-tarefa são comparadas com
    a saída real dos blocos dela (a execução da revisão final é
    reaproveitada; os blocos só rodam de novo se ela não executou). Alguma
    verificável ausente → não feita, e o developer recebe a comparação;
    todas encontradas → feita; nenhuma verificável → vale a palavra do
    developer: feita se ele encerrou o ciclo por conta própria, não pelo
    teto. Suíte vermelha ou diff vazio → não feita, e o developer já recebe
    o motivo pelo feedback de sempre.
    """
    intent = parse_intent(state)
    blocos = [int(i) for i in sub.get("reproduction") or []]
    esperadas_intent = intent.expected_outputs if isinstance(intent, StructuredIntentV2) else []
    fora = _saidas_na_base(state)
    esperadas = [(int(i), esperadas_intent[int(i) - 1]) for i in sub.get("expected") or []
                 if 1 <= int(i) <= len(esperadas_intent) and int(i) not in fora]
    pronta_para_conferir = suite_verde and houve_mudanca
    execs = [e for e in execucoes if e.get("bloco") in blocos]
    if pronta_para_conferir and blocos and not execs:
        execs = _executar_reproducao(state, ctx, indices=blocos)
    comparacoes = comparar_saidas(esperadas, execs) if pronta_para_conferir else []

    if not pronta_para_conferir:
        base = "suite_vermelha" if not suite_verde else "sem_mudanca"
        concluida = False
    elif verificaveis(comparacoes):
        base = "comparacao"
        concluida = not faltantes(comparacoes)
    elif config.SUBTASK_CHECK == "hybrid" and semantic_review_enabled():
        # Decisão 40: nada verificável → o revisor de sub-tarefa decide.
        return None, None, execs
    else:
        base = "palavra_do_developer"
        concluida = str(state.get("stop_reason") or "") == "concluiu"

    issues: list[str] = []
    if not concluida and base == "comparacao":
        saida = "\n".join(str(e.get("saida", "")) for e in execs if e.get("executado"))
        issues = [COMPARACAO_DE_SAIDAS, *comparacao_de_saidas(comparacoes, saida=saida)]
    parecer = ValidationResult(is_valid=concluida, issues=issues)
    ctx.telemetry.emit_validation(
        parecer, executions=execs, scope="subtask", subtask=sub.get("id"),
        deterministic=True, basis=base, comparisons=comparacoes,
    )
    # Sem nada a dizer (teto do ciclo, suíte vermelha, diff vazio), nenhum
    # parecer volta ao developer: o feedback de sempre já explica.
    return concluida, (parecer if issues else None), execs


def _revisar_subtarefa_pelo_modelo(
    state: WorkflowState, ctx: RunContext, sub: dict[str, Any], execucoes_sub: list[dict[str, Any]],
    *, basis: str | None = None,
) -> tuple[bool, ValidationResult | None]:
    """
    Revisão de sub-tarefa pelo modelo (`SUBTASK_CHECK=llm`, rodada 4; em
    `hybrid`, rodada 6, só quando nenhuma saída esperada é verificável, com
    `basis="revisao_do_modelo"` no evento). Com `REVIEW_STRICT=on`, aprovar
    listando critérios não cobertos não fecha a sub-tarefa.
    """
    extras = {"basis": basis} if basis else {}
    try:
        parecer = ctx.invoke_structured(
            ValidationResult,
            [("system", SYSTEM_PROMPT_SUBTAREFA),
             ("user", _build_subtask_review_prompt(state, ctx, sub, execucoes_sub))],
        )
        if config.REVIEW_STRICT == "on" and parecer.is_valid and parecer.missing_criteria:
            parecer = parecer.model_copy(update={"is_valid": False})
        ctx.telemetry.emit_validation(
            parecer, executions=execucoes_sub, scope="subtask", subtask=sub.get("id"), **extras,
        )
        return parecer.is_valid, parecer
    except StructuredOutputError as exc:
        ctx.telemetry.emit_error(exc)
        return False, None


def _avancar_plano(
    state: WorkflowState, ctx: RunContext, *, houve_mudanca: bool,
    suite_verde: bool = True, execucoes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Confere a sub-tarefa corrente com os blocos de reprodução dela e avança o
    plano: feita → próxima; não feita → mais um ciclo, até o teto, depois
    adiada (uma vez) e abandonada. Plano esgotado com a tarefa aberta →
    pede replanejamento, enquanto houver cota.
    """
    plano = dict(state.get("plan") or {})
    subtasks: list[dict[str, Any]] = list(plano.get("subtasks") or [])
    status = [dict(s) for s in plano.get("status") or []]
    atual = state.get("subtask_current")
    parecer: ValidationResult | None = None

    sub = next((s for s in subtasks if s.get("id") == atual), None)
    linha = next((s for s in status if s.get("id") == atual), None)
    if sub is not None and linha is not None:
        concluida = False
        if config.SUBTASK_CHECK in ("deterministic", "hybrid"):
            veredito, parecer, execs = _verificar_subtarefa(
                state, ctx, sub, houve_mudanca=houve_mudanca, suite_verde=suite_verde,
                execucoes=execucoes or [],
            )
            if veredito is None:
                # Híbrido (decisão 40): nada verificável, suíte verde e diff
                # presente; o revisor de sub-tarefa decide com a execução feita.
                concluida, parecer = _revisar_subtarefa_pelo_modelo(
                    state, ctx, sub, execs, basis="revisao_do_modelo",
                )
            else:
                concluida = veredito
        elif houve_mudanca and semantic_review_enabled():
            execucoes_sub = _executar_reproducao(state, ctx, indices=list(sub.get("reproduction") or []))
            concluida, parecer = _revisar_subtarefa_pelo_modelo(state, ctx, sub, execucoes_sub)
        linha["ciclos"] = int(linha.get("ciclos", 0)) + 1
        if concluida:
            linha["status"] = STATUS_FEITA
        else:
            teto = config.SUBTASK_MAX_CYCLES * (2 if linha.get("adiada_antes") else 1)
            if linha["ciclos"] >= teto:
                linha["status"] = STATUS_ABANDONADA if linha.get("adiada_antes") else STATUS_ADIADA
                linha["adiada_antes"] = True
            else:
                linha["status"] = STATUS_EM_ANDAMENTO

    proximo = _proxima_subtarefa(status)
    replan = (proximo is None and not plano.get("esgotado")
              and int(state.get("replans", 0)) < config.PLANNER_MAX_REPLANS)
    plano["status"] = status
    if proximo is None and not replan:
        plano["esgotado"] = True
    ctx.telemetry.emit_plan({
        "evento": "avanco", "status": status, "subtask_current": proximo, "replan_requested": replan,
    })
    return {
        "plan": plano,
        "subtask_current": proximo,
        "subtask_review": parecer.model_dump() if (parecer is not None and proximo == atual) else None,
        "replan_requested": replan,
    }

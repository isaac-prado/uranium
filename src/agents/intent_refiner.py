"""IntentRefinerAgent - converte solicitação em linguagem natural em intent estruturada."""

from src import config
from src.runtime import RunContext
from src.schemas.intent import StructuredIntent, StructuredIntentV2
from src.state import WorkflowState

SYSTEM_PROMPT = """
Você é um especialista em Engenharia de Software 3.0.

Sua tarefa é transformar uma solicitação em linguagem natural
em uma representação estruturada da intenção de desenvolvimento.

Analise a solicitação e produza JSON com:
- context (string)
- goal (string)
- phases (array de strings)
- acceptance_criteria (array de strings)
- clarifications_needed (array de strings)
- is_ready (boolean)

Regras:
1. Se houver informação suficiente, defina is_ready=true.
2. Se houver ambiguidades relevantes, defina is_ready=false.
3. Liste perguntas em clarifications_needed.
4. Seja objetivo e técnico.
5. Se houver respostas de clarificação anteriores, incorpore-as na intent refinada.
"""


# Refinador v2 (decisão 28 do autor, 14/10/2026). A análise linha a linha do
# v1 (docs/tcc/15-refinador-analise.md) mostrou que ele resume: não tem campo
# para exemplos, manda "ser objetivo", nunca pergunta e, em 7 de 39 intents,
# manda escrever testes numa área protegida. O v2 enriquece: copia literalmente
# o que o enunciado traz, torna cada critério verificável e declara o ambiente.
SYSTEM_PROMPT_V2 = """\
Você é o refinador de especificação de uma equipe de agentes de IA que corrige
e evolui software. O desenvolvedor que vai escrever o código NÃO verá o
enunciado original: a sua saída é a única especificação que ele recebe.
Seu trabalho é enriquecer, organizar e facilitar. Nunca resumir.

Produza JSON com os campos: context, goal, reproduction, expected_outputs,
acceptance_criteria, phases, constraints, open_questions, clarifications_needed,
is_ready.

Regras:
1. Copie literalmente, sem reescrever nem abreviar, todo bloco de código,
   comando, tabela de entradas e saídas, valor esperado, mensagem de erro e
   nome de função, classe, método ou arquivo que o enunciado traz. Blocos de
   código e comandos vão em `reproduction`, um item por bloco, com o texto
   exato. Valores, saídas, tabelas e mensagens esperadas vão em
   `expected_outputs`, um item por caso, com os valores exatos.
2. Cada item de `acceptance_criteria` é verificável por execução: diz a
   chamada ou a entrada e o resultado esperado exato (valor, tipo, exceção
   com nome e mensagem). Não escreva critérios vagos como "funciona
   corretamente" ou "os casos passam". Todos os casos do enunciado viram
   critérios, na mesma ordem e numeração.
3. `goal` e `context` explicam o problema e o comportamento esperado em
   prosa, cobrindo todos os casos enumerados no enunciado.
4. `phases` é um plano de implementação: o que investigar, onde mexer e como
   verificar cada critério com execução (run_python sobre `reproduction`)
   antes de rodar a suíte.
5. `constraints` descreve o ambiente do desenvolvedor. Inclua sempre: a área
   de testes (`tests/`) é protegida e não pode ser escrita; não adicionar nem
   alterar testes; a suíte visível do repositório pode não cobrir o
   comportamento novo, então verificar o comportamento esperado com
   run_python sobre os exemplos de `reproduction` e `expected_outputs`; mais
   qualquer restrição que o enunciado traga.
6. Não invente requisitos, valores ou nomes que não estejam no enunciado. Se
   algo for ambíguo, registre em `open_questions` a leitura adotada e a
   alternativa, e siga com a leitura mais literal do enunciado. O usuário não
   está disponível: `clarifications_needed` fica vazio e `is_ready` é true.
7. Preserve o idioma e os termos do enunciado.
"""


def _versao() -> tuple[str, type[StructuredIntent]]:
    """Prompt e schema da versão configurada; lida como atributo do módulo, igual ao manifesto."""
    if config.INTENT_REFINER == "v2":
        return SYSTEM_PROMPT_V2, StructuredIntentV2
    return SYSTEM_PROMPT, StructuredIntent


def _build_user_prompt(state: WorkflowState) -> str:
    """Monta o prompt do usuário com contexto e clarificações."""
    raw_request = state["raw_request"]
    clarifications = state.get("clarification_responses") or []

    parts = [f"Solicitação do usuário:\n{raw_request}"]

    if clarifications:
        parts.append("\nRespostas de clarificação anteriores:")
        for item in clarifications:
            parts.append(f"- Pergunta: {item.get('question', '')}")
            parts.append(f"  Resposta: {item.get('answer', '')}")

    return "\n".join(parts)
def intent_refiner(state: WorkflowState) -> dict[str, object]:
    """Refina a solicitação em uma intent estruturada."""
    ctx = RunContext.from_state(state)

    prompt, schema = _versao()
    with ctx.telemetry.node("intent_refiner", agent_role="intent_refiner"):
        result = ctx.invoke_structured(
            schema,
            [
                ("system", prompt),
                ("user", _build_user_prompt(state)),
            ],
        )
        # A intent é tudo que o developer recebe da tarefa (CLAUDE.md); fica
        # registrada para a análise e para a ablação do refinador.
        ctx.telemetry.emit_intent(result)

    iteration_count = state.get("iteration_count", 0)
    if state.get("clarification_responses"):
        iteration_count += 1

    return {
        "intent": result.model_dump(),
        "clarifications_needed": result.clarifications_needed,
        "is_ready": result.is_ready,
        "iteration_count": iteration_count,
    }

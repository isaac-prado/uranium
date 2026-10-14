"""Schema da intenção estruturada produzida pelo IntentRefinerAgent."""

from pydantic import BaseModel, Field, field_validator


class StructuredIntent(BaseModel):
    """Representação estruturada da intenção de desenvolvimento."""

    context: str = Field(description="Contexto atual do sistema")
    goal: str = Field(description="Objetivo principal da solicitação")
    phases: list[str] = Field(description="Fases sugeridas de implementação")
    acceptance_criteria: list[str] = Field(
        description="Critérios de aceitação"
    )
    clarifications_needed: list[str] = Field(
        default_factory=list,
        description="Perguntas adicionais necessárias",
    )
    is_ready: bool = Field(
        description="Indica se a intent está pronta para desenvolvimento",
    )


# Chaves que só o refinador v2 preenche (decisão 28 do autor, 14/10/2026).
# A presença de qualquer uma delas no estado identifica uma intent v2.
V2_KEYS = ("reproduction", "expected_outputs", "constraints", "open_questions")


class StructuredIntentV2(StructuredIntent):
    """
    Intent do refinador v2: enriquece em vez de resumir.

    O developer do orchestration não vê o enunciado; esta estrutura é a única
    especificação que ele recebe. Por isso carrega, literalmente, os trechos
    de reprodução, as saídas esperadas e as restrições do ambiente que o v1
    descartava (docs/tcc/15-refinador-analise.md).
    """

    reproduction: list[str] = Field(
        default_factory=list,
        description="Blocos de código, comandos e exemplos do enunciado, copiados literalmente",
    )
    expected_outputs: list[str] = Field(
        default_factory=list,
        description="Saídas, valores, tabelas e mensagens esperadas do enunciado, copiados literalmente",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Restrições do ambiente de desenvolvimento e do enunciado",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Ambiguidades do enunciado, com a leitura adotada e a alternativa",
    )

    @field_validator(*V2_KEYS, mode="before")
    @classmethod
    def _achatar_listas(cls, valor):
        """
        O modelo às vezes devolve `reproduction` como lista de listas (um bloco
        por item, cada um partido em linhas) ou com itens vazios; isso matou a
        tomlkit-0003 rep01 da rodada 2 com StructuredOutputError antes do
        primeiro turno. Achata um nível e descarta vazios; o que não é texto
        continua inválido.
        """
        if not isinstance(valor, list):
            return valor
        itens = []
        for item in valor:
            if isinstance(item, list):
                partes = [x for x in item if isinstance(x, str)]
                if len(partes) != len(item):
                    return valor  # deixa o pydantic apontar o item inválido
                item = "\n".join(partes)
            if isinstance(item, str) and not item.strip():
                continue
            itens.append(item)
        return itens

    def to_markdown(self) -> str:
        """Texto que o developer e o revisor recebem no lugar do JSON."""
        partes = ["# Objetivo", self.goal.strip(), "", "# Contexto", self.context.strip()]
        if self.reproduction:
            partes += ["", "# Como reproduzir"]
            for bloco in self.reproduction:
                b = bloco.strip()
                partes += [b if b.startswith("```") else f"```\n{b}\n```", ""]
        if self.expected_outputs:
            partes += ["", "# Saídas e valores esperados", *(f"- {x.strip()}" for x in self.expected_outputs)]
        partes += ["", "# Critérios de aceitação",
                   *(f"{i}. {c.strip()}" for i, c in enumerate(self.acceptance_criteria, 1))]
        if self.phases:
            partes += ["", "# Plano", *(f"{i}. {f.strip()}" for i, f in enumerate(self.phases, 1))]
        if self.constraints:
            partes += ["", "# Restrições do ambiente", *(f"- {x.strip()}" for x in self.constraints)]
        if self.open_questions:
            partes += ["", "# Pontos em aberto (leitura adotada)", *(f"- {x.strip()}" for x in self.open_questions)]
        return "\n".join(partes).strip() + "\n"


def intent_as_text(intent: StructuredIntent) -> str:
    """Como a intent entra no prompt: v2 em markdown; v1 no JSON de sempre."""
    if isinstance(intent, StructuredIntentV2):
        return intent.to_markdown()
    return intent.model_dump_json(indent=2)

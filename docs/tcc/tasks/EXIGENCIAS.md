## Natureza deste documento

Estas são **exigências minhas, do autor do trabalho**, para que o projeto seja finalizado. Não são sugestões e não estão abertas a substituição por alternativa que pareça mais conveniente. Se um item for impossível como escrito, **pare e relate**, dizendo o que impede; não troque o item por outro.

Precedência: este documento vence o `BACKLOG.md`, o dossiê e qualquer plano anterior. As invariantes do `PROMPT_AUDITORIA.md` continuam valendo integralmente (oráculo, detector de trapaça, guarda de caminho, pino de provedor).

**Proibições que valem em todas as etapas.** Não altere o detector de trapaça, o oráculo, a guarda de caminho nem o pino de provedor. Não cite `docs/dossie-metodologico.html` como fonte de número: ele tem valores que não reproduzem, e a fonte única passa a ser `docs/tcc/01-inventario.md`. Não invente número: todo valor vem de arquivo, com o caminho ao lado. Pare no fim de cada etapa e espere minha aprovação.

---

## E0 — Verificação do stack (somente leitura, primeira etapa)

Preciso saber, com evidência `arquivo:linha`, o que este repositório realmente usa hoje. Produza `docs/tcc/05-stack.md` respondendo:

1. **O LangGraph ainda é usado?** Onde, em qual braço, e de que forma. Especificamente: o braço `orchestration` é um `StateGraph` compilado com nós e arestas condicionais de verdade, ou degenerou em chamadas sequenciais que só *parecem* um grafo? Mostre o grafo como ele é montado hoje, nó por nó e aresta por aresta. O braço `single-agent` passa pelo LangGraph também, ou tem caminho próprio?
2. **Versões.** O que está declarado em `pyproject.toml` e no lockfile para `langgraph` e `langchain`, e o que está efetivamente instalado.
3. **O LangSmith.** Confirme que foi removido do código e liste **todos** os lugares que ainda o anunciam (`pyproject.toml`, `src/agents/README.md`, `projeto.md`, `README.md`). O resumo da minha Nota 1 promete "instrumentado com LangSmith"; escreva o parágrafo de declaração dessa mudança para o texto do TCC, dizendo o que substituiu o LangSmith (telemetria JSONL própria) e por que isso é mais adequado para o estudo.
4. **Documentação que descreve arquitetura superada.** O `README.md` descreve papéis que não existem mais e cita `scripts/run_pipeline.py`, que não existe (contradição C5 do inventário). Liste tudo nessa classe. Não corrija ainda.
5. **O que o braço orquestrado tem de assimetria estrutural declarável:** `MAX_VALIDATION_ITERATIONS`, `MAX_CLARIFICATION_ITERATIONS`, `SEMANTIC_REVIEW`, e o fato de um turno contar só a chamada do developer (folgas F5, F6, F7 do inventário). Diga, para cada uma, se é consequência necessária da topologia ou escolha de implementação.

Pare.

---

## E1 — Fechar a conta dos tokens antes de qualquer experimento pago

**Exigência:** eu não aceito rodar a ablação do `intent_refiner` nem a coleta definitiva antes de saber, em número, de onde vem cada token do prompt. Custo zero, dados que já existem.

Construa o script de contabilidade de contexto. Para cada execução com instrumentação completa, reconstrua a composição do prompt **por turno e por categoria**: prompt de sistema, primeira mensagem entregue ao agente, saída de cada ferramenta separada por nome, mensagens do assistente, mensagens de feedback da suíte.

**Teste de completude, que é o ponto do exercício:** a soma reconstruída até o turno *n* tem de bater com o `tokens_prompt` medido no turno *n*. Relate a discrepância em porcentagem. Se não fechar, existe conteúdo não instrumentado, e achar isso é mais importante que o resto desta etapa.

Instrumente também, porque hoje ninguém mede: **o tamanho da primeira mensagem entregue ao agente que escreve código, em cada braço.** É o teste direto da hipótese de compressão do enunciado. Se o intent reescrito for maior que o enunciado cru, a hipótese cai sem precisar de ablação.

Entregue em `docs/tcc/06-contabilidade-contexto.md` a tabela por braço com a fração de cada categoria, e a conclusão de qual fonte explica o crescimento de contexto 2,3× maior do braço orquestrado.

Pare.

---

## E2 — Equalizar o que não é arquitetura, e declarar o que é

**Corrija**, com teste de igualdade literal que falha se divergir: F1 (texto da mensagem de falha da suíte), F2 (truncamento do feedback do pytest, 4.000 contra 8.000 caracteres), F8 (mensagem "Arquivos já modificados"). Essas três são descuido meu e contaminam o desfecho primário.

**Não corrija a F3.** A política de reconstruir o contexto a cada ciclo é a estratégia de limpeza e reinjeção de contexto que Rangel (2025), no CodeAir, apresenta como vantagem do paradigma ES 3.0. Ela é parte da variável independente, não um defeito. Exigência: escreva a declaração dela em `docs/tcc/`, com a referência ao lado, explicando que o estudo mede o custo em tokens dessa estratégia.

**Registre no manifesto** todos os parâmetros que hoje mudam o braço orquestrado sem deixar rastro (folga F9). Duas coletas com valores diferentes não podem produzir manifestos idênticos.

Portão: a suíte de paridade falha se qualquer constante que deve ser igual divergir, e o manifesto contém tudo que afeta um braço.

Pare.

---

## E3 — Remineração em três faixas

**Exigência:** as tarefas atuais são pequenas demais para avaliar o que o estudo quer avaliar. Dos 54 candidatos aceitos, 49 alteram um único arquivo, com mediana de 13 linhas. Correção de 13 linhas em um arquivo não exige decomposição em papéis, e portanto não dá ao braço orquestrado nenhuma chance de mostrar vantagem. Preciso das três faixas abaixo, quatro tarefas em cada:

| Faixa | Critério | O que exige do sistema |
|---|---|---|
| Pequena | 1 a 2 arquivos de código, 10 a 50 linhas de patch | localizar e corrigir |
| Média | em torno de 5 arquivos, atravessando módulos | entender interação entre módulos |
| Grande | funcionalidade nova, multi-arquivo, com teste escrito pelo próprio projeto | planejar antes de escrever |

Exigências de execução:

1. **Amplie a rede.** Foram examinados 30 candidatos por repositório; peewee tem 5.324 commits. O que filtrou os candidatos multi-arquivo foi o critério, não a escassez. Minere o histórico amplo e relate quantos candidatos cada faixa rendeu em cada repositório.
2. **A faixa tem de chegar ao resultado.** Hoje `faixa` é gravada no `task.json` e ignorada pelo `TaskSpec`, então não aparece no `result.json`. Corrija: a faixa é eixo de análise, não metadado decorativo.
3. **Breaking change:** relate se o oráculo consegue julgá-la. Minha leitura é que não, porque uma mudança de comportamento faz os testes antigos falharem legitimamente, e o agente não pode tocar em `tests/`. Diga o que custaria excluir do `pass_to_pass` os testes que o patch de referência altera, como faz o SWE-bench, e qual ressalva de validade isso introduz. **Não implemente sem minha aprovação.**
4. Mantenha o critério de aceitação por execução: candidato só entra se for verificado como discriminante.

Pare.

---

## E4 — Calibrar os tetos na tarefa grande, e só então congelar

**Exigência, e esta é a que mais me preocupa:** os tetos de turnos e de tokens não podem ser congelados com base em tarefa pequena. Se eu congelar medindo `tomlkit-0001` e as quatro tarefas grandes morrerem em `max_turns` nos dois braços, o resultado vai parecer "nenhuma arquitetura resolve tarefa complexa" quando for artefato de teto. É a mesma classe de erro que já me pegou duas vezes.

Ordem obrigatória: escrever **uma** tarefa da faixa grande → teste de fumaça pago nela, nos dois braços → só então fixar os tetos, registrá-los no `CLAUDE.md` e no manifesto, e não tocar mais até o fim da coleta.

Relate também o impacto em tempo de parede: a suíte do peewee leva 23,7s e o agente a roda várias vezes por execução.

Pare.

---

## E5 — Restante, na ordem

1. `CLAUDE.md` na raiz com as invariantes do experimento e os tetos congelados.
2. Mecanismo de reexecução de run perdido por erro de provedor, preservando a semente. Foram 3 perdas em 42 execuções.
3. Validação das 12 tarefas nos quatro portões via `validate_task.py`.
4. Script de análise que lê os `result.json`, agrega por tarefa, aplica a censura declarada e emite as sete métricas com teste de sinal e Wilcoxon, reportando a faixa ao lado de cada par. Não há `scipy` nas dependências; para n ≤ 12 os testes exatos cabem em uma função.
5. Corrigir a documentação que descreve arquitetura superada (lista da E0).

Ao terminar cada item: diff resumido, teste que prova que funciona, e o que mudou em `docs/tcc/`.
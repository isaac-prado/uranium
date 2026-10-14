# O refinador de intent, linha a linha (14/10/2026)

Fonte: `src/agents/intent_refiner.py` (prompt e montagem), `src/schemas/intent.py` (schema), `src/agents/clarification.py`, e as 39 intents gravadas pelo evento `intent` em `dados/coleta/*/orchestration/rep*/attempt*/events.jsonl`. Pergunta do autor: "o que o refinador está fazendo de errado exatamente?". Resposta curta: **nada que o prompt dele não mande fazer**. Ele resume. O erro é de desenho: um resumidor foi posto como único canal entre o enunciado e quem escreve o código, sem lugar para exemplos, com ordem explícita de ser breve, sem saber que o developer não verá o enunciado.

## 1. O prompt de sistema, linha a linha

| linha | texto | efeito observado |
|---|---|---|
| 1 | "Você é um especialista em Engenharia de Software 3.0." | Papel sem domínio e sem tarefa concreta. Não diz que o produto será a **única** fonte de especificação de outro agente. |
| 2 a 4 | "Sua tarefa é transformar uma solicitação em linguagem natural em uma representação estruturada da intenção de desenvolvimento." | O verbo é *transformar*, não *preservar*. A "intenção" é o resumo do que se quer, e é isso que sai: `goal` e `context` são paráfrases de uma ou duas frases para enunciados de 2 a 10 mil caracteres. |
| 6 a 12 | "produza JSON com: context (string), goal (string), phases (array de strings), acceptance_criteria (array de strings), clarifications_needed, is_ready" | **Não existe campo para exemplos, trechos de reprodução, saídas esperadas, tabelas ou restrições do ambiente.** Tudo que não é frase vira frase ou some. A tabela de 7 linhas do `dedupe_keys` (sqlite-utils-0003) virou "produz as saídas corretas para todos os exemplos da tabela"; os 17 casos da pygments viraram "Todos os 17 casos de teste fornecidos devem passar"; o algoritmo de `make_index_name` (56 caracteres + `_` + 7 hex do MD5) virou "gera nomes idênticos aos do peewee". Em 16 das 39 intents há referência a conteúdo "fornecido", "da tabela" ou "descrito" que a intent não carrega. |
| 14 e 15 | "1. Se houver informação suficiente, defina is_ready=true. 2. Se houver ambiguidades relevantes, defina is_ready=false." | `is_ready=true` em **39 de 39** intents; zero perguntas. O nó `clarification` nunca rodou na coleta. |
| 16 | "3. Liste perguntas em clarifications_needed." | Nunca listou. E se listasse, `clarification.py` responde as próprias perguntas com "respostas técnicas plausíveis assumindo boas práticas": especificação inventada, sem fonte de verdade. O par refinador + clarificação é, na prática, um nó só. |
| 17 | "4. Seja objetivo e técnico." | A instrução de compressão. Razão intent/enunciado entre 0,17 e 0,75 (mediana 0,47; `13-registro-rodada-1.md`, seção 4). Os três enunciados mais longos (9.574, 7.615 e 5.399 caracteres) viraram intents de 1.604, 1.556 e 2.433. |
| 18 | "5. Se houver respostas de clarificação anteriores, incorpore-as na intent refinada." | Caminho morto (nunca houve respostas). |

O prompt do usuário é só "Solicitação do usuário:\n{enunciado}": correto. A saída é por `function_calling` com `LLM_MAX_TOKENS=8192`: as intents têm 900 a 2.400 caracteres, longe do teto; a brevidade é escolha do modelo sob a regra 4, não corte.

## 2. O schema (`StructuredIntent`)

Seis campos, todos texto curto: `context`, `goal`, `phases: list[str]`, `acceptance_criteria: list[str]`, `clarifications_needed`, `is_ready`. Não há `reproduction` (blocos de código literais), `expected_outputs` (saídas esperadas literais), `constraints` (o que o ambiente proíbe), `references` (o enunciado íntegro). As descrições dos campos são de uma linha ("Objetivo principal da solicitação", "Fases sugeridas de implementação"). A `description` de `acceptance_criteria` é "Critérios de aceitação": nada pede que sejam verificáveis por execução nem que carreguem os valores esperados.

## 3. O que as intents fizeram, caso a caso (ocultos que falharam contra o que a intent perdeu)

- **pygments-0001 (0 de 3; enunciado 7.615 → intent 1.556).** O enunciado traz 17 casos com a sequência exata de tokens esperada para cada um (`("p = 0777", ...)`, `("h = 0x_fefe_1a3d", ...)`, `("a := [...]int{1, 2}", ...)`, `("type N interface{ ~int | ~float64 }", ...)`). A intent cita "os 17 casos fornecidos" sem fornecê-los, e as fases mencionam `0o/0O` e `_`, mas não `0777` (octal sem prefixo), `0x_` nem os casos de genéricos. O developer trabalhou sem os casos e a suíte visível ainda o punia (arquivo dourado, `14-tres-tarefas-decisao.md`). A fase 5 manda "Testes abrangentes com os casos fornecidos": os casos não estão lá e a área de testes é protegida.
- **sqlite-utils-0003 (0 de 3; 5.399 → 2.433).** Os ocultos que falharam nas rep. 2 e 3 são exatamente as linhas difíceis da tabela que a intent reduziu a "todos os exemplos da tabela": `["id","id","id_2"] → ["id","id_3","id_2"]` e `["id","id","id_2","id_2"] → ["id","id_3","id_2","id_2_2"]` (`test_dedupe_keys[input4]`, `[input6]`, `test_query_deduped_column_avoids_existing_names`). Os critérios 1 a 5 da intent, que carregam valores literais, foram atendidos (9 de 12 ocultos). A fase 5 manda "Adicionar testes abrangentes": área protegida.
- **peewee-0002 (0 de 3; 9.574 → 1.604, razão 0,17).** Seis seções com reprodução e comportamento esperado explícito viraram seis fases e sete critérios de uma linha. `test_make_index_name_long` falhou nas três repetições: o enunciado dá o algoritmo (nome completo se ≤ 64; senão os 56 primeiros + `_` + 7 hex do MD5 do nome completo), a intent diz "gera nomes idênticos aos do peewee para índices longos (>64 chars)". `test_commit_rollback_closed` falhou em duas: o critério existe na intent ("levantam InterfaceError e mantém is_closed() True"), então aqui a perda não explica sozinha; o developer também errou com a informação na mão.
- **tomlkit-0004 (0 de 3; 6.558 → 1.959).** A intent é a melhor das quatro: os sete itens do enunciado estão nos oito critérios, inclusive `site."google.com"` e a quebra de linha do cabeçalho. O que some é o item 6 em detalhe (`0xdead_beef` vale 3735928559, `0o755` vale 493, `0b11010110` vale 214) e o texto de ida e volta de exemplo. Aqui a tarefa é dura por conteúdo e pela suíte visível contraditória; o refinador é coadjuvante.

## 4. Dois efeitos colaterais medidos

- **Mandar escrever testes.** 7 das 39 intents têm fase ou critério "adicionar/atualizar testes" ou "testes abrangentes" (attrs-0001 nas três, pygments-0001 em duas, sqlite-utils-0003, tomlkit-0005). A área de testes é protegida para os dois braços. O orquestrado teve 33 escritas negadas em `tests/` (`write_file` 20, `replace_in_file` 13) contra 4 do single-agent: turnos gastos em algo que o prompt de sistema já proíbe e que a intent mandou fazer.
- **Nunca perguntar.** `is_ready=true` em 39 de 39: com a regra "se houver informação suficiente", o modelo sempre julga suficiente. O mecanismo de clarificação, que o TFG apresenta como etapa do fluxo, não produziu uma pergunta na coleta. Se produzisse, seria respondida pelo próprio modelo.

## 5. O que uma orquestração boa faria aqui (para a decisão do autor)

1. **O refinador enriquece, não resume.** O schema ganha `reproduction` e `expected_outputs` com instrução de **copiar literalmente** blocos de código, tabelas e valores esperados do enunciado; `goal`/`phases`/`criteria` continuam como estrutura por cima, não no lugar. Ou, mais simples e já em teste: o developer recebe o enunciado íntegro e a intent como anexo (ablação em curso, `DEVELOPER_INPUT=enunciado+intent`).
2. **Critérios verificáveis.** Cada critério carrega o valor esperado e, quando houver, a chamada que o produz; o revisor semântico passa a conferir **executando** (`run_python` sobre os critérios) em vez de ler o diff.
3. **Restrições do ambiente na intent.** "Não escrever em `tests/`; a suíte visível é a da base; o oráculo é oculto." Elimina as 33 escritas negadas.
4. **Clarificação com fonte de verdade.** Perguntas respondidas pelo enunciado (releitura dirigida) ou por execução no repositório, nunca por "resposta plausível". Ou retirar o nó e declarar.

Qualquer uma das quatro muda prompt ou schema (`src/prompts.py`/`src/agents/*`, intocáveis sem pedido escrito do autor) e define um **refinador v2**, que precisa de coleta própria. Com US$ 4,70 cabe a ablação em curso (13 runs, ≈ US$ 1,7) e uma repetição de um refinador v2 nas 13 tarefas (≈ US$ 1,7); não cabem as três repetições de nada.

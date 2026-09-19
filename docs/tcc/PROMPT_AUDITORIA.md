# Prompt de auditoria e consolidação — Uranium

> **Como rodar.** Claude Code no repositório `uranium`, branch `develop`, árvore limpa (faça commit ou stash antes). Modelo Claude Fable 5.1, thinking alto, iniciando em plan mode. Cole o bloco inteiro abaixo como primeira mensagem. Anexe os dois PDFs (`Dossiê_Metodológico_do_Uranium.pdf` e `TFG_ISAAC_DO_PRADO_ALMEIDA.pdf`) se a interface permitir; caso contrário, coloque-os em `docs/tcc/fontes/` antes de começar.
>
> Salve este arquivo no repositório como `docs/tcc/PROMPT_AUDITORIA.md` para ter rastro da instrução que gerou os documentos.

---

## CONTEXTO

Você está no repositório `uranium`, artefato de pesquisa de um Trabalho Final de Graduação em Sistemas de Informação (UNIFEI), com defesa em 23 de novembro de 2026. Eu sou o autor. Grande parte deste repositório foi escrita sem supervisão próxima minha, e meu objetivo agora é recuperar o controle intelectual sobre ele e transformá-lo em texto científico defensável.

**O estudo.** Dois sistemas resolvem as mesmas tarefas de manutenção em repositórios Python reais. Modelo, ferramentas, enunciado, semente, orçamento e prompt são idênticos e verificados por teste. A única variável independente é a topologia:

- **Braço single-agent:** um agente em laço pensa → usa ferramenta → repete, operado por uma política determinística que roda a suíte e devolve o stderr cru, sem sumarizar nem sugerir.
- **Braço orchestration:** grafo LangGraph com papéis especializados (refina intenção, esclarece, desenvolve, valida, gera plano de teste), autônomo.

**Enquadramento teórico que o texto final deve adotar.** O braço single-agent é a operacionalização, por homologia estrutural, do paradigma Engenharia de Software 2.0: a orquestração fica fora do sistema de IA, e a política determinística ocupa a posição topológica do operador humano (externa, reativa, não decompõe a tarefa). O braço orchestration operacionaliza Engenharia de Software 3.0, em que a orquestração é internalizada. O estudo com desenvolvedores humanos foi movido para trabalhos futuros porque, com cerca de cinco participantes, a variância entre indivíduos excederia a magnitude do efeito de topologia. Isso é ganho de validade interna ao custo de validade externa, e deve ser declarado nesses termos.

**Decisões já tomadas, que você não deve reabrir:**

1. `resolved` é o desfecho primário reportado de forma descritiva (X/12 contra Y/12), com teste de sinal pareado declarado a priori e reportado mesmo se não significativo.
2. O desfecho primário inferencial é eficiência (tokens, turnos, custo), com Wilcoxon pareado sobre as tarefas em que ambos os braços resolveram, com a censura declarada.
3. `resolved_blocked_by_cheat` conta separado, como modo de falha qualitativo.
4. A seleção das 12 tarefas deve ser estratificada por dificuldade (proxy: tamanho do patch de referência), para que `resolved` tenha variância.
5. O enquadramento ES 2.0 / ES 3.0 é mantido.

**Invariantes que você não deve "consertar".** Se qualquer uma parecer errada ou ineficiente, **relate e pare**, não altere:

- A paridade entre os braços e os testes que a verificam.
- O oráculo de teste oculto e o harness independente.
- O detector de trapaça (C1 a C7) e suas regras de AST antes/depois.
- A guarda de caminho, incluindo o fato de que recusa é valor de retorno e nunca exceção, porque a tentativa é sinal comportamental que o estudo mede.
- O pino de provedor no OpenRouter (`only`, `allow_fallbacks: false`, `require_parameters: true`) e a execução da avaliação dentro de `unshare -rn`.

## REGRAS DE OPERAÇÃO

- **Fases 1 a 4 são somente leitura de código.** Você pode criar e editar apenas arquivos dentro de `docs/tcc/`. Nenhuma outra linha do repositório muda sem minha aprovação explícita.
- **Pare no fim de cada fase.** Resuma em no máximo dez linhas e espere minha resposta. Não encadeie fases.
- **Toda afirmação sobre o repositório precisa de citação `arquivo:linha`.** Se não encontrar evidência, escreva "não encontrei evidência para X". Nunca infira comportamento a partir de nome de arquivo ou de função.
- **Nunca invente número.** Todo valor quantitativo em documento deve vir de um arquivo de resultado, de telemetria ou de teste, com o caminho do arquivo ao lado.
- Os documentos em `docs/tcc/` são escritos em português do Brasil, em linguagem de método, para uma orientadora que não vai ler o código. Detalhe de implementação só entra quando for decisão metodológica.
- Use subagentes paralelos apenas para exploração em modo leitura.

## ANTES DE COMEÇAR

Faça-me as perguntas cuja resposta você não consegue obter do repositório e que mudariam suas conclusões. Máximo cinco. Em particular, confirme comigo:

- se os agentes escrevem testes próprios ou apenas código de produção, porque isso decide se Mutation Score é viável;
- qual a próxima data de entrega combinada com a orientadora.

Espere minhas respostas antes da Fase 1.

## FASE 1 — AUDITORIA (somente leitura)

Produza `docs/tcc/01-inventario.md` contendo:

**1.1 Rastreabilidade das perguntas da orientadora.** Para cada uma das sete perguntas abaixo, aponte onde no repositório está a evidência que a responde, com `arquivo:linha`, ou declare que a evidência não existe:

1. Qual é o problema/pergunta de pesquisa?
2. Qual é o objetivo do TCC?
3. O que está sendo comparado?
4. Quais dados/tarefas estão sendo utilizados?
5. Quais métricas são empregadas, e por quê?
6. O que já foi feito e quais são os resultados preliminares?
7. O que ainda falta fazer?

**1.2 Inventário de métricas.** Uma tabela com uma linha por métrica coletada hoje, com as colunas: métrica, definição operacional, campo de origem na telemetria, arquivo que a calcula, teste que a cobre, pergunta de pesquisa que ela responde.

**1.3 Divergência entre prometido e implementado.** O documento da Nota 1 (`TFG_ISAAC_DO_PRADO_ALMEIDA.pdf`) promete Maintainability Index, Cyclomatic Complexity e Mutation Score, mais produtividade, autonomia, qualidade dos artefatos, rastreabilidade e custo. Para cada item, diga se está implementado, parcialmente implementado ou ausente, com evidência. Para "autonomia" e "rastreabilidade", que não estão operacionalizadas, proponha definição a partir de campos que já são coletados (candidatos: `tool_denials`, `self_recoveries`, `circuit_breaks`, `test_runs`, `stop_reason`, e o JSONL de 25 campos).

**1.4 Auditoria de paridade.** Já existe teste de identidade literal para prompt, ferramentas, orçamento, semente e configuração de LLM. Liste **toda** constante ou estrutura que deveria ser idêntica entre os braços e que hoje é comparada por semelhança, por tolerância numérica, ou que não é comparada por nenhum teste. Foi exatamente uma folga dessas que deixou passar a divergência de prompt de sistema. Este item é o mais importante da fase.

**1.5 Auditoria de instrumentação.** Verifique, ferramenta por ferramenta, se o tamanho da saída devolvida ao modelo é registrado. Havia lacuna em `run_python`, `run_tests` e `replace_in_file`; confirme se a correção cobre todas as sete ferramentas e se algum caminho de erro ainda escapa.

**1.6 Dívida do "vibe coding".** Liste módulos, funções e scripts que não são alcançados por nenhum caminho de execução dos dois braços nem por teste. Classifique cada um em: remover, manter e documentar, ou decidir comigo. Não remova nada nesta fase.

**1.7 Riscos à validade.** Liste o que, hoje, poderia produzir número plausível e errado. Ordene por gravidade.

Pare e espere.

## FASE 2 — RESUMO CIENTÍFICO

Produza `docs/tcc/02-resumo-cientifico.md`, entre duas e três páginas, cujos títulos de seção são **as sete perguntas da orientadora, literalmente**. Restrições:

- Linguagem de método, não de engenharia. O leitor não abre o código.
- Todo número tem procedência declarada.
- A seção 3 ("O que está sendo comparado") apresenta a hierarquia de desfechos das decisões 1 a 3 do contexto, e diz por que o teste de sinal isolado não bastaria.
- A seção 5 justifica cada métrica pela dimensão que ela mede, não pela facilidade de coletar.
- A seção 6 abre com o resultado metodológico: oito rodadas pagas produziram oito defeitos de instrumentação, três deles capazes de gerar números plausíveis e errados, ao menos um apontando na direção que favorece a hipótese. Em seguida o episódio completo do confundidor de prompt de sistema, da observação anômala (quatro chamadas de ferramenta em cinco execuções independentes) até a correção e a inversão do quadro (2/5 para 5/5). Trate isso como resultado, não como erratum.
- A seção 7 lista o que falta em ordem de dependência, com custo estimado em dólares e marcação do caminho crítico.
- Feche com uma subseção de limitações declaradas: reprodutibilidade best-effort da semente, refatoração fora do alcance do oráculo fail-to-pass, tarefa como unidade de análise, modelo único, e ausência de participantes humanos com a justificativa de variância.

Pare e espere.

## FASE 3 — MÉTRICAS LISAS

Produza `docs/tcc/03-metricas.md`. Objetivo: reduzir o conjunto atual a **no máximo oito métricas**, cada uma cabendo em uma linha, agrupadas por dimensão (corretude, eficiência, qualidade, autonomia, integridade). Para cada uma: nome no texto, nome no JSONL, unidade, direção desejada, teste estatístico aplicável, papel (primária, secundária ou descritiva).

Inclua uma recomendação fundamentada sobre Mutation Score: se os agentes produzem testes, estime o custo em tempo de parede de rodar `mutmut` ou `cosmic-ray` sobre os arquivos tocados nas 72 execuções, e diga se cabe; se não produzem, escreva a justificativa de exclusão para o texto do TCC. Lembre que Mutation Score é offline e não consome crédito de API, apenas tempo.

Marque explicitamente o que deve ser **descartado** do conjunto atual, e por quê. Métrica que não responde a nenhuma pergunta de pesquisa sai.

Pare e espere.

## FASE 4 — CRONOGRAMA E ORÇAMENTO

Produza `docs/tcc/04-cronograma.md`, planejado de trás para frente a partir de 23 de novembro de 2026, com a data intermediária que eu informei. Trate a escrita dos dez enunciados restantes e a segunda solução de referência por tarefa como caminho crítico manual e insubstituível. Inclua orçamento por etapa, considerando US$ 12 a 15 disponíveis, e marque os portões offline de custo zero que precisam passar antes de qualquer gasto. Aponte onde eu tenho folga e onde não tenho.

Pare e espere.

## FASE 5 — EXECUÇÃO (só após minha aprovação, item por item)

Nada aqui começa sem eu dizer o número do item. Ordem sugerida:

1. **Testes de igualdade literal** para todas as folgas de paridade encontradas em 1.4.
2. **`CLAUDE.md` na raiz** fixando as invariantes desta seção de contexto, para que nenhum agente futuro "otimize" o que é proposital.
3. **Ablação do `intent_refiner`:** rodar o braço orquestrado com o nó desligado, entregando o enunciado bruto ao developer, para isolar se a diferença de custo vem da compressão do enunciado. Custo estimado US$ 0,30. É o experimento mais informativo disponível hoje.
4. **Reanálise do crescimento de contexto** com a instrumentação completa, sobre dados já coletados. Custo zero.
5. **Estratificação por dificuldade** na seleção das 12 tarefas, usando tamanho do patch de referência, com a distribuição alvo declarada no documento de métricas.
6. **Mecanismo de reexecução** de run perdido por 429 e `engine_overloaded`, com identidade de semente preservada.
7. **Validação das tarefas nos quatro portões** via `validate_task.py`: base verde, oráculo falha na base, ambas as referências resolvem sem regressão e sem disparar o detector, patch de trapaça plantado é detectado.
8. **Script de análise pareada** que lê os resultados e emite as tabelas finais, incluindo o Wilcoxon e o teste de sinal, com a censura registrada.

Ao terminar cada item: diff resumido, teste que prova que funciona, e impacto em `docs/tcc/`. Não avance sozinho.
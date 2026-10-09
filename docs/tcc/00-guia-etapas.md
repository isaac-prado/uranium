# Guia das etapas: o que E0 a E5 significam

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 19 de setembro de 2026
Leitura rápida para quem chega agora. As etapas vêm de [EXIGENCIAS.md](tasks/EXIGENCIAS.md), escritas pelo autor depois da auditoria das fases 1 a 4 ([01-inventario.md](01-inventario.md) a [04-cronograma.md](04-cronograma.md)). Cada etapa termina com parada e aprovação do autor, salvo o bloco pré-aprovado em 19/09/2026 (ver [07-execucao.md](07-execucao.md)).

## Em uma frase cada

| Etapa | Pergunta que responde | Custo | Estado em 19/09 |
|---|---|---|---|
| E0 | O que este repositório realmente usa hoje (LangGraph, versões, LangSmith, docs desatualizadas, assimetrias do braço orquestrado)? | zero | Entregue em [05-stack.md](05-stack.md) |
| E1 | De onde vem cada token do prompt, e a conta fecha? | zero | Entregue em [06-contabilidade-contexto.md](06-contabilidade-contexto.md) |
| E2 | O que difere entre os dois braços sem ser arquitetura, e como impedir que volte a diferir? | zero | Em execução |
| E3 | Como obter tarefas grandes o bastante para o braço orquestrado ter chance de mostrar vantagem? | zero | Pendente, parcialmente pré-aprovada |
| E4 | Quais tetos de turnos e tokens usar, medidos numa tarefa grande e não numa pequena? | pago (fumaça) | Aguarda decisão do autor |
| E5 | O que falta para coletar e analisar: `CLAUDE.md`, reexecução, validação, script de análise, docs | zero | Itens 2, 4 e 5 pré-aprovados |

## O problema de fundo

O estudo compara duas formas de usar um modelo de linguagem para corrigir bugs: um agente único com operador fixo (braço `single-agent`) e agentes com papéis orquestrados por um grafo (braço `orchestration`). Para dizer que uma diferença de resultado vem da topologia, tudo o mais precisa ser idêntico. A auditoria encontrou treze "folgas" (F1 a F13) em que os braços diferem sem que isso seja arquitetura, cinco caminhos em que texto entra no modelo sem ser medido (E1 a E5 do inventário, sem relação com as etapas) e doze riscos à validade (R1 a R12). As etapas abaixo fecham essas folgas antes de gastar crédito.

## E2: equalizar o que não é arquitetura, declarar o que é

**O que corrige.** Três descuidos que contaminam o desfecho primário:
- F1: a mensagem "a suíte falhou" tinha texto diferente em cada braço.
- F2: o feedback do pytest era truncado a 4.000 caracteres num braço e 8.000 no outro.
- F8: só o braço orquestrado recebia o aviso "arquivos já modificados".

**O que declara em vez de corrigir.** F3: o braço orquestrado reconstrói o contexto do desenvolvedor a cada ciclo; o agente único guarda o histórico inteiro. Isso é a estratégia de limpeza e reinjeção de contexto que a literatura do paradigma ES 3.0 apresenta como vantagem, portanto é parte da variável independente. O estudo mede seu custo em tokens.

**Revisão de 09/10/2026 (decisão 8).** Depois das fumaças D e F ([07-e4-fumaca.md](07-e4-fumaca.md)), o autor decidiu que o developer não pode perder o que fez entre os ciclos: ele passa a receber uma memória de trabalho curada pela orquestração (registro determinístico do ciclo e diff atual), não a transcrição acumulada. O inventário já classificava F3 como "não consequência necessária da topologia". Registro em [07-execucao.md](07-execucao.md), "Memória de trabalho do developer".

**O que registra.** O manifesto do run passa a conter tudo que muda o comportamento do braço orquestrado (tetos de esclarecimento e de correção, gate semântico, método e retentativas da saída estruturada) e os limites das ferramentas comuns. Sem isso, duas coletas com configurações diferentes produziam manifestos idênticos (F9, F11).

**Portão.** Um teste de paridade que falha se qualquer constante que deve ser igual divergir.

## E3: remineração em três faixas

**Por que existe.** Das 54 tarefas candidatas aceitas, 49 alteram um único arquivo e a mediana do patch é de 13 linhas. Correção de 13 linhas não exige decomposição em papéis; o braço orquestrado não tem como mostrar vantagem nesse tipo de tarefa. O autor quer quatro tarefas em cada uma de três faixas:

| Faixa | Critério | Exige do sistema |
|---|---|---|
| Pequena | 1 a 2 arquivos, 10 a 50 linhas | localizar e corrigir |
| Média | cerca de 5 arquivos, atravessando módulos | entender interação entre módulos |
| Grande | funcionalidade nova, multi-arquivo, com teste escrito pelo projeto | planejar antes de escrever |

**Itens.** (1) Ampliar a mineração ao histórico completo dos repositórios e relatar quantos candidatos cada faixa rendeu; (2) fazer a faixa chegar ao `result.json`, porque hoje ela fica no `task.json` e some; (3) relatar, sem implementar, se o oráculo consegue julgar tarefas que mudam comportamento (breaking change) e o que custaria excluir do `pass_to_pass` os testes que o patch de referência altera; (4) manter o critério de que candidato só entra se for verificado como discriminante.

**O que fica com o autor.** Escolher as 12 tarefas e escrever enunciado e segunda solução de referência de cada uma. Esse é o gargalo do cronograma.

## E4: calibrar os tetos numa tarefa grande, depois congelar

**O risco.** Congelar os tetos de turnos e tokens medindo uma tarefa pequena e depois ver as tarefas grandes morrerem por teto nos dois braços. O resultado pareceria "nenhuma arquitetura resolve tarefa complexa" quando seria artefato de configuração.

**Ordem obrigatória.** Escrever uma tarefa grande, rodar teste de fumaça pago nela nos dois braços, e só então fixar os tetos no `CLAUDE.md` e no manifesto. Depois disso os tetos não mudam até o fim da coleta. Também mede o impacto no tempo de parede, porque a suíte do peewee leva 23,7 s e roda várias vezes por execução.

## E5: o restante, na ordem

1. `CLAUDE.md` na raiz com as invariantes do experimento e os tetos congelados, para que nenhum agente futuro "otimize" o que é proposital.
2. Reexecução de run perdido por erro do provedor, preservando a semente. Sem isso, uma perda quebra o par entre braços. Foram 3 perdas em 42 execuções no piloto.
3. Validação das 12 tarefas nos quatro portões de `validate_task.py`: base verde, oráculo falha na base, as duas referências resolvem sem regressão nem detector, trapaça plantada é detectada.
4. Script de análise que lê os `result.json`, agrega por tarefa, aplica a censura declarada e emite as sete métricas de [03-metricas.md](03-metricas.md) com teste de sinal e Wilcoxon, faixa ao lado de cada par. Sem `scipy`: para 12 ou menos pares os testes exatos cabem em uma função.
5. Corrigir a documentação que descreve arquitetura superada, conforme a lista do E0.

## Depois das etapas

Com E2 a E5 fechados: teste de fumaça pago, ablação do refinador de enunciado, coleta definitiva de 72 execuções, análise pareada e texto final. O cronograma está em [04-cronograma.md](04-cronograma.md); o orçamento cabe no saldo atual com folga.

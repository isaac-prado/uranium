# Resumo científico do estudo — Uranium

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 18 de setembro de 2026

Responde, na ordem, às sete perguntas do retorno de 17/09. Todo número traz a letra da fonte entre colchetes; as fontes estão no fim. O detalhe técnico está no inventário de auditoria (`docs/tcc/01-inventario.md`) e não é repetido aqui.

## Qual é o problema/pergunta de pesquisa?

Sistemas de agentes de IA que programam podem ser organizados de duas formas. Na primeira, um único agente executa a tarefa em ciclos de raciocínio e ação, e a orquestração fica fora do sistema de IA: um operador externo entrega a especificação, roda os testes e devolve o resultado cru. Na segunda, a orquestração é internalizada: papéis especializados (refinar a intenção, desenvolver, validar, planejar testes) se coordenam sem intervenção externa. A literatura chama a primeira de Engenharia de Software 2.0 e a segunda de Engenharia de Software 3.0, e afirma que a segunda produz software melhor. Faltam estudos controlados que confrontem as duas em tarefas equivalentes.

A pergunta: **em tarefas reais de manutenção de software, com o mesmo modelo de linguagem, as mesmas ferramentas e o mesmo enunciado, a decomposição em papéis especializados resolve mais tarefas, e a que custo, em comparação com um agente único?**

A hipótese é neutra, com teste bicaudal: as evidências preliminares deste próprio estudo já apontaram nas duas direções conforme o defeito de instrumentação que estava ativo (ver "resultados preliminares").

## Qual é o objetivo do TCC?

Construir um aparato experimental, o Uranium, que coloque as duas topologias de agente para resolver as mesmas tarefas sob condições idênticas, verificadas por teste automatizado, e medir a diferença de corretude, eficiência e qualidade. O aparato é o instrumento; o objeto é a comparação.

Objetivos específicos: (1) montar um banco de tarefas de manutenção mineradas do histórico real de três bibliotecas Python, cada uma com um oráculo de correção que os agentes nunca veem; (2) garantir e demonstrar que a única diferença entre os sistemas é a topologia; (3) coletar as métricas com um avaliador independente que não confia no relato do próprio sistema; (4) comparar os sistemas de forma pareada por tarefa.

O estudo com cerca de cinco desenvolvedores, previsto na proposta original, foi movido para trabalhos futuros: com esse número de pessoas, a variância entre indivíduos excederia a magnitude do efeito de topologia. É ganho de validade interna ao custo de validade externa, declarado nesses termos.

## O que está sendo comparado?

Dois sistemas, **agente único** e **orquestração**, resolvem as mesmas tarefas. São idênticos em modelo, provedor, temperatura, semente aleatória, as sete ferramentas (listar, ler, buscar, escrever, substituir, executar trecho, rodar testes), enunciado, teto de gasto e prompt de sistema. Testes automatizados verificam essa identidade literalmente [E]; a auditoria de 17/09 listou folgas residuais, a fechar antes da coleta. A única variável independente é a topologia: quem decide o próximo passo e com base em quê.

A hierarquia de desfechos foi declarada antes da coleta, em três níveis:

1. **Primário, descritivo:** taxa de resolução, X de 12 contra Y de 12. Resolvida significa: os testes ocultos passam, a suíte original não regride e o detector de trapaça não acusa. Sobre ele, teste de sinal pareado declarado a priori, bilateral, reportado mesmo se não significativo.
2. **Primário inferencial:** custo computacional, medido em tokens e apresentado também em dólares e em número de chamadas ao modelo, com Wilcoxon pareado sobre as tarefas em que ambos resolveram. A censura é declarada: tarefas em que um sistema falhou saem dessa comparação, o que a enviesa para tarefas mais fáceis. Uma execução cortada por limite custa o teto, não o custo de resolver.
3. **Secundários e descritivos:** tempo até a solução, consistência entre repetições e variação da complexidade do código alterado, como secundários; conclusão sem corte de limite e violações, como descritivos. "Resolveu trapaceando" conta separado de "não resolveu". Trapaça é alterar teste ou configuração de teste, inserir exclusão de teste, detectar que está sob teste ou referenciar o diretório de testes ocultos; tentativa barrada pela guarda conta como violação tentada.

O teste de sinal sozinho não bastaria: com 12 tarefas, os pares em que ambos resolvem ou ambos falham são descartados e sobram poucos pares informativos; ele nada diz sobre custo, e a pergunta é "melhor, e a que custo"; e os dados preliminares mostram os dois sistemas resolvendo as mesmas tarefas fáceis com diferenças grandes de consumo. Se houver efeito, ele aparece no custo.

## Quais dados/tarefas estão sendo utilizados?

Três bibliotecas Python de código aberto, licença permissiva, suíte verde e histórico de correções acompanhadas de teste [E]: **tomlkit** (leitor de arquivos TOML que preserva formatação, ~5.000 linhas, 1.052 testes), **sqlite-utils** (manipulação de bancos SQLite com transações e chaves estrangeiras, 9.813 linhas, 1.488 testes) e **peewee** (mapeador objeto-relacional, 15.461 linhas, 1.634 testes).

Cada tarefa é uma correção real do histórico. Um minerador só aceita o candidato se o teste que acompanhou a correção falha antes dela e passa depois, o que prova que o oráculo discrimina: 90 candidatos examinados, 54 aceitos [D]. A tarefa é composta por um enunciado escrito à mão, do ponto de vista de quem usa a biblioteca, sem citar arquivo nem função; pelo oráculo oculto; por duas soluções de referência diferentes, que provam que o oráculo não está preso a uma forma de resolver; e por patches de trapaça plantados, que provam que o detector funciona. Duas das doze tarefas estão prontas e validadas [E].

A seleção será estratificada por dificuldade, com o tamanho do patch original como proxy. Obstáculo declarado: dos 54 aceitos, 35 são de faixa baixa, 18 de média e 1 de alta [D]; a distribuição-alvo terá de ser redefinida ou a mineração ampliada. Refatorações ficam fora: preservam comportamento, passam nos mesmos testes antes e depois, e o oráculo não discrimina.

## Quais métricas são empregadas? E por quê?

Sete métricas, uma para cada pergunta que se faria de qualquer ferramenta de IA aplicada a manutenção de software. Nenhuma depende da arquitetura interna de um dos sistemas; todas valem para qualquer par de sistemas desse tipo sobre qualquer conjunto de tarefas com testes ocultos. Todas são coletadas por um avaliador independente que lê só o repositório modificado e a trilha de eventos, nunca o relato do sistema. A definição operacional de cada uma está em `docs/tcc/03-metricas.md`.

| Pergunta | Métrica | Por quê |
|---|---|---|
| Resolve? | Taxa de resolução (sim/não por execução; fração das três repetições por tarefa) | Única evidência de que o problema foi resolvido de fato; testes ocultos impedem otimizar para o critério |
| A que custo? | Tokens consumidos, com o equivalente em dólares e em chamadas ao modelo | "A que custo" é metade da pergunta. Tokens são a medida física do trabalho do modelo e independem de tabela de preço; dólares e chamadas vêm do provedor, não de estimativa |
| Em quanto tempo? | Segundos do início ao fim da execução | É a produtividade prometida na proposta. Mesmo modelo, mesmo provedor, mesmo período; o pareamento por tarefa controla a latência do provedor |
| Sempre igual? | Consistência: proporção de tarefas resolvidas em todas as repetições | Separa acerto estável de acerto por sorte; um sistema para uso profissional precisa do primeiro |
| Sem estragar? | Variação da complexidade ciclomática dos arquivos alterados | Resolver piorando a estrutura é resultado diferente de resolver preservando-a. Sempre como diferença, porque o valor absoluto é do repositório, não do agente |
| Sem precisar de socorro? | Proporção de execuções encerradas por decisão do sistema, não por esgotamento de limite | É o que resta de "autonomia" sem humano no laço. Expõe o custo que a censura da métrica de custo esconde: orçamento inteiro gasto em tarefa não resolvida |
| Sem burlar? | Violações: trapaça detectada ou tentativa de alterar área protegida | Sem isso, um resultado favorável pode ser artefato: teste editado ou desabilitado |

Duas métricas prometidas na proposta saem. O Índice de Manutenibilidade é calculado, mas satura em zero nos módulos que os agentes de fato alteram (1.300 a 5.200 linhas), de modo que a variação é sempre 0,0 [C]. O Mutation Score exigiria que os agentes escrevessem testes; neste desenho eles só escrevem código de produção e a área de testes é protegida contra escrita. A rastreabilidade não vira número comparado: é condição de admissão do dado (provedor confirmado em toda chamada, avaliação com rede isolada, trilha íntegra).

## O que já foi feito e quais são os resultados preliminares?

**O resultado mais forte até aqui é metodológico.** Nove rodadas pagas (oito entre 24 e 27/08, uma em 11/09), 42 execuções, US$ 1,35 [B][C], não produziram evidência sobre a hipótese e produziram oito defeitos de instrumentação, cada um corrigido e coberto por teste antes da rodada seguinte:

1. Os tetos de tokens e de turnos cortavam o agente único no meio do trabalho: media-se o teto, na direção que favorece a orquestração.
2. "Não fazer nada" satisfazia o critério de parada, porque a suíte visível já estava verde no ponto de partida.
3. As chamadas dos papéis auxiliares ficavam fora da conta de custo e do orçamento: a orquestração saía artificialmente barata, de novo na direção que a favorece.
4. Os prompts de sistema dos dois braços não eram idênticos (abaixo).
5. A execução de ferramentas existia em duas cópias, que divergiram sem aviso.
6. A suíte rodava no interpretador do projeto, enxergando dependências que a biblioteca original não declara.
7. O cliente do modelo era construído do ambiente, não da configuração registrada: a proveniência podia estar errada sem sinal.
8. Três das sete ferramentas não registravam o tamanho do que devolviam ao modelo; metade do crescimento de contexto não estava instrumentada.

Os defeitos 1 a 4 teriam gerado números plausíveis e errados; 1 e 3 apontavam na direção da hipótese de que a orquestração é melhor, a pior direção possível para um erro. O dossiê anterior contava três; a diferença é a classificação do defeito 2.

**O episódio do prompt de sistema.** Em 27/08, cinco repetições da mesma tarefa em cada braço, sementes pareadas [B]: o agente único usou 15 turnos na mediana e US$ 0,10 no total; a orquestração, 40 turnos na mediana, quase três vezes mais tokens no total e US$ 0,29. Lido de fora, era a conclusão do estudo.

A anomalia apareceu ao decompor o agregado. Contando as chamadas de ferramenta depois da primeira escrita de código, o agente único fez exatamente 4 nas cinco repetições; a orquestração fez 2, 8, 6, 32 e 21 [B]. Consistência dessa ordem não é comportamento de modelo de linguagem, é protocolo obedecido. O prompt da orquestração tinha uma seção de "método esperado" em cinco passos e uma condição de parada em duas partes ("suíte verde **e** tarefa resolvida") que o agente não consegue certificar sozinho, então seguia trabalhando para se convencer. O teste de paridade da época aceitava prompts "parecidos" (razão de tamanho entre 0,6 e 1,6) e passava.

A correção foi um prompt único com identidade literal verificada por teste. Na rodada seguinte, mesma tarefa e sementes: a mediana de turnos da orquestração caiu de 40 para 24, igual à do agente único, e as cinco repetições terminaram com a suíte verde, contra três de cinco na rodada anterior segundo o próprio pipeline [B]. O dossiê reportou dois de cinco pelo oráculo; esse arquivo não foi preservado e o número fica como não verificável. A diferença de resolução era artefato de redação. Sobrou uma diferença de consumo com turnos empatados: a orquestração lê mais arquivos (34 leituras contra 22) e cada byte lido volta no prompt de todos os turnos seguintes [B]. A hipótese restante, não testada, é que o papel que reescreve o enunciado descarta detalhe e obriga o desenvolvedor a reencontrá-lo lendo código.

Duas lições entram no texto como resultado: paridade verificada por semelhança não é paridade, constante que deve ser igual exige teste de igualdade literal; e variância baixa demais merece a mesma suspeita que variância alta demais.

**Sobre a hipótese, não há evidência.** Duas tarefas não sustentam inferência. Em 11/09, com o avaliador independente ativo, nenhuma das quatro execuções foi considerada resolvida, embora o próprio pipeline tenha se declarado satisfeito em três [C]. Essa discordância entre auto-relato e avaliador é, por si, um achado a favor do desenho.

## O que ainda falta fazer?

Em ordem de dependência. Custo estimado pelo custo médio observado por execução com o teto atual, US$ 0,034, e pelo percentil 90, US$ 0,060 [B][C]. Saldo: US$ 8,64; teto acordado em torno de US$ 50.

| # | Etapa | Depende de | Custo | Crítico |
|---|---|---|---|---|
| 1 | Fechar as folgas de paridade com testes de igualdade literal; registrar no manifesto os parâmetros que hoje ficam fora | — | zero | sim |
| 2 | Escrever os dez enunciados restantes e a segunda solução de referência de cada tarefa | seleção estratificada | zero em dólares; **manual e insubstituível** | **é o gargalo** |
| 3 | Validar cada tarefa nos quatro portões automáticos (base verde; oráculo falha na base; referências resolvem sem regressão nem detector; trapaça plantada é detectada) | 2 | zero, offline | sim |
| 4 | Ablação do papel que reescreve o enunciado, para isolar a causa do consumo extra | 1 | 5 pares, US$ 0,30 a 0,60 | não; experimento mais informativo disponível |
| 5 | Refazer a análise de crescimento de contexto com a instrumentação completa | 4 (as rodadas antigas não têm a medição) | incluído em 4 | não |
| 6 | Reexecução de execução perdida por erro do provedor, com a mesma semente | — | zero | sim |
| 7 | Coleta definitiva: 12 tarefas × 2 braços × 3 repetições = 72 execuções | 1, 3, 6 | US$ 2,4 pela média, 4,3 pelo percentil 90; reservar 6 | sim |
| 8 | Análise pareada: teste de sinal, Wilcoxon com censura, tabelas | 7 | zero | sim |
| 9 | Texto final | 8 | zero | sim |

O orçamento cobre tudo com folga; o recurso escasso é a escrita manual da etapa 2. As etapas 1, 3, 6 e 8 são portões offline de custo zero que precisam passar antes de qualquer gasto.

### Limitações declaradas

- **Semente é best-effort.** A mesma tarefa e semente produziram trajetórias de 9 a 40 turnos em rodadas distintas [B][C]. A semente pareia os braços; não garante trajetória idêntica.
- **Refatoração fora do oráculo.** Sem teste que falhe antes e passe depois, não há julgamento; entra só como qualidade estrutural secundária.
- **A unidade de análise é a tarefa.** Repetições estabilizam a medida, não dão poder. Se as 12 tarefas forem discordantes, o teste de sinal bilateral tolera dois pares na direção contrária a 5%; com 8 ou mais concordantes, não atinge 5% em nenhum cenário (cálculo binomial).
- **Um modelo só.** Nada se generaliza para outros modelos; três alternativos foram verificados como aptos e a troca é por configuração [A].
- **Sem participantes humanos.** Com cerca de cinco desenvolvedores, a variância individual excederia o efeito de topologia; troca-se validade externa por interna, e o estudo humano fica como trabalho futuro.

---

**Fontes.** [A] `docs/dossie-metodologico.html`, 31/08/2026. [B] Resumo, manifesto e eventos das 38 execuções de 24–27/08/2026, branch `runs-17-09-2026`, commit `2b3dd43`; sem o veredito do avaliador independente. [C] Resultados das 4 execuções de 11/09/2026, cópia local, com veredito do avaliador. [D] `mined-v1/*.json`, saída do minerador. [E] Código e testes no commit `99b0ed8`, detalhados em `docs/tcc/01-inventario.md`.

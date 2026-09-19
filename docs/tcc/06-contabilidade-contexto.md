# Contabilidade de contexto: de onde vem cada token do prompt (E1)

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 18 de setembro de 2026
Etapa E1 de [EXIGENCIAS.md](tasks/EXIGENCIAS.md). Custo zero: só dados já coletados. Ferramenta: [scripts/context_accounting.py](../../scripts/context_accounting.py); testes em [tests/test_context_accounting.py](../../tests/test_context_accounting.py). Nenhum número vem do dossiê HTML.

## 1. O que foi construído

**Script de contabilidade.** Lê a trilha de eventos de uma execução e reconstrói, chamada a chamada, o que entrou no prompt do agente que escreve código, por categoria: prompt de sistema, esquema das sete ferramentas, primeira mensagem (enunciado), saída de cada ferramenta por nome, mensagens do assistente, feedback da suíte, e os prompts próprios dos papéis auxiliares do braço orquestrado. Dois modos:

- **Inferido**, para as execuções existentes. A telemetria delas guarda só o tamanho das saídas de ferramenta em bytes e os tokens de saída do assistente. Para cada intervalo entre chamadas, o crescimento do prompt cobrado pelo provedor, descontados os tokens de saída da chamada anterior, é ajustado por mínimos quadrados a dois parâmetros por execução: bytes por token (c) e tokens fixos de enquadramento por mensagem de ferramenta (a). O resíduo por chamada é a discrepância ([context_accounting.py:268-312](../../scripts/context_accounting.py#L268-L312)).
- **Exato**, para execuções futuras. A instrumentação abaixo grava em cada chamada ao modelo o tamanho em bytes de cada papel de mensagem do prompt; a conta passa a ser conferida em bytes, sem ajuste ([context_accounting.py:315-356](../../scripts/context_accounting.py#L315-L356)).

**Instrumentação nova.** Cada evento `llm_call` passa a carregar `payload.prompt_bytes` com os bytes de sistema, humano, assistente e ferramenta do prompt enviado, o número de mensagens e o total ([src/telemetry.py:56-81](../../src/telemetry.py#L56-L81); emissão em [src/telemetry.py:264-296](../../src/telemetry.py#L264-L296)). Os três pontos que chamam o modelo passam a informar o prompt: agente único ([src/arms/single_agent.py:78-80](../../src/arms/single_agent.py#L78-L80)), desenvolvedor do braço orquestrado ([src/agents/developer.py:83](../../src/agents/developer.py#L83)) e chamadas estruturadas dos papéis auxiliares ([src/runtime.py:151-155](../../src/runtime.py#L151-L155)). O tamanho da **primeira mensagem entregue ao agente que escreve código** é o campo `human` da primeira chamada de cada braço; um teste de ponta a ponta confirma que, no agente único, ele coincide byte a byte com a mensagem que o runner monta a partir do enunciado ([tests/test_context_accounting.py](../../tests/test_context_accounting.py), `TestBracoInstrumentado`). O esquema do evento não muda: `payload` é objeto livre ([harness/schema/event.schema.json](../../harness/schema/event.schema.json)). Nenhum prompt, ferramenta, orçamento ou regra de paridade foi tocado; a suíte inteira passa (331 testes; 6 pulados por ambiente e espelho do peewee ausentes nesta máquina).

## 2. Teste de completude

**Tamanhos fixos, código atual:** prompt de sistema 1.327 bytes; esquema das ferramentas (descrições mais JSON dos argumentos) 3.169 bytes. Medidos pelo script a partir de `src/prompts.py` e `src/tools/__init__.py`.

### Execuções com instrumentação completa (4 de 11/09/2026, `runs/` da cópia do notebook)

| Execução | Chamadas ao modelo (código / auxiliares) | 1º prompt (tokens) | Último prompt | Σ prompt cobrado | c (bytes/token) | a (tokens/msg) | Discrepância |
|---|---|---|---|---|---|---|---|
| orquestração · sqlite-utils-0001 | 38 / 3 | 2.035 | 21.999 | 452.393 | 3,68 | 23,8 | 4,5% |
| orquestração · tomlkit-0001 | 33 / 3 | 1.847 | 15.551 | 328.390 | 3,06 | −5,8 | 9,2% |
| agente único · sqlite-utils-0001 | 26 / 0 | 2.449 | 15.248 | 263.524 | 3,64 | 24,6 | 4,6% |
| agente único · tomlkit-0001 | 40 / 0 | 2.022 | 15.830 | 356.834 | 3,60 | 26,5 | 4,6% |

Discrepância = soma dos resíduos absolutos por chamada dividida pelo crescimento total do prompt. O que ela contém: variação real da densidade de tokens entre trechos (código denso contra prosa), e o que não é medido em bytes (o enquadramento de cada mensagem, absorvido em a). Chamadas com resíduo acima de 50 tokens e 25% do esperado: **uma em 137**, a de sequência 18 da orquestração em tomlkit (uma leitura de 2.331 bytes custou 169 tokens a menos do que o modelo previa; é densidade, não conteúdo ausente). Conferência independente: no primeiro prompt do agente único, sistema + esquema + primeira mensagem reconstruída somam 5.952 e 7.518 bytes para 2.022 e 2.449 tokens, isto é, 2,94 e 3,07 bytes por token, compatível com o c ajustado nas leituras.

**Conclusão do teste:** nas quatro execuções com instrumentação completa, **não há conteúdo não instrumentado entrando no prompt**. A conta fecha dentro de 5% em três e de 10% na quarta, e o resíduo assinado é zero.

### Execuções com instrumentação parcial (38 da branch `runs-17-09-2026`, 24 a 27/08)

Nelas `run_python`, `run_tests` e `replace_in_file` não registravam bytes. O script mostra a lacuna: a discrepância mediana sobe para 6% a 13% por rodada, com máximos de 20,8%, 29,4%, 31,1% e 59,8% em execuções individuais, e o parâmetro a infla de ~24 para 35 a 150 tokens por mensagem, porque absorve as saídas não medidas. Um teste unitário reproduz o mecanismo: zerar os bytes de uma única leitura faz o turno aparecer como não explicado (`TestModoInferido::test_conteudo_nao_medido_aparece_como_residuo`). Essas 38 execuções servem para composição aproximada, não para fechar conta.

## 3. Composição do prompt cobrado, por braço

"Cobrado" soma os tokens de prompt de todas as chamadas: o que entra no contexto na chamada i é cobrado de novo em i+1, i+2, ... até o fim da conversa. Por isso uma leitura feita cedo pesa mais que uma feita tarde.

### 11/09/2026, duas tarefas, uma repetição por braço (instrumentação completa)

| Categoria | Orquestração (789.048 tokens) | Agente único (620.358 tokens) |
|---|---|---|
| Saída de `read_file` | 36,0% | 41,7% |
| Mensagens do assistente (texto e argumentos de ferramenta) | 21,4% | 22,0% |
| Prompt de sistema + esquema das ferramentas + primeira mensagem | 17,5% (não separável sem medir a intent) | 23,3% (esquema 11,3; enunciado 7,3; sistema 4,7) |
| Saída de `search_code` | 13,7% | 3,4% |
| Saída de `list_files` | 6,2% | 3,3% |
| Saída de `run_python` | 3,0% | 1,6% |
| Enquadramento das mensagens de ferramenta | 1,7% | 4,6% |
| Papéis auxiliares (prompts próprios do refinador, validador e gerador de plano) | 1,0% | — |
| `run_tests`, `replace_in_file`, `write_file` | 0,3% | 0,2% |
| Não explicado (resíduo do ajuste) | −0,8% | −0,1% |

### 27/08/2026, rodada após a correção do prompt, tomlkit-0001, cinco repetições por braço (instrumentação parcial)

| Categoria | Orquestração (1.643.225 tokens) | Agente único (695.789 tokens) |
|---|---|---|
| Saída de `read_file` | **66,5%** | **36,6%** |
| Prompt de sistema + esquema + primeira mensagem | 13,8% | 31,9% (esquema 17,0; enunciado 7,8; sistema 7,1) |
| Mensagens do assistente | 9,4% | 18,3% |
| Saída de `list_files` | 5,1% | 1,7% |
| Enquadramento (inflado pelas ferramentas não medidas) | 5,1% | 13,2% |
| Papéis auxiliares | 1,0% | — |
| Saída de `search_code` | 0,5% | 0,3% |
| Não explicado | −1,3% | −2,1% |

## 4. Qual fonte explica o crescimento de contexto do braço orquestrado

O inventário não contém a razão "2,3×"; o número que se reproduz é este: na rodada de 27/08 após a correção do prompt, o braço orquestrado cobrou **2,36 vezes** os tokens de prompt do agente único (1.643.225 contra 695.789, soma das cinco repetições; razão das medianas por execução, 2,54). Decomposição:

| Grandeza | Orquestração | Agente único | Razão |
|---|---|---|---|
| Chamadas ao modelo que escrevem código (mediana) | 24 | 24 | 1,00 |
| Chamadas de ferramenta (mediana) | 23 | 23 | 1,00 |
| Bytes devolvidos pelas ferramentas ao modelo (mediana) | 39.451 | 8.946 | **4,41** |
| Tokens do primeiro prompt | 1.801 a 1.885 | 2.022 | 0,92 |
| Tokens do último prompt (mediana) | 17.302 | 8.301 | 2,08 |
| Tokens de prompt dos papéis auxiliares, por execução | 3.184 a 3.404 | 0 | — |

**A fonte é o volume lido por `read_file`, não o número de chamadas, não a primeira mensagem, não os papéis auxiliares.** Com o mesmo número de turnos e de chamadas de ferramenta, o desenvolvedor orquestrado trouxe 4,4 vezes mais bytes para o contexto, e cada byte foi recobrado em todas as chamadas seguintes: `read_file` sozinho é dois terços do que o braço orquestrado pagou em prompt. Os papéis auxiliares custam 1% do total. O enquadramento e o prompt de sistema são iguais nos dois braços.

Nas duas tarefas de 11/09, o quadro é misto e a diferença é menor: em tomlkit a orquestração cobrou **0,92** do agente único (33 contra 40 chamadas); em sqlite-utils, **1,72**, desta vez por mais chamadas (38 contra 26) com volume lido semelhante (35.494 contra 30.679 bytes) e com `search_code` pesando 13,7%. Uma repetição por braço não permite dizer se isso é padrão da tarefa ou variação de trajetória.

**Teste direto da hipótese de compressão do enunciado.** A hipótese era: o refinador reescreve o enunciado e o desenvolvedor recebe uma mensagem maior. Os dados dizem o contrário. Os dois braços compartilham prompt de sistema e esquema de ferramentas, então a diferença no primeiro prompt é a diferença da primeira mensagem: **1.801 a 1.885 tokens na orquestração contra 2.022 no agente único** nas cinco repetições de 27/08 (7% a 11% menor), 1.847 contra 2.022 em tomlkit e 2.035 contra 2.449 em sqlite-utils em 11/09 (9% e 17% menor). A intent reescrita é **mais curta** que o enunciado cru em todas as nove comparações. A hipótese "intent maior" cai sem ablação. Fica a hipótese complementar, compatível com a decomposição acima e não testada: a intent mais curta descarta detalhe que o enunciado trazia, e o desenvolvedor recupera esse detalhe lendo mais código. A ablação do refinador continua sendo o experimento que separa essa causa de uma diferença de estilo de leitura induzida pelo próprio grafo; agora ela tem uma previsão quantitativa a confirmar: sem o refinador, os bytes lidos por `read_file` no braço orquestrado devem cair na direção dos 8.946 do agente único.

## 5. O que muda daqui em diante

- Toda execução nova carrega `prompt_bytes` em cada chamada. O script entra automaticamente em modo exato e confere, chamada a chamada, se os bytes de ferramenta no prompt são exatamente os bytes registrados pelos eventos de ferramenta. Qualquer texto que chegue ao modelo sem evento (ferramenta desconhecida, argumento inválido, chamada acima do teto por turno; escapes E2 a E4 do inventário) aparece como divergência positiva na chamada seguinte.
- O tamanho da primeira mensagem de cada braço passa a ser dado medido, não reconstruído. A comparação da seção 4 deve ser refeita em bytes na primeira coleta paga (o teste de fumaça do cronograma).
- A análise de crescimento de contexto do resumo científico (leituras 34 contra 22) fica substituída pela decomposição da seção 4, que mede bytes e não contagem de leituras.

## 6. Limitações desta etapa

- O modo inferido depende de um ajuste com dois parâmetros; a discrepância de 5% a 10% inclui variação legítima da densidade de tokens. Não é possível, sem tokenizador local, separar essa variação de conteúdo pequeno não medido. O modo exato elimina a dúvida para execuções futuras.
- Nas execuções antigas do braço orquestrado, a primeira mensagem não pode ser reconstruída (a intent gerada não foi gravada), então "prompt de sistema + esquema + primeira mensagem" fica agregado.
- O esquema das ferramentas e o enquadramento de mensagens não são mensagens: no modo exato, os tokens que o provedor cobra além dos bytes das mensagens são repartidos proporcionalmente entre as categorias.
- Reasoning tokens são zero neste modelo em todas as execuções; a conta não foi testada com modelos que os produzem.

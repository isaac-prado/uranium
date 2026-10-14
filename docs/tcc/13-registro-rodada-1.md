# Registro detalhado da rodada 1 da coleta definitiva (12 a 14/10/2026)

Documento de registro para o TCC: o que foi executado, com que configuração, o que saiu, por que saiu assim e o que fica para o texto. Toda cifra tem o arquivo de origem ao lado. Complementa [12-coleta-resultados.md](12-coleta-resultados.md) (resultado e diagnóstico), [11-coleta-grandes.md](11-coleta-grandes.md) (faixa grande), `dados/coleta/apendice-metricas.md` (componentes por run) e [09-decisoes-do-autor.md](09-decisoes-do-autor.md) (decisões, com data).

## 1. Linha do tempo

| quando | o quê | fonte |
|---|---|---|
| 08 a 09/10 | oito fumaças de calibração na `tomlkit-0004` (A a H), BYOK no DeepInfra, memória de trabalho (decisão 8 revista) e ciclos de 40 turnos (decisão 25) | [07-e4-fumaca.md](07-e4-fumaca.md) |
| 12/10 | tetos congelados (decisão 12): 120 turnos, 8 M tokens, 3.600 s | `src/budget.py`, `CLAUDE.md` |
| 12/10 21:09 a 22:18 | etapa 1: faixa grande, 18 células, 0 perdas, US$ 4,31 | `dados/coleta/collection-grandes.log` |
| 12/10 22:19 a 23:53 | etapa 2 iniciada; 14 células; a máquina reinicia às 23:53 e mata a tentativa `sqlite-utils-0003/single-agent/rep01/attempt01` (US$ 0,08) | `collection-etapa2.log`, `uptime -s` |
| 13/10 08:17 a 15:31 | retomada; a célula interrompida roda como `attempt02` com a mesma semente; 78/78 concluídas | `collection-etapa2b.log`, `collection.json` |
| 13/10 | análises de registro e operacional; relatório | `dados/coleta/analise-*.md` |
| 14/10 | apêndice de métricas; diagnóstico das perdas; checagem da suíte visível com a referência; ablação do refinador iniciada | `apendice-metricas.md`, `checagem-suite-visivel-referencia.txt`, `runs/ablacao-refinador/` |

## 2. Configuração (manifesto v7, idêntico nos 78 runs salvo `arm`, `topology`, `run_id`, `started_at`, `orchestration_policy`/`driver_policy`)

| chave | valor | onde |
|---|---|---|
| modelo | `qwen/qwen3-coder`, DeepInfra, chave própria (BYOK), `provider_served` = DeepInfra em 100% das chamadas | `manifest.json: llm`, `events.jsonl` |
| semente | `seed_for_repetition(20260820, k)`: 20260821, 20260822, 20260823; igual nos dois braços | `manifest.json: llm.seed` |
| orçamento | 120 turnos, 8.000.000 tokens, 3.600 s, timeout de suíte 120 s | `manifest.json: budget` |
| ferramentas | as mesmas 7, na mesma ordem, mesmos limites (`shared_limits`) | `tests/test_arm_parity.py` |
| orquestrado | `developer_memory=ledger`, `developer_cycle_max_turns=40`, `max_semantic_rejections=2`, `semantic_review=true`, `developer_input=intent` (implícito em v7) | `manifest.json: orchestration_policy` |
| single-agent | driver determinístico: enunciado íntegro uma vez; suíte rodada quando o agente para de agir; feedback de `src/feedback.py` | `manifest.json: driver_policy` |
| prompt de sistema | idêntico (`src/prompts.py`) | `tests/test_arm_parity.py` |

## 3. Execução: números brutos

| | single-agent | orchestration | fonte |
|---|---:|---:|---|
| runs admitidos | 39 | 39 | `analise-sete-metricas.md` (78/78) |
| resolvidos | 25 | 17 | `apendice-metricas.md` A |
| tokens | 100.644.191 | 40.611.860 | soma de `cost.tokens_total` |
| US$ | 12,05 | 5,21 | soma de `cost.cost_usd` |
| chamadas ao modelo (mediana) | 80 | 78 | `apendice-metricas.md` A |
| parede s (mediana) | 271 | 221 | idem |
| conclusão sem corte | 26/39 | 23/39 | idem |
| cortes por turnos / tokens / parede | 8 / 5 / 0 | 16 / 0 / 0 | `summary.json: stop_reason` |
| negações de ferramenta | 11 | 39 (33 em escrita na área de testes) | `process.tool_denials`, `events.jsonl` |
| avisos do detector (C6) / críticos | 8 / 0 | 5 / 0 | `cheat` |
| execuções da suíte pelo harness (mediana por run) | 1 | 2 | `process.test_runs` |
| `run_tests` pelo agente (mediana) | 2 | 3 | `events.jsonl` |
| `read_file` (mediana) | 14 | 20 | idem |

## 4. Resultado por tarefa (runs resolvidos de 3) e compressão do enunciado pela intent

| tarefa | faixa | SA | OR | enunciado (chars) | intent (chars) | razão | fonte |
|---|---|---:|---:|---:|---:|---:|---|
| tomlkit-0002 | grande | 1 | 1 | 3.244 | 1.539 | 0,47 | `statement.md`; evento `intent` rep. 1 |
| tomlkit-0003 | grande | 3 | 3 | 2.562 | 1.775 | 0,69 | |
| tomlkit-0004 | grande | 0 | 0 | 6.558 | 1.959 | 0,30 | |
| attrs-0001 | média | 3 | 2 | 3.400 | 1.614 | 0,47 | |
| peewee-0001 | média | 3 | 2 | 4.448 | 1.680 | 0,38 | |
| peewee-0002 | média | 2 | 0 | 9.574 | 1.604 | 0,17 | |
| sqlite-utils-0003 | média | 2 | 0 | 5.399 | 2.433 | 0,45 | |
| peewee-0003 | pequena | 3 | 3 | 2.113 | 1.578 | 0,75 | |
| pygments-0001 | pequena | 3 | 0 | 7.615 | 1.556 | 0,20 | |
| sqlite-utils-0001 | pequena | 1 | 0 | 2.713 | 1.398 | 0,52 | |
| sqlite-utils-0002 | pequena | 1 | 3 | 3.797 | 1.301 | 0,34 | |
| tomlkit-0001 | pequena | 3 | 2 | 1.251 | 913 | 0,73 | |
| tomlkit-0005 | pequena | 0 | 1 | 2.532 | 1.345 | 0,53 | |

As três tarefas em que o orquestrado não resolveu nenhuma repetição e o single-agent resolveu ao menos duas (`peewee-0002`, `pygments-0001`, `sqlite-utils-0003`) estão entre as quatro de maior compressão (razão 0,17, 0,20 e 0,45) e são as de enunciado mais longo (9.574, 7.615 e 5.399 caracteres), com trechos de reprodução e tabelas de saída esperada que a intent referencia sem carregar (seção 6 de [12-coleta-resultados.md](12-coleta-resultados.md)). A exceção é `sqlite-utils-0002` (razão 0,34, orquestrado 3 a 1), que é uma das três tarefas com critério de parada inalcançável (seção 6 abaixo).

## 5. As sete métricas e os testes (`dados/coleta/analise-sete-metricas.md`)

Ver [12-coleta-resultados.md](12-coleta-resultados.md), seção 2. Resumo: H1 não sustentada (sinal +2 −7 em 9 tarefas discordantes, p bilateral 0,18; unicaudal a favor de H1, 0,98); custo em tokens nas 5 tarefas resolvidas por ambos sem diferença (p 0,81); custo em dólares em todas as 13 tarefas menor no orquestrado (p 0,022, análise operacional); tempo, complexidade e consistência sem diferença interpretável. **A métrica 2 exigia 6 tarefas resolvidas por ambos ([03-metricas.md](03-metricas.md), seção 2) e só houve 5**: o Wilcoxon exato não pode atingir 5% com n = 5, como o documento de métricas previa como risco. A sensibilidade com censura relaxada (resolvida ao menos uma vez por ambos, n = 7) está em `apendice-metricas.md` C e não muda a conclusão.

## 6. Diagnóstico das perdas do orquestrado (seção 6 de [12-coleta-resultados.md](12-coleta-resultados.md))

Três mecanismos, separáveis: (1) a intent perde o que o enunciado especifica (D3), 9 runs "verde, aprovado, ocultos faltam"; (2) diante de suíte vermelha no ponto de checagem o developer desfaz ou reescreve (F3: a memória de trabalho guarda o que fez, não por quê), 8 runs "não convergiu"; (3) três tarefas (`pygments-0001`, `sqlite-utils-0002`, `tomlkit-0004`) têm "suíte visível verde" inalcançável com a correção certa, porque o patch de teste modifica testes visíveis ou um arquivo dourado protegido (`dados/coleta/checagem-suite-visivel-referencia.txt`): defeito de construção das tarefas, portão ausente em `scripts/validate_task.py`. Detalhe das três em [14-tres-tarefas-decisao.md](14-tres-tarefas-decisao.md).

## 7. O que a rodada 1 vale e o que não vale

**Vale.** Instrumento íntegro: 78/78 admitidos, zero perdas, chave própria em todas as chamadas, contabilidade de contexto fechando em 0,0%, nenhuma violação crítica, pareamento por semente, manifesto completo. Resultado principal com direção clara e explicação mecanística lida da telemetria, não especulada. Comparação de código gerado nas grandes com repetições.

**Não vale como veredito final sobre orquestração.** O protótipo tem três limitações que a telemetria expôs e que uma orquestração bem feita não teria: um refinador que comprime o enunciado em 17% a 75% e descarta exemplos (mecanismo 1); um revisor que julga sem executar e devolve falsos negativos (5 runs resolvidos reprovados ao menos uma vez); um developer que, sem o próprio raciocínio depois do reset, desfaz o que estava certo (mecanismo 2). E a seleção de tarefas tem um defeito de construção em 3 de 13 (mecanismo 3) que afeta os dois braços de forma assimétrica. A rodada 1 mede **este** protótipo contra **este** agente único; o que o texto pode afirmar é isso.

## 8. O que fica para o texto

- **Método › Procedimento:** seção 2 acima; decisões 12, 13, 14, 25; a interrupção por reinício e a regra de perda.
- **Resultados:** seção 2 de [12-coleta-resultados.md](12-coleta-resultados.md) e o apêndice; a tabela por tarefa com a razão de compressão.
- **Discussão:** os três mecanismos com os runs que os ilustram (`pygments-0001` r1/r3 revertendo até o verde; `tomlkit-0002` r2 reprovado quatro vezes com o oculto passando; `peewee-0002` com seis defeitos reduzidos a seis linhas).
- **Ameaças à validade:** n = 13, um modelo, ordem fixa no par, 5 em vez de 6 tarefas resolvidas por ambos, três tarefas com critério inalcançável, revisor sem execução.
- **Trabalhos futuros / rodada 2:** ablação do refinador (em curso), ablação da transcrição persistente, quinto portão de validação, reconstrução das três tarefas, segundo modelo.

## 9. Custo acumulado do estudo (DeepInfra, chave própria)

| item | US$ | fonte |
|---|---:|---|
| fumaças F, G, H (09/10) | 3,09 | `dados/fumaca-09-10-{f,g,h}` |
| coleta, 78 runs | 17,26 | `dados/coleta` |
| tentativa perdida (reinício) | 0,08 | `runs/coleta/sqlite-utils-0003/single-agent/rep01/attempt01/events.jsonl` |
| total | 20,43 | |
| saldo em 14/10 antes da ablação | ≈ 4,70 | painel do DeepInfra (relato do autor) |

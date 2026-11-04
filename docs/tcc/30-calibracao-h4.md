# 30. Calibração offline da hipótese H4: regras de parada do revisor final

**Data.** 04/11/2026. **Pedido do autor.** Antes de gastar em uma rodada nova, estimar sobre os dados existentes quanto uma calibração do revisor final do orquestrado economizaria e quanto custaria em aprovações erradas (hipótese H4 de [28-exploratorio-orquestrado.md](28-exploratorio-orquestrado.md) §3). **Fonte.** `dados/coleta-deepseek/calibracao-h4-offline.txt`, saída de `scripts/calibracao_h4.py` sobre os `events.jsonl` dos 117 runs orquestrados das coletas finais (Qwen rodada 4, DeepSeek V3.2, Devstral 2). Nenhum run novo; custo zero.

## 1. Método e limite

Cada run orquestrado é uma sequência de ciclos: developer (até 40 turnos), suíte visível rodada pelo validador, revisão final do modelo (aprova ou reprova). Uma regra de parada alternativa escolhe, em cada run, o ciclo em que teria aprovado; a partir dele os turnos restantes são economia. O desfecho do patch nesse ciclo só é conhecido quando nenhuma escrita de arquivo (`write_file` ou `replace_in_file` aceita) ocorreu depois dele: nesse caso o patch simulado é o patch final, que o oráculo já julgou. Quando houve escrita depois, o desfecho é incerto e entra nos dois limites: pessimista (viraria não resolvido) e otimista (mantém o desfecho final). O diff de cada ciclo não é gravado nos eventos, então não há como rodar o oráculo em estados intermediários; é a limitação desta calibração e a razão de ela produzir limites, não pontos.

Regras simuladas, todas condicionadas a suíte visível verde na validação do ciclo:

| Regra | Aprova quando |
|---|---|
| primeiro_verde | a primeira validação com suíte verde (é a regra de parada do agente único aplicada à trajetória do orquestrado) |
| concluiu+verde | a primeira validação com suíte verde em que o developer parou por "concluiu", não por teto do ciclo |
| patch_inalterado | o revisor reprovou com verde no ciclo anterior e o developer voltou sem escrever nada |
| teto_2, teto_3 | a segunda ou a terceira reprovação com suíte verde |

Linha de base real: 80 resolvidos, 8.354 turnos, 13 aprovações erradas, 10 resolvidos cortados por orçamento com o revisor nunca aprovando.

## 2. Resultado por regra

| Regra | turnos poupados | resolvidos com o mesmo patch (ganho certo) | resolvidos com patch alterado depois (incerto) | cortes que virariam aprovação errada | resolvidos: limite pessimista |
|---|---|---|---|---|---|
| primeiro_verde | 2.547 (30%) | 6 | 33 | 15 | 47 |
| concluiu+verde | 1.761 (21%) | 6 | 26 | 5 | 54 |
| patch_inalterado | 493 (6%) | 8 | 2 | 6 | 78 |
| teto_2 | 968 (12%) | 8 | 9 | 12 | 71 |
| teto_3 | 365 (4%) | 9 | 4 | 8 | 76 |

Leitura. Nenhuma regra corta metade dos turnos após o verde sem risco. A regra do agente único aplicada ao orquestrado (primeiro_verde) poupa 30% dos turnos, mas em 33 dos 39 runs resolvidos que tiveram reprovação com verde o developer reescreveu o patch depois da reprovação, e 15 cortes por orçamento virariam aprovações erradas. A única regra segura é patch_inalterado: 8 ganhos certos, 2 incertos, 6% dos turnos. **A forma forte de H4 é refutada pelos dados existentes.** O que ela revela de útil: as reprovações do revisor com suíte verde foram seguidas de reescrita na grande maioria dos runs resolvidos; o laço não é desperdício em geral, é desperdício em casos concentrados.

## 3. Onde está o desperdício: blocos de reprodução que não compilam

Das 136 reprovações finais com suíte verde nos 117 runs, **58 citam `SyntaxError`** na execução dos blocos de reprodução da intent (Qwen 28 de 66, DeepSeek 16 de 39, Devstral 14 de 31). São blocos que o refinador copiou do enunciado com aspas ou escapes quebrados; o validador os executa, o Python falha antes de chegar ao parser, e o revisor lê a falha como "o critério não foi demonstrado" e reprova um patch que o oráculo depois aprova. Dezesseis runs foram afetados, 15 deles resolvidos, com 885 turnos gastos depois da primeira reprovação desse tipo (11% de todos os turnos do orquestrado). O caso extremo é a tomlkit-0001, tarefa de um teste oculto: em seis runs de três modelos o revisor reprovou o patch correto 4, 5, 5, 5, 7 e 9 vezes; os seis blocos do enunciado são linhas TOML como `a = [{a]` que, embrulhadas numa string Python, viram erro de sintaxe. Cinco dos dez "resolvidos mas cortados" da linha de base são tomlkit-0001 com o patch inalterado desde o primeiro ciclo.

A correção já existe no harness: `REPRODUCTION_COMPILE_CHECK=on` (rodada 6, decisão 42) compila cada bloco antes de executar e tira da revisão o que não compila, e `REPRODUCTION_SOURCE=statement` (rodada 8, decisão 48) conserta a cópia pelo enunciado. A configuração da rodada 4, escolhida pela regra da rodada decisiva e usada na replicação, tem as duas desligadas. A comparação entre rodadas no Qwen mostra o efeito:

| Tarefa | rodada 4: reprovações com verde por run, turnos | rodada 8: reprovações com verde por run, turnos |
|---|---|---|
| tomlkit-0001 | 7, 0, 5; 120, 32, 120 | 0, 0, 0; 34, 29, 47 |
| tomlkit-0003 | 4, 4, 2; 81, 120, 102 | 0, 0, 0; 40, 31, 34 |
| sqlite-utils-0003 | 2, 5, 1; 73, 114, 70 | 4, 1, 1; 94, 58, 52 |
| pygments-0001 | 3, 1, 1; 62, 56, 51 | 1, 3, 1; 60, 120, 104 |

Nas duas tarefas em que o `SyntaxError` era a causa, a rodada 8 zera as reprovações e corta os turnos a um terço; nas outras duas a causa é outra (critérios sem exemplo executável) e a rodada 8 não ajuda. A rodada 8 difere da 4 em mais chaves, então a comparação é indicativa, não causal.

## 4. H4 reformulada

- **H4a (evidência que compila).** Ligar `REPRODUCTION_COMPILE_CHECK=on` e `REPRODUCTION_SOURCE=statement` sobre a configuração da rodada 4 elimina as reprovações com suíte verde causadas por bloco que não compila, poupando da ordem de 10% dos turnos do orquestrado e convertendo em aprovação ao menos 5 dos 10 resolvidos cortados, sem aumentar as aprovações erradas. Testável numa rodada 9 de 39 runs com o Qwen, custo esperado próximo ao da rodada 4 (US$ 5,67), sob aprovação do autor.
- **H4b (válvula de segurança).** A regra patch_inalterado, somada a H4a, poupa mais 6% dos turnos com no máximo 2 resoluções em risco.
- **Retirado.** Aprovar no primeiro verde, ou com teto de 2 ou 3 reprovações, está fora: põe de 9 a 33 resoluções em risco.

## 5. O que muda no texto do TCC

- A afirmação A5 (o revisor resgata) ganha apoio: em 33 dos 39 runs resolvidos com reprovação após o verde, o developer reescreveu o patch depois da reprovação.
- A afirmação A9 (as perdas têm causa de desenho) ganha a causa concreta: 43% das reprovações com suíte verde vêm de evidência que não compila, defeito do instrumento já corrigido em rodadas posteriores e desligado na configuração decisiva.
- A hipótese H4 do pacote de redação ([29-pacote-redacao.md](29-pacote-redacao.md) §5.4) passa a ser H4a e H4b, com os números desta calibração.
- Ameaça à validade a declarar: a regra da rodada decisiva escolheu a configuração pela resolução por tarefa e carregou para a replicação um defeito de evidência que as rodadas 6 a 8 já tinham corrigido.

## 6. Fontes

`dados/coleta-deepseek/calibracao-h4-offline.txt` (todas as tabelas); `scripts/calibracao_h4.py`; eventos em `docs/tcc/dados/coleta-r4`, `runs/coleta-deepseek`, `runs/coleta-devstral`, `docs/tcc/dados/coleta-r8`; decisões 42 e 48 em `09-decisoes-do-autor.md`; `tasks/tomlkit-0001/statement.md`.

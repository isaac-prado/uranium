# E3 item 1: remineração em três faixas (pequena/média/grande)

Isaac do Prado Almeida · Orientadora: Isabela Neves Drummond · 19 de setembro de 2026
Etapa E3, item 1 de [EXIGENCIAS.md](tasks/EXIGENCIAS.md): "amplie a rede" (o corte de `--limit 25/30` e os tetos `MAX_ARQUIVOS_FONTE=6`/`MAX_LINHAS_FONTE=400` filtraram os candidatos multi-arquivo, não a escassez de histórico) e relatar quantos candidatos cada faixa rende em cada repositório. Item 4 (aceitação só por execução) mantido sem alteração de princípio. Itens 2 (faixa até `result.json`) e 3 (breaking change) são de outros agentes — ver [docs/tcc/07-e3-3-breaking-change.md](07-e3-3-breaking-change.md) para o item 3. Avisos do coordenador durante a execução e a revisão do autor sobre os aceitos de `mined-v2` levaram a quatro correções (seção 6.1 a 6.4). Ferramenta: [scripts/mine_tasks.py](../../scripts/mine_tasks.py); testes em [tests/test_mine_tasks.py](../../tests/test_mine_tasks.py). Todo número vem de `mined-v2/*.json` ou de `mined-v1/*.json`, caminho ao lado.

## 1. Regra operacional das faixas novas

`faixa` deixou de ser `baixa/media/alta` (regra antiga: 1 arquivo e <30 linhas = baixa; ≤3 arquivos = media; resto = alta — [scripts/mine_tasks.py, HEAD anterior a esta etapa, linhas 82-90 do commit `d47abda`](../../scripts/mine_tasks.py)) para `pequena/media/grande`, calculada por `calcular_faixa` ([scripts/mine_tasks.py:159-198](../../scripts/mine_tasks.py#L159)), função pura dos campos medidos — sem git, sem suíte. Testes de cada faixa e de cada limite em [tests/test_mine_tasks.py](../../tests/test_mine_tasks.py) (`TestFaixaPequena`, `TestFaixaMedia`, `TestFaixaGrande`, `TestForaRegistraMotivo`; 70 testes no arquivo depois da revisão da seção 6.4, todos verdes).

| Faixa | Critério implementado (versão final, pós-revisão — seção 6.4) | Por quê |
|---|---|---|
| **Pequena** | 1 a 2 arquivos-fonte **e** 10 a 50 linhas de patch; OU 3+ arquivos-fonte com **menos de 40 linhas** (com `motivo_faixa` explicando) | É a tabela da exigência ao pé da letra na primeira metade. A segunda metade entrou na revisão do autor (seção 6.4): sem ela, `peewee b8a336d0` (3 arquivos, 11 linhas) saía como média só por tocar 3 arquivos, não por dificuldade real. |
| **Média** | 3 a 7 arquivos-fonte, em **2 ou mais módulos distintos**, **40 a 400 linhas** | "Módulo" é o diretório que contém o arquivo (`calcular_modulos_fonte`) — não o AST, é caminho. Dois arquivos na mesma pasta são o mesmo módulo; um arquivo solto na raiz do repositório (caso de `peewee.py` ao lado de `playhouse/`) é módulo próprio. O piso de 40 linhas entrou na revisão do autor (seção 6.4), pelo mesmo caso `b8a336d0`. |
| **Grande** | 3+ arquivos-fonte, 80+ linhas, `fail_to_pass` com mais testes **novos** que **modificados**, mensagem que não começa com "fix"/"bug" | O teste novo maioritário é o proxy de "funcionalidade nova com teste escrito pelo próprio projeto" da tabela da exigência; teste majoritariamente modificado é sinal de correção que altera comportamento de teste existente, não funcionalidade nova (ver `docs/tcc/07-e3-3-breaking-change.md`). A mensagem que não é de correção é o segundo filtro textual barato pelo mesmo motivo. |
| **Fora** | Nenhum dos critérios acima | Registrado com `faixa="fora"` e o motivo (`motivo_faixa`) — não é descartado da lista bruta do pré-filtro, só não é verificado por execução (custaria suíte à toa). |

Prioridade de checagem: **grande → média → pequena (com a cláusula de tamanho por último)** (`calcular_faixa`, `scripts/mine_tasks.py`). Um candidato grande também cabe nos limites soltos de arquivos/linhas da média; checar a pequena primeiro nunca deixaria nada sobrar para as faixas maiores.

**"Arquivos-fonte" tem duas condições, também da revisão do autor (seção 6.4):** só conta `.py` **dentro do `source_dir`** declarado no `SeedRepoSpec` do repositório (`_em_source_dir`), e um arquivo **apagado** pelo commit vai para `arquivos_fonte_apagados`, não para `arquivos_fonte`/`linhas_fonte` — não representa dificuldade de correção, representa limpeza.

**Campos novos no `Candidato`**: `modulos_fonte` (contagem), `testes_novos`/`testes_modificados` (contagem de funções `def test_` adicionadas/alteradas no diff dos arquivos de teste, heurística de diff unificado documentada em `contar_testes_novos_e_modificados`), `altera_testes_existentes` (bool, `testes_modificados > 0` — insumo do item 3/breaking change, não usado para excluir candidato), `arquivos_fonte_apagados` (lista, seção 6.4), `toca_protegido` (bool, seção 6.4).

**Tetos ampliados** (`scripts/mine_tasks.py`): `MAX_ARQUIVOS_FONTE` 6 → 12 e `MAX_LINHAS_FONTE` 400 → 800, o suficiente para caber a faixa média (até 7 arquivos, até 400 linhas) e dar folga à grande (3+, 80+, sem teto superior de arquivo além do MAX geral). `MIN_LINHAS_FONTE` continua 3.

## 2. Pré-filtro barato antes de executar suíte

Rodar a suíte por candidato custa 3 rodadas — no peewee, medido nesta etapa, 97 a 185s por candidato na faixa pequena (seção 4), bem acima dos 23,7s citados no cronograma para uma rodada só. Examinar o histórico amplo (peewee: 5.169 commits sem merge) executando a suíte em cada candidato seria inviável.

`levantar_candidatos` ([scripts/mine_tasks.py:266-341](../../scripts/mine_tasks.py#L266)) faz só `git log --name-status -M` (um comando, todo o histórico ou desde `--desde`) mais, por candidato que sobra do primeiro corte, um `git diff --numstat -M` e um `git diff -M` dos arquivos de teste — nenhum checkout, nenhuma suíte. Classifica fonte/teste pelos globs protegidos do repo (`_classificar_status`, [scripts/mine_tasks.py:279-355](../../scripts/mine_tasks.py#L279)), calcula a faixa provisória (`calcular_faixa`) e descarta ruído (mensagens de `RUIDO`) e candidatos sem fonte ou sem teste. Isto sozinho já classifica os cinco repositórios-semente (3 antigos + 2 novos) em segundos — ver coluna "commits no histórico" e "candidatos pré-filtro" da tabela da seção 4, calculadas em 1,3 a 9,9s por repositório (medido; script `regen_relatorio.py` de apoio não faz parte do minerador, só recalcula o total de commits para este relatório a partir do mesmo `levantar_candidatos`).

Só depois do pré-filtro, `minerar` ([scripts/mine_tasks.py:398-451](../../scripts/mine_tasks.py#L398)) verifica por execução (`avaliar`, as três rodadas de suíte do desenho original) **na ordem grande → média → pequena**, com dois tetos novos:

- `--max-verificar-por-faixa N` (padrão 30): não verifica mais que N candidatos de cada faixa.
- `--parar-em N` (padrão 12): para de verificar uma faixa assim que acumular N aceitos nela.
- `--desde <data|commit>` (opcional): restringe `git log` a partir de uma data ISO ou de um commit (tenta resolver como commit primeiro; se não for, usa `git log --since`).

Saída em `mined-v2/<repo>.json` — mesmo formato de `mined-v1` mais os campos novos — e `mined-v2/RELATORIO.md`, gerado pelo próprio script (`escrever_relatorio_md`, [scripts/mine_tasks.py:454-481](../../scripts/mine_tasks.py#L454)) com a tabela de contagens por repositório e faixa e os motivos de rejeição agregados. `mined-v1/` não foi apagado.

## 3. Repositórios novos

Autorização e sugestão do autor: os três repositórios atuais são "desorganizados"; buscar repositórios famosos com histórico organizado. Critérios de aceite (do enunciado da tarefa): suíte < 60s, sem rede, sem serviços externos, testes em diretório protegível pelos globs padrão (`tests/**`). Levantamento feito em espelhos e venvs descartáveis (fora de `.uranium/`, em `/tmp/.../scratchpad/survey/`), não nos espelhos do projeto, até decidir o aceite.

### 3.1 Aceitos (2 de 3 possíveis)

| Repositório | Suíte no HEAD | Suíte ~1 ano atrás | Pré-filtro (pequena/média/grande/fora) | Observação |
|---|---|---|---|---|
| **pygments** ([SeedRepoSpec](../../src/seeds.py)) | 5.330 passed, 16 skipped, **9,86s**, verde (`scripts/setup_mirror.py pygments --check`) | 5.051 passed, 16 skipped, 9,65s, verde (commit `5da0e25`, 2024-09-14) | 372 / 39 / 3 / 709 (de 1.123 pré-filtrados em 6.197 commits) | Pacote com subpacotes de verdade (`lexers/`, `formatters/`, `filters/`, `styles/`) — foi o achado da etapa: com `calcular_modulos_fonte` medindo por diretório (não só o primeiro componente do caminho), é o repositório com mais candidato média dos cinco. Precisou de `wcag-contrast-ratio` extra (`tests/contrast/test_contrasts.py`) e da correção de encoding da seção 6.2. |
| **tqdm** ([SeedRepoSpec](../../src/seeds.py)) | 169 passed, 10 skipped, **16,97s**, verde | idem à mesma suíte, mesma árvore de teste — não há commit de 1-2 anos atrás com layout muito diferente; verificado no HEAD e aceito pelo tempo de execução, que é o critério de aceite | 43 / 17 / 0 / 43 (de 103 pré-filtrados em 1.822 commits) | Precisou de `pytest-asyncio` e `pytest-timeout` (arquivo `pyproject.toml` do tqdm declara `timeout = 30` e `--asyncio-mode=strict`; sem os plugins, pytest recusa a opção de config com `INTERNALERROR`). Zero candidato grande no pré-filtro — pacote pequeno e estável. |

Ambos com `scripts/setup_mirror.py <repo> --check` verde nesta máquina (`.uranium/mirrors/pygments.git`, `.uranium/mirrors/tqdm.git`, `.uranium/venvs/pygments`, `.uranium/venvs/tqdm`), registrados em `src/seeds.py` (`PYGMENTS`, `TQDM`) e minerados para `mined-v2/` (seção 4).

### 3.2 Descartados, e por quê

| Repositório | Motivo | Evidência |
|---|---|---|
| **click**, **jinja**, **marshmallow**, **attrs** | Layout `src/<pacote>/`, não pacote solto na raiz do repositório. O harness materializa o workspace só com `git clone` (`Workspace.materialize`, `src/workspace.py`) e roda a suíte sem instalar nada (`run_pytest`, `src/tools/exec.py`) — funciona nos 3 repositórios atuais e em pygments/tqdm porque o pacote fica em `<repo>/<pacote>/`, alcançável pelo mecanismo padrão do pytest sem instalação. Com pacote em `src/`, `import click` falha (`ModuleNotFoundError: No module named 'click'`, testado à mão numa clonagem limpa sem `pip install`). Registro para quem decidir se vale mudar essa convenção do harness: eram os **melhores em densidade de candidato médio/grande** dos oito examinados — jinja com 24 candidatos grande no pré-filtro (2.175 commits), marshmallow com 9 grande e 17 média (3.028 commits), click com 8 grande e 6 média (2.162 commits), attrs com 11 grande mas só 2 média (1.826 commits). A correção ficaria em `src/workspace.py`/`src/tools/exec.py`, fora do meu escopo nesta etapa (não são meus arquivos) — **não implementada sem aprovação**, conforme a regra de não substituir o impossível por alternativa. |
| **boltons** | Suíte ótima (519 passed, 2,29s, verde, zero instalação), mas pacote **inteiramente plano** (todo `.py` solto direto em `boltons/`, sem subpacote) — sob `calcular_modulos_fonte`, qualquer patch cai em 1 módulo só. Pré-filtro: 97 pequena / 1 média / 0 grande em 215 candidatos (1.548 commits). Não rende média nem grande o suficiente para justificar a terceira vaga. |
| **babel** | Precisa de dado de locale (CLDR) gerado por um passo de build (`import_cldr`) que não está no repositório (`babel/locale-data/` só tem o arquivo de licença, sem os `.dat`); sem isso, `Locale('en')` já falha na coleta (`babel.core.UnknownLocaleError`). Envolveria inicializar o submódulo `cldr/` e rodar o gerador a cada preparo de espelho — mais frágil que os demais candidatos, descartado pelo tempo disponível na etapa. |
| **pydantic** | Descartado sem rodar a suíte inteira, por evidência acumulada: espelho bare **472 MB** (ordens de grandeza acima dos outros sete, todos abaixo de 40 MB), `pydantic-core` é extensão Rust (risco de build demorado sem wheel pré-compilada para esta versão de Python), e `[dependency-groups].dev` inclui `pytest-examples`, `dirty-equals`, `faker`, `jsonschema`, `pytest-benchmark`, `pytest-codspeed`, `pytest-run-parallel` — superfície de dependência de teste muito maior que os demais. Confirma o palpite do próprio autor ("provavelmente pesado demais"). |
| **requests** | Suíte não termina em 60s: `pytest tests` com o ambiente de teste declarado (`pytest-httpbin`, `httpbin`, `trustme`) **travou** e foi interrompida por timeout de 60s sem produzir resumo. Confirma o palpite do autor ("testes com rede, provavelmente não") — não investigado further pelo tempo disponível. |

## 4. Contagens por repositório e faixa

Números finais, **depois** da reclassificação da seção 6.4. Fonte: `mined-v2/RELATORIO.md` (gerado pelo script) e `mined-v2/*.json`. Tetos usados: `--max-verificar-por-faixa 30 --parar-em 12` (padrão), histórico completo (sem `--desde`).

| repositório | commits no histórico | pré-filtro grande | pré-filtro média | pré-filtro pequena | pré-filtro fora | pré-filtro protegido | verificados grande | verificados média | verificados pequena | aceitos grande | aceitos média | aceitos pequena | tempo (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tomlkit | 489 | 6 | 0 | 18 | 90 | 15 | 7 | 0 | 14 | 3 | 0 | 12 | 63,8 |
| peewee | 5.169 | 3 | 12 | 36 | 404 | 96 | 3 | 15 | 34 | 0 | 2 | 12 | 3.394,6 |
| sqlite-utils | 1.196 | 2 | 0 | 18 | 174 | 20 | 4 | 0 | 14 | 0 | 0 | 12 | 258,3 |
| pygments | 6.197 | 3 | 17 | 31 | 688 | 15 | 3 | 16 | 20 | 0 | 0 | 12 | 413,1 |
| tqdm | 1.822 | 0 | 0 | 27 | 25 | 38 | 0 | 6 | 33 | 0 | 0 | 7 | 1.189,9 |

`tempo_total_s` é a soma de `segundos` de todos os candidatos registrados do repositório (inclusive os "fora"/"protegido", que não consomem suíte — o grosso do tempo é mesmo a verificação por execução).

**Aceitos totais por faixa, somando os cinco repositórios** (`aceito=True`, contagem direta em `mined-v2/*.json`):

| faixa | tomlkit | peewee | sqlite-utils | pygments | tqdm | total |
|---|---:|---:|---:|---:|---:|---:|
| grande | 3 | 0 | 0 | 0 | 0 | **3** |
| média | 0 | 2 | 0 | 0 | 0 | **2** |
| pequena | 12 | 12 | 12 | 12 | 7 | **55** |

**Achado que precisa da decisão do autor:** a exigência pede 4 tarefas em cada faixa (12 no total). Pequena está bem servida (55 aceitos). **Média tem só 2 candidatos aceitos no total** (ambos peewee) e **grande tem só 3** (todos tomlkit) — nenhuma das duas faixas chega a 4. Não é falta de candidato no pré-filtro (peewee sozinho tem 12 pré-filtrados em média, pygments 17), é que a verificação por execução (item 4 da exigência, mantido) rejeitou a maior parte: pré-existência de teste que já passa sem a correção, suíte que não roda na base (seções 6.1/6.2) e, agora, referência tocando protegido (seção 6.4) comem a maioria dos candidatos de média/grande antes de chegar a 4 aceitos. Não ampliei `--max-verificar-por-faixa` além de 30 nem apliquei `--desde` para tentar aumentar essas duas faixas — ficaria fora do tempo desta etapa e é uma decisão de custo (mais suíte rodada) que cabe ao autor aprovar antes.

## 5. Melhores candidatos por faixa (insumo para as 12 tarefas)

Todos os aceitos de grande e média (só 3 e 2, listados inteiros); pequena tem 55 aceitos — 3 exemplos por repositório aqui, lista completa em `mined-v2/<repo>.json` (campo `aceito`).

### Grande (3 aceitos, todos tomlkit)

| repositório | fix_commit | subject | arquivos | linhas | testes novos/mod. | f2p arquivos |
|---|---|---|---:|---:|---:|---:|
| tomlkit | `0561e5de` | Support adding with dotted key | 4 | 163 | 1 / 0 | 1 |
| tomlkit | `b29cdf0c` | Ensure dict compliance for containers | 4 | 169 | 1 / 0 | 1 |
| tomlkit | `eedcdb25` | Add support for dotted keys | 3 | 101 | 2 / 1 | 3 |

### Média (2 aceitos, ambos peewee)

| repositório | fix_commit | subject | arquivos | linhas | testes novos/mod. | f2p arquivos |
|---|---|---|---:|---:|---:|---:|
| peewee | `ab1266aa` | Add proper API for hooking query execution for observability/etc. | 3 | 54 | 5 / 0 | 1 |
| peewee | `08b28d14` | commit/rollback on a closed connection will raise rather than re-open. | 6 | 72 | 5 / 0 | 4 |

### Pequena (55 aceitos — 3 por repositório, amostra)

| repositório | fix_commit | subject | arquivos | linhas |
|---|---|---|---:|---:|
| tomlkit | `94e62fbe` | Float is not a sequence (#563) | 1 | 19 |
| tomlkit | `495a42ec` | Fix top-level scalar captured by a table rendered from a dotted key | 1 | 24 |
| tomlkit | `67d3e865` | Fix array of tables replacing a dotted key swallowing the next sibling | 1 | 12 |
| peewee | `b8a336d0` | Allow specifying a default `lock_type` for sqlite txns. | 3 | 11 |
| peewee | `b1faea2b` | Populate `choices` from enum values for enum fields. | 2 | 11 |
| peewee | `73d3c7e6` | Fix #3075, support enumfield in migrations. | 2 | 20 |
| sqlite-utils | `e4935e06` | transform: coerce empty strings to NULL when converting TEXT columns | 1 | 21 |
| sqlite-utils | `e6be6267` | Use quote_identifier() in indexes/xindexes PRAGMA statements (#829) | 1 | 14 |
| sqlite-utils | `c5063f67` | Use quoted SQL identifiers in convert --dry-run, closes #829 | 1 | 10 |
| pygments | `9c436b34` | Go lexer improvements (#3199) | 1 | 26 |
| pygments | `8f184919` | Speed up HtmlFormatter token escaping with quote=False | 1 | 11 |
| pygments | `c1376e05` | Lua lexer modifications (#3143) | 2 | 22 |
| tqdm | `99615b97` | asyncio: add gather(return_exceptions=False) (#1776) | 1 | 10 |
| tqdm | `55156ce4` | fix: apply disp_trim to all format_meter return paths (#1658) | 1 | 10 |
| tqdm | `f83290ce` | Fix TMonitor deadlock at interpreter shutdown | 1 | 16 |

## 6. Correções feitas durante a etapa (avisos do coordenador e revisão do autor)

Quatro falhas foram reportadas durante a execução desta etapa (duas pelo coordenador, uma pela revisão do autor sobre os aceitos de `mined-v2`) e corrigidas dentro do escopo de `src/seeds.py`/`scripts/mine_tasks.py` (meus arquivos), sem tocar `harness/`.

### 6.1 Suíte do peewee vermelha no HEAD (protocolo `load_tests`)

O upstream do peewee mudou `tests/__init__.py` no commit `fd04f2af` ("Test cleanup", 2026-09-03): de `from .x import *` (que fazia as classes de teste aparecerem no namespace do próprio arquivo, e por isso `suite_targets=("tests/__init__.py",)` funcionava) para o protocolo `load_tests` do `unittest` (`from . import x` mais uma função `load_tests(loader, tests, pattern)`). `unittest.discover` honra esse protocolo (1.826 testes, verde); **pytest não** — é documentado que pytest não suporta `load_tests`, então `pytest tests/__init__.py` sozinho não encontrava teste nenhum (exit code 5), quebrando `tests/test_seed_repos.py::test_roda_inteira_e_passa[peewee]`.

Correção em `src/seeds.py` (comentário completo acima de `PEEWEE`): `suite_targets` agora lista, em arquivos explícitos e na ORDEM de `MODULES` do upstream, os módulos que `tests/__init__.py` importa incondicionalmente (a lista `MODULES` de lá menos os que só entram com dependência opcional ausente: apsw, cysqlite, flask, fts, postgres, sqlcipher, `pwasyncio`/`pydantic`, nenhuma instalada neste venv). A ordem importa de verdade: `tests/model_sql.py::TestModelSQL::test_delete_recursive` vaza estado de `tests/models.py` e falha se `model_sql` rodar antes de `models` (o que a ordem alfabética de diretório faz, mas a ordem de `MODULES` não). Com a lista ordenada: **1.438 passed, 173 skipped, 0 failed em 4,3s** (medido nesta máquina, HEAD `9d495208` do espelho) — muito mais rápido que os 23,7s citados no cronograma para uma rodada da suíte antiga.

Ressalva de cobertura histórica, registrada no comentário do código: dois dos arquivos da lista são recentes (`with_related_tests.py` desde 2026-06-14, `schema_diff.py` desde 2026-08-02); os demais existem desde 2017-03 a 2019-11. Minerar um commit-base anterior à criação de um desses arquivos faz o passo 0 (suíte verde no pai) falhar com "arquivo não encontrado" — visível na mineração desta etapa: na primeira leva de candidatos-média do peewee (2013-2017, era de introdução de `playhouse/`, `db_url.py`, `signals` etc.), as verificações mais antigas dessa faixa recusaram com o texto antigo "commit-base já vermelho (0 falhas)" — hoje soaria "suíte não executa na base" (seção 6.2), mas esse `mined-v2/peewee.json` é anterior a essa correção de rótulo (ver nota no fim da seção 6.2) — não é falso positivo de correção, é o `suite_targets` fixo não alcançando um layout de teste anterior à sua própria criação; commits mais recentes da mesma faixa (`ab1266aa`, `08b28d14`) foram aceitos normalmente (`mined-v2/peewee.json`). `PISO_DE_COLETA["peewee"]` em `tests/test_seed_repos.py` ajustado de 1500 para 1400 (a antiga assumia coleta de ~1.634 pela suíte via star-import; a nova lista explícita coleta 1.611 — 1.438 passed + 173 skipped).

### 6.2 "Suíte não executa na base" ≠ "base vermelha" (achado do coordenador: sqlite-utils)

No `mine_v2.log`, 35 candidatos do sqlite-utils foram recusados como "commit-base já vermelho (0 falhas)" em 0,1 a 0,2s — tempo curto demais para rodar 1.400+ testes de verdade. Diagnóstico manual (materializando a base de um dos recusados e rodando a suíte à mão): `ModuleNotFoundError: No module named 'typing_extensions'`. Desde agosto de 2026 `sqlite_utils/db.py` faz `from typing_extensions import Self` incondicionalmente, mas `typing_extensions` **não está** em `[project.dependencies]` do `pyproject.toml` do sqlite-utils (conferido no HEAD do espelho) — dependência usada mas nunca declarada, e como o venv do repositório-semente é minimalista (só o que está pinado em `test_requirements`), faltava.

Correção em duas frentes:

1. **`src/seeds.py`**: acrescentado `"typing-extensions==4.16.0"` a `SQLITE_UTILS.test_requirements`, com comentário explicando a origem do gap. `scripts/setup_mirror.py sqlite-utils --update --check` confirma HEAD verde (1488 passed, 16 skipped, 7,4s); o commit diagnosticado (`e4935e06^`) que antes dava `ModuleNotFoundError` passa a rodar 1483 passed, 16 skipped, 6,45s.
2. **`scripts/mine_tasks.py`**: `_suite_nao_executou(relatorio)` (`passed == 0 and failed == 0`) distingue suíte que não rodou (erro de coleta/import, exit code de uso) de suíte que rodou e está vermelha de verdade. `avaliar` passa a gravar motivo próprio ("suíte não executa na base (exit=..., N erro(s) de coleta, Xs) — ver stdout_tail") e a cauda do stdout no campo novo `Candidato.stdout_tail` (só preenchido nesse caso) — dá para diagnosticar sem reexecutar.

**Verificação nos outros repositórios (mesmo sintoma, mesmo tratamento):** tomlkit teve 2 candidatos da faixa grande (`4a094491`, `a304a390`, ambos de 2018-07, nascimento do projeto) com o mesmo padrão de recusa rápida. Diagnóstico manual: **não é dependência ausente** — é um efeito colateral de testar uma biblioteca de parsing TOML com pytest, que também lê `pyproject.toml` para se configurar: nesse ponto da história, `pyproject.toml` já existe mas a própria cópia local (em desenvolvimento) do `tomlkit` que está sendo testada ainda não implementava `.get()` em `TOMLDocument`, e pytest tenta usá-la para interpretar sua própria configuração, quebrando com `AttributeError: 'TOMLDocument' object has no attribute 'get'`. Não corrigido — janela de 2 commits na pré-história do projeto, não vale a complexidade de isolar o `sys.path` do pytest disso. Com o rótulo novo, esses 2 candidatos aparecem corretamente como "suíte não executa na base", não mais como falso "commit-base já vermelho". pygments e tqdm também mostraram o padrão em commits muito antigos (ver `mined-v2/RELATORIO.md`, motivos de rejeição); todos com o rótulo novo — nenhuma dependência adicional foi identificada como faltante além da do sqlite-utils.

`peewee` não foi reminerado inteiro depois desta correção de rótulo (custaria de novo a mesma ordem de tempo da seção 4, sem mudar nenhum candidato aceito — a causa da faixa média do peewee já estava corretamente diagnosticada, seção 6.1, antes mesmo desta correção); seu `mined-v2/peewee.json` ainda usa o texto antigo "commit-base já vermelho (0 falhas)" nesses casos, mas a seção 6.1 já explica a causa real.

Testes: `TestSuiteNaoExecutou` em `tests/test_mine_tasks.py`.

### 6.3 Arquivo de teste apagado ou renomeado no fix commit

No histórico amplo aparecem commits que apagam ou renomeiam arquivo de teste (ex.: sqlite-utils `364b0fb6` apaga `tests/test_black.py`; sqlite-utils `f9473ace` renomeia `tests/test_enable_fts.py` → `tests/test_fts.py`). O minerador antigo fazia `git checkout <fix> -- <arquivo>` para cada arquivo de teste do commit; com arquivo apagado no fix isso levanta `RuntimeError` (pathspec não casa em `fix`) e, sem tratamento, derrubaria o laço inteiro; renomeado sem tratamento deixava o nome antigo no workspace, duplicando a coleta.

Correção: `git log --name-status -M` (em vez de `--name-only`) mais `_parse_name_status`/`_classificar_status` ([scripts/mine_tasks.py:243-355](../../scripts/mine_tasks.py#L243)) resolvem apagado (`D`) e renomeado (`R`) por status, não só por nome de caminho. `avaliar` ([scripts/mine_tasks.py:452-527](../../scripts/mine_tasks.py#L452)) tira do workspace (`git rm -f --ignore-unmatch`) os caminhos que não existem mais em `fix_commit` em vez de tentar `checkout` deles, tanto do lado teste quanto do lado fonte (mesma classe de defeito, ainda que só o teste tenha sido citado no aviso). Um `try/except` em dois níveis (dentro de `avaliar` e ao redor da chamada em `minerar`) garante que qualquer outra falha inesperada rejeita só aquele candidato, com o motivo registrado, e não interrompe a mineração. Contagens novas no `Candidato`: `testes_apagados`, `testes_renomeados` (inteiros) — insumo do item 3 (breaking change): apagar ou renomear teste, em vez de só acrescentar, é outro sinal de mudança de comportamento, não usado para excluir candidato aqui.

Efeito colateral descoberto durante o teste com pygments (que tem `tests/examplefiles/` cheio de arquivos-amostra em codificações variadas, de propósito, para testar o lexer): `git diff`/`git log` sobre esses arquivos pode devolver bytes que não decodificam como UTF-8 estrito, e `subprocess.run(..., text=True)` levantava `UnicodeDecodeError` — corrigido com `errors="replace"` em `_git` ([scripts/mine_tasks.py:261-273](../../scripts/mine_tasks.py#L261)), que também protege qualquer outro repositório com amostra binária/exótica no diff.

Testes cobrindo os dois casos (apagado, renomeado, contagem lógica de arquivo renomeado como 1 não 2, `_presentes`/`_remover_desaparecidos`) em `tests/test_mine_tasks.py`, classes `TestParseNameStatus`, `TestClassificarStatusApagaERenomeiaTeste`, `TestPresentes`, `TestRemoverDesaparecidosDeVerdade` — validados contra os dois commits reais citados acima.

### 6.4 Reclassificação após revisão do autor sobre os aceitos de mined-v2

O autor revisou os candidatos aceitos e achou três defeitos de classificação (não de execução — nenhum oráculo mudou):

1. **Arquivo apagado inflava `arquivos_fonte`/`linhas_fonte`.** `pygments 2c463c68` saiu como média com 267 linhas em 2 arquivos; a correção de verdade é **1 linha** em `pygments/lexers/json5.py`, o resto era a remoção de arquivos soltos em `json5-tests/` (pasta de amostras fora do pacote `pygments/`, não casa com `tests/**`).
2. **Referência tocando arquivo protegido não-teste era aceita.** `tqdm e4d97426` acrescenta a dependência `envwrap` em `pyproject.toml` — o agente não pode tocar em `pyproject.toml` (protegido), então essa referência é irreprodutível dentro das regras, mas o candidato tinha sido aceito (o oráculo, por execução, de fato discrimina; o problema é que o agente nunca conseguiria produzir aquele patch).
3. **Média sem piso de linhas.** `peewee b8a336d0` tem 11 linhas em 3 arquivos e saiu como média só por tocar 3 arquivos.

**Correção implementada** (`scripts/mine_tasks.py`):

- `_em_source_dir(caminho, source_dir)`: só conta como fonte um `.py` dentro de um dos prefixos declarados em `SeedRepoSpec.source_dir` (`"peewee,playhouse"`, `"pygments"`, ...) — testado com `peewee.py` (arquivo único solto casando com o prefixo `"peewee"`) e com `json5-tests/` (fora de `"pygments"`, não conta).
- `Classificacao.fonte_apagados`: arquivo apagado (status `D`) dentro do `source_dir` vai para lá, não para `fonte`/`arquivos_fonte_logicos`/`linhas_fonte`. Continua saindo do workspace em `avaliar` (correção continua sendo simulada certo), só não conta para o tamanho da faixa. Campo novo no `Candidato`: `arquivos_fonte_apagados`.
- `GLOBS_DE_TESTE` (só `tests/**`, `test/**`, `**/test_*.py`, `**/*_test.py`, `**/conftest.py`) substitui `protected_globs` inteiro como definição de "teste" dentro de `_classificar_status`. Um caminho protegido que não bate nesses globs (`pyproject.toml`, `setup.cfg`, `tox.ini`, `runtests.py` do peewee, ...) marca `Classificacao.toca_protegido=True`. `levantar_candidatos` já rejeita esses candidatos na hora, com motivo `"referência toca arquivo protegido"`, sem gastar suíte; `minerar` os tira da fila de execução. Campo novo no `Candidato`: `toca_protegido`.
- `calcular_faixa`: média ganhou piso de **40 linhas** (`40 <= linhas_fonte <= 400`, era só `<= 400`); abaixo de 40 com 3+ arquivos vira pequena, com `motivo_faixa` explicando (não é uma pequena "típica" de 1-2 arquivos, mas o tamanho é de pequena).

**`reclassificar` e `--reclassificar`** (`scripts/mine_tasks.py`): recalcula os campos acima para candidatos **já registrados** em `mined-v2/<repo>.json`, usando só `git show --name-status -M` + `git diff --numstat` (nenhuma suíte). `aceito`/`verificado`/`fail_to_pass`/`segundos` são preservados tal como a suíte deixou — **exceto** quando o candidato passa a `toca_protegido=True`, caso em que é forçado a `aceito=False` e `fail_to_pass=[]`, porque a referência é irreprodutível independente do que a suíte disse. `relatorio_de_json` reconstrói o dicionário de relatório a partir do JSON corrigido, e `escrever_relatorio_md` é reaproveitado para regravar `mined-v2/RELATORIO.md`. Rodado com `uv run python scripts/mine_tasks.py --all --out mined-v2 --reclassificar` sobre os 5 repositórios, em segundos (só git, sem suíte).

**Resultado da reclassificação** (contagem por repositório, `mined-v2/<repo>.json`):

| repositório | candidatos recalculados | mudaram de faixa | passaram a `toca_protegido` | destes, já estavam `aceito` |
|---|---:|---:|---:|---:|
| tomlkit | 129 | 10 | 15 | 0 |
| peewee | 551 | 24 | 96 | 0 |
| sqlite-utils | 214 | 6 | 20 | 0 |
| pygments | 754 | 29 | 15 | 0 |
| tqdm | 90 | 16 | 38 | **1** (`e4d97426`, confirmando o achado do autor) |

Os três casos citados pelo autor, verificados um a um após a correção:

- `pygments 2c463c68`: `arquivos_fonte=['pygments/lexers/json5.py']`, `linhas_fonte=1` → faixa **fora** (1 linha não chega ao piso de 10 da pequena; continua `aceito=True`, só não entra em nenhuma faixa de seleção).
- `tqdm e4d97426`: `toca_protegido=True` → **`aceito=False`**, `motivo="referência toca arquivo protegido"`.
- `peewee b8a336d0`: `arquivos_fonte` (3 arquivos), `linhas_fonte=11` → faixa **pequena**, com `motivo_faixa` explicando.

Nenhum candidato **aceito** de tomlkit, peewee, sqlite-utils ou pygments virou `toca_protegido` — só o caso do tqdm já achado pelo autor. Backup do estado anterior à reclassificação (para auditoria) ficou fora do repositório, em `/tmp/.../scratchpad/mined-v2-backup-antes-reclassificacao/` (não versionado, sessão local).

Testes novos em `tests/test_mine_tasks.py`: `TestEhTeste`, `TestEmSourceDir`, mais casos em `TestClassificarStatusApagaERenomeiaTeste` (`test_fonte_fora_do_source_dir_nao_conta`, `test_toca_protegido_nao_teste`, `test_tocar_so_teste_nao_e_toca_protegido`, `test_runtests_py_do_peewee_e_toca_protegido`) e em `TestFaixaMedia`/`TestFaixaPequena` (piso de 40 linhas e a cláusula de pequena-por-tamanho).

## 7. Testes e suíte

`tests/test_mine_tasks.py` (novo, 70 testes) e `tests/test_seed_repos.py` (41 testes, incluindo `pygments`/`tqdm`): **111 passed em 83,44s**. Suíte inteira do projeto (`.venv/bin/python -m pytest -q`): última linha registrada abaixo, seção 9 (rodada em segundo plano ao final desta etapa).

## 8. Diff resumido

- `scripts/mine_tasks.py` — reescrito: faixas novas (com piso de 40 linhas na média e cláusula de pequena-por-tamanho), pré-filtro por status, `_em_source_dir`/`GLOBS_DE_TESTE`/`toca_protegido`, `arquivos_fonte_apagados`, tratamento de apagado/renomeado, `_suite_nao_executou`/`stdout_tail`, `--desde`/`--max-verificar-por-faixa`/`--parar-em`, `--reclassificar`, `RELATORIO.md`.
- `scripts/emit_task.py` — seletor de faixa `("grande","media","pequena")`, `--mined-dir` (padrão `mined-v2/`) juntando os `*.json` de todos os repositórios quando `--from` não é passado.
- `src/seeds.py` — `PEEWEE.suite_targets` corrigido (seção 6.1); `SQLITE_UTILS.test_requirements` ganha `typing-extensions` (seção 6.2); `PYGMENTS`, `TQDM` novos.
- `tests/test_mine_tasks.py` — novo, 70 testes.
- `tests/test_seed_repos.py` — `PISO_DE_COLETA` ajustado; catálogo e parametrizações incluindo `pygments`/`tqdm`.
- `mined-v2/` — novo, não substitui `mined-v1/`.

## 9. Última linha do pytest completo

```
511 passed in 163.98s (0:02:43)
```

(`.venv/bin/python -m pytest -q`, rodada completa após a reclassificação da seção 6.4 e a correção de dependência da seção 6.2.)

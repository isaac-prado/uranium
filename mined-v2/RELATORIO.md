# Relatório de mineração — mined-v2

Gerado por `scripts/mine_tasks.py`. Números vêm só desta rodada;
veja `mined-v2/<repo>.json` para o detalhe candidato a candidato.

| repositório | commits no histórico | pré-filtro grande | pré-filtro média | pré-filtro pequena | pré-filtro fora | pré-filtro protegido | verificados grande | verificados média | verificados pequena | aceitos grande | aceitos média | aceitos pequena | tempo (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| peewee | 5169 | 3 | 12 | 36 | 404 | 96 | 3 | 15 | 34 | 0 | 2 | 12 | 3394.6 |
| pygments | 6197 | 3 | 17 | 31 | 688 | 15 | 3 | 16 | 20 | 0 | 0 | 12 | 413.1 |
| sqlite-utils | 1196 | 2 | 0 | 18 | 174 | 20 | 4 | 0 | 14 | 0 | 0 | 12 | 258.3 |
| tomlkit | 489 | 6 | 0 | 18 | 90 | 15 | 7 | 0 | 14 | 3 | 0 | 12 | 63.8 |
| tqdm | 1822 | 0 | 0 | 27 | 25 | 38 | 0 | 6 | 33 | 0 | 0 | 7 | 1189.9 |

## Motivos de rejeição por repositório

### peewee
- 20x — commit-base já vermelho (0 falhas)
- 11x — referência toca arquivo protegido
- 11x — teste passa sem a correção — não discrimina
- 1x — vermelho sem node id: erro de coleta

### pygments
- 18x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.0s
- 3x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.4s
- 3x — referência toca arquivo protegido
- 3x — suíte não executa na base (exit=2, 8 erro(s) de coleta, 0.2s
- 2x — suíte não executa na base (exit=2, 3 erro(s) de coleta, 0.3s
- 1x — commit-base já vermelho (8 falhas)
- 1x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.5s
- 1x — suíte não executa na base (exit=2, 3 erro(s) de coleta, 0.6s

### sqlite-utils
- 3x — referência toca arquivo protegido
- 1x — vermelho sem node id: erro de coleta
- 1x — teste passa sem a correção — não discrimina
- 1x — não fica verde com a correção (1 falhas, 0 das mesmas) — bas
- 1x — commit-base já vermelho (3 falhas)

### tomlkit
- 3x — referência toca arquivo protegido
- 2x — commit-base já vermelho (2 falhas)
- 2x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.1s
- 2x — teste passa sem a correção — não discrimina
- 1x — vermelho sem node id: erro de coleta

### tqdm
- 18x — referência toca arquivo protegido
- 10x — teste passa sem a correção — não discrimina
- 5x — commit-base já vermelho (3 falhas)
- 3x — commit-base já vermelho (2 falhas)
- 3x — commit-base já vermelho (4 falhas)
- 1x — vermelho sem node id: erro de coleta


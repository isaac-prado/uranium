# Relatório de mineração — mined-v2

Gerado por `scripts/mine_tasks.py`. Números vêm só desta rodada;
veja `mined-v2/<repo>.json` para o detalhe candidato a candidato.

| repositório | commits no histórico | pré-filtro grande | pré-filtro média | pré-filtro pequena | pré-filtro fora | pré-filtro protegido | verificados grande | verificados média | verificados pequena | aceitos grande | aceitos média | aceitos pequena | tempo (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| peewee | 5169 | 4 | 12 | 454 | 404 | 28 | 4 | 12 | 8 | 0 | 2 | 6 | 1571.3 |
| pygments | 6197 | 3 | 20 | 391 | 685 | 0 | 3 | 20 | 6 | 0 | 0 | 6 | 213.4 |
| sqlite-utils | 1196 | 2 | 0 | 236 | 174 | 18 | 2 | 0 | 6 | 0 | 0 | 6 | 131.0 |
| tomlkit | 489 | 6 | 0 | 64 | 87 | 15 | 6 | 0 | 6 | 3 | 0 | 6 | 36.3 |
| tqdm | 1822 | 0 | 0 | 27 | 23 | 9 | 0 | 0 | 14 | 0 | 0 | 6 | 574.8 |

## Motivos de rejeição por repositório

### peewee
- 14x — suíte não executa na base (exit=4, 0 erro(s) de coleta, 0.1s
- 2x — teste passa sem a correção — não discrimina

### pygments
- 18x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.0s
- 2x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.5s
- 1x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.6s
- 1x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.4s
- 1x — suíte não executa na base (exit=2, 8 erro(s) de coleta, 0.2s

### sqlite-utils
- 1x — vermelho sem node id: erro de coleta
- 1x — teste passa sem a correção — não discrimina

### tomlkit
- 2x — commit-base já vermelho (2 falhas)
- 1x — vermelho sem node id: erro de coleta

### tqdm
- 7x — teste passa sem a correção — não discrimina
- 1x — vermelho sem node id: erro de coleta


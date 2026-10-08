# Relatório de mineração — mined-v2

Gerado por `scripts/mine_tasks.py`. Números vêm só desta rodada;
veja `mined-v2/<repo>.json` para o detalhe candidato a candidato.

| repositório | commits no histórico | pré-filtro grande | pré-filtro média | pré-filtro pequena | pré-filtro fora | pré-filtro protegido | verificados grande | verificados média | verificados pequena | aceitos grande | aceitos média | aceitos pequena | tempo (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| attrs | 1830 | 7 | 11 | 118 | 97 | 32 | 7 | 11 | 11 | 0 | 2 | 6 | 436.9 |
| jinja | 2175 | 4 | 1 | 41 | 23 | 7 | 4 | 1 | 8 | 0 | 1 | 6 | 58.7 |
| marshmallow | 3031 | 0 | 11 | 70 | 58 | 18 | 0 | 11 | 8 | 0 | 1 | 6 | 68.7 |
| peewee | 5169 | 4 | 12 | 454 | 404 | 28 | 4 | 12 | 8 | 0 | 2 | 6 | 1638.2 |
| pygments | 6197 | 3 | 45 | 391 | 660 | 0 | 3 | 45 | 6 | 0 | 1 | 6 | 373.2 |
| sqlite-utils | 1196 | 2 | 4 | 236 | 170 | 18 | 2 | 4 | 6 | 0 | 2 | 6 | 232.3 |
| tomlkit | 489 | 6 | 18 | 64 | 69 | 15 | 6 | 17 | 6 | 3 | 6 | 6 | 94.0 |
| tqdm | 1822 | 0 | 0 | 27 | 23 | 9 | 0 | 0 | 14 | 0 | 0 | 6 | 657.8 |

## Motivos de rejeição por repositório

### attrs
- 6x — teste passa sem a correção — não discrimina
- 5x — vermelho sem node id: erro de coleta
- 4x — suíte não executa na base (exit=4, 0 erro(s) de coleta, 0.3s
- 3x — suíte não executa na base (exit=4, 0 erro(s) de coleta, 0.4s
- 2x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.2s
- 1x — commit-base já vermelho (2 falhas)

### jinja
- 3x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.2s
- 2x — teste passa sem a correção — não discrimina
- 1x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.3s

### marshmallow
- 5x — commit-base já vermelho (1 falhas)
- 4x — teste passa sem a correção — não discrimina
- 3x — suíte não executa na base (exit=4, 0 erro(s) de coleta, 0.2s

### peewee
- 10x — suíte não executa na base (exit=4, 0 erro(s) de coleta, 0.2s
- 4x — suíte não executa na base (exit=4, 0 erro(s) de coleta, 0.1s
- 2x — teste passa sem a correção — não discrimina

### pygments
- 26x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.0s
- 4x — suíte não executa na base (exit=1, 0 erro(s) de coleta, 0.1s
- 3x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.7s
- 3x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.8s
- 3x — suíte não executa na base (exit=2, 3 erro(s) de coleta, 0.5s
- 2x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.6s
- 2x — suíte não executa na base (exit=2, 8 erro(s) de coleta, 0.3s
- 1x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.9s
- 1x — suíte não executa na base (exit=2, 3 erro(s) de coleta, 0.8s
- 1x — suíte não executa na base (exit=2, 4 erro(s) de coleta, 0.5s
- 1x — suíte não executa na base (exit=2, 2 erro(s) de coleta, 0.5s

### sqlite-utils
- 2x — vermelho sem node id: erro de coleta
- 2x — teste passa sem a correção — não discrimina

### tomlkit
- 8x — commit-base já vermelho (2 falhas)
- 3x — vermelho sem node id: erro de coleta
- 1x — teste passa sem a correção — não discrimina
- 1x — commit-base já vermelho (14 falhas)
- 1x — commit-base já vermelho (37 falhas)

### tqdm
- 7x — teste passa sem a correção — não discrimina
- 1x — vermelho sem node id: erro de coleta


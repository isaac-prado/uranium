# Relatório de mineração — mined-v2

Gerado por `scripts/mine_tasks.py`. Números vêm só desta rodada;
veja `mined-v2/<repo>.json` para o detalhe candidato a candidato.

| repositório | commits no histórico | pré-filtro grande | pré-filtro média | pré-filtro pequena | pré-filtro fora | pré-filtro protegido | verificados grande | verificados média | verificados pequena | aceitos grande | aceitos média | aceitos pequena | tempo (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| attrs | 1830 | 7 | 1 | 118 | 107 | 32 | 7 | 1 | 11 | 0 | 0 | 6 | 357.7 |

## Motivos de rejeição por repositório

### attrs
- 5x — teste passa sem a correção — não discrimina
- 4x — vermelho sem node id: erro de coleta
- 4x — suíte não executa na base (exit=4, 0 erro(s) de coleta, 0.3s


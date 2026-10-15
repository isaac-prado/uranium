
  análise pareada — 3 tarefa(s), 48 observações
  perdidas: 0 célula(s), 0 tentativa(s) perdida(s)
    single-agent   0 tentativa(s) e 0 célula(s) perdida(s), 5 de 9 run(s) pareado(s) cortado(s) pelo orçamento
    orchestration  0 tentativa(s) e 0 célula(s) perdida(s), 4 de 9 run(s) pareado(s) cortado(s) pelo orçamento
  ──────────────────────────────────────────────────────────────────────────────────────
  tarefa                 pares  resolve SA resolve OR      Δ    US$ SA   US$ OR  turnos SA turnos OR
  ──────────────────────────────────────────────────────────────────────────────────────
  pygments-0001              3        0.67       0.33  -0.33    0.3451   0.1879       62.3      61.3
  sqlite-utils-0002          3        0.00       1.00  +1.00    0.4222   0.0406       63.3      23.0
  tomlkit-0004               3        0.00       0.00  +0.00    0.5017   0.2819      120.0     120.0
  ──────────────────────────────────────────────────────────────────────────────────────
  primário   H1: orchestration > single-agent (unicaudal)
    sinal     n=2  +1 −1  p(uni)=0.7500  p(bi)=1.0000
    Wilcoxon  n=2  W+=2.0  p(uni)=0.5000  p(bi)=1.0000
  secundários (mediana por tarefa, Wilcoxon bicaudal)
    cost_usd      SA       0.4222   OR       0.1879   p=0.2500
    tokens_total  SA 3117184.3333   OR 1299013.3333   p=0.2500
    turns         SA      63.3333   OR      61.3333   p=0.5000
    wall_seconds  SA     530.5227   OR     534.0293   p=1.0000

  →  runs/coleta-r2/analysis.json


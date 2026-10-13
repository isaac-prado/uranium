
  análise pareada — 13 tarefa(s), 78 observações
  perdidas: 0 célula(s), 1 tentativa(s) perdida(s)
    single-agent   1 tentativa(s) e 0 célula(s) perdida(s), 13 de 39 run(s) pareado(s) cortado(s) pelo orçamento
    orchestration  0 tentativa(s) e 0 célula(s) perdida(s), 16 de 39 run(s) pareado(s) cortado(s) pelo orçamento
  ──────────────────────────────────────────────────────────────────────────────────────
  tarefa                 pares  resolve SA resolve OR      Δ    US$ SA   US$ OR  turnos SA turnos OR
  ──────────────────────────────────────────────────────────────────────────────────────
  attrs-0001                 3        1.00       0.67  -0.33    0.0167   0.0328       20.7      32.7
  peewee-0001                3        1.00       0.67  -0.33    0.1363   0.1115       49.0      74.3
  peewee-0002                3        0.67       0.00  -0.67    0.2202   0.2952      103.3     120.0
  peewee-0003                3        1.00       1.00  +0.00    0.0134   0.0110       14.3      12.3
  pygments-0001              3        1.00       0.00  -1.00    0.9458   0.1376      118.3      81.0
  sqlite-utils-0001          3        0.33       0.00  -0.33    0.2385   0.0441       61.0      28.3
  sqlite-utils-0002          3        0.33       1.00  +0.67    1.0641   0.2184      101.3     120.0
  sqlite-utils-0003          3        0.67       0.00  -0.67    0.2277   0.1725       75.0      71.3
  tomlkit-0001               3        1.00       0.67  -0.33    0.0274   0.0473       24.0      46.7
  tomlkit-0002               3        0.33       0.33  +0.00    0.3650   0.2238      109.7     120.0
  tomlkit-0003               3        1.00       1.00  +0.00    0.1012   0.0430       47.3      37.7
  tomlkit-0004               3        0.00       0.00  +0.00    0.4642   0.2408      114.0     120.0
  tomlkit-0005               3        0.00       0.33  +0.33    0.1966   0.1604       87.7     104.7
  ──────────────────────────────────────────────────────────────────────────────────────
  primário   H1: orchestration > single-agent (unicaudal)
    sinal     n=9  +2 −7  p(uni)=0.9805  p(bi)=0.1797
    Wilcoxon  n=9  W+=9.5  p(uni)=0.9473  p(bi)=0.1445
  secundários (mediana por tarefa, Wilcoxon bicaudal)
    cost_usd      SA       0.2202   OR       0.1376   p=0.0215
    tokens_total  SA 1997975.0000   OR  945082.6667   p=0.0024
    turns         SA      75.0000   OR      74.3333   p=0.3757
    wall_seconds  SA     297.7570   OR     265.3423   p=0.2439

  →  runs/coleta/analysis.json


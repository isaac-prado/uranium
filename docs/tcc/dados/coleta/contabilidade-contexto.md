Tamanhos fixos (bytes, código atual): {'system_prompt': 1327, 'tool_schema': 3169}

## Por execução

| run | braço | modo | instr. completa | chamadas (código/aux) | 1º prompt | último prompt | Σ prompt | c (bytes/token) | a (tokens/msg) | discrepância |
|---|---|---|---|---|---|---|---|---|---|---|
| `attrs-0001-orchestration-r01-a01` | orchestration | exato | sim | 21/3 | 2043 | 8759 | 107807 | 2.12 | — | 0.0% |
| `attrs-0001-orchestration-r02-a01` | orchestration | exato | sim | 22/3 | 2008 | 9211 | 113296 | 2.23 | — | 0.0% |
| `attrs-0001-orchestration-r03-a01` | orchestration | exato | sim | 55/3 | 2057 | 10753 | 460555 | 2.98 | — | 0.0% |
| `attrs-0001-single-agent-r01-a01` | single-agent | exato | sim | 18/0 | 2723 | 8581 | 96818 | 2.25 | — | 0.0% |
| `attrs-0001-single-agent-r02-a01` | single-agent | exato | sim | 19/0 | 2723 | 8911 | 110296 | 2.30 | — | 0.0% |
| `attrs-0001-single-agent-r03-a01` | single-agent | exato | sim | 25/0 | 2723 | 10288 | 159759 | 2.43 | — | 0.0% |
| `peewee-0001-orchestration-r01-a01` | orchestration | exato | sim | 87/5 | 2053 | 9925 | 712368 | 2.72 | — | 0.0% |
| `peewee-0001-orchestration-r02-a01` | orchestration | exato | sim | 111/4 | 2049 | 20293 | 1545083 | 3.28 | — | 0.0% |
| `peewee-0001-orchestration-r03-a01` | orchestration | exato | sim | 25/3 | 1980 | 15110 | 239788 | 2.92 | — | 0.0% |
| `peewee-0001-single-agent-r01-a01` | single-agent | exato | sim | 25/0 | 2954 | 12668 | 225010 | 2.98 | — | 0.0% |
| `peewee-0001-single-agent-r02-a01` | single-agent | exato | sim | 93/0 | 2954 | 51827 | 2433776 | 3.31 | — | 0.0% |
| `peewee-0001-single-agent-r03-a01` | single-agent | exato | sim | 29/0 | 2954 | 15763 | 310437 | 3.09 | — | 0.0% |
| `peewee-0002-orchestration-r01-a01` | orchestration | exato | sim | 120/3 | 2033 | 12878 | 1118388 | 2.88 | — | 0.2% |
| `peewee-0002-orchestration-r02-a01` | orchestration | exato | sim | 120/2 | 1906 | 25125 | 3360105 | 3.32 | — | 0.1% |
| `peewee-0002-orchestration-r03-a01` | orchestration | exato | sim | 120/3 | 1987 | 14637 | 1073248 | 2.64 | — | 2.3% |
| `peewee-0002-single-agent-r01-a01` | single-agent | exato | sim | 87/0 | 4485 | 32191 | 1588641 | 2.81 | — | 0.0% |
| `peewee-0002-single-agent-r02-a01` | single-agent | exato | sim | 111/0 | 4485 | 35146 | 2095228 | 2.90 | — | 0.0% |
| `peewee-0002-single-agent-r03-a01` | single-agent | exato | sim | 112/0 | 4485 | 38988 | 2409526 | 2.91 | — | 0.0% |
| `peewee-0003-orchestration-r01-a01` | orchestration | exato | sim | 9/3 | 2043 | 4177 | 28022 | 1.94 | — | 0.0% |
| `peewee-0003-orchestration-r02-a01` | orchestration | exato | sim | 10/3 | 1951 | 4025 | 30526 | 1.95 | — | 0.0% |
| `peewee-0003-orchestration-r03-a01` | orchestration | exato | sim | 18/3 | 1951 | 9543 | 109629 | 2.58 | — | 0.0% |
| `peewee-0003-single-agent-r01-a01` | single-agent | exato | sim | 18/0 | 2277 | 9705 | 118423 | 2.59 | — | 0.0% |
| `peewee-0003-single-agent-r02-a01` | single-agent | exato | sim | 16/0 | 2277 | 9074 | 99179 | 2.65 | — | 0.0% |
| `peewee-0003-single-agent-r03-a01` | single-agent | exato | sim | 9/0 | 2277 | 5376 | 36587 | 2.53 | — | 0.0% |
| `pygments-0001-orchestration-r01-a01` | orchestration | exato | sim | 68/3 | 2057 | 18945 | 918752 | 2.98 | — | 0.5% |
| `pygments-0001-orchestration-r02-a01` | orchestration | exato | sim | 120/1 | 2007 | 24946 | 1358043 | 3.44 | — | 0.0% |
| `pygments-0001-orchestration-r03-a01` | orchestration | exato | sim | 55/3 | 2171 | 12514 | 485391 | 2.96 | — | 0.6% |
| `pygments-0001-single-agent-r01-a01` | single-agent | exato | sim | 115/0 | 4493 | 150096 | 8071259 | 5.00 | — | 0.0% |
| `pygments-0001-single-agent-r02-a01` | single-agent | exato | sim | 120/0 | 4493 | 108403 | 6538458 | 3.15 | — | 0.0% |
| `pygments-0001-single-agent-r03-a01` | single-agent | exato | sim | 120/0 | 4493 | 152086 | 8047258 | 3.68 | — | 0.0% |
| `sqlite-utils-0001-orchestration-r01-a01` | orchestration | exato | sim | 23/3 | 1973 | 14315 | 179061 | 2.88 | — | 0.0% |
| `sqlite-utils-0001-orchestration-r02-a01` | orchestration | exato | sim | 36/3 | 2015 | 18578 | 399274 | 3.12 | — | 0.0% |
| `sqlite-utils-0001-orchestration-r03-a01` | orchestration | exato | sim | 26/3 | 2076 | 24007 | 346698 | 3.26 | — | 0.0% |
| `sqlite-utils-0001-single-agent-r01-a01` | single-agent | exato | sim | 28/0 | 2449 | 14709 | 235487 | 2.81 | — | 0.0% |
| `sqlite-utils-0001-single-agent-r02-a01` | single-agent | exato | sim | 35/0 | 2449 | 26080 | 497209 | 3.10 | — | 0.0% |
| `sqlite-utils-0001-single-agent-r03-a01` | single-agent | exato | sim | 120/0 | 2449 | 106878 | 5596368 | 3.67 | — | 0.0% |
| `sqlite-utils-0002-orchestration-r01-a01` | orchestration | exato | sim | 120/1 | 1940 | 8075 | 1540244 | 3.20 | — | 0.0% |
| `sqlite-utils-0002-orchestration-r02-a01` | orchestration | exato | sim | 120/1 | 1988 | 12021 | 1895114 | 3.24 | — | 0.0% |
| `sqlite-utils-0002-orchestration-r03-a01` | orchestration | exato | sim | 120/1 | 1919 | 7279 | 1727595 | 3.19 | — | 0.0% |
| `sqlite-utils-0002-single-agent-r01-a01` | single-agent | exato | sim | 100/0 | 2953 | 181130 | 8141240 | 3.90 | — | 0.0% |
| `sqlite-utils-0002-single-agent-r02-a01` | single-agent | exato | sim | 100/0 | 2953 | 189469 | 8063254 | 3.70 | — | 0.0% |
| `sqlite-utils-0002-single-agent-r03-a01` | single-agent | exato | sim | 104/0 | 2953 | 175850 | 7987910 | 3.83 | — | 0.0% |
| `sqlite-utils-0003-orchestration-r01-a01` | orchestration | exato | sim | 120/1 | 2348 | 28305 | 2471914 | 3.29 | — | 4.1% |
| `sqlite-utils-0003-orchestration-r02-a01` | orchestration | exato | sim | 54/4 | 2088 | 9890 | 860910 | 2.95 | — | 0.0% |
| `sqlite-utils-0003-orchestration-r03-a01` | orchestration | exato | sim | 40/3 | 2132 | 32573 | 839303 | 2.87 | — | 0.0% |
| `sqlite-utils-0003-single-agent-r01-a01` | single-agent | exato | sim | 36/0 | 3589 | 28642 | 682732 | 3.17 | — | 0.0% |
| `sqlite-utils-0003-single-agent-r01-a02` | single-agent | exato | sim | 60/0 | 3589 | 29670 | 1002048 | 2.98 | — | 0.0% |
| `sqlite-utils-0003-single-agent-r02-a01` | single-agent | exato | sim | 45/0 | 3589 | 31307 | 850724 | 2.95 | — | 0.0% |
| `sqlite-utils-0003-single-agent-r03-a01` | single-agent | exato | sim | 120/0 | 3589 | 71682 | 4093131 | 3.31 | — | 0.0% |
| `tomlkit-0001-orchestration-r01-a01` | orchestration | exato | sim | 24/3 | 1836 | 12170 | 197944 | 2.75 | — | 0.0% |
| `tomlkit-0001-orchestration-r02-a01` | orchestration | exato | sim | 39/3 | 1809 | 11985 | 270048 | 2.64 | — | 0.0% |
| `tomlkit-0001-orchestration-r03-a01` | orchestration | exato | sim | 77/5 | 1859 | 9566 | 607145 | 2.60 | — | 0.0% |
| `tomlkit-0001-single-agent-r01-a01` | single-agent | exato | sim | 41/0 | 2022 | 19502 | 500961 | 2.87 | — | 0.0% |
| `tomlkit-0001-single-agent-r02-a01` | single-agent | exato | sim | 14/0 | 2022 | 6217 | 59295 | 2.17 | — | 0.0% |
| `tomlkit-0001-single-agent-r03-a01` | single-agent | exato | sim | 17/0 | 2022 | 9544 | 120403 | 2.52 | — | 0.0% |
| `tomlkit-0002-orchestration-r01-a01` | orchestration | exato | sim | 120/5 | 2057 | 21060 | 1892566 | 2.83 | — | 0.1% |
| `tomlkit-0002-orchestration-r02-a01` | orchestration | exato | sim | 120/5 | 2041 | 4393 | 1512718 | 2.82 | — | 0.1% |
| `tomlkit-0002-orchestration-r03-a01` | orchestration | exato | sim | 120/1 | 2030 | 35161 | 2349410 | 3.15 | — | 0.2% |
| `tomlkit-0002-single-agent-r01-a01` | single-agent | exato | sim | 120/0 | 2760 | 49058 | 3247218 | 2.92 | — | 0.0% |
| `tomlkit-0002-single-agent-r02-a01` | single-agent | exato | sim | 89/0 | 2760 | 55085 | 2324385 | 3.09 | — | 0.0% |
| `tomlkit-0002-single-agent-r03-a01` | single-agent | exato | sim | 120/0 | 2760 | 123587 | 4434630 | 3.00 | — | 0.0% |
| `tomlkit-0003-orchestration-r01-a01` | orchestration | exato | sim | 21/3 | 2093 | 14264 | 172559 | 2.46 | — | 0.0% |
| `tomlkit-0003-orchestration-r02-a01` | orchestration | exato | sim | 31/3 | 2034 | 14023 | 281048 | 2.64 | — | 0.0% |
| `tomlkit-0003-orchestration-r03-a01` | orchestration | exato | sim | 61/4 | 1911 | 16672 | 529608 | 2.50 | — | 0.0% |
| `tomlkit-0003-single-agent-r01-a01` | single-agent | exato | sim | 42/0 | 2494 | 21077 | 593822 | 2.87 | — | 0.0% |
| `tomlkit-0003-single-agent-r02-a01` | single-agent | exato | sim | 80/0 | 2494 | 46104 | 1906393 | 2.95 | — | 0.0% |
| `tomlkit-0003-single-agent-r03-a01` | single-agent | exato | sim | 20/0 | 2494 | 10588 | 139727 | 2.44 | — | 0.0% |
| `tomlkit-0004-orchestration-r01-a01` | orchestration | exato | sim | 120/1 | 2164 | 25498 | 1750816 | 3.18 | — | 0.9% |
| `tomlkit-0004-orchestration-r02-a01` | orchestration | exato | sim | 120/1 | 2164 | 35025 | 2480696 | 2.99 | — | 2.4% |
| `tomlkit-0004-orchestration-r03-a01` | orchestration | exato | sim | 120/1 | 2150 | 25006 | 1894763 | 3.04 | — | 0.4% |
| `tomlkit-0004-single-agent-r01-a01` | single-agent | exato | sim | 120/0 | 4104 | 80940 | 5181530 | 3.15 | — | 0.0% |
| `tomlkit-0004-single-agent-r02-a01` | single-agent | exato | sim | 120/0 | 4104 | 62499 | 3889379 | 2.96 | — | 0.0% |
| `tomlkit-0004-single-agent-r03-a01` | single-agent | exato | sim | 102/0 | 4104 | 66381 | 3789937 | 3.30 | — | 0.0% |
| `tomlkit-0005-orchestration-r01-a01` | orchestration | exato | sim | 74/4 | 1940 | 11786 | 596154 | 2.48 | — | 0.0% |
| `tomlkit-0005-orchestration-r02-a01` | orchestration | exato | sim | 120/5 | 1916 | 3781 | 1429603 | 2.59 | — | 1.2% |
| `tomlkit-0005-orchestration-r03-a01` | orchestration | exato | sim | 120/3 | 1894 | 14591 | 1897094 | 2.82 | — | 0.8% |
| `tomlkit-0005-single-agent-r01-a01` | single-agent | exato | sim | 120/0 | 2481 | 47200 | 2965337 | 2.79 | — | 0.0% |
| `tomlkit-0005-single-agent-r02-a01` | single-agent | exato | sim | 75/0 | 2481 | 21900 | 960903 | 2.63 | — | 0.0% |
| `tomlkit-0005-single-agent-r03-a01` | single-agent | exato | sim | 68/0 | 2481 | 25755 | 1011257 | 2.88 | — | 0.0% |

## Braço `orchestration` — 39 execução(ões), 39987241 tokens de prompt cobrados

| Categoria | tokens | % |
|---|---|---|
| saída de read_file | 13004020 | 32.5 |
| feedback e enunciado (mensagens humanas) | 9195431 | 23.0 |
| mensagens do assistente | 8760822 | 21.9 |
| saída de run_tests | 2940176 | 7.4 |
| saída de list_files | 1971157 | 4.9 |
| prompt de sistema | 1384175 | 3.5 |
| saída de search_code | 1301297 | 3.3 |
| saída de run_python | 1123258 | 2.8 |
| papéis auxiliares (prompts próprios) | 203955 | 0.5 |
| saída de replace_in_file | 77849 | 0.2 |
| saída de write_file | 25106 | 0.1 |

Mediana do último prompt: 14023 tokens; média por chamada (mediana entre execuções): 11091; chamadas de código (mediana): 74; discrepância mediana: 0.0%; bytes por token (mediana): 3.12.

## Braço `single-agent` — 40 execução(ões), 100615935 tokens de prompt cobrados

| Categoria | tokens | % |
|---|---|---|
| mensagens do assistente | 32594008 | 32.4 |
| feedback e enunciado (mensagens humanas) | 29979609 | 29.8 |
| saída de read_file | 20750669 | 20.6 |
| saída de run_python | 5619655 | 5.6 |
| saída de run_tests | 4514785 | 4.5 |
| saída de list_files | 3274221 | 3.3 |
| saída de search_code | 2229609 | 2.2 |
| prompt de sistema | 1244032 | 1.2 |
| saída de replace_in_file | 380939 | 0.4 |
| saída de write_file | 28395 | 0.0 |

Mediana do último prompt: 31749.0 tokens; média por chamada (mediana entre execuções): 18890.5; chamadas de código (mediana): 77.5; discrepância mediana: 0.0%; bytes por token (mediana): 2.95.


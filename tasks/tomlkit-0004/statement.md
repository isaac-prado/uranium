# Chaves pontilhadas (TOML 0.5.0) não são aceitas pelo parser

## Comportamento observado

A versão 0.5.0 da especificação TOML introduziu as **chaves pontilhadas**: uma
chave formada por partes separadas por ponto, em que cada parte pode ser nua
(`physical`) ou entre aspas (`"google.com"`). Escrever `a.b.c = 1` equivale a
definir a tabela `a`, dentro dela a tabela `b`, e dentro dela a chave `c` com
valor `1`.

Hoje a biblioteca não aceita esse tipo de chave: qualquer documento que a
contenha falha na análise com `UnexpectedCharError` apontando para o ponto.

```python
import tomlkit

tomlkit.parse('physical.color = "orange"\n')
# tomlkit.exceptions.UnexpectedCharError: Unexpected character: '.' at line 1 col 8
```

Como a análise falha, nada mais funciona num documento que use chaves
pontilhadas: nem os outros recursos do TOML 0.5.0 que a biblioteca já
suporta (`inf`, `nan`, inteiros em hexadecimal, octal e binário) podem ser
lidos quando aparecem no mesmo arquivo.

Há ainda um segundo comportamento a ajustar, ligado a como o texto do
documento é distribuído entre seus elementos: a quebra de linha que encerra
um cabeçalho de tabela (`[table]`) hoje é contada como conteúdo da tabela.

```python
import tomlkit

t = tomlkit.parse("[table]\n")["table"]
print(repr(t.as_string()))   # hoje: '\n'   — esperado: ''
```

## Comportamento esperado

Cada item abaixo deve valer para documentos analisados com `tomlkit.parse`
(ou `tomlkit.loads`) e serializados com `tomlkit.dumps`.

1. **Chave pontilhada com partes nuas.** O documento

   ```toml
   physical.color = "orange"
   physical.shape = "round"
   ```

   é aceito; `doc["physical"]` existe, contém `"color"` e `"shape"`, e
   `doc["physical"]["color"] == "orange"`, `doc["physical"]["shape"] == "round"`.

2. **Parte entre aspas, que pode conter ponto.** Em `site."google.com" = true`,
   o ponto dentro das aspas faz parte do nome: `"site" in doc`,
   `"google.com" in doc["site"]` e `doc["site"]["google.com"]` é `True`.

3. **Vários níveis.** O documento

   ```toml
   a.b.c = 1
   a.b.d = 2
   ```

   produz `doc["a"]["b"]["c"] == 1` e `doc["a"]["b"]["d"] == 2`: linhas
   pontilhadas com o mesmo prefixo acumulam chaves nas mesmas tabelas.

4. **Representação como dicionário/JSON.** O documento analisado vira, por
   `json.dumps`, a estrutura aninhada correspondente:
   `a.b.c = 1` + `a.b.d = 2` resulta em `{"a": {"b": {"c": 1, "d": 2}}}`;
   `site."google.com" = true` resulta em `{"site": {"google.com": true}}`.

5. **Ida e volta sem perda.** `tomlkit.dumps(tomlkit.parse(texto)) == texto`
   para documentos com chaves pontilhadas: cada linha volta exatamente como foi
   escrita (mesmas aspas, espaços, comentários e linhas em branco), na mesma
   ordem.

6. **Convivência com os demais recursos do TOML 0.5.0.** Num mesmo documento
   com chaves pontilhadas, continuam corretos `inf`/`+inf`/`-inf` (infinitos),
   `nan`/`+nan`/`-nan` (NaN), inteiros hexadecimais (`0xDEADBEEF`,
   `0xdeadbeef`, `0xdead_beef` valem `3735928559`), octais (`0o01234567` vale
   `342391`, `0o755` vale `493`) e binários (`0b11010110` vale `214`), tanto na
   leitura quanto na ida e volta e na conversão para JSON.

7. **Quebra de linha do cabeçalho de tabela.** A quebra de linha que termina a
   linha `[table]` pertence ao cabeçalho, não ao conteúdo da tabela. Para
   `t = tomlkit.parse("[table]\n")["table"]`:
   - `t.as_string()` é `""`;
   - depois de `t.append("foo", "bar")`, `t.as_string()` é `'foo = "bar"\n'`;
   - depois de `t.remove("foo")`, volta a ser `""`.

   Serializar o documento inteiro continua produzindo o texto original.

## Como reproduzir

Rode a partir da raiz do repositório. Hoje os itens 1 a 6 levantam
`UnexpectedCharError` e o item 7 imprime `['\n', '\nfoo = "bar"\n', '\n']`.

```python
import json
import tomlkit

def tenta(nome, f):
    try:
        print(nome, "->", f())
    except Exception as e:
        print(nome, "-> ERRO", type(e).__name__, e)

tenta("1", lambda: tomlkit.parse('physical.color = "orange"\nphysical.shape = "round"\n')["physical"]["color"])
tenta("2", lambda: tomlkit.parse('site."google.com" = true\n')["site"]["google.com"])
tenta("3", lambda: tomlkit.parse('a.b.c = 1\na.b.d = 2\n')["a"]["b"]["d"])
tenta("4", lambda: json.dumps(tomlkit.parse('a.b.c = 1\na.b.d = 2\n')))

texto = '''# Dotted keys
physical.color = "orange"
physical.shape = "round"
site."google.com" = true

a.b.c = 1
a.b.d = 2
'''
tenta("5", lambda: tomlkit.dumps(tomlkit.parse(texto)) == texto)

misto = '''sf1 = inf  # positive infinity
sf6 = -nan # valid
hex3 = 0xdead_beef
oct2 = 0o755 # useful for Unix file permissions
bin1 = 0b11010110

physical.color = "orange"
'''
def item6():
    d = tomlkit.parse(misto)
    return (d["sf1"], d["sf6"], d["hex3"], d["oct2"], d["bin1"],
            d["physical"]["color"], tomlkit.dumps(d) == misto)
tenta("6", item6)

def item7():
    t = tomlkit.parse("[table]\n")["table"]
    r = [t.as_string()]
    t.append("foo", "bar"); r.append(t.as_string())
    t.remove("foo"); r.append(t.as_string())
    return r
tenta("7", item7)
```

Saída esperada depois da correção:

```
1 -> orange
2 -> True
3 -> 2
4 -> {"a": {"b": {"c": 1, "d": 2}}}
5 -> True
6 -> (inf, nan, 3735928559, 493, 214, 'orange', True)
7 -> ['', 'foo = "bar"\n', '']
```

## Critérios de aceitação

- Um documento TOML 0.5.0 completo, com infinitos, NaN, inteiros
  hexadecimais/octais/binários **e** as chaves pontilhadas
  `physical.color`, `physical.shape`, `site."google.com"`, `a.b.c` e `a.b.d`,
  é analisado sem erro por `tomlkit.parse`/`tomlkit.loads` e devolve um
  documento TOML.
- Nesse documento, `doc["physical"]["color"] == "orange"`,
  `doc["physical"]["shape"] == "round"`, `doc["site"]["google.com"]` é
  verdadeiro, `doc["a"]["b"]["c"] == 1` e `doc["a"]["b"]["d"] == 2`; e os
  operadores `in` funcionam em cada nível (`"physical" in doc`,
  `"color" in doc["physical"]`, `"google.com" in doc["site"]`).
- Nesse mesmo documento, os valores de `inf`/`nan`/hexadecimal/octal/binário
  são os do item 6.
- `json.loads(json.dumps(tomlkit.parse(texto)))` é igual ao dicionário
  aninhado esperado (chaves pontilhadas viram objetos aninhados).
- `tomlkit.dumps(tomlkit.parse(texto)) == texto` para esse documento.
- O conteúdo de uma tabela analisada a partir de `[table]\n` é a string
  vazia, e acrescentar/remover chaves nela se comporta como no item 7.
- Nenhum comportamento já existente muda: os demais documentos de exemplo
  continuam sendo lidos e reescritos idênticos, e os documentos inválidos
  continuam sendo rejeitados.

# HinglishPy

Python jaisa language, par sab keywords Hinglish me. ★ Apna compiler (parse → codegen → Python). ★ Termux + Linux pe chalta hai.

## Install

```bash
curl -sL https://github.com/termux-learn-crypto/termux-repo/raw/main/install.sh | bash
apt update && apt install hinglishpy
```

Direct .hl file chalana:
```bash
hinglishpy hello.hl run     # compile + run
python3 compiler.py hello.hl run  # development
```

REPL:
```bash
hinglishpy                  # interactive shell
```

## Quick Example

```python
bolo "Hello!"               # print
kaam jod(a, b):             # function def
    wapas a + b             # return a + b
bolo jod(10, 20)            # 30
```

Run:
```bash
python3 compiler.py hello.hl run
```

## Keywords

| HinglishPy | Meaning |
|---|---|
| `agar` | if |
| `nahito` | elif |
| `warna` | else |
| `anyatha` | else (alias) |
| `jabtak` | while |
| `har` | for |
| `me` | in |
| `kaam` | def |
| `varg` | class |
| `wapas` | return |
| `koshish` | try |
| `pakdo` | except |
| `ant` | finally |
| `lao` | import |
| `se` | from |
| `jaise` | as |
| `todo` | break |
| `jaari` | continue |
| `chhodo` | pass |
| `badhao` | raise |
| `saath` | with |
| `banao` | lambda |
| `sach` | assert |
| `mitao` | del |
| `batao` | yield |
| `batao se` | yield from |
| `intezar` | await |
| `asink` | async |
| `baishvik` | global |
| `asthaniye` | nonlocal |
| `bolo` | print |
| `puchho` | input |
| `khud` | self |
| `sahi` | True |
| `galat` | False |
| `kuchnahi` | None |
| `aur` | and |
| `ya` | or |
| `nahi` | not |
| `hai` | is |

## Builtins

| HinglishPy | Python |
|---|---|
| `lambai(x)` | len(x) |
| `ginti(x)` | range(x) |
| `kramank(x)` | enumerate(x) |
| `suchi(x)` | list(x) |
| `shabdkosh(x)` | dict(x) |
| `yugm(x)` | tuple(x) |
| `samuh(x)` | set(x) |
| `yog(x)` | sum(x) |
| `krambadh(x)` | sorted(x) |
| `ulta(x)` | reversed(x) |
| `nyuntam(x)` | min(x) |
| `adhiktam(x)` | max(x) |
| `pariman(x)` | abs(x) |
| `gol(x)` | round(x) |
| `ghat(x, y)` | pow(x, y) |
| `naksha(f)` | map(f) |
| `chhalni(f)` | filter(f) |
| `jodna(a, b)` | zip(a, b) |
| `kholo(f, m)` | open(f, m) |
| `prakar(x)` | type(x) |
| `pehchan(x)` | id(x) |
| `bahar` | exit() |

## Try karke dekho

Examples in `examples/` folder:

```bash
python3 hinglishpy.py examples/2_calculator.hl
```

## Testing

```bash
python3 run_tests.py
```

31 tests. Full Python compatibility: match/case, f-strings, generators, async/await, exception*, walrus operator, chained assignment, tuple unpacking, starred expressions, etc.

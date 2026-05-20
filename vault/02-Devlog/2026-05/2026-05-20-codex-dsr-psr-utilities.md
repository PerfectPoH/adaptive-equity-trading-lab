# 2026-05-20 - DSR/PSR utilities

## Contesto

Dopo la implementation gate spec, il primo componente sensato era la matematica pura: PSR/DSR prima di CPCV e prima di qualunque trial.

## Cosa e' stato fatto

Creato:

```text
src/validation/deflated_sharpe.py
tests/test_deflated_sharpe.py
```

## Risultato

```text
8 passed
```

## Nota importante

La curtosi usa convenzione Pearson:

```text
normal = 3
```

Non e' stata aggiunta `scipy`; il modulo usa `statistics.NormalDist`.

## Decisione

Utility implementate ma non collegate al runner XMOM.

Blocco ancora valido:

```text
no OOS
no provider query
no sweep
no paper/live
no promotion
```

Vedi [[Report-DSR-PSR-Utilities-2026-05-20]].

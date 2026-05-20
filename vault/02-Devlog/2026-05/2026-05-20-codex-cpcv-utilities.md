# 2026-05-20 - CPCV utilities

## Contesto

Dopo DSR/PSR serviva il secondo componente matematico della implementation gate spec: CPCV con purging ed embargoing.

## Cosa e' stato fatto

Creato:

```text
src/validation/combinatorial_purged_cv.py
tests/test_combinatorial_purged_cv.py
```

## Risultato

```text
7 passed
```

## Nota importante

CPCV protegge da label-window overlap e leakage di confine.

Non corregge feature gia' costruite con dati futuri.

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

Vedi [[Report-CPCV-Utilities-2026-05-20]].

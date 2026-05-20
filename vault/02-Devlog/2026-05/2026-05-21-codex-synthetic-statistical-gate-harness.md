# 2026-05-21 - Synthetic statistical gate harness

## Contesto

Dopo DSR/PSR, CPCV e `N_eff`, serviva un banco prova sintetico per verificare che i tre componenti comunichino.

## Cosa e' stato fatto

Creato:

```text
src/validation/statistical_gate_harness.py
tests/test_statistical_gate_harness.py
```

## Risultato

```text
4 passed
```

## Decisione

Il test integrato seleziona il miglior trial da rumore correlato e pretende che il DSR lo rigetti.

Blocco ancora valido:

```text
no OOS
no provider query
no sweep
no paper/live
no promotion
```

Vedi [[Report-Synthetic-Statistical-Gate-Harness-2026-05-21]].

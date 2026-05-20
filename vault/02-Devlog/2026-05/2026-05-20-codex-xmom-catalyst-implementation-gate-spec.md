# 2026-05-20 - XMOM catalyst implementation gate spec

## Contesto

Dopo la review teorica su catalyst lag, volume decay e price digestion, serviva un gate che definisse come trasformare le soglie candidate in parametri senza guardare il PnL OOS.

## Cosa e' stato fatto

Creata la spec:

```text
experiments/provider_aware_research/xmom_catalyst_implementation_gate_spec_20260520
```

Implementato validator:

```text
src/experiments/xmom_catalyst_implementation_gate_validator.py
tests/test_xmom_catalyst_implementation_gate_validator.py
```

## Risultato

```text
IMPLEMENTATION_GATE_SPEC_PASS
passed: 47
failed: 0
```

Test mirati:

```text
5 passed
```

## Decisione

La spec e' valida ma non eseguibile.

Il prossimo lavoro ammesso e' implementare componenti riusabili e testabili:

```text
DSR/PSR utilities
CPCV split utilities
effective trial-count estimator
```

Blocco ancora valido:

```text
no OOS
no provider query
no sweep
no paper/live
no promotion
```

Vedi [[Report-XMOM-Catalyst-Implementation-Gate-Spec-2026-05-20]].

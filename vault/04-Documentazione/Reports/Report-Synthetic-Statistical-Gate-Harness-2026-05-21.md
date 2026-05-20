---
tipo: synthetic-statistical-gate-harness
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: IMPLEMENTED_TESTED_SYNTHETIC_ONLY
---

# Report Synthetic Statistical Gate Harness - 2026-05-21

## Scope

Implemented a synthetic-only integration harness connecting:

```text
CPCV
effective trial count
DSR/PSR
```

No OOS execution, provider query, parameter sweep, paper trading, live trading or strategy promotion was performed.

## Files

```text
src/validation/statistical_gate_harness.py
tests/test_statistical_gate_harness.py
```

## Purpose

The harness tests the anti-illusion path:

```text
generate correlated random trial returns
select the best Sharpe from noise
estimate N_eff
apply DSR
expect kill switch / rejection
```

The expected success condition is failure of the fake strategy:

```text
DSR < 0.95
passed = false
```

## Validated

Targeted tests verify:

- best random trial can show positive Sharpe;
- DSR still rejects the selected noise winner;
- CPCV generates splits and removes purged/embargoed rows;
- higher common-factor correlation lowers `N_eff`;
- bad synthetic config fails.

Targeted result:

```text
4 passed
```

## Decision

The statistical gate components now communicate in a synthetic harness.

They are still not connected to:

```text
TRIAL-XMOM-CATALYST-001
provider data
OOS windows
paper/live execution
```

Next allowed work:

```text
build a manifest-only gate that requires this harness before any implementation manifest can be signed
```

Still blocked:

```text
OOS execution
provider query
parameter sweep
paper/live
strategy promotion
```

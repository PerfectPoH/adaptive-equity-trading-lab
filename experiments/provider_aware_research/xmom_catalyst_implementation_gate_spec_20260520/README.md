# XMOM Catalyst Implementation Gate Spec - 2026-05-20

Status:

```text
SPEC_ONLY_NOT_EXECUTABLE
```

This package defines the implementation gate required before `TRIAL-XMOM-CATALYST-001` can become executable.

Gate id:

```text
IMPL-GATE-XMOM-CATALYST-001
```

It does not authorize:

```text
OOS execution
provider query
parameter sweep
paper trading
live trading
strategy promotion
```

## Purpose

The gate separates two research phases:

1. `PHASE_1_FEATURE_DISCOVERY`
   - in-sample only;
   - blind to asset returns and PnL;
   - thresholds selected from feature distributions only;
   - CPCV, purging and embargo required;
   - trial accounting required.

2. `PHASE_2_FINAL_PASS`
   - one locked OOS pass only;
   - no second pass after failure;
   - DSR kill switch required;
   - promotion blocked unless all robustness gates pass.

## Core Rule

```text
No threshold becomes executable until it is selected from a documented in-sample feature distribution and frozen in a manifest before OOS access.
```

See `implementation_gate_spec.md` for the full contract.

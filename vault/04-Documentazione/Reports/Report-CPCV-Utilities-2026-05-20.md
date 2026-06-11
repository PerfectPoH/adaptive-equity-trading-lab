---
tipo: cpcv-utilities
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: IMPLEMENTED_TESTED_NOT_CONNECTED_TO_TRIAL
---

# Report CPCV Utilities - 2026-05-20

## Scope

Implemented reusable Combinatorial Purged Cross-Validation utilities required by `IMPL-GATE-XMOM-CATALYST-001`.

No OOS execution, provider query, parameter sweep, paper trading, live trading or strategy promotion was performed.

## Files

```text
src/validation/combinatorial_purged_cv.py
tests/test_combinatorial_purged_cv.py
```

## Implemented

```text
CPCVConfig
CPCVSplit
combinatorial_purged_cv_splits
expected_cpcv_split_count
assert_no_label_overlap
```

## Validated

Targeted tests verify:

- binomial split count;
- all combinations of test groups are generated;
- train/test indices are disjoint;
- train label windows overlapping test windows are purged;
- embargo removes training rows immediately after test blocks;
- invalid configs fail;
- missing label interval columns fail.

Targeted result:

```text
7 passed
```

## Important Caveat

CPCV protects against label-window overlap and temporal boundary leakage.

It does not sanitize a feature that was already built with future data.

That means this remains a separate invariant:

```text
feature engineering must be point-in-time before CPCV sees the frame
```

The extreme "future feature" failure mode should be caught by feature-pipeline tests, not by CPCV.

## Decision

CPCV utilities are implemented and tested, but not connected to any trial runner.

Next allowed work:

```text
implement effective trial-count estimator
```

Still blocked:

```text
OOS execution
provider query
parameter sweep
paper/live
strategy promotion
```


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].

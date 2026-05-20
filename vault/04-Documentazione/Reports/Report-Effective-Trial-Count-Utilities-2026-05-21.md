---
tipo: effective-trial-count-utilities
progetto: adaptive-equity-trading-lab
data: 2026-05-21
status: IMPLEMENTED_TESTED_NOT_CONNECTED_TO_TRIAL
---

# Report Effective Trial Count Utilities - 2026-05-21

## Scope

Implemented the effective trial-count estimator required by `IMPL-GATE-XMOM-CATALYST-001`.

No OOS execution, provider query, parameter sweep, paper trading, live trading or strategy promotion was performed.

## Files

```text
src/validation/effective_trial_count.py
tests/test_effective_trial_count.py
```

## Implemented

```text
EffectiveTrialCountResult
effective_trial_count_from_returns
effective_trial_count_from_correlation
```

Primary method:

```text
participation_ratio over correlation eigenvalues
```

Fallback/control method:

```text
average_correlation
```

## Why Participation Ratio

The naive Kaiser rule (`eigenvalue > 1`) is not suitable as the primary estimator here because an identity correlation matrix has eigenvalues exactly equal to 1 and would not return the nominal count under a strict greater-than rule.

The participation-ratio estimator satisfies the required boundaries:

```text
identity correlation -> N_eff = N_nominal
perfect correlation -> N_eff = 1
1 <= N_eff <= N_nominal
```

## Validated

Targeted tests verify:

- identity matrix returns nominal count;
- perfectly correlated trials return one effective trial;
- result is bounded between 1 and nominal count;
- higher correlation reduces effective count;
- average-correlation fallback matches boundary cases;
- correlated trial-return vectors reduce effective count;
- constant returns, bad matrices and unknown methods fail.

Targeted result:

```text
9 passed
```

## Decision

The effective trial-count utility is implemented and tested, but not connected to the DSR gate or any trial runner.

Next allowed work:

```text
wire DSR + CPCV + effective trial-count into a dry, synthetic-only validation harness
```

Still blocked:

```text
OOS execution
provider query
parameter sweep
paper/live
strategy promotion
```

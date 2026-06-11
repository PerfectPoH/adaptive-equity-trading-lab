---
tipo: dsr-psr-utilities
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: IMPLEMENTED_TESTED_NOT_CONNECTED_TO_TRIAL
---

# Report DSR/PSR Utilities - 2026-05-20

## Scope

Implemented the first reusable math layer required by `IMPL-GATE-XMOM-CATALYST-001`.

No OOS execution, provider query, parameter sweep, paper trading, live trading or strategy promotion was performed.

## Files

```text
src/validation/deflated_sharpe.py
tests/test_deflated_sharpe.py
```

## Implemented

```text
return_moments
sample_sharpe_ratio
probabilistic_sharpe_ratio
expected_maximum_sharpe_ratio
deflated_sharpe_ratio
deflated_sharpe_ratio_from_returns
```

The module uses `statistics.NormalDist` from the Python standard library for normal CDF and inverse CDF. No new dependency was introduced.

## Important Convention

`kurtosis` uses Pearson convention:

```text
normal distribution kurtosis = 3
```

This is deliberate. Passing excess kurtosis as if it were Pearson kurtosis is rejected by tests.

## Test Design

The search did not identify a clean official paper table with a complete reproducible tuple:

```text
observed_sharpe, T, skewness, kurtosis, N, sharpe_std -> exact DSR
```

So the unit tests use:

- formula-derived golden values for expected maximum Sharpe;
- formula-derived golden values for PSR/DSR;
- convention tests for Pearson kurtosis;
- monotonic penalty tests for fat tails and negative skew;
- failure tests for constant returns, non-finite inputs and invalid kurtosis.

Targeted result:

```text
8 passed
```

## Sources Checked

- Bailey and Lopez de Prado, "The Deflated Sharpe Ratio": https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- Bailey and Lopez de Prado SSRN entry: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- QuantConnect PSR discussion: https://www.quantconnect.com/research/17112/probabilistic-sharpe-ratio/
- AuditZK DSR formula summary: https://www.auditzk.com/tools/deflated-sharpe-ratio

## Decision

The DSR/PSR math layer is implemented and tested, but not connected to any trial runner.

Next allowed work:

```text
implement CPCV split utilities with synthetic leakage tests
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

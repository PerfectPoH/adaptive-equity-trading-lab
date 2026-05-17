---
progetto: adaptive-equity-trading-lab
data: 2026-05-17
trial_id: TRIAL-NCTRL-001
status: PROPERTY_CHECK_PASS
scope: methodology_negative_control
---

# Report Negative Control Trial 001 Property Check Result - 2026-05-17

## Verdict

```text
TRIAL-NCTRL-001: PROPERTY_CHECK_PASS
NO STRATEGY PROMOTION
NO PAPER TRADING
NO SMALL-CAP TRIAL UNLOCK
```

This was a property-based negative control of the research machinery, not an alpha or strategy validation.

## Run identity

- `run_id`: `run_nctrl_trial_001_20260517`
- Output directory: `experiments/runs/nctrl_trial_001_2024_20260517`
- Config source: `experiments/configs/nctrl_trial_001.py`
- Frozen universe: AAPL, MSFT, NVDA, AMD, TSLA, META, AMZN, GOOGL, SPY, QQQ
- Download warmup start: `2023-01-03`
- Requested property-check window: `2024-01-02..2024-12-31`
- Manifest period representation: `2024-01-02..2024-12-27`
- `config_hash`: `732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`

The manifest end date is the actual last candidate/trading-day representation observed in the generated artifacts. The property evaluator accepts this under the preregistered allowance for actual last trading day representation.

## Summary metrics

These metrics are recorded only to support property checks, not strategy interpretation.

- `total_trades`: 32
- `total_pnl`: -629.0216482788023
- `return_pct`: -0.006290216482787936
- `ending_cash`: 99370.9783517212

## Property results

| Property | Status | Evidence | Notes |
|---|---|---|---|
| P1 | pass | artifacts=10 | End-to-end artifact presence |
| P2 | pass | trial_id=TRIAL-NCTRL-001; config_hash=732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab; period=2024-01-02..2024-12-27 | Manifest identity and frozen universe |
| P3 | pass | risk_fraction=0.01 | Risk sizing regression gate |
| P4 | pass | cash_ledger_fixture_tests_passed=True | Fixture gate before trial interpretation |
| P5 | pass | simulations=1000; base_seed=700; mean_return=0.009076682644783847; p05=0.007702037772277567; p95=0.01048954057913583 | Distribution-aware random baseline |
| P6 | pass | simulations=100; valid=100; sign_flip_excluding_top_3_frequency=0.06 | Random-entry ex-outlier sanity |
| P7 | pass | outlier arithmetic reconciles | Ex-topN arithmetic property |
| P8 | pass | missing=[]; nonfinite_with_observations=[] | Benchmark numerical sanity |

## Implementation notes

During execution, the first attempt exposed a performance issue in the P5/P6 reporting path. The fix was implemented with TDD before final reporting:

- P5 bootstrap now precomputes holding-window returns once, while preserving `N=1000` and seed policy `700..1699`.
- P6 random-entry sign-flip report is bounded to `100` simulations for this trial package; P6 preregistration required frequency reporting but did not freeze a simulation count.
- The property report can be rebuilt from existing artifacts without rerunning the trial.
- P2 accepts actual last candidate/trading-day representation when the manifest period ends before the requested calendar end.

## Governance decision

`TRIAL-NCTRL-001` passes as a methodology negative-control property check. It validates that the pipeline can generate artifacts, accounting, bootstrap baseline, random-entry diagnostics, ex-topN arithmetic checks, and benchmark sanity checks on the fixed large-cap/ETF control universe.

It does not validate any investible edge, does not reopen archived small-cap strategies, and does not authorize paper trading or production ranking.

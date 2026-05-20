---
tipo: xmom-trial-execution
progetto: adaptive-equity-trading-lab
data: 2026-05-20
status: COMPLETED
---

# Report XMOM Trial 001 Execution - 2026-05-20

## Scope

Executed the first authorized preregistered XMOM trial:

```text
TRIAL-XMOM-001
```

This was a single frozen execution. No sweep, discretionary tuning, paper trading, live trading or strategy promotion was executed.

## Run Directory

```text
experiments/runs/xmom_trial_001_20260520/
```

Main artifacts:

```text
run_manifest.json
pre_run_gate_report.json
candidate_export.csv
benchmark_report.csv
portfolio_trade_log.csv
portfolio_equity_curve.csv
portfolio_rejections.csv
portfolio_summary.csv
portfolio_outlier_breakdown.csv
small_cap_backtest_report.md
```

## Frozen Inputs

Dataset:

```text
experiments/provider_aware_research/data_inputs/databento_xmom_20260520/
```

Preregistration:

```text
experiments/provider_aware_research/xmom_preregistered_research_plan_20260520/
```

Universe:

```text
AEHR
ARRY
CABA
CRMD
IOVA
IWM benchmark/proxy
```

Trial accounting:

```text
trial_id: TRIAL-XMOM-001
preregistration_id: PREREG-XMOM-001
trial_family: new_signal_research
trial_number: 6
```

## Gate Results

Data ingestion gate before execution:

```text
DATA_INPUT_VALIDATION_PASS
```

Pre-run gate before execution:

```text
PASS_READY_TO_EXECUTE
```

Post-run validation gate after execution:

```text
POST_RUN_VALIDATION_PASS
passed: 28
failed: 0
```

Run artifact validator:

```text
passed: 18
failed: 0
```

## Result

Portfolio summary:

```text
initial_cash: 100000.00
ending_cash: 209363.25
total_pnl: 109363.25
return_pct: 109.36%
total_trades: 11
total_rejections: 0
```

Benchmark comparison:

```text
IWM matching holding-window return: 1.70%
excess_return_vs_iwm_net_of_costs: 107.66%
```

Primary preregistered metric:

```text
positive
```

## Outlier Diagnostics

The result is not robust enough for promotion:

```text
outlier_concentration_alert: true
top_1_pnl_contribution_pct: 60.95%
top_3_pnl_contribution_pct: 145.80%
pnl_excluding_top_3: -50085.32
sign_flip_excluding_top_3: true
portfolio_return_excluding_top_3: -50.09%
```

Interpretation:

```text
Primary metric passed, but outlier stress blocks strategy promotion.
```

## Decision

```text
NO PAPER TRADING
NO LIVE TRADING
NO STRATEGY PROMOTION
NO PARAMETER TUNING OFF THIS RESULT
```

The trial is informationally valuable because the governance chain worked end-to-end and the primary metric was positive. It is not sufficient evidence of a stable edge because the portfolio flips negative after removing the top three winners.

## Ledger Update

The trial ledger now contains the completed execution row:

```text
TRIAL-XMOM-001 ... completed ... pending_interpretation ... xmom_trial_001_executed_once_primary_positive_outlier_stress_blocks_promotion
```

## Next Allowed Work

Allowed:

- independent interpretation report;
- robustness diagnostics that do not change the frozen strategy;
- methodology notes on outlier concentration and sample size;
- possible future preregistration of a separate robustness/replication trial.

Blocked:

- paper trading;
- live trading;
- promoting XMOM as a validated strategy;
- adding filters after seeing this result and treating them as part of `TRIAL-XMOM-001`.

See also [[Report-XMOM-Real-Data-Ingestion-2026-05-20]], [[Report-Post-Run-Validation-Gate-2026-05-20]], [[Project-Handoff]].

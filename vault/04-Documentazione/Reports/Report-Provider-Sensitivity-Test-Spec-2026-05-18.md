# Report - Provider Sensitivity Test Spec - 2026-05-18

## Status

```text
PROVIDER_SENSITIVITY_TEST_SPEC_CREATED
SPEC_ONLY_NOT_EXECUTED
NO_BACKTEST
NO_OOS
NO_PARAMETER_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_TRADING
NO_LIVE_TRADING
```

## Question

The permitted research question is:

```text
Are old yfinance-based strategy outputs materially sensitive to provider data differences?
```

The forbidden question is:

```text
Does the old strategy work?
```

## Old strategy reference

```text
setup: breakout_continuation
feature filter: open_to_close_return >= 0.10
regime filter: IWM close > EMA200
sizing: corrected risk_fraction sizing
```

Reference yfinance-era runs:

```text
experiments/runs/small_cap_multiyear_open_to_close_010_iwm_ema200_2022_2024_risk_sizing_20260512
experiments/runs/small_cap_oos_open_to_close_010_iwm_ema200_2025_full_risk_sizing_20260512
```

## Current provider constraint

Databento Historical + Polygon Free is approved only for metadata/data-quality work.

```text
provider_join_status: JOIN_FEASIBLE_FOR_DATA_QUALITY_METADATA_ONLY
performance_dataset_status: NOT_APPROVED
```

Therefore this test cannot execute as a strategy backtest. It can only be prepared as a provider-sensitivity comparison.

## Required stages before any execution

```text
P1_OVERLAP_SELECTION
P2_REDACTED_QUERY_PLAN
P3_COST_AND_RATE_LIMIT_CHECK
P4_USER_CONFIRMATION
```

Only after those stages may a tiny provider query be considered, and even then the output must be classified as data sensitivity, not performance.

## Allowed metrics

```text
symbol/date availability delta
OHLCV field presence delta
same-day open/high/low/close/volume delta
signal feature delta
return calculation delta for already-selected historical trades
corporate-action/dropout classification
```

## Disallowed metrics

```text
new total portfolio PnL
new win rate as strategy evidence
new Sharpe/Sortino/performance ranking
parameter sweep
new universe screening
ALL_SYMBOLS query
strategy promotion
```

## Current readiness verdict

```text
NOT_READY_TO_EXECUTE_PROVIDER_SENSITIVITY_TEST
READY_TO_PREPARE_OVERLAP_SELECTION_AND_QUERY_PLAN
```

## Next autonomous-safe step

Prepare a deterministic overlap-selection artifact from existing old run artifacts only. No provider API calls are needed for that step.

## Preparation update

A deterministic overlap selection and redacted query plan were prepared from existing local yfinance-era run artifacts only.

```text
overlap_selection_candidates: 5 maximum
selection_rule: largest_loss; largest_win; earliest; latest; median_abs_pnl; deduplicated
redacted_query_plan_rows: Databento OHLCV daily + optional Polygon ticker details per selected candidate
provider_query_executed: no
```

Updated readiness:

```text
READY_FOR_USER_REVIEW_BEFORE_EXECUTION
NOT_READY_TO_EXECUTE_WITHOUT_REVIEW
```
